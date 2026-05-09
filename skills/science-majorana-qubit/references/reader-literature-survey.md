# Dispersive / Quantum Capacitance Readout — Detailed Literature Survey

> Generated 2026-05-07. This file provides detailed paper-by-paper findings that complement the SKILL.md Section 五 references.

---

## Primary Experimental Papers (Majorana C_q / RF Reflectometry)

### R-A: Single-shot parity readout of a minimal Kitaev chain
- **arXiv:** 2507.01606 (July 2025)
- **Authors:** Nick van Loo, Francesco Zatelli, Gorm O. Steffensen, ..., Leo P. Kouwenhoven (TU Delft / QuTech)
- **Key result:** First demonstration of single-shot parity readout using quantum capacitance C_q in a 2-dot Kitaev chain. Parity lifetimes >1 ms. This is THE paper establishing C_q as viable Majorana parity readout.

### R-B: Gate reflectometry in a minimal Kitaev chain device
- **arXiv:** 2508.06403 (August 2025)
- **Authors:** Yining Zhang, Ivan Kulesh, ..., Srijit Goswami (TU Delft / QuTech)
- **Key result:** RF gate reflectometry resolves charge stability diagrams, distinguishes ECT from CAR, and C_q signal indicates parity switching even in closed (lead-decoupled) regime. 15 pages, 4 main + 5 supplementary figures.

### R-C: Predictive simulations of the dynamical response of mesoscopic devices
- **arXiv:** 2502.12960 (February 2025)
- **Authors:** Samuel Boutin, Torsten Karzig, ..., Roman M. Lutchyn, Bela Bauer (Microsoft Station Q)
- **Key result:** General framework for simulating dispersive gate sensing (DGS) of QDs coupled to topological superconductors. Uses tensor-network-inspired approximations to reduce the Hilbert space. Demonstrates on the Aghaee et al. (2024) parity readout setup. 28 pages, 14 figures.

### R-D: Interferometric Single-Shot Parity Measurement in InAs-Al Hybrid
- **arXiv:** 2401.09549 (2024)
- **Authors:** Morteza Aghaee et al. (Microsoft Quantum, ~150 authors)
- **Key result:** Landmark single-shot parity measurement using quantum-dot-based interferometry. This is the experimental benchmark referenced by the Boutin et al. theory paper.

### R-E: Parity readout in Majorana box qubits from the dispersive to the resonant regime
- **arXiv:** 2603.06482 (March 2026)
- **Authors:** Sara M. Benjadi, Reinhold Egger
- **Key result:** Theoretical χ_z(ω) formalism covering full crossover from resonant to dispersive regime. Lindblad master equation with decoherence channels. Semi-classical factorization valid in dispersive regime (~few % error). 12 pages, 4 figures.

### R-F: Microwave spectroscopy of Majorana vortex modes
- **arXiv:** 2309.04050 (September 2023)
- **Authors:** Zhibo Ren, Justin Copenhaver, Leonid Rokhinson, Jukka I. Väyrynen
- **Key result:** Proposes microwave-based dispersive readout of Majorana vortex pair charge — specifically for Fe-based superconductors (FeTeSe!). Microwave resonator above vortices couples to charge. 5+3 pages.

### R-G: Quantum Inductance as a Phase-Sensitive Probe of Fermion Parity Switching
- **arXiv:** 2603.12256 (March 2026)
- **Authors:** Binayyak B. Roy, Jay D. Sau, Sumanta Tewari
- **Key result:** C_q alone can give false positives from disorder-induced avoided crossings. Quantum inductance L_q provides complementary phase-sensitive information. Combined C_q + L_q = robust topological identification.

---

## hBN Dielectric Properties

### R-H: Miniaturizing transmon qubits using van der Waals materials
- **arXiv:** 2109.02824 (2021) | Published: Nano Letters (DOI: 10.1021/acs.nanolett.1c04160)
- **Authors:** Abhinandan Antony, Martin V. Gustafsson, ..., Kin Chung Fong (Raytheon BBN / Columbia / NIMS)
- **Key result:** hBN used as insulating dielectric in NbSe₂ parallel-plate capacitors for transmons. >1000× area reduction. T₁ = 1.06 μs. Proves hBN works as low-loss dielectric in superconducting quantum circuits.

### hBN Material Properties Table

| Property | Value | Notes |
|----------|-------|-------|
| Static ε_r (in-plane) | ~3.76 | Depends on crystal quality |
| Static ε_r (out-of-plane) | ~6.9 | For parallel-plate geometry |
| High-frequency ε_r (in-plane) | ~4.5 | At RF/microwave frequencies |
| High-frequency ε_r (out-of-plane) | ~3.0 | At RF/microwave frequencies |
| Band gap | ~5.9 eV | Excellent insulator |
| Breakdown field | ~0.7 V/nm (7 MV/cm) | High-quality exfoliated hBN |
| Loss tangent (tan δ) | ~10⁻⁴ – 10⁻⁵ | At mK, microwave frequencies |
| Thermal conductivity | ~400 W/m·K (in-plane) | Good for mK thermalization |
| Typical thickness in vdW devices | 1–50 nm | Few layers to tens of layers |

### Capacitance Calculation for Parallel-Plate hBN

```
C = ε₀ ε_r A / d
```
- ε_r (out-of-plane, RF) ≈ 3.0
- **Example:** A = 1 μm², d = 10 nm → C ≈ 2.66 fF
- **Example:** A = 100 × 100 nm², d = 5 nm → C ≈ 0.53 fF

**Recommended for QD coupling:** 10–20 nm hBN thickness → C_gate ~ 0.3–30 fF depending on area.

### hBN in QD-Superconductor Hybrid Devices

**Gap identified:** No dedicated papers found on hBN specifically in QD-superconductor hybrid devices for Majorana physics. This is a research opportunity. Precedent exists in:
- hBN as gate dielectric in 2D material quantum dots (graphene, TMDs)
- hBN as tunnel barrier in vdW Josephson junctions
- FeTeSe is a vdW material → natural stacking compatibility with hBN

---

## LC Resonator Design Parameters (~20 mK)

| Parameter | Typical Range | Notes |
|-----------|--------------|-------|
| Resonant frequency f₀ | 100–500 MHz | Below Al gap (~90 GHz), below FeTeSe gap (~2–4 meV) |
| Chip inductor L | 200–500 nH | Superconducting Nb or Al, Q > 10³ at mK |
| Parasitic capacitance C_p | 0.1–1 pF | On-chip + bonding pads |
| Quantum capacitance C_q | 0.1–10 fF | ΔC_q signal ~0.1–1 fF (parity-dependent) |
| Loaded Q factor | 100–1000 | Coupling-limited |
| Internal Q factor | 10³–10⁵ | Superconducting at mK |
| Carrier power | −120 to −90 dBm | Single-photon regime to avoid quasiparticle poisoning |
| Phase sensitivity | ~1–10 μrad/√Hz | State-of-the-art |
| Integration time | 1–10 μs | For >99% single-shot fidelity |

### Dispersive Regime Conditions (from Benjadi & Egger 2026)
- Detuning Δ = ω_r − ω_q must be large vs. coupling g
- Dispersive shift: χ = g²/Δ (per quantum)
- Critical photon number: n_crit = Δ²/(4g²)
- For Majorana: qubit ~ few GHz, resonator ~ 100–500 MHz → deep dispersive regime

### Signal Chain Architecture
```
RF source → directional coupler → attenuators (mK) → LC resonator + device
                                                       ↓
LNA (4K) ← isolator ← directional coupler (reflected)
    ↓
IQ mixer → digitizer → C_q extraction
```
