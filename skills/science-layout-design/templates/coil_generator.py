#!/usr/bin/env python3
"""
Standalone coil generator — creates a 6-coil array with fanout.
Copy this into your layout script and call create_6coil_array(cell).

Usage:
  from coil_generator import create_6coil_array
  create_6coil_array(my_cell, layer_ebl=2)
"""

import numpy as np
import gdspy

def create_6coil_array(cell, track_width=0.15, loop_radius=0.40, 
                       pitch=0.25, r_neck=None, layer_ebl=2):
    """
    Create 6 superconducting coils (3 north, 3 south) in a cell.
    
    Args:
        cell: gdspy.Cell to add coils to
        track_width: wire width in um (default 0.15 = 150nm)
        loop_radius: coil turn radius in um (default 0.40)
        pitch: axis-to-axis distance in um (default 0.25)
        r_neck: neck smoothing radius (default = track_width)
        layer_ebl: GDS layer number (default 2)
    
    Returns:
        (north_wires, south_wires): sorted lists of gdspy.Path objects
    """
    if r_neck is None:
        r_neck = track_width
    
    r_outer = loop_radius + track_width / 2
    L = 0.8 + 2 * r_outer
    d_inner = L / 2
    d_outer = d_inner * (1 + np.sqrt(7)) / 2
    
    yc = pitch / 2 + r_neck
    xc = np.sqrt((loop_radius + r_neck)**2 - yc**2)
    theta_c = np.arctan2(yc, xc)
    
    def make_coil(cx, cy, angle_deg):
        a = np.radians(angle_deg)
        apex_x = cx - loop_radius * np.cos(a)
        apex_y = cy - loop_radius * np.sin(a)
        
        w2 = gdspy.Path(track_width, (apex_x, apex_y))
        w2.segment(0.005, direction=a + np.pi/2, layer=layer_ebl)
        w2.turn(loop_radius, -(np.pi - theta_c), layer=layer_ebl)
        w2.turn(r_neck, np.pi/2 - theta_c, layer=layer_ebl)
        w2.segment(2.0, layer=layer_ebl)
        
        w1 = gdspy.Path(track_width, (apex_x, apex_y))
        w1.segment(0.005, direction=a - np.pi/2, layer=layer_ebl)
        w1.turn(loop_radius, np.pi - theta_c, layer=layer_ebl)
        w1.turn(r_neck, -(np.pi/2 - theta_c), layer=layer_ebl)
        w1.segment(2.0, layer=layer_ebl)
        
        cell.add([w1, w2])
        return w1, w2
    
    n_wires, s_wires = [], []
    for cx, cy, ang in [(-d_outer, d_outer, 90), (0, d_inner, 90), (d_outer, d_outer, 90)]:
        w1, w2 = make_coil(cx, cy, ang)
        n_wires.extend([w1, w2])
    for cx, cy, ang in [(-d_outer, -d_outer, 270), (0, -d_inner, 270), (d_outer, -d_outer, 270)]:
        w1, w2 = make_coil(cx, cy, ang)
        s_wires.extend([w1, w2])
    
    north = sorted(n_wires, key=lambda w: w.x)
    south = sorted(s_wires, key=lambda w: w.x)
    return north, south

if __name__ == '__main__':
    # Quick test
    lib = gdspy.GdsLibrary()
    cell = lib.new_cell('TEST_COILS')
    n, s = create_6coil_array(cell)
    lib.write_gds('/tmp/test_coils.gds')
    print(f"Generated {len(n)} north + {len(s)} south wires → /tmp/test_coils.gds")
