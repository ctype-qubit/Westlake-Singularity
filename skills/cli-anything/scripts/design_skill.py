#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 2 -- Map analysis.json to architecture.json.

Reads the analysis produced by ``analyze_target.py``, selects an appropriate
skill structure based on the detected target type, and writes an
``architecture.json`` that ``init_skill.py`` and later phases consume.

Usage:
    python design_skill.py --analysis analysis.json [--config config.yaml] \
        [--output architecture.json]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Config loading (pyyaml optional)
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """Load a YAML file. Falls back to a naive parser if pyyaml is absent."""
    try:
        import yaml  # type: ignore[import-untyped]
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        pass

    # Minimal fallback: handles flat key: value and simple lists.
    data: dict = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                val = val.strip().strip('"').strip("'")
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
                elif val in ("true", "True"):
                    val = True
                elif val in ("false", "False"):
                    val = False
                elif val in ("null", "None", "~", ""):
                    val = None
                data[key.strip()] = val
    return data


# ---------------------------------------------------------------------------
# Skill-type specific structure builders
# ---------------------------------------------------------------------------

def _to_kebab(name: str) -> str:
    """Convert a name to kebab-case."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name)
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", s)
    return s.strip("-").lower()


def _base_architecture(analysis: dict, config: dict) -> dict:
    """Return the common skeleton shared by all skill types."""
    skill_name = _to_kebab(
        config.get("output", {}).get("skill_name")
        or analysis.get("target_name", "unnamed-skill")
    )
    return {
        "skill_name": skill_name,
        "skill_type": analysis.get("target_type", "unknown"),
        "target_name": analysis.get("target_name", ""),
        "confidence": analysis.get("confidence", 0),
        "designed_at": datetime.now(timezone.utc).isoformat(),
        "structure": {
            "sections": [],
            "scripts": [],
            "references": [],
        },
        "triggers": [],
        "platforms": config.get("platforms", {}).get("enabled", ["claude-code"]),
        "primary_platform": config.get("platforms", {}).get("primary", "claude-code"),
    }


def _design_cli(arch: dict, analysis: dict) -> dict:
    """CLI tool-augmentation design."""
    arch["skill_type"] = "tool-augmentation"

    capabilities = analysis.get("capabilities", [])
    command_examples = []
    for cap in capabilities:
        name = cap.get("name", "")
        desc = cap.get("description", "")
        command_examples.append({"command": name, "description": desc})

    arch["structure"]["sections"] = [
        "overview",
        "usage",
        "command-reference",
        "examples",
        "error-handling",
        "troubleshooting",
    ]
    arch["structure"]["scripts"] = ["run_command.sh"]
    arch["structure"]["references"] = ["help-output.txt"]
    arch["command_examples"] = command_examples

    # Trigger keywords from capability names and descriptions
    triggers = set()
    triggers.add(analysis.get("target_name", ""))
    for cap in capabilities:
        triggers.add(cap.get("name", ""))
        for word in cap.get("description", "").split()[:3]:
            if len(word) > 3:
                triggers.add(word.lower())
    arch["triggers"] = sorted(t for t in triggers if t)

    return arch


def _design_api(arch: dict, analysis: dict) -> dict:
    """API integration design."""
    arch["skill_type"] = "api-integration"

    endpoints = []
    for cap in analysis.get("capabilities", []):
        endpoints.append({
            "name": cap.get("name", ""),
            "description": cap.get("description", ""),
        })

    arch["structure"]["sections"] = [
        "overview",
        "authentication",
        "endpoints",
        "request-examples",
        "response-handling",
        "error-codes",
    ]
    arch["structure"]["scripts"] = ["call_api.sh"]
    arch["structure"]["references"] = ["openapi-spec.json"]
    arch["endpoint_references"] = endpoints

    triggers = {analysis.get("target_name", "")}
    for ep in endpoints:
        for word in ep.get("name", "").split():
            w = word.strip("/").lower()
            if len(w) > 2 and w not in ("get", "post", "put", "delete", "patch"):
                triggers.add(w)
    arch["triggers"] = sorted(t for t in triggers if t)

    return arch


def _design_library(arch: dict, analysis: dict) -> dict:
    """Library capability-wrapper design."""
    arch["skill_type"] = "capability-wrapper"

    usage_patterns = []
    for cap in analysis.get("capabilities", []):
        usage_patterns.append({
            "symbol": cap.get("name", ""),
            "description": cap.get("description", ""),
        })

    arch["structure"]["sections"] = [
        "overview",
        "installation",
        "core-api",
        "usage-patterns",
        "advanced-usage",
        "troubleshooting",
    ]
    arch["structure"]["scripts"] = []
    arch["structure"]["references"] = ["source-files.txt"]
    arch["usage_patterns"] = usage_patterns

    triggers = {analysis.get("target_name", "")}
    for pat in usage_patterns[:10]:
        triggers.add(pat.get("symbol", "").lower())
    arch["triggers"] = sorted(t for t in triggers if t)

    return arch


def _design_workflow(arch: dict, analysis: dict) -> dict:
    """Workflow orchestrator design."""
    arch["skill_type"] = "workflow-orchestrator"

    steps = []
    for i, cap in enumerate(analysis.get("capabilities", []), 1):
        steps.append({
            "step": i,
            "name": cap.get("name", f"step-{i}"),
            "description": cap.get("description", ""),
        })

    arch["structure"]["sections"] = [
        "overview",
        "prerequisites",
        "workflow-steps",
        "decision-points",
        "outputs",
        "troubleshooting",
    ]
    arch["structure"]["scripts"] = ["run_workflow.sh"]
    arch["structure"]["references"] = ["workflow-diagram.md"]
    arch["step_instructions"] = steps

    triggers = {analysis.get("target_name", "")}
    for step in steps:
        for word in step.get("name", "").split():
            if len(word) > 3:
                triggers.add(word.lower())
    arch["triggers"] = sorted(t for t in triggers if t)

    return arch


def _design_service(arch: dict, analysis: dict) -> dict:
    """Service connector design."""
    arch["skill_type"] = "service-connector"

    actions = []
    for cap in analysis.get("capabilities", []):
        actions.append({
            "action": cap.get("name", ""),
            "description": cap.get("description", ""),
        })

    arch["structure"]["sections"] = [
        "overview",
        "connection-setup",
        "available-actions",
        "action-examples",
        "error-handling",
        "troubleshooting",
    ]
    arch["structure"]["scripts"] = ["connect.sh"]
    arch["structure"]["references"] = ["service-docs.md"]
    arch["action_mappings"] = actions

    triggers = {analysis.get("target_name", "")}
    for act in actions:
        for word in act.get("action", "").split():
            w = word.strip("/").lower()
            if len(w) > 3:
                triggers.add(w)
    arch["triggers"] = sorted(t for t in triggers if t)

    return arch


_DESIGNERS = {
    "cli": _design_cli,
    "api": _design_api,
    "library": _design_library,
    "workflow": _design_workflow,
    "service": _design_service,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def design(analysis: dict, config: dict | None = None) -> dict:
    """Build architecture dict from analysis and optional config."""
    config = config or {}
    arch = _base_architecture(analysis, config)
    target_type = analysis.get("target_type", "unknown")
    designer = _DESIGNERS.get(target_type)
    if designer:
        arch = designer(arch, analysis)
    else:
        # Fallback: generic design
        arch["skill_type"] = "generic"
        arch["structure"]["sections"] = ["overview", "usage", "examples", "troubleshooting"]
        arch["triggers"] = [analysis.get("target_name", "")]
    return arch


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map analysis.json to skill architecture.json.",
    )
    parser.add_argument("--analysis", required=True, help="Path to analysis.json.")
    parser.add_argument("--config", default=None, help="Path to config.yaml (optional).")
    parser.add_argument("--output", default="architecture.json", help="Output path (default: architecture.json).")
    args = parser.parse_args()

    analysis_path = Path(args.analysis)
    if not analysis_path.is_file():
        print(f"Error: analysis file not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    analysis = json.loads(analysis_path.read_text())
    config = _load_yaml(args.config) if args.config else {}

    arch = design(analysis, config)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(arch, indent=2, ensure_ascii=False) + "\n")
    print(f"Architecture written to {out_path}")


if __name__ == "__main__":
    main()
