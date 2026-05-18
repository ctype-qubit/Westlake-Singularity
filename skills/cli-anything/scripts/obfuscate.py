#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 7 -- PyArmor obfuscation wrapper.

Reads config.yaml to determine which scripts to protect, verifies they are
not Apache 2.0 derived files, runs PyArmor on each, and copies everything
to an output directory.

Usage:
    python obfuscate.py --config config.yaml \
        [--input-dir ./scripts] [--output-dir ./dist-protected]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Apache 2.0 exclusion list
# ---------------------------------------------------------------------------
# These scripts are derived from Apache 2.0 licensed code and must NOT be
# obfuscated.  They should be distributed in source form with proper license
# headers intact.

APACHE_EXCLUSIONS: set[str] = {
    "run_eval.py",
    "improve_description.py",
    "run_loop.py",
    "run_trigger_eval.py",
    "eval_runner.py",
    "eval_harness.py",
    "quick_validate.py",
    "package_skill.py",
}


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """Load YAML with pyyaml or naive fallback."""
    try:
        import yaml  # type: ignore[import-untyped]
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        pass

    data: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    with open(path) as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line[0].isspace() and ":" in stripped:
                # Save previous list
                if current_key and current_list is not None:
                    data[current_key] = current_list
                    current_list = None
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.startswith("[") and val.endswith("]"):
                    data[key] = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
                    current_key = None
                elif val in ("true", "True"):
                    data[key] = True
                    current_key = None
                elif val in ("false", "False"):
                    data[key] = False
                    current_key = None
                elif val in ("null", "None", "~", ""):
                    data[key] = None
                    current_key = key
                else:
                    data[key] = val
                    current_key = None
            elif stripped.startswith("- ") and current_key:
                if current_list is None:
                    current_list = []
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
        if current_key and current_list is not None:
            data[current_key] = current_list
    return data


def _get_protect_scripts(config: dict) -> list[str]:
    """Extract the list of scripts to protect from config."""
    obfuscation = config.get("obfuscation", {})
    if isinstance(obfuscation, dict):
        scripts = obfuscation.get("protect_scripts", [])
        if isinstance(scripts, list):
            return scripts
    return []


# ---------------------------------------------------------------------------
# PyArmor check
# ---------------------------------------------------------------------------

def _check_pyarmor() -> bool:
    """Return True if pyarmor is available."""
    try:
        result = subprocess.run(
            ["pyarmor", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


# ---------------------------------------------------------------------------
# Obfuscation
# ---------------------------------------------------------------------------

def obfuscate(
    config_path: str,
    input_dir: str,
    output_dir: str,
) -> dict:
    """Run obfuscation pipeline. Returns a summary dict."""
    config = _load_yaml(config_path)

    obfuscation_cfg = config.get("obfuscation", {})
    if isinstance(obfuscation_cfg, dict) and not obfuscation_cfg.get("enabled", False):
        print("Warning: obfuscation.enabled is false in config. Proceeding anyway.")

    protect_scripts = _get_protect_scripts(config)
    if not protect_scripts:
        print("No scripts listed in obfuscation.protect_scripts. Nothing to do.")
        return {"protected": [], "copied": [], "skipped": [], "errors": []}

    if not _check_pyarmor():
        print("Error: pyarmor is not installed or not in PATH.", file=sys.stderr)
        print("Install it with: pip install pyarmor", file=sys.stderr)
        sys.exit(1)

    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    protected: list[str] = []
    copied: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    # Process scripts listed for protection
    for script_name in protect_scripts:
        src = inp / script_name
        if not src.is_file():
            errors.append(f"{script_name}: not found in {inp}")
            continue

        if script_name in APACHE_EXCLUSIONS:
            print(f"  SKIP (Apache 2.0): {script_name}")
            skipped.append(script_name)
            # Copy as-is instead
            shutil.copy2(src, out / script_name)
            copied.append(script_name)
            continue

        print(f"  Protecting: {script_name} ... ", end="", flush=True)
        try:
            result = subprocess.run(
                ["pyarmor", "gen", "-O", str(out), str(src)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print("OK")
                protected.append(script_name)
            else:
                print("FAILED")
                stderr = result.stderr.strip()
                errors.append(f"{script_name}: pyarmor failed -- {stderr[:200]}")
                # Copy source as fallback
                shutil.copy2(src, out / script_name)
                copied.append(script_name)
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            errors.append(f"{script_name}: pyarmor timed out")
            shutil.copy2(src, out / script_name)
            copied.append(script_name)
        except OSError as exc:
            print("ERROR")
            errors.append(f"{script_name}: {exc}")

    # Copy all non-protected scripts as-is
    if inp.is_dir():
        for src_file in sorted(inp.glob("*.py")):
            name = src_file.name
            if name in protect_scripts:
                continue  # Already handled
            dest = out / name
            if not dest.exists():
                shutil.copy2(src_file, dest)
                copied.append(name)

    summary = {
        "protected": protected,
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
    }

    # Print summary
    print(f"\nObfuscation summary:")
    print(f"  Protected:  {len(protected)} files")
    print(f"  Copied:     {len(copied)} files (unprotected)")
    print(f"  Skipped:    {len(skipped)} files (Apache 2.0)")
    if errors:
        print(f"  Errors:     {len(errors)}")
        for err in errors:
            print(f"    - {err}")

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PyArmor obfuscation wrapper for SkillAnything scripts.",
    )
    parser.add_argument("--config", required=True, help="Path to config.yaml.")
    parser.add_argument("--input-dir", default="./scripts", help="Scripts directory (default: ./scripts).")
    parser.add_argument("--output-dir", default="./dist-protected", help="Output directory (default: ./dist-protected).")
    args = parser.parse_args()

    if not Path(args.config).is_file():
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    if not Path(args.input_dir).is_dir():
        print(f"Error: input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    obfuscate(
        config_path=args.config,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
