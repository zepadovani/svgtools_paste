import xml.etree.ElementTree as ET
import copy
import os

# --- Configuração Global de Namespaces ---
ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

def get_svg_metadata(svg_path):
    """
    Analisa um arquivo SVG e extrai metadados essenciais para o dimensionamento.
    """
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

def combine_all_groups(container_path, source_path, output_path, x_mm, y_mm):
    """
    Combina SVGs, colando TODOS os grupos de primeiro nível do SVG de origem
    no de destino, preservando as dimensões físicas.
    """
    # 1. Extrai os metadados de cada SVG.
    container_meta = get_svg_metadata(container_path)
    source_meta = get_svg_metadata(source_path)
    
    # 2. Calcula o fator de escala único para todos os grupos.
    scale_factor = source_meta['units_per_mm'] / container_meta['units_per_mm']
    print(f"Fator de escala calculado para todos os grupos: {scale_factor:.4f}")
    
    # 3. Converte a posição de colagem (em mm) para as unidades do container.
    x_pos_units = x_mm * container_meta['units_per_mm']
    y_pos_units = y_mm * container_meta['units_per_mm']

    # 4. Encontra todos os grupos de primeiro nível no SVG de origem.
    # A busca é por '{namespace}g' para encontrar tags <g> no namespace correto.
    ns_tag = f"{{{source_meta['namespace']}}}g"
    top_level_groups = source_meta['root'].findall(ns_tag)

    if not top_level_groups:
        raise ValueError(f"Nenhum grupo ('<g>') de primeiro nível encontrado em '{source_path}'.")

    print(f"Encontrados {len(top_level_groups)} grupos para processar.")

    # 5. Itera sobre cada grupo encontrado.
    for i, group_to_copy in enumerate(top_level_groups):
        group_id = group_to_copy.get('id', f'grupo_importado_{i+1}')
        print(f"Processando grupo: '{group_id}'...")

        # 6. Cria um grupo "wrapper" para aplicar a transformação.
        wrapper_group = ET.Element('g', {
            'id': f'wrapper_for_{group_id}',
            'transform': f'translate({x_pos_units} {y_pos_units}) scale({scale_factor})'
        })
        
        # 7. Copia o conteúdo do grupo original para o wrapper.
        # O grupo original em si é copiado para manter sua própria 'id' e atributos.
        wrapper_group.append(copy.deepcopy(group_to_copy))
            
        # 8. Adiciona o grupo wrapper ao SVG do container.
        container_meta['root'].append(wrapper_group)
    
    # 9. Salva o resultado.
    container_meta['tree'].write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSucesso! Todos os {len(top_level_groups)} grupos foram colados em '{output_path}'.")

if __name__ == "__main__":
    try:
        combine_all_groups(
            container_path='container.svg',
            source_path='topaste3.svg',
            output_path='combined_from_topaste3.svg',
            x_mm=0,
            y_mm=0
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"\nERRO: {e}")
