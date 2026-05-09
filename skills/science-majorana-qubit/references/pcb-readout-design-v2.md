# PCB Readout Design v2.0 — Corrected Parameters

> Derived from 2026-05-09 session. Replaces v1.0 with self-consistent LC parameters.
> All values verified via f₀ = 1/(2π√(LC)) and Wheeler spiral inductor formula.

## Pitfalls fixed from v1.0

1. **LC不自洽 (平均误差 65.6%)**: v1.0 手动填的L和C值没有验算f₀。所有9通道的实际f₀与标称差29-124%。
2. **螺旋电感重叠**: v1.0 建议8圈/6mm外径, 填充因子1.6>1, 线圈重叠。
3. **50Ω微带线偏差**: v1.0 W=0.42mm → Z₀=46.5Ω, 修正为W=0.38mm → Z₀=50.1Ω。

## Corrected 9-Channel FDM Table

| CH | f₀ (MHz) | C_NP0 (pF) | L (nH) | Spiral | L_wheeler (nH) |
|----|----------|------------|--------|--------|-----------------|
| 1  | 200      | 1.00       | 633    | 9t,12mm| 562 (-11%)      |
| 2  | 250      | 1.00       | 405    | 7t,13mm| 358 (-12%)      |
| 3  | 300      | 0.75       | 375    | 7t,12mm| 340 (-9%)       |
| 4  | 350      | 0.75       | 276    | 6t,12mm| 250 (-9%)       |
| 5  | 400      | 0.75       | 211    | 5t,14mm| 192 (-9%)       |
| 6  | 450      | 0.50       | 250    | 6t,10mm| 224 (-10%)      |
| 7  | 500      | 0.50       | 203    | 5t,13mm| 183 (-10%)      |
| 8  | 550      | 0.50       | 167    | 5t,10mm| 156 (-7%)       |
| 9  | 600      | 0.50       | 141    | 5t,7mm | 131 (-7%)       |

Wheeler formula: L ≈ 2.34 × μ₀ × n² × d_avg / (1 + 2.75 × ρ)
Accuracy ±15%. Final L needs HFSS/CST EM simulation verification.

## 50Ω Transmission Line

- **Microstrip** (Layer 1→Layer 2, Rogers RO4003C, εr=3.38, h=0.2mm): W=**0.38mm** → Z₀=**50.1Ω** ✅
- **CPW**: W=0.30mm, G=0.22mm → Z₀≈44.6Ω. Needs parameter tuning for exact 50Ω.

## Octave Simulation Results (ΔCq=0.5fF, CH5)

| Parameter | Value |
|-----------|-------|
| SNR | 19 (25.6 dB) — single-shot feasible |
| Δf | 133 kHz |
| Δφ | 1.15° |
| P_device@MXC | -70 dBm (100 pW) — safe |
| Channel spacing/BW | 2.5× (Q=30, 50MHz spacing) |
| 9-ch self-consistency | ≤ 0.78 MHz error |

## KiCad Project Files

Generated `.kicad_sch` and `.kicad_pro` for 1-channel readout circuit (RF SMP in → coupling cap → spiral inductor + tuning cap // bias tee → bonding pad → QD gate).

Windows: Open with KiCad 8.0 via `readout_1ch.kicad_pro`.
