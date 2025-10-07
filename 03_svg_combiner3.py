import xml.etree.ElementTree as ET
import copy
import os

# --- Configuração Global de Namespaces ---
ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

def get_svg_metadata(svg_path):
    # ... (código da função get_svg_metadata permanece o mesmo) ...
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Erro de parse no arquivo '{svg_path}': {e}")

    namespace = root.tag.split('}')[0][1:] if '}' in root.tag else ''
    width_str = root.get('width')
    viewbox_str = root.get('viewBox')
    
    if not width_str or not viewbox_str:
        raise ValueError(f"O SVG '{svg_path}' deve ter os atributos 'width' e 'viewBox'.")

    if 'mm' not in width_str:
        raise ValueError(f"A largura (width) do SVG '{svg_path}' deve ser em 'mm'.")
    
    physical_width_mm = float(width_str.replace('mm', ''))
    viewbox_width = float(viewbox_str.split()[2])
    
    if physical_width_mm == 0:
        raise ValueError(f"A largura física do SVG '{svg_path}' não pode ser zero.")
        
    units_per_mm = viewbox_width / physical_width_mm
    
    print(f"Analisando '{os.path.basename(svg_path)}': {units_per_mm:.4f} unidades de viewBox / mm")
    
    return {
        'tree': tree,
        'root': root,
        'namespace': namespace,
        'units_per_mm': units_per_mm
    }

def combine_all_elements(container_path, source_path, output_path, x_mm, y_mm):
    """
    Combina SVGs, colando TODOS os elementos desenháveis de primeiro nível 
    do SVG de origem no de destino, preservando as dimensões físicas.
    """
    # 1. Extrai os metadados de cada SVG.
    container_meta = get_svg_metadata(container_path)
    source_meta = get_svg_metadata(source_path)
    
    # 2. Calcula o fator de escala único para todos os elementos.
    scale_factor = source_meta['units_per_mm'] / container_meta['units_per_mm']
    print(f"Fator de escala calculado para todos os elementos: {scale_factor:.4f}")
    
    # 3. Converte a posição de colagem (em mm) para as unidades do container.
    x_pos_units = x_mm * container_meta['units_per_mm']
    y_pos_units = y_mm * container_meta['units_per_mm']

    # 4. Cria um único grupo "wrapper" que aplicará a transformação a todos os elementos.
    wrapper_group = ET.Element('g', {
        'id': f'wrapper_for_{os.path.basename(source_path).replace(".", "_")}',
        'transform': f'translate({x_pos_units} {y_pos_units}) scale({scale_factor})'
    })

    # 5. Itera sobre todos os filhos diretos da raiz do SVG de origem.
    elements_copied_count = 0
    # Tags que não representam elementos visuais e devem ser ignoradas.
    # Adicionamos os namespaces do inkscape/sodipodi aqui também.
    tags_to_ignore = ['defs', 'style', 'metadata', 'namedview']

    for element in source_meta['root']:
        # Extrai o nome da tag sem o namespace (ex: 'g' ou 'namedview')
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag_name not in tags_to_ignore:
            print(f"Copiando elemento: <{tag_name}> com id '{element.get('id', 'N/A')}'...")
            wrapper_group.append(copy.deepcopy(element))
            elements_copied_count += 1

    if elements_copied_count == 0:
        raise ValueError(f"Nenhum elemento desenhável (como <g>, <path>, <rect>) foi encontrado em '{source_path}'.")

    # 6. Adiciona o grupo wrapper (com todos os elementos dentro) ao SVG do container.
    container_meta['root'].append(wrapper_group)
    
    # 7. Salva o resultado.
    container_meta['tree'].write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSucesso! {elements_copied_count} elementos foram colados em '{output_path}'.")

if __name__ == "__main__":
    try:
        combine_all_elements(
            container_path='container3.svg',
            source_path='topaste3.svg',
            output_path='out/combined3.svg',
            x_mm=0,
            y_mm=0
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"\nERRO: {e}")
