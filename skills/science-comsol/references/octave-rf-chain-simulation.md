# Octave RF Chain Simulation — Worked Example

> Generated 2026-05-09 for 6-Coil + 9-QD readout validation.
> GNU Octave 8.4.0. No toolboxes needed beyond core.

## What this simulates

1. **LC resonator S11** around resonance: |S11| and phase vs frequency
2. **Quantum capacitance response**: ΔCq → Δf → Δφ derivation
3. **Full signal chain budget**: RF source → directional coupler → 60dB attenuator chain → TWPA → HEMT LNA → room-temp amplifier
4. **SNR estimation**: carrier amplitude, noise floor, single-shot feasibility
5. **9-channel FDM validation**: all f₀ = 1/(2π√(LC)) self-consistent

## Key results (ΔCq = 0.5 fF, CH5: 400 MHz, L=211nH, C=0.75pF, Q=30)

| Parameter | Value | Notes |
|-----------|-------|-------|
| SNR | **19 (25.6 dB)** | Single-shot feasible |
| Δf | 133 kHz | From ΔCq=0.5fF |
| Δφ | 1.15° | Phase shift at resonance |
| P_device | -70 dBm (100 pW) | Safe, no device heating |
| T_sys | 3 K | HEMT noise temperature |
| 9-ch self-consistency | ≤ 0.78 MHz error | All channels verified |

## Pitfalls caught

1. **LC self-consistency**: Must verify f₀ = 1/(2π√(LC)) for EACH channel. Original report had 65% average error because L and C were filled in manually without calculation.
2. **Spacing/BW ratio**: Q=30, BW_max=20MHz@600MHz, 50MHz spacing → 2.5×. Slightly below 3× ideal but workable. Recommend Q≥35 for better isolation.
3. **Octave signal package**: Not needed for basic RF simulation. Remove `pkg load signal` line.

## Script template

Save as `.m` file, run with `octave --no-gui script.m`:
```octave
f0 = 400e6; L = 211e-9; C = 0.75e-12; Q = 30;
Delta_Cq = 0.5e-15;
f = linspace(f0 - 5*f0/Q, f0 + 5*f0/Q, 1000);
w = 2*pi*f;
Z_res = 1 ./ (1./(1i*w*L) + 1i*w*C);
R_parallel = Q * w(round(end/2)) * L;
Z_res_lossy = 1 ./ (1./Z_res + 1/R_parallel);
S11 = (Z_res_lossy - 50) ./ (Z_res_lossy + 50);
Delta_f = -f0 * Delta_Cq / (2*C);
Delta_phase = -2 * Q * Delta_f / f0;
% ... chain budget, SNR calculation ...
```

## Integration with COMSOL

Octave gives circuit-level S-parameters and SNR. For EM-level validation (spiral inductor L and Q, transmission line Z₀), use COMSOL RF Module via the `comsol-simulation` skill.
