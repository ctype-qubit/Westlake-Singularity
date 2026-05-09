"""
Canonical COMSOL simulation template via mph.
Copy this, modify the MODEL SECTION, and run via Windows Python.

Usage (from WSL):
  /mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe script.py
"""

import mph
import json
import sys
import os
import traceback
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
OUTPUT_DIR    = r"C:\Users\Admin\hermes_comsol"
MODEL_NAME    = "MyModel"
OUTPUT_FILE   = os.path.join(OUTPUT_DIR, "result.json")
MPH_SAVE_PATH = os.path.join(OUTPUT_DIR, f"{MODEL_NAME}.mph")

result = {"status": "unknown", "steps": []}


def log(step, extra=None):
    entry = step
    if extra:
        entry = f"{step}: {extra}"
    result["steps"].append(entry)
    print(f"  [{len(result['steps'])}] {step}")


def main():
    try:
        # ── 1. START ──────────────────────────────────────────
        log("Starting COMSOL client")
        client = mph.start()
        result["comsol_version"] = client.version
        log("Connected", f"COMSOL {client.version}")

        # ── 2. CREATE/LOAD MODEL ──────────────────────────────
        log("Creating model")
        model = client.create(MODEL_NAME)

        # ══════════════════════════════════════════════════════
        # MODEL SECTION — Customize below
        # ══════════════════════════════════════════════════════

        # --- Geometry ---
        comp = model.java.component().create("comp1", True)
        geom = model.java.component("comp1").geom().create("geom1", 3)

        # Example: create a block
        geom.create("blk1", "Block")
        geom.feature("blk1").set("size", ["1[m]", "2[m]", "0.5[m]"])
        geom.run()
        log("Geometry built")

        # --- Physics ---
        # Add physics interfaces here
        # phys = model.java.component("comp1").physics().create("tag", "PhysicsType", "geom1")
        log("Physics configured")

        # --- Mesh ---
        mesh = model.java.component("comp1").mesh().create("mesh1")
        mesh.autoMeshSize(6)
        mesh.run()
        log("Mesh generated")

        # --- Study & Solve ---
        std = model.java.study().create("std1")
        std.run()
        log("Solved")

        # --- Evaluate ---
        # Use model.evaluate() or global evaluations
        # value = model.evaluate("expression", "V")
        # result["computed_value"] = value
        log("Results evaluated")

        # ══════════════════════════════════════════════════════
        # END MODEL SECTION
        # ══════════════════════════════════════════════════════

        # ── 3. SAVE & CLEANUP ─────────────────────────────────
        model.save(MPH_SAVE_PATH)
        result["model_path"] = MPH_SAVE_PATH
        log("Model saved", MPH_SAVE_PATH)

        client.remove(model)
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        log("ERROR", str(e))

    finally:
        # Write results
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
