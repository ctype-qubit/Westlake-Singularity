---
name: majorana-qubit-measurement-braiding
description: "Complete architecture knowledge base for 丛家祥 (Jiaxiang)'s research group at Westlake University: Majorana-based topological qubits with vortex-pinned measurement-based braiding in FeTeSe, 6-coil array, dual-readout (Layer 0.5 local SQUID + 9-QD VNA), vortex nucleation strategy. Ultimate goal: measurement-based braiding of Majorana qubit arrays for fault-tolerant topological quantum computing."
version: 5.1.0
author: Jupiter (archived for 家祥)
last_calibrated: 2026-05-07
model: deepseek-v4-pro (reasoning_effort=high)
last_ai_meeting: 2026-05-07 — PCB全集 + Nanofab简化 + 文献索引
---

# Majorana Qubit — 测量编织架构永久知识底座

> **绝对终点：** 用 Majorana 零模（MZM）做容错拓扑量子比特，实现基于测量的编织。
>
> **核心宣言：** Microsoft 证明了 MZM 可以被看见。我们正在证明 MZM 可以被编织。
>
> **不移动 MZM，只移动测量。**
>
> **课题组：** 西湖大学 CMP 凝聚态物理，PI 孔令元博士，博士生 丛家祥
>
> **创建：** 2026-05-06 | **v4.0 双读出架构校准：** 2026-05-07

---

## 一、终极目标

完成 **Majorana qubit 阵列的基于测量的编织（Measurement-based Braiding）**，实现普适拓扑量子计算。

**现状 vs 目标：**
- **Microsoft Azure Quantum (2025, Nature, arXiv:2507.08795)** — tetron 单发宇称读出，无编织
- **我们的方案** — 测量序列实现编织。不可编织的 Majorana 只是物理玩具。

---

## 二、完整 3D 器件架构（v4.1 同心 counterwound SQUID）

```
═══════════════════════════════════════════════════════
  Layer 4:  上层 9-QD 阵列 (复制 Layer 3, 完美对齐)
  hBN:      ~10-20 nm
  Layer 3:  下层 9-QD 阵列 (Floating, 桥接 6 线圈)
  hBN:      ~10-20 nm
  Layer 2:  FeTeSe ~200 nm (Majorana 孕育床, Floating)
  hBN:      ~10-20 nm
  ──────────────── ↓ 涡旋 B_z 穿透 ↓ ─────────────
  Layer 1:  6× Field Coils (外环, DC 恒定)
            + Modulation Coils + JJs
  hBN:      ~10-20 nm
  Layer 0.5: 6× Pickup Loops (内环, 同心 ⊂ field coil)
             Front set ← ~1mm → Rear set (counterwound)
  hBN/SiO₂: -
  Layer 0:  Spiral Coil (全局 ~80% Hc1 背景磁场)
═══════════════════════════════════════════════════════
```

**双通道功能分离:**

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  🎯 通道 A: 9-QD + VNA (主战场)                        │
│     → 量子电容 C_q → dispersive readout                │
│     → 测量联合宇称 (MZM 量子关联)                      │
│     → 频率读出, μs 量级                                │
│     → ✅ 实现测量编织 → 拓扑量子门!                    │
│                                                        │
│  🚦 通道 B: 6× Counterwound SQUID (指示灯)             │
│     → 每站点 = Front⊃Rear + Crossover + JJs + Mod      │
│     → 直接探测 DC 磁通 (涡旋存在性)                    │
│     → 6 通道独立, 纯诊断                               │
│     → ✅ 确认"6个涡旋到位" → 通道 A 前提条件           │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

### 🏗️ Layer 0: 磁性地基

```
┌──────────────────────────────────────────────┐
│              Layer 0: 磁性地基                │
│                                              │
│   蚊香盘式 spiral coil（大线圈）              │
│   → 全局背景磁场 ≈ 80% Hc1_thin              │
│   → 全器件 Meissner 态（准失超）             │
│   → 打破时间反演对称性                       │
│                                                │
└──────────────────────────────────────────────┘
```

**🎯 准失超涡旋成核策略（家祥核心设计）：**

FeTeSe ~200 nm 薄膜。Bulk Hc1 ~150-400 Oe，但薄层因退磁效应（N≈1）、Pearl 长度 Λ = 2λ²/d ≈ 1.6-3.1 μm、有限厚度 → Hc1 大幅降低。

```
Step 1: Layer 0 ≈ 80% Hc1_thin
   → 全器件 Meissner 态 → 超导, 零涡旋
   → Meissner 屏蔽超电流流动
   → "准失超"：接近但未失超

Step 2: Layer 1 局域补齐
   → 仅线圈正上方局域 H > Hc1_thin
   → 局域涡旋成核 → 正涡旋精确定位
   → 其余全清洁 Meissner 态！
```

**全局混合态 vs 准失超+局域补齐：**
| 全局混合态 | 我们的方案 |
|-----------|----------|
| 成千上万涡旋 | **恰好6个** |
| 反涡旋需筛选 | **零反涡旋, 全Meissner** |
| 涡旋杂化 | **exp(-d/ξ) 指数隔离** |
| 位置随机 | **微线圈精确控制** |

---

### 🪄 Layer 1: 拓扑涡旋镊子 + SQUID 调制电路

```
┌──────────────────────────────────────────────┐
│        Layer 1: 涡旋镊子 + 调制电路          │
│                                              │
│          C1         C2                        │
│            \       /                          │
│         E1 — E2    ← 交换线圈                │
│            /       \                          │
│          C3         C4                        │
│                                              │
│   6 Field Coils (DC 恒定, 一进一出)           │
│   + Modulation Coil (AC 调制偏置)             │
│   + Josephson Junctions (SQUID 非线性元件)   │
│   ⚡ Field coil 电流永远不变                  │
└──────────────────────────────────────────────┘
```

**Field Coil:**
- 6 个微线圈, DC 恒定电流
- 局域 B_z 补足 Layer 0 的 80% → 超过 Hc1_thin
- 激发正涡旋 (携带 MZM) → pinning 在线圈中心
- 负涡旋排斥到边缘

**Modulation Coil + JJ (SQUID 读出电路):**
- 参照 Moler 组架构 (Björnsson 2005 thesis, Ch.3; Bishop-Van Horn PRB 107, 224509)
- DC SQUID: 超导环 + 两个 JJ
- V ∝ sin(Φ/Φ₀) — 电压对磁通量子周期响应
- Modulation coil: 施加 AC 偏置 → 锁定放大检测
- Feedback: 通过调制线圈电流补偿样品磁通变化 → 线性化输出

**线圈布局:**
- C1-C4: 正方形排列
- E1-E2: 内部交换线圈, E1↔E2 = E1↔最近邻边线圈

**定量约束:**
- ξ_ab ≈ 2-3 nm
- 线圈间距 > 50-100 nm (≳20ξ) → MZM 指数隔离

---

### 📡 Layer 0.5 + Layer 1: 同心 Counterwound SQUID 阵列 ← v4.2

```
┌──────────────────────────────────────────────────────────┐
│   单站点截面: Field Coil ⊃ Pickup Loop (同心嵌套)       │
│                                                          │
│              Top View (俯视)                             │
│         ┌─────────────────────┐                          │
│         │  ╔═══════════════╗  │  ← Field Coil (外环)    │
│         │  ║ ┌───────────┐ ║  │     Layer 1, DC恒定     │
│         │  ║ │ Pickup    │ ║  │                          │
│         │  ║ │ Loop      │ ║  │  ← Pickup Loop (内环)   │
│         │  ║ │ (较小)    │ ║  │     Layer 0.5            │
│         │  ║ └────┬──────┘ ║  │     ~0.5-1 μm below     │
│         │  ╚══════╪════════╝  │     field coil           │
│         └─────────┼───────────┘                          │
│                   │                                      │
│                   │  超导环路                            │
│                   ↓                                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│   Counterwound Pair: Front ← ~1mm → Rear (完全几何对称)  │
│                                                          │
│   Front (~近 FeTeSe)            Rear (~远, reference)    │
│   ┌──────────────────┐         ┌──────────────────┐      │
│   │ ╔══════════════╗ │         │ ╔══════════════╗ │      │
│   │ ║ ┌──────────┐ ║ │         │ ║ ┌──────────┐ ║ │      │
│   │ ║ │ Pickup   │ ║ │         │ ║ │ Pickup   │ ║ │      │
│   │ ║ │ Loop     │ ║ │         │ ║ │ Loop     │ ║ │      │
│   │ ║ └────┬─────┘ ║ │         │ ║ └────┬─────┘ ║ │      │
│   │ ╚══════╪═══════╝ │         │ ╚══════╪═══════╝ │      │
│   └────────┼─────────┘         └────────┼─────────┘      │
│            │         超导环             │                 │
│            └────→ [CROSSOVER 结] ←──────┘                 │
│                        │                                  │
│                   ┌────┴────┐                             │
│                   │ JJ1|JJ2 │  ← 共享 SQUID body         │
│                   └────┬────┘                             │
│                   Modulation Coil                         │
│                 (AC偏置 + Feedback)                       │
│                                                          │
│   ⚡ 关键设计约束:                                       │
│   • Front ↔ Rear Field Coil: 几何全对称                  │
│   • Front ↔ Rear Pickup Loop: 几何全对称                 │
│   • Front ↔ Rear Modulation Coil: 位置对称               │
│   • Front ↔ Rear JJ: 位置对称                            │
│   • Pickup loop 中间 CROSSOVER 结 → 相位反转!            │
│   • 唯一不对称: 仅 Front 局域有涡旋磁通                  │
└──────────────────────────────────────────────────────────┘
```

**CROSSOVER 结 (相位反转, 家祥核心设计约束):**

超导环路中的"结" = lithographic crossover:
```
Front Pickup (顺绕) → [CROSSOVER] → Rear Pickup (反绕) → JJs → Mod Coil → 回到 Front
```

两个 pickup loops 在超导环路中串联但**绕向相反**。Crossover 结实现相位翻转。结果：
- Layer 0 全局场 → Front + Rear 等量同向磁通 → 经 crossover 相位反转 → **净 Φ = 0**
- 局域涡旋磁通 → 仅 Front 接收 → 无抵消 → **差分信号输出**

**为什么需要全对称 (家祥核心约束):**
- Field coil / Pickup loop / Modulation coil / JJ 位置 → Front ↔ Rear 完全几何对称
- 任何几何不对称 → 全局场不完全抵消 → 虚假背景信号
- "打结" (crossover) 是实现 counterwound 超导环路的标准 lithographic 技术

**双读出架构 (目标优先级):**

```
┌─────────────────────────────────────────────────────┐
│              ⚠️ 终极目标: 测量编织                    │
│         通道 A: 9-QD + VNA (主战场!)                 │
│         → 联合宇称测量 → 编织序列 → 拓扑量子门       │
│                                                     │
│              🔧 辅助验证: 涡旋配置                    │
│         通道 B: Local SQUID (Counterwound)           │
│         → 确认 6 个涡旋 pinning 成功                 │
│         → 涡旋数量对、位置对 → 通道 A 前提条件       │
└─────────────────────────────────────────────────────┘
```

**6 站点 = 6 套完整 Counterwound SQUID:**

```
每个涡旋位点 (C1/C2/C3/C4/E1/E2) 配备:

   Front (近FeTeSe)  ←─1mm─→  Rear (远)
   ┌────Field⊃Pickup─┐       ┌────Field⊃Pickup─┐
   │    (同心嵌套)     │       │    (同心嵌套)     │
   └────────┬─────────┘       └────────┬─────────┘
            │      CROSSOVER 结      │
            └──────────┬─────────────┘
                  ┌────┴────┐
                  │ JJ1|JJ2 │  ← 共享 SQUID body
                  └────┬────┘
                  Modulation Coil
                       ↓
              独立读出通道 × 6
```

**Pickup Coil = "涡旋指示灯" 🚦 (家祥定义):**

```
完整架构的功能分层:

  🎯 主战场: 9-QD + VNA
     → 联合宇称测量 → 编织序列 → 拓扑量子门
     → 这是实现 Majorana 量子计算的地方!
     
  🚦 指示灯: 6× Counterwound SQUID
     → 每个涡旋位点一个独立指示灯
     → 亮 = 涡旋到位 | 灭 = 涡旋丢失
     → 纯粹诊断功能, 不参与编织
     
  ⚙️ 驱动器: 6× Field Coil (Layer 1)
     → DC 恒定 → 涡旋成核 + pinning
```

**操作流程:**
**一套 Counterwound SQUID 完整连线 (家祥精确设计):**

```
┌──────────────────────────────────────────────────────────┐
│  一套 = 7 根线 (基于 Moler/Ketchen counterwound 架构)   │
│                                                          │
│  ┌─ Field Coil ────────────────────────────── 3 根 ─┐   │
│  │                                                   │   │
│  │   I_in (1根进)                                    │   │
│  │     │                                             │   │
│  │     ├──→ [Front Field Coil] ──→ GND (出1)        │   │
│  │     │       手性: 顺时针 B_z↑                     │   │
│  │     │                                             │   │
│  │     └──→ [Rear Field Coil]  ──→ GND (出2)        │   │
│  │             手性: 逆时针 B_z↓                     │   │
│  │                                                   │   │
│  │  ⚡ 精髓: 一进两出接地 → 电流自发均分            │   │
│  │     Front/Rear 手性相反 → Rear场远离FeTeSe无影响  │   │
│  │     对称性由 lithography 保证, 无需电路调校       │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─ Pickup Coil ───────────────────────────── 2 根 ─┐   │
│  │                                                   │   │
│  │   Front Pickup ─→ [CROSSOVER 结] ─→ Rear Pickup  │   │
│  │        │                               │          │   │
│  │        └──→ [JJ1 | JJ2] ─→ ←──┘                  │   │
│  │                  │                                │   │
│  │              2 根引出 (超导环路两端)              │   │
│  │                                                   │   │
│  │  ⚡ CROSSOVER 结: Front顺绕→反绕Rear → 相位反转  │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─ Modulation Coil ──────────────────────── 2 根 ─┐    │
│  │                                                   │   │
│  │   AC 调制 + DC 反馈                               │   │
│  │   → 保持 SQUID 在最佳工作点 (线性区)              │   │
│  │                                                   │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ═══════════════════════════════════════════════════════  │
│  一套 = 3 (Field) + 2 (Pickup) + 2 (Mod) = 7 根        │
│  六套 = 42 根线 (室温 → ~20 mK 稀释制冷机)              │
│  ═══════════════════════════════════════════════════════  │
└──────────────────────────────────────────────────────────┘
```

---

### 🧱 Dielectric 1: hBN ~10-20 nm

### ⚛️ Layer 2: FeTeSe ~200 nm (Majorana 孕育床)

| 参数 | 值 | 来源 |
|------|----|----|
| T_c (bulk) | ~14.5 K | Hsu et al., PNAS 105, 14262 |
| Hc1 (‖c, bulk) | ~150-400 Oe | Lei et al., PRB 84, 014520 |
| Hc2 (‖c) | ~45 T | Fang et al., PRB 81, 220509(R) |
| ξ_ab | ~2-3 nm | 从 Hc2 推算 |
| λ_ab | ~400-560 nm | Biswas et al., PRB 81, 224520 |
| **Λ (Pearl, d=200nm)** | **~1.6-3.1 μm** | Λ = 2λ²/d |
| 多能隙 | Δ₁~1.5, Δ₂~2.5, Δ₃~4 meV | STM/ARPES |

**拓扑分类:** ARPES确认Dirac表面态(2023), AB振荡+helical边缘态(2025)

### 🧱 Dielectric 2-3: hBN

### 🔗 Layer 3-4: 9-QD 双阵列 (量子电容读出)

```
9条连接:
QD1: C1-E1   QD2: C3-E1   QD3: E1-E2
QD4: C2-E2   QD5: C4-E2   QD6: C1-C2
QD7: C1-C3   QD8: C4-C2   QD9: C4-C3
```

**功能:** 测量联合宇称 → 实现测量编织序列

---

## 三、读出方案完整对比

| 维度 | 通道 A: 9-QD + VNA | 通道 B: Local SQUID |
|------|-------------------|-------------------|
| 探测对象 | 联合宇称 (量子关联) | DC 磁通 (涡旋存在) |
| 物理原理 | C_q dispersive readout | SQUID V-Φ 非线性 |
| 频率 | RF 100-500 MHz | DC/低频 AC |
| 速度 | μs 量级 | ms 量级 |
| 功能 | 实现编织门 | 验证涡旋配置 |
| 可寻址性 | 9条路径可选 | 6个独立 SQUID |
| 实现层 | Layer 3-4 + PCB | Layer 0.5 + Layer 1 |

**读出流程:**
1. 启动 Layer 0 → 全 Meissner 态
2. 启动 Layer 1 field coils → 局域涡旋成核
3. **通道 B 验证:** Local SQUID 确认 6 个涡旋到位
4. **通道 A 操作:** VNA 脉冲序列 → 联合宇称测量 → 编织

---

## 四、实验验证文献

### [EXP1] Moler 组: 局域场线圈涡旋操控 ⭐⭐⭐⭐⭐
**Bishop-Van Horn, Mueller, Moler — PRB 107, 224509 (2023)**
- 用微米级 field coil 对 **200nm Nb 薄膜** 施加局域 AC 磁场
- 阈值处产生 **单个涡旋-反涡旋对**
- 反涡旋被推走, 涡旋 **受陷 (trapped) 在场线圈下方**
- 直接验证了 Layer 1 field coil 涡旋钉扎的可行性！
- 200nm Nb 薄膜, 与我们的 200nm FeTeSe 厚度一致

### [EXP2] Moler 组: SuperScreen 仿真引擎
**Bishop-Van Horn & Moler — CPC 280, 108464 (2022)**
- 开源 Python 包, 求解 2D London 方程
- 支持: 非均匀场 + 钉扎涡旋 + 多层级 + 任意几何
- 可直接用于仿真我们的 Layer 0+1+FeTeSe 结构

### [EXP3] Moler 组: Scanning SQUID 源头文献
**Björnsson PhD Thesis, Stanford (2005)**
- Moler 组扫描 SQUID 显微镜的完整描述
- DC SQUID 设计: pickup loop + JJ pair + modulation coil
- 稀释制冷机 (base 11 mK) → 与我们的 ~20 mK 环境一致
- 磁屏蔽 (三层 mu-metal, 81dB reduction)
- 灵敏度: ~7-50 μΦ₀/√Hz

### [EXP4] Moler 组 FeSe 涡旋成像
**Zhang et al., PRB 100, 024514 (2019)**
- Moler 组直接用 scanning SQUID 成像 FeSe (铁基超导体!) 中的涡旋
- 同一材料家族, 证明了 SQUID 对铁基超导体涡旋探测的可行性

---

## 五、理论文献

| # | 文献 | 状态 | 要点 |
|---|------|------|------|
| R1 | Microsoft tetron (arXiv:2507.08795) | Nature 2025 | 单发读出, 无编织 |
| R2 | Frey et al. (arXiv:2508.10106) | PRB 113, 115513 (2026) | 测量编织仿真, Editors' Suggestion |
| R3 | Hodge et al. (arXiv:2508.10107) | preprint | 投影测量 TQC, >99% fidelity |
| R4 | Hodge et al. (arXiv:2503.09800) | PRB 113, 035429 (2026) | MZM 融合动力学 |
| R5 | FeTeSe vortex MZM (Science 360, 182; Nat. Phys. 15, 1181) | 2018-2019 | 涡旋 ZBP 实验 |
| R8 | Peeters et al. (arXiv:2602.09107) | preprint 2026 | Negative hybridization |
| R9 | Ren et al. (arXiv:2309.04050) | 2023 | Fe基SC 涡旋微波读出 |
| R10 | Roy/Sau/Tewari (arXiv:2603.12256) | preprint 2026 | ⚠️ C_q+L_q combined parity probe |
| R11 | van Loo et al. (arXiv:2507.01606) | 2025 | Single-shot C_q in Kitaev chain |
| R12 | Benjadi & Egger (arXiv:2603.06482) | 2026 | Dispersive→resonant crossover theory |
| R13 | Bonderson/Freedman/Nayak (PRL 101, 010501) | 2008 | Measurement-only TQC 理论基础 |

### ⚠️ 关键警示 (2026-05-07 组会确认)
**Roy, Sau, Tewari (arXiv:2603.12256):** C_q 单独可产生 disorder 导致的 false positive。必须结合 **量子电感 L_q** 进行相敏甄别。设计需预留 L_q 测量能力。

### Microsoft Tetron 对比 (2026-05-07 组会确认)
- Tetron: 2 parallel InAs-Al nanowires, 4 MZM, trivial backbone
- 2 interferometer loops (X, Z only), 无编织能力
- Assignment errors: Z ~1%, X ~4%
- 两个时间尺度: τ_Z (内源) ≪ τ_X (外源 poisoning)

---

## 六、关键物理参数速查

| 参数 | 值 |
|------|----|
| FeTeSe ξ_ab | 2-3 nm |
| FeTeSe λ_ab | 400-560 nm |
| FeTeSe Λ (d=200nm) | 1.6-3.1 μm |
| 线圈最小间距 | >50-100 nm (>20ξ) |
| hBN ε_r (RF, ⊥) | 3.0 |
| hBN 推荐厚度 | 10-20 nm |
| LC 谐振 f₀ | 100-500 MHz |
| ΔC_q | 0.1-1 fF |
| SQUID 灵敏度 | ~7-50 μΦ₀/√Hz |
| 工作温度 | ~20 mK |

---

## 七、PCB 电路全集 (2026-05-07 组会)

详见 `/root/ai_meeting_mars_pcb_report.md`

| 参数 | 值 |
|------|----|
| 推荐方案 B 总接线数 | 44 根 (Field:12 + SQUID:12 + Mod:12 + Spiral:2 + Gate:9 + RF:2) |
| 线材 | NbTi 超导线 (0.1mm Φ) |
| 热负荷 @ MXC | ~6.4 μW (在 10-15 μW 制冷功率内) |
| Field Coil 电流 | 0-10 mA/ch, DC 恒定, 一进两出接地 |
| SQUID FLL | 6 通道, 基于 Moler 组架构, 建议 FPGA 数字 FLL |
| 射频链 | RF 源 100-500 MHz → 定向耦合器 → 衰减器 (总-60dB) → 4K LNA → IQ 混频 |
| 磁屏蔽 | 3 层 μ-metal + 超导屏蔽罐 + 各级 RC/铜粉滤波 |

## 八、Nanofab 简化方案 (2026-05-07 组会)

详见 `/root/ai_meeting_venus_nanofab_report.md`

**方案 A (推荐): 双层 resist + 单次 Nb 沉积合并 L0.5+L1**
- PMMA/P(MMA-MAA) 双层 resist + 灰度 EBL 两次曝光
- 单次 Nb 200nm 沉积同时形成 pickup loop (L0.5) 和 field coil (L1)
- 节省 1 次 lithography + 1 次金属沉积
- 自然形成 ~400nm 垂直间距

**CROSSOVER 简化: 共面 JJ 手性方案**
- Front/Rear loops 共用 SQUID body 中的 JJ pair
- "CROSSOVER" 通过 JJ 手性配置实现，不需要 lithographic air bridge
- 1 周验证时间

## 九、额外结构提案 (2026-05-07 组会)

| 优先级 | 提案 | 成本 | 价值 |
|--------|------|------|------|
| P1 | Hall Bar + Fiducial Markers | 零额外 litho | 调试必备 |
| P2 | 差分参考通道 | +1 谐振器 +1 QD | √2-2× SNR 提升 |
| P2 | Braiding Witness QDs (6个) | +6 QD | 审稿杀手锏 — 编织序列实时可视化 |
| P3 | 片上超导微波开关 (NbN KI) | 需要 NbN 工艺 | 大幅减少 RF 线 |
| P3 | CBT 温度计 | +4 线 | mK 级温度验证 |

## 十、历史版本

- v1.0 (2026-05-06): 初始架构
- v2.0 (2026-05-06): 家祥详细描述, 7组文献
- v3.0 (2026-05-07): v4 Pro 深度校准, FeTeSe参数, Rachel组动态
- v3.1 (2026-05-07): 准失超策略 + SuperScreen
- v4.0 (2026-05-07): Layer 0.5 双读出 + Moler实验验证 + Björnsson thesis
- v4.1 (2026-05-07): 同心嵌套设计 (Field coil ⊃ Pickup loop)
- v4.2 (2026-05-07): CROSSOVER 结相位反转 + Front↔Rear 全对称 + 指示灯比喻
- **v4.3 (2026-05-07): 6× 独立 SQUID = 6 指示灯, 通道 A/B 功能完全分离**
- v4.5 (2026-05-07): 精确连线设计: 7根/套, 6套=42根, Field Coil 3线一进两出
- **v5.0 (2026-05-07): 完整 GDS 版图 v3 — Counterwound SQUID, Mars生成+验证**
- **v5.1 (2026-05-07): AI组会 — PCB电路全集 + Nanofab简化 + 53篇文献索引 + 57.gds版图分析。详见 references/ai-meeting-2026-05-07.md**
- **v5.1 (2026-05-07): AI组会 — Mars PCB电路全集(44线,FLL,VNA链) + Venus nanofab简化(双层resist合并L0.5+L1,共面CROSSOVER) + Saturn 53篇文献(7角度) + Braiding Witness QD + 差分参考通道 + Roy/Sau/Tewari C_q+L_q警示**

## 十一、文件存档位置*v5.0 (2026-05-07): 完整 GDS 版图 v3 — Counterwound SQUID, Mars生成+验证**
- **v5.1 (2026-05-07): AI组会 — Mars PCB电路全集(44线,FLL,VNA链) + Venus nanofab简化(双层resist合并L0.5+L1,共面CROSSOVER) + Saturn 53篇文献(7角度) + Braiding Witness QD + 差分参考通道 + Roy/Sau/Tewari C_q+L_q警示**

## 八、文件存档位置

| 文件 | 内容 |
|------|------|
| `~/.hermes/skills/research/majorana-qubit-measurement-braiding/SKILL.md` | 本知识底座 |
| `references/ai-meeting-2026-05-07.md` | **AI组会记录：PCB/Nanofab/文献/GDS分析速查** |
| `references/comsol-setup.md` | **COMSOL 6.4 仿真环境：安装路径/mph使用/仿真域** |
| `/root/majorana_braiding_literature_report.md` | 测量编织文献 |
| `/root/FeTeSe_vortex_MZM_research_report.md` | FeTeSe 材料 |
| `/root/majorana_readout_literature_summary.md` | 量子电容读出 |
| `/root/ai_meeting_mars_pcb_report.md` | Mars: MS tetron分析 + 6-coil PCB全集 (~66KB) |
| `/root/ai_meeting_venus_nanofab_report.md` | Venus: L0.5 nanofab简化 + 额外结构 (~49KB) |
| `/root/ai_meeting_saturn_literature_report.md` | Saturn: 7角度53篇文献 (~15KB) |
| `/root/ai_meeting_summary_report.md` | Jupiter: 总报告 + 决策清单 |
| `references/pcb-readout-design-v2.md` | **PCB读出设计v2.0: 9通道FDM自洽参数 + 50Ω微带 + 螺旋电感Wheeler + Octave SNR验证** |
| `/mnt/c/Users/Admin/Desktop/majorana qubit/README_完整读出方案.md` | 完整读出方案：MS拆解→6-Coil→设备→接线 (v2.0, 已修正LC) |
| `/mnt/c/Users/Admin/Desktop/majorana qubit/PCB_参考设计_6Coil_9QD.md` | PCB参考设计 (v2.0, 已修正) |
| `/mnt/c/Users/Admin/Desktop/majorana qubit/kicad_project/` | KiCad原理图+项目文件 |
| `/root/.hermes/cache/documents/doc_a9e995f0963f_PhysRevB.107.224509.pdf` | Moler PRB 涡旋操控 |
| `/root/.hermes/cache/documents/doc_46a8b68a20eb_1-s2.0-S0010465522001837-main.pdf` | SuperScreen |
| `/root/.hermes/cache/documents/doc_50944207937e_bjornsson_thesis (1).pdf` | Björnsson thesis |
| /root/ai_meeting_venus_nanofab_report.md | 2026-05-07 组会: L0.5 nanofab简化+额外结构提案 |
| /root/ai_meeting_saturn_literature_report.md | 2026-05-07 组会: 7角度53篇文献索引 |
| /root/ai_meeting_summary_report.md | 2026-05-07 组会: Jupiter汇总报告 |

---

*"Microsoft 证明了 MZM 可以被看见。我们正在证明 MZM 可以被编织。"*
*—— 丛家祥 & Jupiter，西湖大学，2026*

*此文档由 Jupiter（木星）代表 丛家祥 创建和维护。v4.0 双读出架构，2026-05-07*
