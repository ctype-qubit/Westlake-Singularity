# Fan-Out Routing Guide for Dense Multi-Layer GDS Layouts

> Captured 2026-05-07 from 57.gds fan-out work. 54 signal wires from a 91μm-wide device core to 4 chip edges.
>
> ⚠️ **CRITICAL: Programmatic fan-out FAILED after 10+ iterations.** The agent was unable to produce a zero-short fan-out programmatically despite using two-layer routing, track isolation, global spacing, and manual polygon construction. The fundamental issue: 15 wires starting in a 91μm X-range with shared X coordinates produce edge-case overlaps at Phase 1 (horizontal micro-shifts at near-identical Y). **The user (丛家祥) ultimately completed the fan-out manually in KLayout using multi-layer stitching.** Programmatic fan-out should ONLY be attempted for layouts with ample spacing (>50μm between adjacent device wires). For dense layouts, generate the core device programmatically and route fan-out manually in KLayout.
>
> **What the user actually did (57.gds v4):** See `references/gds-v4-fanout-analysis.md` for the complete architecture — multi-row 1000×1000μm bond pads on 3 damascene layers (L1/L4/L7), L8 via fence at mid-range, 98 routing traces on L1. This is the reference to study, not the programmatic approach below.

## The Problem

When fanning out many wires from a dense device core to bond pads at the chip edge, single-layer routing is geometrically impossible if:
- Multiple wires share the same X (or Y) coordinate at the device end
- Wire pitch at device end (e.g. 5μm) is much smaller than bond pad pitch (e.g. 350μm)
- Wires from different edges cross each other's routing space

## Correct Architecture: Two-Layer PCB-Style Routing

Use two metal layers like a real PCB:

| Layer | Purpose |
|-------|---------|
| L_H (horizontal) | All X-direction runs: micro-shifts at device end, track segments, pad approaches |
| L_V (vertical) | All Y-direction runs: device-to-track drops, track-to-pad drops |
| L_PAD | Bond pads (200×200μm recommended) |

Vias: overlap between L_H and L_V at junction points is the via. No separate via polygons needed.

## Wire Path (per wire, N-edge example)

```
Device end (ox, oy)
    │
    ├── Phase 1: L_H micro-shift from ox to ux at oy (only if ox ≠ ux)
    │
    ├── Phase 2: L_V vertical from (ux, oy) to (ux, track_y)
    │
    ├── Phase 3: L_H horizontal from (ux, track_y) to (pad_x, track_y)  
    │
    └── Phase 4: L_V vertical from (pad_x, track_y) to (pad_x, CHIP_EDGE)
                                                           │
                                                      Bond Pad (L_PAD)
```

## Critical Design Rules

### 1. Unique X/Y Assignment (Phase 1 input)
- Every wire needs a unique departure coordinate (ux for N/S edges, uy for E/W edges)
- Minimum pitch between ux/uy values: `wire_width + 2μm` (e.g. 6μm + 2μm = 8μm, round to 14μm for safety)
- Resolve shared ox using global spacing (sort all ox values, space from smallest to largest at min pitch)
- Wires with shared ox at different oy MUST all get unique ux — vertical overlaps at same X are fatal

### 2. Track Zone Isolation (Phase 3)
- N/S edge horizontal tracks: Y zone must NOT overlap E/W pad horizontal Y zone
- E/W edge horizontal tracks: X zone must NOT overlap N/S pad horizontal X zone
- Compute: `N_track_min = max(max_device_oy + 200, EW_pad_Y_max + 500)`
- This prevents cross-edge L_H-L_H overlaps

### 3. Wire Width and Y-Overlap in Phase 1
- Horizontal micro-shifts at device end happen at different Y (each wire's oy)
- BUT: if `|oy_i - oy_j| < wire_width`, the horizontal segments overlap in Y
- Mitigation: these segments are at DIFFERENT X ranges (unique ux), so no 2D overlap
- CAUTION: after global spacing, ux values near each other combined with close oy can still cause edge touches. Manually adjust in KLayout if needed.

### 4. Use Exact Rectangle Polygons, NOT gdspy.Path
- gdspy.Path objects have end-cap expansion that causes false overlaps at junctions
- Compute polygon corners manually:
```python
def wire_rect(x1, y1, x2, y2, w):
    dx, dy = x2-x1, y2-y1
    L = math.hypot(dx, dy)
    if L < 0.01: return None
    nx, ny = -dy/L * w/2, dx/L * w/2
    return [(x1+nx,y1+ny), (x1-nx,y1-ny), (x2-nx,y2-ny), (x2+nx,y2+ny)]
```

## Common Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| 100s of L_H overlaps | Track zones from different edges overlap in Y | Add SAFE_MARGIN (≥500μm) between N/S tracks and E/W pad zones |
| L_V overlaps near device | Multiple wires at same ox → verticals at same X overlap | Stagger ux values for wires sharing ox (use global spacing) |
| L_H overlaps near device | Phase 1 shifts at very close Y (< wire_width) | X ranges are far apart → false positive (OK) or micro-adjust in KLayout |
| Path end-cap false overlaps | gdspy.Path creates round/square caps | Use manual polygon corners instead |

## Verification

After generating GDS, run per-layer boolean collision check with area threshold:
```python
for i in range(len(polygons)):
    for j in range(i+1, len(polygons)):
        inter = gdspy.boolean(pi, pj, 'and')
        if inter and inter.area() > 1.0:  # >1μm² = real short
            report_short(i, j, inter)
```

Expect: 0 real shorts on L_PAD, ≤20 edge-touch artifacts on L_H/L_V (acceptable, fixable in KLayout).

## Bond Pad Specs

**What the user actually used (57.gds v4):** 1000×1000μm pads, multi-row staggered placement (N-edge at Y=12080 and Y=14080), distributed across 3 routing layers (L1/L4/L7). This is the proven approach — study `references/gds-v4-fanout-analysis.md`.

Legacy programmatic approach (inferior):
- Size: 200×200μm (standard for Al ultrasonic wire bonding)
- Pitch: 350μm minimum (150μm gap between 200μm pads)
- Placement: ±14500μm from center on a 30mm chip (500μm edge margin)
