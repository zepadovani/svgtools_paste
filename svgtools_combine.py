
import xml.etree.ElementTree as ET
import copy
import os

# --- Global Namespace Configuration ---
ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

def _get_svg_metadata(svg_path):
    """
    Parses an SVG file and extracts essential metadata for scaling.
    Internal helper function.
    """
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Parse error in file '{svg_path}': {e}")

    width_str = root.get('width')
    viewbox_str = root.get('viewBox')
    
    if not width_str or not viewbox_str:
        raise ValueError(f"The SVG '{svg_path}' must have 'width' and 'viewBox' attributes.")

    if 'mm' not in width_str:
        raise ValueError(f"The width of SVG '{svg_path}' must be in 'mm'.")
    
    physical_width_mm = float(width_str.replace('mm', ''))
    viewbox_width = float(viewbox_str.split()[2])
    
    if physical_width_mm == 0:
        raise ValueError(f"The physical width of SVG '{svg_path}' cannot be zero.")
        
    units_per_mm = viewbox_width / physical_width_mm
    
    print(f"Analyzing '{os.path.basename(svg_path)}': {units_per_mm:.4f} viewBox units / mm")
    
    return {
        'tree': tree,
        'root': root,
        'units_per_mm': units_per_mm
    }

def _build_transform_string(transformations, scale_factor, container_units_per_mm):
    """
    Builds the transform string from a list of transformation dictionaries.
    The dimension-preserving scale is always applied first.
    Internal helper function.
    """
    # The scale to maintain dimensions is always the first transformation.
    transform_parts = [f"scale({scale_factor})"]

    for transform in transformations:
        t_type = transform.get('type')
        t_value = transform.get('value')

        if t_type == 'translate':
            # Convert translation from mm to the container's viewBox units
            x_units = t_value[0] * container_units_per_mm
            y_units = t_value[1] * container_units_per_mm
            transform_parts.append(f"translate({x_units} {y_units})")
        elif t_type == 'scale':
            # Allow for additional scaling
            transform_parts.append(f"scale({t_value})")
        elif t_type == 'rotate':
            transform_parts.append(f"rotate({t_value})")
        # Other transform types (e.g., skewX, skewY) could be added here
        
    return " ".join(transform_parts)

def combinesvg(container_path, source_path, output_path, transformations=None):
    """
    Pastes all drawable elements from a source SVG into a container SVG, preserving the 
    physical dimensions of the pasted content and grouping them.

    This function addresses a common problem in SVG manipulation where simply copying
    elements from one file to another leads to incorrect scaling. SVGs define a
    relationship between a physical dimension (e.g., width in 'mm') and an internal
    coordinate system ('viewBox'). This relationship can differ between SVGs.

    The core logic is as follows:
    1.  Calculate a 'units_per_mm' ratio for both the container and source SVGs.
        This ratio is `viewBox_width / physical_width_mm`.
    2.  Determine a `dimension_scale_factor` by dividing the source's ratio by the
        container's ratio (`source_units_per_mm / container_units_per_mm`).
    3.  Create a wrapper group ('<g>') element in the container SVG.
    4.  Apply a 'transform' attribute to this group. The first transformation is always
        `scale(dimension_scale_factor)` to ensure the pasted content retains its
        original physical size in the new coordinate system.
    5.  Additional user-defined transformations (translate, scale, rotate) are
        appended to the transform string. Translations in 'mm' are correctly
        converted to the container's viewBox units.
    6.  All drawable elements from the source SVG (paths, rects, groups, etc.,
        ignoring metadata) are deep-copied into this wrapper group.
    7.  The final modified container SVG is saved to the specified output path.

    Args:
        container_path (str): Path to the destination SVG file.
        source_path (str): Path to the source SVG file to be pasted.
        output_path (str): Path to save the combined SVG file.
        transformations (list, optional): A list of dictionaries, each specifying a
            transformation to apply. Defaults to None.
            Example: [{'type': 'translate', 'value': [10, 5]}, # in mm
                      {'type': 'scale', 'value': 0.5},
                      {'type': 'rotate', 'value': 45}]
    """
    if transformations is None:
        transformations = []

    # 1. Extract metadata from each SVG.
    container_meta = _get_svg_metadata(container_path)
    source_meta = _get_svg_metadata(source_path)
    
    # 2. Calculate the scale factor to preserve dimensions.
    dimension_scale_factor = source_meta['units_per_mm'] / container_meta['units_per_mm']
    print(f"Dimension preservation scale factor: {dimension_scale_factor:.4f}")
    
    # 3. Build the final transform string.
    transform_string = _build_transform_string(
        transformations,
        dimension_scale_factor,
        container_meta['units_per_mm']
    )
    print(f"Final transform string: '{transform_string}'")

    # 4. Define the wrapper group ID based on the source filename.
    source_prefix = os.path.basename(source_path).replace('.svg', '')
    wrapper_id = source_prefix

    # 5. Create the wrapper group that will apply the transformation.
    wrapper_group = ET.Element('g', {
        'id': wrapper_id,
        'transform': transform_string
    })

    # 6. Iterate over all drawable elements and copy them into the wrapper.
    elements_copied_count = 0
    tags_to_ignore = ['defs', 'style', 'metadata', 'namedview', 'sodipodi:namedview']

    for element in source_meta['root']:
        # Normalize tag name to remove namespace for comparison
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        if tag_name not in tags_to_ignore:
            wrapper_group.append(copy.deepcopy(element))
            elements_copied_count += 1

    if elements_copied_count == 0:
        raise ValueError(f"No drawable elements found in '{source_path}'.")

    # 7. Add the wrapper group to the container SVG.
    container_meta['root'].append(wrapper_group)
    
    # 8. Ensure the output directory exists.
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 9. Save the result.
    container_meta['tree'].write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSuccess! {elements_copied_count} elements from '{source_path}' were pasted into '{output_path}' within the group ID '{wrapper_id}'.")
