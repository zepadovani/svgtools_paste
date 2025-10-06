import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Register SVG namespaces
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")

def parse_svg_size(size_value):
    """Extract numeric value and unit from SVG size attribute"""
    if size_value is None:
        return None, None
    
    # Extract unit and value
    if size_value.endswith('mm'):
        return float(size_value[:-2]), 'mm'
    elif size_value.endswith('cm'):
        return float(size_value[:-2]) * 10, 'mm'  # Convert to mm
    elif size_value.endswith('pt'):
        return float(size_value[:-2]) * 0.352778, 'mm'  # Convert to mm
    elif size_value.endswith('px'):
        return float(size_value[:-2]) * 0.264583, 'mm'  # Convert to mm
    else:
        # No unit, assume raw value
        return float(size_value), None

def get_svg_dimensions(svg_file):
    """Get the exact dimensions of an SVG file with unit preservation"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # Extract width, height, and viewBox
    width_attr = root.get('width')
    height_attr = root.get('height')
    viewbox_attr = root.get('viewBox')
    
    # Parse dimensions
    width_value, width_unit = parse_svg_size(width_attr)
    height_value, height_unit = parse_svg_size(height_attr)
    
    # Parse viewBox
    viewbox = None
    if viewbox_attr:
        parts = viewbox_attr.strip().split()
        if len(parts) == 4:
            viewbox = tuple(float(part) for part in parts)
    
    return {
        'width_value': width_value,
        'width_unit': width_unit,
        'height_value': height_value,
        'height_unit': height_unit,
        'viewbox': viewbox,
        'raw_width': width_attr,
        'raw_height': height_attr,
        'raw_viewbox': viewbox_attr
    }

def calculate_scaling_factor(source_dims, target_dims):
    """Calculate the scaling factor needed to maintain proper dimensions"""
    # If both source and target have mm dimensions and viewbox, we can calculate the exact scaling
    if (source_dims['width_value'] and source_dims['viewbox'] and 
        target_dims['width_value'] and target_dims['viewbox']):
        
        # Calculate the scaling factors
        source_scale = source_dims['viewbox'][2] / source_dims['width_value']
        target_scale = target_dims['viewbox'][2] / target_dims['width_value']
        
        return target_scale / source_scale
    
    return 1.0  # Default no scaling

def paste_svg_with_dimension_preservation(base_svg_path, insert_svg_path, output_path, x_mm=0, y_mm=0):
    """
    Paste one SVG into another while preserving the exact dimensions in millimeters.
    
    Args:
        base_svg_path: Path to the base/container SVG
        insert_svg_path: Path to the SVG to be pasted
        output_path: Path where combined SVG will be saved
        x_mm: X position in mm for pasting
        y_mm: Y position in mm for pasting
    """
    # Get dimensions of both SVGs
    base_dims = get_svg_dimensions(base_svg_path)
    insert_dims = get_svg_dimensions(insert_svg_path)
    
    print(f"Base SVG dimensions: width={base_dims['width_value']}{base_dims['width_unit'] or ''}, "
          f"height={base_dims['height_value']}{base_dims['height_unit'] or ''}")
    print(f"Insert SVG dimensions: width={insert_dims['width_value']}{insert_dims['width_unit'] or ''}, "
          f"height={insert_dims['height_value']}{insert_dims['height_unit'] or ''}")
    
    # Parse the SVG files
    base_dom = minidom.parse(base_svg_path)
    insert_dom = minidom.parse(insert_svg_path)
    
    # Get root elements
    base_root = base_dom.documentElement
    insert_root = insert_dom.documentElement
    
    # Make sure defs element exists in base SVG
    defs_elements = base_dom.getElementsByTagName('defs')
    if defs_elements:
        defs_element = defs_elements[0]
    else:
        defs_element = base_dom.createElement('defs')
        base_root.appendChild(defs_element)
    
    # Get all namespaces from both SVGs and ensure they're in the output
    base_attrs = dict(base_root.attributes.items())
    insert_attrs = dict(insert_root.attributes.items())
    
    # Add xlink namespace if not present
    if 'xmlns:xlink' not in base_attrs:
        base_root.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
    
    # Create a unique ID for the inserted content
    symbol_id = f"inserted_svg_{os.path.basename(insert_svg_path).replace('.', '_')}"
    
    # Extract the content to be inserted, skipping the SVG root tag
    insert_content = []
    for node in insert_root.childNodes:
        if node.nodeType != node.TEXT_NODE:  # Skip text nodes
            insert_content.append(node)
    
    # Create a symbol element that preserves the exact dimensions
    symbol = base_dom.createElement('symbol')
    symbol.setAttribute('id', symbol_id)
    
    # Set the viewBox to match the original SVG
    if insert_dims['raw_viewbox']:
        symbol.setAttribute('viewBox', insert_dims['raw_viewbox'])
    
    # Set width and height on the symbol
    if insert_dims['raw_width']:
        symbol.setAttribute('width', insert_dims['raw_width'])
    if insert_dims['raw_height']:
        symbol.setAttribute('height', insert_dims['raw_height'])
    
    # Add all insert content to the symbol
    for node in insert_content:
        # Import nodes to avoid DOM tree mixing issues
        clone = node.cloneNode(True)
        imported_node = base_dom.importNode(clone, True)
        symbol.appendChild(imported_node)
    
    # Add the symbol to the defs section
    defs_element.appendChild(symbol)
    
    # Calculate the needed scaling factor
    scale_factor = calculate_scaling_factor(insert_dims, base_dims)
    
    # Create a use element referencing the symbol
    use_element = base_dom.createElement('use')
    use_element.setAttribute('xlink:href', f"#{symbol_id}")
    use_element.setAttribute('x', str(x_mm))
    use_element.setAttribute('y', str(y_mm))
    
    # Set exact dimensions on the use element to ensure proper sizing
    if insert_dims['raw_width']:
        use_element.setAttribute('width', insert_dims['raw_width'])
    if insert_dims['raw_height']:
        use_element.setAttribute('height', insert_dims['raw_height'])
    
    # Ensure no aspect ratio scaling
    use_element.setAttribute('preserveAspectRatio', 'xMinYMin meet')
    
    # If scaling is needed, add a transform attribute
    if scale_factor != 1.0:
        print(f"Applying scale factor: {scale_factor}")
        use_element.setAttribute('transform', f"scale({scale_factor})")
    
    # Add the use element to the base SVG
    base_root.appendChild(use_element)
    
    # If we need to expand the base SVG dimensions to fit the inserted content
    if base_dims['width_value'] and insert_dims['width_value']:
        required_width = x_mm + insert_dims['width_value']
        if required_width > base_dims['width_value']:
            base_root.setAttribute('width', f"{required_width}mm")
            
            # Also update viewBox if present
            if base_dims['viewbox']:
                vb_x, vb_y, vb_width, vb_height = base_dims['viewbox']
                new_vb_width = vb_width * (required_width / base_dims['width_value'])
                base_root.setAttribute('viewBox', f"{vb_x} {vb_y} {new_vb_width} {vb_height}")
    
    if base_dims['height_value'] and insert_dims['height_value']:
        required_height = y_mm + insert_dims['height_value']
        if required_height > base_dims['height_value']:
            base_root.setAttribute('height', f"{required_height}mm")
            
            # Also update viewBox if present
            if base_dims['viewbox']:
                vb_x, vb_y, vb_width, vb_height = base_dims['viewbox']
                new_vb_height = vb_height * (required_height / base_dims['height_value'])
                base_root.setAttribute('viewBox', f"{vb_x} {vb_y} {vb_width} {new_vb_height}")
    
    # Write the combined SVG to the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        # Use toxml() to get a proper XML declaration
        f.write(base_dom.toxml())
    
    print(f"Combined SVG saved to {output_path}")
    print(f"Dimensions of inserted content: width={insert_dims['width_value']}{insert_dims['width_unit'] or ''}, "
          f"height={insert_dims['height_value']}{insert_dims['height_unit'] or ''}")

if __name__ == "__main__":
    # Specify file paths
    base_svg = "container.svg"
    insert_svg = "topaste.svg"
    output_svg = "combined_mm_preserved.svg"
    
    # Position for pasting (in mm)
    x_position = 0  # mm from left
    y_position = 0  # mm from top
    
    # Execute the paste operation
    paste_svg_with_dimension_preservation(
        base_svg_path=base_svg,
        insert_svg_path=insert_svg,
        output_path=output_svg,
        x_mm=x_position,
        y_mm=y_position
    )