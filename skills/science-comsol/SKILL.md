---
name: comsol-simulation
description: Run COMSOL Multiphysics simulations via mph Python API — the Hermes→COMSOL bridge for WSL→Windows, including setup, troubleshooting, and API patterns.
---

# COMSOL Simulation via mph (WSL → Windows Bridge)

COMSOL Multiphysics 6.4 is installed on Windows at `D:\COMSOL64\Multiphysics`. The `mph` Python package provides a Pythonic interface. Because mph requires OS-level authentication (Windows), scripts must execute via **Windows Python**, not the WSL Python environment.

## Architecture

```
WSL (Hermes)                    Windows
┌──────────────┐               ┌─────────────────────────┐
│ write .py    │───/mnt/c/──→  │ C:\Users\Admin\         │
│ call win py  │──subprocess─→ │ hermes_comsol\*.py      │
│ read results │←──JSON/MPH──  │ mph.start() → COMSOL    │
└──────────────┘               │ mph.Client() → Server   │
                               └─────────────────────────┘
```

- COMSOL native auth (NTLM/Kerberos) only works from Windows processes
- WSL can execute Windows binaries (`.exe`), but the Java client process runs on Linux and can't use Windows auth
- **Workaround**: run the entire mph script via Windows Python
- mph installed in BOTH: WSL Python (for API reference/testing) AND Windows Python at `C:\Users\Admin\PyCharmMiscProject\.venv\`

## Quick Start

```bash
# From WSL, run a COMSOL script on Windows Python:
/mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe \
  "C:\Users\Admin\hermes_comsol\my_script.py"
```

Scripts should use this pattern (see `templates/comsol_template.py`):
```python
import mph
client = mph.start()           # auto-handles server + auth + connect
model = client.create('Name')  # or client.load('file.mph')
# ... build, solve, evaluate ...
model.save('output.mph')
client.remove(model)
```

## COMSOL Installation Details

| Item | Value |
|------|-------|
| Version | 6.4.0.293 |
| Path (Windows) | `D:\COMSOL64\Multiphysics` |
| Path (WSL) | `/mnt/d/COMSOL64/Multiphysics` |
| Server exe | `bin/win64/comsolmphserver.exe` |
| Licensed modules | 47 (AC/DC, RF, Semiconductor, Structural Mechanics, Wave Optics, ...) |
| WSL work dir | `C:\Users\Admin\hermes_comsol\` ↔ `/mnt/c/Users/Admin/hermes_comsol/` |
| Windows Python | `C:\Users\Admin\PyCharmMiscProject\.venv\Scripts\python.exe` |

## API Pitfalls

### Study creation
mph's `Node.create()` passes a type argument even for studies, causing:
```
StudyListClient.create(String, String) — no matching overload
```
**Fix**: use Java API directly:
```python
std = model.java.study().create("std1")
std.run()
```

### Energy/post-solve evaluation
The client-side physics object in client-server mode may not expose all methods that the server-side API has. Some evaluation methods (e.g., `intTotalEnergy()`) may not exist on the client proxy.
**Workaround**: use mph's `model.evaluate()` or global evaluation nodes:
```python
(model/'evaluations').create('EvalGlobal')
# ... configure expression ...
```

### mph model creation API (2026-05-09 verified)
The mph Python API uses `model.create()` for all node types, NOT dotted attribute access:
```python
# ✅ CORRECT (mph 1.x):
comp = model.create('Component', 'comp1')
geom = comp.create('Geometry', 'geom1')
emw = comp.create('Physics', 'emw', 'ElectromagneticWaves')
std = model.create('Study', 'std1')

# ❌ WRONG — these DO NOT exist:
model.comments("...")         # AttributeError: no 'comments'
model.component('comp1')       # AttributeError: no 'component'
comp.geom('geom1')             # AttributeError: no 'geom'
```

**Geometry creation** uses `WorkPlane` for 2D sketches:
```python
wp = geom.create('WorkPlane', 'wp1')
sk = wp.create('Polygon', 'spiral')
sk.property('x', [x0, x1, ...])  # list of x-coords
sk.property('y', [y0, y1, ...])  # list of y-coords
geom.run()  # IMPORTANT: must call run() after geometry changes
```

**Parameter creation**: `model.create('Parameter', 'name', 'value')`.

**Frequency study**: use `range()` syntax:
```python
freq.property('frequencies', 'range(100[MHz],50[MHz],600[MHz])')
```

### Octave as lightweight alternative
When COMSOL is unavailable or too slow, GNU Octave can do RF circuit S-parameter simulations. Install via `apt-get install -y octave`. Useful for:
- LC resonator frequency sweeps
- S-parameter chain budgets (directional coupler → attenuator → LNA)
- SNR estimation from ΔCq
- Channel spacing/FDM analysis

See `references/octave-rf-chain-simulation.md` for a complete worked example.

### mph on WSL (not needed for running, only for reference)
- Install: `pip3 install mph` (works)
- Discovery fails because mph looks for Linux COMSOL in `/usr/local`, not Windows
- Even with symlinks, client-server auth fails cross-platform
- Use WSL mph only for `help()` / doc lookup, never for running simulations

## Script Execution Pattern

Always: write script → save to `/mnt/c/Users/Admin/hermes_comsol/` → execute via Windows Python → read JSON results or .mph output.

For JSON result passing, scripts should:
1. Accept parameters via CLI args or input file
2. Save results to a JSON file
3. Print JSON to stdout (parsed by caller)

See `templates/comsol_template.py` for the canonical template.

## Verification

Run the capacitor test:
```bash
/mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe \
  "C:\Users\Admin\hermes_comsol\test_simulation.py"
```
Should produce `capacitor_test.mph` and report `status: success`.
