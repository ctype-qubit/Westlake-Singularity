# Code Obfuscation Guide

How to protect SkillAnything's proprietary scripts using PyArmor while respecting open-source
license obligations.

---

## What to Obfuscate

Obfuscation applies only to SkillAnything's original scripts. Never obfuscate code derived from
Apache 2.0 licensed sources (CLI-Anything, Dazhuang Skill Creator, Anthropic Skill Creator) or
any other third-party code.

### Scripts to Obfuscate

These are SkillAnything originals listed in `config.yaml` under `obfuscation.protect_scripts`:

| Script | Phase | Purpose |
|--------|-------|---------|
| `analyze_target.py` | 1 | Target analysis and classification |
| `design_skill.py` | 2 | Skill architecture generation |
| `init_skill.py` | 3 | Skill directory scaffolding |
| `generate_tests.py` | 4 | Eval and trigger query generation |
| `package_multiplatform.py` | 7 | Multi-platform packaging |
| `obfuscate.py` | -- | The obfuscation wrapper itself |

### Scripts to NOT Obfuscate

- Any script adapted from Apache 2.0 licensed projects
- Third-party libraries and dependencies
- Agent markdown files (`agents/*.md`) -- these are plain text instructions
- Template files (`templates/**`) -- these are user-facing scaffolds
- Eval runner scripts derived from open-source eval frameworks
- Generated skill scripts (the output belongs to the user)

### How to Decide

If a script was written entirely by the SkillAnything team and does not derive from any
open-source project, it can be obfuscated. When in doubt, check the `NOTICE` file for
attribution requirements.

---

## Installing PyArmor

PyArmor is a Python tool for obfuscating Python scripts. It transforms source code into
bytecode protected by a runtime shield.

### Requirements

- Python 3.8 or later
- pip

### Installation

```bash
pip install pyarmor
```

Verify installation:

```bash
pyarmor --version
```

### License

PyArmor has a free tier for non-commercial use and trial purposes. Commercial distribution
requires a PyArmor license. See https://pyarmor.dashingsoft.com/ for license details.

---

## Running Obfuscation

### Using the SkillAnything Wrapper

The recommended approach uses the built-in obfuscation script:

```bash
python -m scripts.obfuscate --config config.yaml --output dist/obfuscated/
```

This reads `obfuscation.protect_scripts` from config.yaml and obfuscates each listed script.

### Manual Obfuscation

To obfuscate individual scripts directly with PyArmor:

```bash
# Obfuscate a single script
pyarmor gen scripts/analyze_target.py

# Obfuscate with output directory
pyarmor gen -O dist/obfuscated/scripts/ scripts/analyze_target.py

# Obfuscate multiple scripts
pyarmor gen -O dist/obfuscated/scripts/ \
  scripts/analyze_target.py \
  scripts/design_skill.py \
  scripts/init_skill.py \
  scripts/generate_tests.py \
  scripts/package_multiplatform.py \
  scripts/obfuscate.py
```

### PyArmor Options

Commonly used options for SkillAnything:

| Option | Purpose |
|--------|---------|
| `-O <dir>` | Output directory for obfuscated files |
| `--platform <name>` | Target platform (linux.x86_64, darwin.x86_64, windows.x86_64) |
| `--restrict` | Restrict obfuscated scripts from being imported by non-obfuscated code |
| `--pack` | Pack into a single executable |

### Cross-Platform Builds

To distribute for multiple platforms:

```bash
# macOS (Intel)
pyarmor gen --platform darwin.x86_64 -O dist/macos-x64/scripts/ scripts/*.py

# macOS (Apple Silicon)
pyarmor gen --platform darwin.aarch64 -O dist/macos-arm64/scripts/ scripts/*.py

# Linux
pyarmor gen --platform linux.x86_64 -O dist/linux-x64/scripts/ scripts/*.py

# Windows
pyarmor gen --platform windows.x86_64 -O dist/windows-x64/scripts/ scripts/*.py
```

---

## Verifying Obfuscated Code

After obfuscation, verify that the protected scripts still work correctly.

### Basic Verification

```bash
# Run the obfuscated script to check it executes
python dist/obfuscated/scripts/analyze_target.py --help

# Run the full pipeline with obfuscated scripts
cd dist/obfuscated/
python -m scripts.analyze_target --target "jq" --output test-analysis.json
```

### Automated Verification

Run the existing eval suite against obfuscated scripts to ensure behavior is identical:

```bash
# Point the pipeline at obfuscated scripts
SA_SCRIPTS_DIR=dist/obfuscated/scripts/ python -m scripts.run_eval \
  --eval-set sa-workspace/<skill-name>/evals/evals.json \
  --skill-path sa-workspace/<skill-name>
```

### Checklist

- [ ] Each obfuscated script runs without import errors
- [ ] `--help` output is identical to the original
- [ ] Full pipeline produces the same analysis.json for a known target
- [ ] Eval scores match within variance of non-obfuscated runs
- [ ] No PyArmor runtime files are missing from the distribution

---

## Distribution Variants

SkillAnything supports two distribution modes:

### Open Source Distribution

All scripts are distributed as plain Python source. Suitable for community editions,
self-hosted deployments, and contributions.

```
dist/
  scripts/
    analyze_target.py       (source)
    design_skill.py         (source)
    init_skill.py           (source)
    generate_tests.py       (source)
    package_multiplatform.py (source)
  agents/
  templates/
  config.yaml
```

Configuration:

```yaml
obfuscation:
  enabled: false
```

### Commercial Distribution

Proprietary scripts are obfuscated. Open-source-derived scripts remain as source (per
Apache 2.0 license requirements). Agent files and templates remain as plain text.

```
dist/
  scripts/
    analyze_target.py       (obfuscated)
    design_skill.py         (obfuscated)
    init_skill.py           (obfuscated)
    generate_tests.py       (obfuscated)
    package_multiplatform.py (obfuscated)
    run_eval.py             (source — Apache 2.0 derived)
    aggregate_benchmark.py  (source — Apache 2.0 derived)
    improve_description.py  (source — Apache 2.0 derived)
    run_loop.py             (source — Apache 2.0 derived)
  pyarmor_runtime/          (PyArmor runtime files — must be included)
  agents/
  templates/
  config.yaml
  NOTICE                    (attribution file — required)
```

Configuration:

```yaml
obfuscation:
  enabled: true
  tool: pyarmor
  protect_scripts:
    - analyze_target.py
    - design_skill.py
    - init_skill.py
    - generate_tests.py
    - package_multiplatform.py
    - obfuscate.py
```

### Important Notes

1. The `NOTICE` file must always be included in distributions, per Apache 2.0 requirements.
2. The `pyarmor_runtime/` directory must be bundled with commercial distributions -- obfuscated
   scripts will not run without it.
3. Generated skills (the output of the pipeline) are never obfuscated. They belong to the user.
4. Agent markdown files are never obfuscated. They are instructions, not executable code.
