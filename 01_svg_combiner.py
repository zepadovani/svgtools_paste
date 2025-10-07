import xml.etree.ElementTree as ET
import copy
import os

# --- Configuração Global de Namespaces ---
# Registra os namespaces que serão usados ao escrever o arquivo SVG final.
# Isso garante que o arquivo de saída tenha os prefixos corretos (ex: <svg>, <sodipodi:namedview>).
ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

def get_svg_metadata(svg_path):
    """
    Analisa um arquivo SVG e extrai metadados essenciais para o dimensionamento.

    Retorna um dicionário contendo:
    - A árvore XML e o elemento raiz.
    - O namespace principal do SVG.
    - A largura física em mm.
    - A largura do viewBox em unidades internas.
    - A proporção calculada de "unidades por milímetro".
    """
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Erro de parse no arquivo '{svg_path}': {e}")

    # Extrai o namespace da tag raiz (ex: {http://www.w3.org/2000/svg})
    namespace = root.tag.split('}')[0][1:] if '}' in root.tag else ''

    # Pega os atributos de dimensão e viewBox
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
        
    # Calcula a proporção fundamental: quantas unidades internas cabem em 1mm.
    units_per_mm = viewbox_width / physical_width_mm
    
    print(f"Analisando '{svg_path}': {units_per_mm:.4f} unidades de viewBox / mm")
    
    return {
        'tree': tree,
        'root': root,
        'namespace': namespace,
        'units_per_mm': units_per_mm
    }

def combine_svgs(container_path, source_path, output_path, group_id, x_mm, y_mm):
    """
    Combina dois SVGs, colando um grupo do SVG de origem no de destino,
    preservando as dimensões físicas através de um fator de escala.
    """
    # 1. Extrai os metadados e a proporção "unidades/mm" de cada SVG.
    container_meta = get_svg_metadata(container_path)
    source_meta = get_svg_metadata(source_path)

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 2. Encontra o grupo a ser copiado no SVG de origem.
    ns = {'svg': source_meta['namespace']}
    group_to_copy = source_meta['root'].find(f".//svg:g[@id='{group_id}']", ns)
    
    if group_to_copy is None:
        raise ValueError(f"Grupo com id='{group_id}' não encontrado em '{source_path}'.")

    # 3. Calcula o fator de escala para a conversão de coordenadas.
    # Para o conteúdo da origem ter o mesmo tamanho no destino, precisamos
    # converter suas unidades internas para as unidades do novo ambiente.
    scale_factor = source_meta['units_per_mm'] / container_meta['units_per_mm']
    print(f"Fator de escala calculado: {scale_factor:.4f}")
    
    # 4. Converte a posição de colagem (em mm) para as unidades do viewBox do container.
    x_pos_units = x_mm * container_meta['units_per_mm']
    y_pos_units = y_mm * container_meta['units_per_mm']

    # 5. Cria um grupo "wrapper" para aplicar o posicionamento e a escala.
    # A transformação é aplicada ao grupo todo, de uma só vez.
    wrapper_group = ET.Element('g', {
        'id': f'wrapper_for_{group_id}',
        'transform': f'translate({x_pos_units} {y_pos_units}) scale({scale_factor})'
    })
    
    # 6. Copia todos os elementos de dentro do grupo original para o wrapper.
    for element in group_to_copy:
        wrapper_group.append(copy.deepcopy(element))
        
    # 7. Adiciona o grupo wrapper ao SVG do container.
    container_meta['root'].append(wrapper_group)
    
    # 8. Salva o resultado.
    container_meta['tree'].write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSucesso! O grupo '{group_id}' foi colado em '{output_path}'.")

if __name__ == "__main__":
    try:
        combine_svgs(
            container_path='container.svg',
            source_path='topaste.svg',
            output_path='out/combined1.svg',
            group_id='gesture_paths',
            x_mm=0,  # Posição X em mm no destino
            y_mm=0   # Posição Y em mm no destino
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"\nERRO: {e}")
