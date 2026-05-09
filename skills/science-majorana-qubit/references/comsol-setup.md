# COMSOL Simulation Environment

## Installation
- **Product**: COMSOL Multiphysics 6.4.0.293
- **Location**: `D:\COMSOL64\Multiphysics` (Windows) / `/mnt/d/COMSOL64/Multiphysics` (WSL)
- **COMSOL with Python**: Server binary at `bin/win64/comsolmphserver.exe`
- **mph Python package**: NOT installed by default — must `pip install mph` separately

## Current Python Environments (checked 2026-05-07)
- WSL `/usr/bin/python3`: no mph
- Windows Store Python: no mph
- PyCharm venv `/mnt/c/Users/Admin/PyCharmMiscProject/.venv/`: no mph

## Usage Workflow
1. On Windows, start the COMSOL server:
   ```
   D:\COMSOL64\Multiphysics\bin\win64\comsolmphserver.exe
   ```
2. In Python (any environment with `mph` installed):
   ```python
   import mph
   client = mph.Client()
   model = client.create("Model")  # or client.load("existing.mph")
   ```
3. Build geometry, set physics, mesh, solve, extract results — all via Python API.

## Relevant Simulation Domains for Majorana Project
- Magneto-static field from 6-coil configuration + spiral background
- RF/microwave LC resonator + quantum capacitance readout
- Thermal: dilution fridge ~20mK, heat load from wiring
- Mechanical stress on FeTeSe/hBN heterostructure

## Notes
- `comsolmphserver.exe` must run on Windows (not WSL). Python client can be on WSL but connection goes over localhost.
- COMSOL license must be active on the Windows side.
- For parameter sweeps, use `client.load()` + parametric sweep — much faster than GUI interaction.
