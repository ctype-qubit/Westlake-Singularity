---
name: layout-design
description: "KLayout/GDSPY micro/nano fabrication layout generation — parameterized mask design for topological qubit devices, wafer-scale deployment, mixed lithography (EBL + optical) routing, and automated DRC validation."
version: 1.1.0
last_updated: 2026-05-07
author: Jupiter (Mars operator)
---

# Micro/Nano Fabrication Layout Design (Mars Specialist)

Generate KLayout/GDSPY mask layouts for topological qubit device fabrication. 
**Mars (火星)** handles code generation, parameter tuning, and GDS output.

## Workflow

### User Request → Jupiter → Mars → GDS on Windows Desktop

```
User: "I need a 6-coil array with 130nm lines on a 2-inch wafer"
  → Jupiter parses specs (linewidth, die size, coil count, wafer size, layers)
    → Mars generates/modifies GDSPY code
      → Mars runs: python3 layout.py
        → Mars copies .gds to /mnt/c/Users/Admin/Desktop/
          → Jupiter: "Done! Your GDS is on the desktop."
```

### Mars Execution Instructions

1. **Receive task** from Jupiter via Pattern B (background profile agent). Do NOT run inline.
2. **Parse requirements** from Jupiter's task: die_size, track_width, loop_radius, pitch, wafer_size, layer assignments
3. **Load template** from the skill's `references/` directory or generate from scratch using the canonical structure below
4. **Write script** with proper GDSPY API calls at `/tmp/mars_layout_{timestamp}.py`
5. **Test** by running `python3 /tmp/mars_layout_{timestamp}.py`
6. **Validate** output GDS:
   ```python
   import gdspy
   lib = gdspy.GdsLibrary()
   lib.read_gds('/tmp/output.gds')
   assert len(list(lib.cells)) >= 2, f"Expected ≥2 cells, got {len(list(lib.cells))}"
   ```
7. **Copy to Windows desktop**: `cp /tmp/output.gds "/mnt/c/Users/Admin/Desktop/"`
8. **Report** to Jupiter: cell names, die count, file path, safety margin

## Canonical Code Structure

Based on proven 6-coil topological qubit layout (Wafer_2Inch_12mm_Die):

### 1. Core Parameters
```python
import gdspy, numpy as np, math, os

# Layer assignments
layer_photo = 1    # Optical lithography (coarse)
layer_ebl = 2      # E-beam lithography (fine)
layer_wafer = 10   # Wafer reference

# Geometry
die_size = 12000.0       # um (12mm)
track_width = 0.15       # um (150nm — EBL resolution)
loop_radius = 0.40       # um (400nm)
r_neck = 0.15            # um (neck smoothing)
pitch = 0.25             # um (250nm axis-to-axis)

# Derived geometry
r_outer = loop_radius + track_width / 2
L = 0.8 + 2 * r_outer
d_inner = L / 2
d_outer = d_inner * (1 + np.sqrt(7)) / 2
```

### 2. Cell Structure
```
WAFER_2INCH_FINAL (top)
  └── CellReference × N (die_count)
       └── UNIT_CELL_12x12mm
            ├── Dicing frame (layer_photo)
            ├── Alignment marks (layer_photo)
            ├── 6-Coil array (layer_ebl)
            ├── EBL fanout routing (layer_ebl)
            ├── Photo-level wide routing (layer_photo)
            └── Bond pads (layer_photo)
```

### 3. Key Algorithms

#### Continuous Coil Generation
```python
def create_continuous_coil(cx, cy, angle_deg, wire_list):
    """Create a continuous superconducting coil pair.
    U-shaped path: apex → 180° turn → neck → straight fanout.
    Generates two parallel wires (w1, w2) forming the coil."""
    a = np.radians(angle_deg)
    apex_x = cx - loop_radius * np.cos(a)
    apex_y = cy - loop_radius * np.sin(a)
    
    # Wire 2 (one side of coil)
    w2 = gdspy.Path(track_width, (apex_x, apex_y))
    w2.segment(0.005, direction=a + np.pi/2, layer=layer_ebl)
    w2.turn(loop_radius, -(np.pi - theta_c), layer=layer_ebl)
    w2.turn(r_neck, np.pi/2 - theta_c, layer=layer_ebl)
    w2.segment(2.0, layer=layer_ebl)
    
    # Wire 1 (other side, mirrored)
    w1 = gdspy.Path(track_width, (apex_x, apex_y))
    w1.segment(0.005, direction=a - np.pi/2, layer=layer_ebl)
    w1.turn(loop_radius, np.pi - theta_c, layer=layer_ebl)
    w1.turn(r_neck, -(np.pi/2 - theta_c), layer=layer_ebl)
    w1.segment(2.0, layer=layer_ebl)
    
    unit_cell.add([w1, w2])
    wire_list.extend([w1, w2])
```

**Geometry derivation:**
```python
yc = pitch / 2 + r_neck
xc = np.sqrt((loop_radius + r_neck)**2 - yc**2)
theta_c = np.arctan2(yc, xc)
```

#### Alignment Marks
```python
def add_cross_mark(cx, cy, label, scale=1.0, layer=layer_photo):
    """Create cross alignment mark with text label.
    Local marks (L1-L4): scale=5 (10um length)
    Global marks (G1-G4): scale=50 (100um length)"""
    mark_len = 2.0 * scale
    mark_width = 0.6 * (1.0 if scale < 5 else scale/5.0)
    r1 = gdspy.Rectangle((cx - mark_width/2, cy - mark_len/2),
                         (cx + mark_width/2, cy + mark_len/2), layer=layer)
    r2 = gdspy.Rectangle((cx - mark_len/2, cy - mark_width/2),
                         (cx + mark_len/2, cy + mark_width/2), layer=layer)
    text = gdspy.Text(label, mark_width*2, (cx + mark_len/2 + 0.5, cy + mark_width), layer=layer)
    unit_cell.add([r1, r2, text])
```

#### Mixed-Lithography Fanout Routing
Three-stage routing from EBL nanowire to bond pad:
```
Stage 1 [EBL]: 150nm wire → fan out to 2um @ handshake point (~55um from center)
Stage 2 [Photo]: 2um → taper to 30um → expand to 50um → reach 80um
Stage 3 [Photo]: 80um line → bond pad (800um × 800um)
```
Each stage ensures minimum inter-wire spacing through offset fan angles.

#### Wafer-Scale Array with X-Offset Algorithm
Maximize die count on wafer by applying a half-die X-offset:
```python
wafer_radius = 25400.0     # 2-inch = 25.4mm
safe_radius = 24800.0      # 600um edge margin
offset_x = die_size / 2.0  # Half-die X offset

for i in range(-5, 6):
    for j in range(-5, 6):
        cx = i * die_size + offset_x
        cy = j * die_size + offset_y
        # Check all 4 corners within safe_radius
        corners = [(cx-die_size/2, cy-die_size/2), (cx+die_size/2, cy-die_size/2),
                   (cx-die_size/2, cy+die_size/2), (cx+die_size/2, cy+die_size/2)]
        if all(np.hypot(px, py) <= safe_radius for px, py in corners):
            top_cell.add(gdspy.CellReference(unit_cell, (cx, cy)))
```

### 4. Output
```python
# Save to Windows desktop
desktop = "/mnt/c/Users/Admin/Desktop/"
file_path = os.path.join(desktop, "Layout.gds")
lib.write_gds(file_path)
```

## Parameter Templates

| Parameter | 150nm Node (default) | 120nm Node | 100nm Node |
|-----------|---------------------|------------|------------|
| track_width | 0.15 um | 0.12 um | 0.10 um |
| loop_radius | 0.40 um | 0.35 um | 0.30 um |
| pitch | 0.25 um | 0.22 um | 0.20 um |
| r_neck | 0.15 um | 0.12 um | 0.10 um |
| est. gap | 100 nm | 100 nm | 100 nm |

## Design Rules (DRC)

When generating layouts, always validate:
1. **Minimum EBL linewidth** ≥ track_width (typically 150nm)
2. **Inter-wire gap** = pitch - track_width (target ≥ 100nm for reliable lift-off)
3. **Photo-to-EBL overlap** at handshake points must be >5um for registration tolerance
4. **Wafer edge margin** ≥ 600um (safe_radius = wafer_radius - 600)
5. **All bond pads** must be within 4000-5000um from die center

## DXF/CAD 文件处理

用户可以在 CAD (AutoCAD/LibreCAD) 中绘制粗结构层版图，导出 DXF，然后 Mars/Jupiter 进行 DXF→GDS 转换，自动补全 EBL 精细层。

### 技术栈
- **ezdxf** (Python库, `pip3 install ezdxf`) — 读取 DXF
- **gdspy** — 转换为 GDS

### 支持的 DXF 实体 → GDS 映射
| DXF 实体 | GDS 转换 | 说明 |
|----------|---------|------|
| LINE | gdspy.Path | 单一线段 |
| LWPOLYLINE / POLYLINE | gdspy.Polygon | 折线/闭合多边形 |
| CIRCLE | gdspy.Round | 圆形 |
| ARC | 分段 Path.turn | 圆弧 |
| TEXT | gdspy.Text | 文字（对准标记标签） |
| INSERT (block) | gdspy.CellReference | 块引用为子单元 |
| DIMENSION | 解析数值 | 提取标注尺寸 |

### 图层映射策略
```
CAD Layer 名称/颜色 → GDS Layer 编号：
  粗结构/焊盘/划片道 → Layer 1 (photo)
  精细结构/线圈      → Layer 2 (EBL)
  对准标记           → Layer 3 (marks)
  晶圆参考           → Layer 10 (wafer)
```

### 工作流程: CAD → DXF → GDS → 桌面
1. 用户在 CAD 中绘制设计，不同工艺元素放不同图层
2. 导出 DXF (推荐 R2010 格式)
3. 发送到 Jupiter → Mars 读取并转换为 GDS
4. Mars 自动添加：EBL精细层、对准标记、划片道、taper过渡
5. GDS 文件直达 `C:\Users\Admin\Desktop\`

### DXF 读取示例
```python
import ezdxf
doc = ezdxf.readfile('design.dxf')
msp = doc.modelspace()
for e in msp:
    layer = e.dxf.layer  # CAD 图层名
    if e.dxftype() == 'LWPOLYLINE':
        points = [(p[0], p[1]) for p in e.get_points()]
        # 根据图层分配 GDS layer
        gds_layer = 1 if 'photo' in layer.lower() else 2
        cell.add(gdspy.Polygon(points, layer=gds_layer))
```

## 大马士革工艺 (Damascene Process) — 关键设计约束

**这是微纳加工版图设计的核心物理约束。** 每一层GDS图层对应一个具体的工艺步骤，图层之间有严格的物理叠层顺序和空间拓扑关系。

### 典型工艺流程 (以6-Coil器件为例)

```
① 匀胶 Spin Coat          → 光刻胶覆盖晶圆表面
② 光刻 Lithography        → 曝光显影，定义图案（Layer 1 光刻）
③ RIE干法刻蚀              → 带着光刻胶向下刻蚀，将图案转移到基底
④ 蒸镀 Evaporation        → 沉积金属（超导薄膜）
⑤ Lift-Off                 → 去除光刻胶，金属留在刻蚀凹槽中
⑥ PECVD SiO₂绝缘层         → 沉积二氧化硅覆盖整个表面
⑦ CMP晶圆抛光              → 化学机械抛光，让表面变平
⑧ 重复①-⑦做上层结构        → 下一层金属/超导结构
```

### 关键物理概念

#### 1. GDS图层 ≠ 画图图层，它们是物理工艺层
每一层GDS图层对应一次完整的光刻循环：
```
GDS Layer 1 (photo) = 第一层金属（粗线，bond pads, 划片道）
GDS Layer 2 (ebl)   = 第二层结构（精细纳米线，线圈）
GDS Layer 3         = 通孔/过孔 (Via，连接Layer 1和Layer 2)
GDS Layer 4         = 第三层金属（顶部电极/栅极）
...
```

#### 2. 图层之间有严格的空间顺序
```
Z轴方向（从下到上）：
  衬底 Substrate
  └─ Layer 1 金属 (粗结构, ~200nm厚)
  │    └─ SiO₂绝缘 + CMP
  │       └─ Layer 2 超导纳米线 (精细结构, ~150nm厚)
  │           └─ SiO₂绝缘 + CMP  
  │              └─ Layer 3 顶部电极/栅极
```

#### 3. 设计规则必须考虑工艺约束
- **对准容差 Overlay Tolerance**: 上层对下层的套刻精度（通常 ±50-100nm）
- **最小间距**: 同层金属间间距由光刻分辨率决定
- **跨层通孔**: Layer N的焊盘必须足够大以覆盖Layer N+1的通孔
- **台阶覆盖 Step Coverage**: 陡峭台阶处金属可能断裂，需要渐变过渡
- **CMP平坦化**: 金属密度分布要均匀，否则CMP会导致凹陷

#### 4. 对版图设计的实际影响

| 工艺约束 | 版图设计对策 |
|---------|-------------|
| 多层对准 | 每层都需要对准靶标，且靶标必须留在前一层不被刻蚀掉 |
| 台阶覆盖 | 从EBL到Photo的扇出要**渐变**，不能有直角突变 |
| CMP密度均匀性 | 大块金属区域要加 dummy fill，避免CMP凹陷 |
| 层间通孔 | Bottom pad要 > Top via 至少 2um 余量 |
| 热量管理 | 大块pad和精细纳米线之间要有热沉路径 |
| 刻蚀选择比 | RIE时不同材料的刻蚀速率不同，影响侧壁角度 |

### 当前6-Coil设计的叠层分析

```
Z ↑
  │  Bond Pads (800um) ── Layer 1 (光刻, ~300nm Au/Al)
  │  Photo Routing (80um→5um taper) ── Layer 1
  │  SiO₂ Insulation + CMP
  │  EBL→Photo 交接点 (~2um) ── Layer 1/2 overlap region
  │  EBL Fanout (2um→0.15um taper) ── Layer 2 (EBL)
  │  超导线圈 (150nm) ── Layer 2 (EBL, ~150nm Nb/TiN)
  │  SiO₂ Insulation + CMP  
  └── 衬底 Substrate
```

### 设计自检清单（每次出图前必须检查）

- [ ] 每个GDS图层是否对应正确的工艺步骤？
- [ ] 不同图层之间是否有足够的overlap余量 (> 2um)？
- [ ] 精细结构是否有渐变的taper过渡到粗结构？
- [ ] 对准靶标是否在所有相关工艺层都存在？
- [ ] EBL层在光刻层上面还是下面？物理顺序是否正确？
- [ ] 最细线宽是否在工艺能力范围内？
- [ ] 是否有大步的线宽突变（需加过渡段）？

## External References: KlayoutClaw Autorouting Engine

### KlayoutClaw Autorouting Engine (from github.com/caidish/KlayoutClaw)

This project provides a sophisticated MCP-based routing engine using scipy/scikit-image.
Key techniques worth integrating:

### 1. Automated Pin-to-Pin Routing
```python
# Hungarian matching + Dijkstra pathfinding pipeline:
# 1. Extract pin centers from layer A and layer B
# 2. Rasterize obstacles into 2D numpy cost grid
# 3. Use scipy.optimize.linear_sum_assignment for optimal pin pairing
# 4. Use skimage.graph.MCP_Geometric for minimum-cost pathfinding
# 5. Compress collinear waypoints with cross-product check
```

### 2. Graduated Damping Cost Field
Instead of hard obstacle boundaries, create concentric cost zones:
```python
# Each concentric layer adds hardness/n_steps to the cost
# Result: cost ramps from 0 at safe_distance to hardness at obstacle boundary
# This produces smooth, natural-looking routes that avoid sharp corners near obstacles
```

### 3. Rasterization via KLayout Native API
```python
# Use kdb.Region.rasterize() for fast obstacle-to-grid conversion
region = kdb.Region()
# ... build region from obstacle layers ...
raster = np.array(region.rasterize(origin, step, ncols, nrows))
cost = np.ones((nrows, ncols), dtype=np.float64)
cost[raster > 0] = -1.0  # impassable
```

### 4. KLayout pya API Integration
For future Python-in-KLayout scripts:
```python
import klayout.db as kdb  # or import pya
layout = kdb.Layout()
layout.read("input.gds")
# Access cells, shapes, regions with native KLayout performance
```

### References
- Full source: https://github.com/caidish/KlayoutClaw
- Routing engine: `tools/route_worker.py` (785 lines, MIT license)
- GDS→Image: `tools/gds_to_image.py`
- Author: caidish (caidish1234@gmail.com)

## Fan-Out Routing to Bond Pads

⚠️⚠️⚠️ **CRITICAL: DO NOT attempt programmatic fan-out from dense device cores.** 

After 10+ iterations across multiple sessions, the agent failed every single attempt to produce a zero-short fan-out. The root cause is mathematical: when 15+ wires start from <100μm span with shared X coordinates, no programmatic routing algorithm can guarantee zero crossing on a single layer, and multi-layer programmatic routing introduces its own crossing pathologies.

The correct methodology, demonstrated by 丛家祥 (家祥), is:

1. **Generate the core device layer programmatically** (L2-L3 EBL fine structures)
2. **Route fan-out manually in KLayout** using the "拼接" (stitching) technique:
   - Break each long wire into short segments drawn by hand
   - Leave intentional micro-overlaps (5-30μm²) at segment joints for reliable connections
   - Reuse existing process layers (L1, L4, L7) for routing — do NOT create new layers
   - Use L8 as a via grid (30×30μm squares in regular arrays) for inter-layer transitions
   - Place large bond pads (1000×1000μm) in multi-row staggered patterns at edges
3. **Validate with Boolean checks but interpret results carefully** — segment-joint overlaps are intentional stitches, not real shorts

For the complete architecture analysis, see `references/gds-v4-fanout-analysis.md`. This is the ONLY verified working fan-out approach for dense topological qubit layouts.

**Agent principle: correctness over speed.** A physical mask design with shorts is scrap silicon. It is ALWAYS better to consume more tokens and deliver a zero-short result than to rush and deliver a broken design. If programmatic routing fails after 3 iterations, STOP and recommend manual KLayout routing.

## Pitfalls

- **GDSPY API**: gdspy v1.6.x uses `cell.references` (not `.elements`), `cell.get_dependencies()` (not `.dependencies`)
- **Coordinate system**: ALL units in micrometers (um). 150nm = 0.15um
- **Path direction**: `gdspy.Path.turn(radius, angle)` — positive angle = counterclockwise
- **Windows path**: Always save to `/mnt/c/Users/Admin/Desktop/` for the user to find
- **Two cells**: Always create a nested structure: top-level (wafer array) + unit cell (die). Never flatten.
- **Sorting**: North/south coil wires must be X-sorted to prevent crossing
- **Memory**: Complex layouts with many dies can use significant memory. Use `gdspy.CellReference` not repeated cell copies.

## References

See `references/` for:
- `canonical-6coil-layout.py` — the full working reference script (家祥's original, annotated)
- `parameter-calculator.py` — tool to compute derived geometry from base parameters
- `wafer-optimizer.py` — script that finds optimal die placement for any wafer size
- **`fabrication-process-reference.md`** — **必须先读！** 完整的大马士革工艺参考、超导器件叠层、工艺参数速查、DRC设计规则、材料表。出任何版图前必须加载此文件。
- **`ebl-75nm-process-guide.md`** — 75nm线宽/50nm间距极限EBL工艺全流程指南（11章）：抗蚀剂选择、冷显影、PEC邻近校正、蒸镀、lift-off、RIE、光刻、PECVD/CMP、表征检测与故障排查。包含完整的推荐参数速查表。
- **`gds-ascii-visualization.md`** — 无需matplotlib/KLayout即可快速可视化GDS图层：ASCII网格渲染、图层着色、对称性检查。
- **`gds-v4-fanout-analysis.md`** — **家祥手工完成的 57.gds v4 扇出架构分析！** 1384多边形的完整图层分配、1000×1000μm多排交错bond pads、L8过孔阵列、L1/L4/L7三层路由。程序化扇出失败后必读此参考。

See `templates/` for reusable snippets:
- `coil_generator.py` — standalone 6-coil array generator with parameter defaults
