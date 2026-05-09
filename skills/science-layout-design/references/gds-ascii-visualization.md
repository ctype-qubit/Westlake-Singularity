# GDS ASCII Visualization Technique

Quick GDS layer inspection without matplotlib/KLayout — render as ASCII grid.

## When to use
- matplotlib not installed (PEP 668 restrictions)
- Quick inspection of small regions (±5-10μm)
- Checking layer overlaps and symmetry
- Understanding device geometry before launching KLayout

## Technique

```python
import gdspy
import numpy as np

lib = gdspy.GdsLibrary()
lib.read_gds('/path/to/file.gds')
cell = lib.cells['MainSymbol']  # or iterate lib.cells
polys = cell.get_polygons(by_spec=True)

# Define grid: 100×100 cells, 0.1μm resolution → ±5μm view
GRID_SIZE = 100
HALF_UM = 5.0
SCALE = GRID_SIZE / (2 * HALF_UM)  # cells per μm

grid = np.full((GRID_SIZE, GRID_SIZE), ' ', dtype='<U2')

# Map layers to characters
layer_chars = {2: 'R', 3: 'G', 5: 'P', 6: 'C'}  # customize per file

for (layer, dp), plist in polys.items():
    char = layer_chars.get(layer, '?')
    for p in plist:
        pb = gdspy.Polygon(p).get_bounding_box()
        cx = (pb[0][0] + pb[1][0]) / 2
        cy = (pb[0][1] + pb[1][1]) / 2
        if abs(cx) > HALF_UM or abs(cy) > HALF_UM:
            continue  # outside zoom window
        for px, py in p:
            gx = int((px + HALF_UM) * SCALE)
            gy = int((py + HALF_UM) * SCALE)
            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                existing = grid[GRID_SIZE - 1 - gy, gx]  # flip Y
                grid[GRID_SIZE - 1 - gy, gx] = 'x' if existing != ' ' else char

# Print with axis labels
print("     " + "".join(str(i % 10) for i in range(GRID_SIZE)))
for row in range(GRID_SIZE):
    y_um = (GRID_SIZE - 1 - row - GRID_SIZE // 2) / SCALE
    label = f"{y_um:4.1f} " if row % 10 == 0 else "     "
    print(label + "".join(grid[row]))
```

## Key parameters
- `HALF_UM`: zoom half-width in μm (5 = ±5μm)
- `SCALE`: cells per μm (10 = 0.1μm resolution per cell)
- `layer_chars`: map GDS layer numbers to single ASCII chars

## Pitfalls
- Grid is O(n²) — keep GRID_SIZE ≤ 200 for performance
- For large die with multiple cells, loop over cells first
- 72-point polygons are typically circles (quantum dots, JJs, vias)
- 4-point polygons are rectangles (bond pads, routing lines)
- Multi-point polygons (>4 but <20) are typically tapered interconnects
- Layer 11 is commonly the wafer boundary frame

## Real example: 57.gds analysis (2026-05-07)
- 30×30mm, 8 layers, single die "MainSymbol"
- Layer 2 (192 poly): EBL fine features, ~0.1μm
- Layer 3 (216 poly): EBL fine features, interleaved with L2
- Layer 6 (18 poly): 10 circular structures (72-pt) = QDs/JJs
- Layer 5 (12 poly): vias at junction points
- Layer 1/4/7: photo-level bus lines fanning out to bond pads
- Pattern: 4-fold symmetric core ±2μm from origin
