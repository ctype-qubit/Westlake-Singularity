# SuperScreen: 2D Superconducting Film Magnetic Response — Key Equations

> Source: Bishop-Van Horn & Moler, Computer Physics Communications 280, 108464 (2022)
> GitHub: github.com/loganbvh/superscreen

## Brandt-Clem 2D London Equation

For a thin superconducting film (thickness d ≪ λ), the 2D London equation in terms of the stream function g(⃗r):

```
H_z,applied(⃗r) = −∫_F [Q_z(⃗r,⃗r′) − δ(⃗r−⃗r′)∇²] g(⃗r′) d²r′
```

where:
- g(⃗r): stream function, related to sheet current density ⃗J = ⃗∇ × (g ẑ)
- Q_z(⃗r,⃗r′): kernel function for out-of-plane field
- F: film region
- Λ = 2λ²/d: Pearl effective penetration depth

## Vortex in Thin Film

A vortex at position ⃗r_v modifies the equation by adding:
```
H_z,applied(⃗r) − Σ_v (Φ_v/μ₀) δ(⃗r − ⃗r_v)
```

## Pearl Vortex Magnetic Field (Analytic)

Fourier transform of H_z for a Pearl vortex at origin:
```
˜H_z(⃗k, z) = (Φ₀/μ₀) e^{−|⃗k|z} / (1 + 2Λ|⃗k|)
```

Real-space via inverse Fourier transform: H_z(⃗r, z) = F⁻¹{˜H_z(⃗k, z)}

## Fluxoid

For a 2D region S with boundary ∂S:
```
Φ_f^S = ∫_S μ₀ H_z(⃗r) d²r + ∮_{∂S} μ₀Λ ⃗J(⃗r) · d⃗r
```

Path-independent for regions with no holes or vortices. Φ_f^S = nΦ₀ for multiply-connected films.

## Multi-layer & Vortex Modeling

SuperScreen supports:
- Multiple superconducting layers at different heights
- Vortices pinned at arbitrary positions with configurable flux quanta
- Arbitrary 2D geometry (polygons, holes, combinations)
- Spatially-varying Λ(x,y)
- Applied inhomogeneous H_z(x,y,z)
- Hole circulating currents for fluxoid state control

## Relevance to Our Architecture

Models exactly: Layer 0 (global field) + Layer 1 (local micro-coil fields) + FeTeSe thin film + pinned vortices at coil centers.
