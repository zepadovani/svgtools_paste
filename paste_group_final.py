import xml.etree.ElementTree as ET
import copy

def get_svg_info(svg_path):
    """
    Extrai informações de viewBox, dimensões, a proporção de unidades por mm e o namespace.
    """
    try:
        # Parse o arquivo para obter a árvore e a raiz
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Erro ao fazer o parse do SVG '{svg_path}': {e}")

    # Extrai o namespace da tag raiz, ex: {http://www.w3.org/2000/svg}
    namespace = ''
    if '}' in root.tag:
        namespace = root.tag.split('}')[0][1:]

    viewbox_str = root.get('viewBox')
    width_str = root.get('width')
    
    if not viewbox_str or not width_str:
        raise ValueError(f"O SVG '{svg_path}' precisa ter os atributos 'viewBox' e 'width' definidos.")

    viewbox = [float(v) for v in viewbox_str.split()]
    
    if 'mm' not in width_str:
        raise ValueError(f"A largura (width) do SVG '{svg_path}' deve estar em 'mm'.")
    width_val = float(width_str.replace('mm', ''))
    
    if width_val == 0:
        raise ValueError(f"A largura (width) do SVG '{svg_path}' não pode ser zero.")
        
    ratio = viewbox[2] / width_val
    
    return {'root': root, 'tree': tree, 'viewbox': viewbox, 'ratio': ratio, 'namespace': namespace}

def paste_group_with_correct_scaling(container_path, to_paste_path, output_path, group_id, x_mm, y_mm):
    """
    Copia um grupo de um SVG para outro, aplicando a escala correta para
    manter as dimensões em mm.
    """
    # Registra namespaces para a serialização (escrita do arquivo)
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

    container_info = get_svg_info(container_path)
    to_paste_info = get_svg_info(to_paste_path)
    
    # Usa o namespace extraído dinamicamente para a busca
    ns = {'svg': to_paste_info['namespace']}
    
    xpath_query = f".//svg:g[@id='{group_id}']"
    group_to_paste = to_paste_info['root'].find(xpath_query, ns)
    
    if group_to_paste is None:
        raise ValueError(f"Não foi possível encontrar o grupo com id='{group_id}' em '{to_paste_path}'. Verifique o ID e o namespace do arquivo.")

    scale_factor = to_paste_info['ratio'] / container_info['ratio']
    
    x_pos_units = x_mm * container_info['ratio']
    y_pos_units = y_mm * container_info['ratio']

    wrapper_group = ET.Element('g', {
        'id': f'wrapper_{group_id}',
        'transform': f'translate({x_pos_units} {y_pos_units}) scale({scale_factor})'
    })
    
    for element in group_to_paste:
        wrapper_group.append(copy.deepcopy(element))
        
    container_root = container_info['root']
    container_root.append(wrapper_group)
    
    tree = container_info['tree']
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"Grupo '{group_id}' colado com sucesso em '{output_path}'.")
    print(f"Fator de escala aplicado para manter as dimensões: {scale_factor:.4f}")

if __name__ == "__main__":
    try:
        paste_group_with_correct_scaling(
            container_path='container.svg',
            to_paste_path='topaste.svg',
            output_path='container_plus_paste.svg',
            group_id='gesture_paths',
            x_mm=0,
            y_mm=0
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Erro: {e}")
