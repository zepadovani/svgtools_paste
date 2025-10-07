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

def build_transform_string(transformations, scale_factor, units_per_mm):
    """
    Constrói a string de transformação a partir de uma lista de dicionários.
    Aplica a escala de preservação de dimensão primeiro.
    """
    # A escala para manter a dimensão é sempre a primeira.
    transform_parts = [f"scale({scale_factor})"]

    for transform in transformations:
        t_type = transform.get('type')
        t_value = transform.get('value')

        if t_type == 'translate':
            # Converte o translate de mm para as unidades do viewBox do container
            x_units = t_value[0] * units_per_mm
            y_units = t_value[1] * units_per_mm
            transform_parts.append(f"translate({x_units} {y_units})")
        elif t_type == 'scale':
            # Permite uma escala adicional
            transform_parts.append(f"scale({t_value})")
        elif t_type == 'rotate':
            transform_parts.append(f"rotate({t_value})")
        # Adicionar outros tipos de transformação aqui (ex: skewX, skewY)
        
    return " ".join(transform_parts)

def combine_all_elements_v4(container_path, source_path, output_path, transformations=None):
    """
    Combina SVGs, colando todos os elementos desenháveis do SVG de origem
    no de destino e aplicando uma lista de transformações.
    """
    if transformations is None:
        transformations = []

    # 1. Extrai os metadados de cada SVG.
    container_meta = get_svg_metadata(container_path)
    source_meta = get_svg_metadata(source_path)
    
    # 2. Calcula o fator de escala para preservar as dimensões.
    dimension_scale_factor = source_meta['units_per_mm'] / container_meta['units_per_mm']
    print(f"Fator de escala para preservação de dimensão: {dimension_scale_factor:.4f}")
    
    # 3. Constrói a string de transformação final.
    transform_string = build_transform_string(
        transformations,
        dimension_scale_factor,
        container_meta['units_per_mm']
    )
    print(f"String de transformação final: '{transform_string}'")

    # 4. Define a ID do grupo wrapper com base no nome do arquivo de origem.
    source_prefix = os.path.basename(source_path).replace('.svg', '')
    wrapper_id = source_prefix

    # 5. Cria o grupo "wrapper" que aplicará a transformação.
    wrapper_group = ET.Element('g', {
        'id': wrapper_id,
        'transform': transform_string
    })

    # 6. Itera sobre todos os elementos desenháveis e os copia para o wrapper.
    elements_copied_count = 0
    tags_to_ignore = ['defs', 'style', 'metadata', 'namedview']

    for element in source_meta['root']:
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        if tag_name not in tags_to_ignore:
            wrapper_group.append(copy.deepcopy(element))
            elements_copied_count += 1

    if elements_copied_count == 0:
        raise ValueError(f"Nenhum elemento desenhável encontrado em '{source_path}'.")

    # 7. Adiciona o grupo wrapper ao SVG do container.
    container_meta['root'].append(wrapper_group)
    
    # 8. Salva o resultado.
    container_meta['tree'].write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSucesso! {elements_copied_count} elementos de '{source_path}' foram colados em '{output_path}' com a ID de grupo '{wrapper_id}'.")

if __name__ == "__main__":
    try:
        # Define a lista de transformações a serem aplicadas.
        # A ordem importa: serão aplicadas na sequência definida.
        # A escala de preservação de dimensão é sempre aplicada primeiro.
        transforms = [
            {'type': 'translate', 'value': [10, 5]},  # Mover 10mm para a direita e 5mm para baixo
            {'type': 'scale', 'value': 3},          # Reduzir pela metade (além da escala de preservação)
            {'type': 'rotate', 'value': 45}           # Rotacionar 45 graus
        ]

        combine_all_elements_v4(
            container_path='container3.svg',
            source_path='topaste3.svg',
            output_path='out/combined4.svg',
            transformations=transforms
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"\nERRO: {e}")
