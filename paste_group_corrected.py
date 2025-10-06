import xml.etree.ElementTree as ET

def get_svg_info(svg_path):
    """Extrai informações de viewBox e dimensões de um arquivo SVG."""
    # ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    viewbox_str = root.get('viewBox')
    width_str = root.get('width')
    
    if not viewbox_str or not width_str:
        raise ValueError(f"SVG {svg_path} não tem viewBox ou width definido.")

    viewbox = [float(v) for v in viewbox_str.split()]
    
    width_val = float(width_str.replace('mm', ''))
    
    # Calcula a proporção de unidades do viewBox por mm
    ratio = viewbox[2] / width_val
    
    return {'root': root, 'viewbox': viewbox, 'ratio': ratio, 'tree': tree}

def paste_group_with_scaling(container_path, to_paste_path, output_path, group_id, x_mm, y_mm):
    """
    Copia um grupo de um SVG para outro, aplicando a escala correta para
    manter as dimensões em mm.
    """
    # Registra namespaces para a saída
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

    # Carrega os SVGs
    container_info = get_svg_info(container_path)
    to_paste_info = get_svg_info(to_paste_path)
    
    # Encontra o grupo a ser copiado
    # O namespace é necessário para o find
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    group_to_paste = to_paste_info['root'].find(f".//svg:g[@id='{group_id}']", ns)
    
    if group_to_paste is None:
        raise ValueError(f"Grupo com id '{group_id}' não encontrado em {to_paste_path}")

    # Calcula o fator de escala
    # scale_factor = (ratio_paste / ratio_container)
    scale_factor = to_paste_info['ratio'] / container_info['ratio']
    
    # Converte o posicionamento em mm para as unidades do viewBox do container
    x_pos_units = x_mm * container_info['ratio']
    y_pos_units = y_mm * container_info['ratio']

    # Cria o grupo que vai receber o conteúdo e aplicar as transformações
    wrapper_group = ET.Element('g', {
        'transform': f'translate({x_pos_units} {y_pos_units}) scale({scale_factor})'
    })
    
    # Copia os filhos do grupo original para o novo grupo
    # É crucial clonar os elementos para não movê-los da árvore original
    for element in group_to_paste:
        wrapper_group.append(element)
        
    # Adiciona o novo grupo ao SVG container
    container_root = container_info['root']
    container_root.append(wrapper_group)
    
    # Salva o resultado
    tree = container_info['tree']
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"Grupo '{group_id}' colado com sucesso em '{output_path}'.")
    print(f"Fator de escala aplicado: {scale_factor}")


if __name__ == "__main__":
    paste_group_with_scaling(
        container_path='container.svg',
        to_paste_path='topaste.svg',
        output_path='container_plus_paste.svg',
        group_id='g99',
        x_mm=0,
        y_mm=0
    )
