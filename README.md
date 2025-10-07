# SVG Paste Utility Module

This utility provides a Python function, `combinesvg`, to accurately paste the contents of one SVG file into another while preserving the physical dimensions of the pasted elements.

## The Problem

When manually or programmatically copying elements from one SVG file to another, a common issue is that the pasted content appears scaled incorrectly. This happens because SVGs use two different coordinate systems:

1.  **Physical Dimensions**: The `width` and `height` attributes of the root `<svg>` element, often specified in physical units like millimeters (`mm`) or inches (`in`). This defines the real-world size of the canvas.
2.  **Internal Coordinate System (ViewBox)**: The `viewBox` attribute defines the coordinate system used *within* the SVG file for placing and sizing elements. For example, `viewBox="0 0 200 150"` means the canvas is 200 units wide and 150 units high.

The relationship between the physical width and the viewBox width (`viewBox_width / physical_width_mm`) can be thought of as a "units per mm" ratio. This ratio is often different between two separate SVG files. Simply copying an element's coordinates from a source file to a destination file ignores this difference, causing the element to appear larger or smaller than intended.

## The Solution

The `combinesvg` function solves this problem by implementing the following logic:

1.  **Calculate 'Units per mm' Ratio**: For both the source (to be pasted) and container (destination) SVGs, it calculates the `units_per_mm` ratio.
2.  **Determine Scale Factor**: It computes a `dimension_scale_factor` by dividing the source's ratio by the container's ratio (`source_units_per_mm / container_units_per_mm`). This factor represents how much an element from the source must be scaled to maintain its physical size within the container's coordinate system.
3.  **Group and Transform**:
    *   It creates a new group (`<g>`) element in the container SVG. The ID of this group is automatically derived from the source filename.
    *   It applies a `transform` attribute to this group. The first transformation is always `scale(...)` using the calculated `dimension_scale_factor`.
    *   It copies all drawable elements (paths, rects, other groups, etc.) from the source SVG into this new group.
4.  **Apply Additional Transformations**: The function can optionally accept a list of additional transformations (`translate`, `scale`, `rotate`).
    *   `translate` values are provided in **millimeters** and are automatically converted to the correct viewBox units for the container SVG.
    *   These are appended to the `transform` string after the initial dimension-preserving scale.
5.  **Save Output**: The resulting combined SVG is saved to a new file.

This approach ensures that all pasted content is correctly scaled and grouped, making complex SVG compositions predictable and accurate.
