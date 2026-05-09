#!/usr/bin/env python3
"""
Layout Parameter Calculator for 6-Coil Design
Given base parameters, compute all derived geometry.

Usage:
  python3 parameter-calculator.py --track-width 0.15 --loop-radius 0.40 --pitch 0.25

Or modify values in the PARAMS dict below.
"""
import math
import numpy as np

def calculate(track_width=0.15, loop_radius=0.40, pitch=0.25, r_neck=None):
    """Compute all derived layout parameters."""
    if r_neck is None:
        r_neck = track_width  # Usually same as track_width
    
    r_outer = loop_radius + track_width / 2
    L = 0.8 + 2 * r_outer
    d_inner = L / 2
    d_outer = d_inner * (1 + np.sqrt(7)) / 2
    
    yc = pitch / 2 + r_neck
    xc = np.sqrt((loop_radius + r_neck)**2 - yc**2)
    theta_c = np.arctan2(yc, xc)
    theta_c_deg = np.degrees(theta_c)
    
    physical_gap = pitch - track_width
    
    print("=" * 50)
    print("  6-Coil Layout Parameters")
    print("=" * 50)
    print(f"\nInput:")
    print(f"  Track width:     {track_width*1000:.0f} nm ({track_width} um)")
    print(f"  Loop radius:     {loop_radius*1000:.0f} nm ({loop_radius} um)")
    print(f"  Pitch:           {pitch*1000:.0f} nm ({pitch} um)")
    print(f"  Neck radius:     {r_neck*1000:.0f} nm ({r_neck} um)")
    print(f"\nDerived:")
    print(f"  Outer radius:    {r_outer*1000:.0f} nm")
    print(f"  Physical gap:    {physical_gap*1000:.0f} nm")
    print(f"  L:               {L*1000:.0f} nm")
    print(f"  d_inner:         {d_inner*1000:.0f} nm")
    print(f"  d_outer:         {d_outer*1000:.0f} nm")
    print(f"  theta_c:         {theta_c_deg:.1f} deg")
    print(f"\nCoil positions:")
    print(f"  North: (-{d_outer:.3f}, {d_outer:.3f}), (0, {d_inner:.3f}), ({d_outer:.3f}, {d_outer:.3f})")
    print(f"  South: (-{d_outer:.3f}, -{d_outer:.3f}), (0, -{d_inner:.3f}), ({d_outer:.3f}, -{d_outer:.3f})")
    
    return {
        'track_width': track_width,
        'loop_radius': loop_radius,
        'pitch': pitch,
        'r_neck': r_neck,
        'r_outer': r_outer,
        'physical_gap': physical_gap,
        'L': L,
        'd_inner': d_inner,
        'd_outer': d_outer,
        'theta_c': theta_c,
    }

if __name__ == '__main__':
    import sys
    params = {}
    for arg in sys.argv[1:]:
        if '=' in arg:
            k, v = arg.split('=')
            params[k.strip('--')] = float(v)
    calculate(**params)
