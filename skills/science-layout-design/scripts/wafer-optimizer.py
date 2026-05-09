#!/usr/bin/env python3
"""
Wafer Optimizer — Find optimal die placement for any wafer size.

Computes the maximum number of dies that fit on a wafer,
trying both centered and X-offset grids.

Usage:
  python3 wafer-optimizer.py --wafer-size 2 --die-size 12
  python3 wafer-optimizer.py --wafer-radius 15000 --die-size 10 --margin 500
"""
import numpy as np
import math
import argparse

def optimize(wafer_radius, die_size, margin=600, try_offset=True):
    """Find optimal die placement maximizing count on wafer."""
    safe_radius = wafer_radius - margin
    best = {'count': 0, 'offset_x': 0, 'offset_y': 0, 'dies': []}
    
    offsets = [(0, 0)]
    if try_offset:
        offsets.extend([(die_size/2, 0), (0, die_size/2), (die_size/2, die_size/2)])
    
    for ox, oy in offsets:
        count = 0
        dies = []
        for i in range(-10, 11):
            for j in range(-10, 11):
                cx = i * die_size + ox
                cy = j * die_size + oy
                corners = [(cx-die_size/2, cy-die_size/2), (cx+die_size/2, cy-die_size/2),
                           (cx-die_size/2, cy+die_size/2), (cx+die_size/2, cy+die_size/2)]
                if all(np.hypot(px, py) <= safe_radius for px, py in corners):
                    count += 1
                    dies.append((cx, cy))
        if count > best['count']:
            best = {'count': count, 'offset_x': ox, 'offset_y': oy, 'dies': dies}
    
    return best

def main():
    parser = argparse.ArgumentParser(description='Wafer die placement optimizer')
    parser.add_argument('--wafer-size', type=float, help='Wafer size in inches')
    parser.add_argument('--wafer-radius', type=float, help='Wafer radius in um')
    parser.add_argument('--die-size', type=float, required=True, help='Die size in mm')
    parser.add_argument('--margin', type=float, default=600, help='Edge margin in um')
    args = parser.parse_args()
    
    wafer_radius = args.wafer_radius
    if args.wafer_size:
        wafer_radius = args.wafer_size * 25.4 / 2 * 1000  # inches → um
    
    die_size_um = args.die_size * 1000
    
    result = optimize(wafer_radius, die_size_um, args.margin)
    
    wafer_inches = wafer_radius * 2 / 25400
    
    print(f"\n{'='*50}")
    print(f"  Wafer Size: {wafer_inches:.1f}\" (R={wafer_radius:.0f} um)")
    print(f"  Die Size:   {args.die_size:.0f} mm ({die_size_um:.0f} um)")
    print(f"  Margin:     {args.margin} um (safe R={wafer_radius-args.margin:.0f} um)")
    print(f"{'='*50}")
    print(f"\n  Best arrangement:")
    print(f"    Dies:     {result['count']}")
    print(f"    Offset:   X={result['offset_x']/1000:.1f}mm, Y={result['offset_y']/1000:.1f}mm")
    
    # Calculate utilization
    die_area = result['count'] * die_size_um**2
    wafer_area = math.pi * wafer_radius**2
    utilization = die_area / wafer_area * 100
    print(f"    Area utilization: {utilization:.1f}%")
    print(f"    Effective dies/wafer: {result['count']}")
    
    # Verify farthest corner
    if result['dies']:
        farthest = max(result['dies'],
                      key=lambda d: max(np.hypot(d[0]+die_size_um/2, d[1]+die_size_um/2),
                                        np.hypot(d[0]-die_size_um/2, d[1]-die_size_um/2)))
        corner_r = max(np.hypot(farthest[0]+die_size_um/2, farthest[1]+die_size_um/2),
                       np.hypot(farthest[0]-die_size_um/2, farthest[1]-die_size_um/2))
        print(f"    Farthest corner at R={corner_r:.0f} um")
        print(f"    Safety margin: {wafer_radius - corner_r:.0f} um {'✅ OK' if wafer_radius - corner_r > 0 else '❌ OVERFLOW'}")
    
    return result

if __name__ == '__main__':
    main()
