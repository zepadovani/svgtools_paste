
from svgtools_paste_svg_functions import combinesvg

if __name__ == "__main__":
    try:
        # Define the list of transformations to be applied.
        # The order matters: they will be applied in the defined sequence.
        # The dimension preservation scale is always applied first.
        transforms = [
            {'type': 'translate', 'value': [50, 50]},  
            {'type': 'scale', 'value': 2},
            {'type': 'rotate', 'value': -45}           # Rotate 30 degrees
        ]

        # Use the combinesvg function from the module
        combinesvg(
            container_path='container.svg',
            source_path='pasteme.svg',
            output_path='out/combined_example_3.svg',
            transformations=transforms
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"\nERROR: {e}")
