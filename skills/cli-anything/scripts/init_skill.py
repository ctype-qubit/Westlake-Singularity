#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 3 -- Scaffold a skill directory from templates.

Creates the standard skill directory layout, populating templates with
data from analysis.json and architecture.json when provided.

Usage:
    python init_skill.py my-skill [--template cli] [--output ./skills] \
        [--analysis analysis.json] [--architecture architecture.json]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template


# ---------------------------------------------------------------------------
# Template loading and rendering
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLD_DIR = _PROJECT_ROOT / "templates" / "skill-scaffold"


def _render(template_text: str, variables: dict) -> str:
    """Perform simple template rendering.

    Supports both ``{{ var }}`` (Jinja2-style) and ``$var`` / ``${var}``
    (Python string.Template). Unknown placeholders are left as-is so that
    downstream tools (or humans) can fill them in.
    """
    # First pass: Jinja2-style {{ var }}
    import re
    def _jinja_replace(m: re.Match) -> str:
        key = m.group(1).strip()
        # Handle simple filters like | default(...)
        key_clean = key.split("|")[0].strip()
        return str(variables.get(key_clean, m.group(0)))

    text = re.sub(r"\{\{\s*(.+?)\s*\}\}", _jinja_replace, template_text)

    # Strip Jinja2 block tags we cannot evaluate ({% ... %})
    text = re.sub(r"\{%.*?%\}", "", text)

    # Second pass: Python string.Template (safe_substitute keeps unknowns)
    try:
        text = Template(text).safe_substitute(variables)
    except (ValueError, KeyError):
        pass

    return text


def _load_template(name: str) -> str:
    """Load a template file from the scaffold directory.  Returns empty string
    if the file does not exist."""
    path = _SCAFFOLD_DIR / name
    if path.is_file():
        return path.read_text()
    return ""


# ---------------------------------------------------------------------------
# Skeleton generators for each template type
# ---------------------------------------------------------------------------

_SECTION_HINTS = {
    "cli": {
        "usage_section": (
            "Run the tool via your terminal. The skill exposes the following commands:\n\n"
            "```bash\n# TODO: Add command examples\n```"
        ),
        "overview": "This skill wraps the **{target_name}** CLI tool, giving the AI agent "
                     "the ability to invoke it on your behalf.",
    },
    "api": {
        "usage_section": (
            "The skill calls the API endpoints listed below.  Authentication tokens "
            "should be provided via environment variables.\n\n"
            "```bash\n# TODO: Add curl / fetch examples\n```"
        ),
        "overview": "This skill integrates with the **{target_name}** API, allowing the AI "
                     "agent to make requests and interpret responses.",
    },
    "library": {
        "usage_section": (
            "Import the library and call functions directly from the AI agent context.\n\n"
            "```python\n# TODO: Add usage examples\n```"
        ),
        "overview": "This skill wraps the **{target_name}** library, exposing its "
                     "capabilities to the AI agent.",
    },
    "workflow": {
        "usage_section": (
            "Follow the step-by-step workflow below.  The AI agent will guide you "
            "through each stage.\n\n1. TODO: Step 1\n2. TODO: Step 2"
        ),
        "overview": "This skill orchestrates the **{target_name}** workflow.",
    },
    "service": {
        "usage_section": (
            "Connect to the service using the credentials/config described below.\n\n"
            "```bash\n# TODO: Add connection examples\n```"
        ),
        "overview": "This skill connects to the **{target_name}** service.",
    },
    "generic": {
        "usage_section": "TODO: Describe how to use this skill.",
        "overview": "This skill enables AI-assisted interaction with **{target_name}**.",
    },
}


def _build_variables(
    skill_name: str,
    template_type: str,
    analysis: dict | None,
    architecture: dict | None,
) -> dict:
    """Merge all sources into a flat variable dict for template rendering."""
    target_name = ""
    if analysis:
        target_name = analysis.get("target_name", skill_name)
    elif architecture:
        target_name = architecture.get("target_name", skill_name)
    else:
        target_name = skill_name

    hints = _SECTION_HINTS.get(template_type, _SECTION_HINTS["generic"])

    variables: dict = {
        "skill_name": skill_name,
        "target_name": target_name,
        "target_type": (analysis or {}).get("target_type", template_type),
        "title": skill_name.replace("-", " ").title(),
        "description": f"AI skill for {target_name}.",
        "overview": hints["overview"].format(target_name=target_name),
        "usage_section": hints["usage_section"],
        "examples_section": "",
        "advanced_section": "",
        "scripts_reference": "",
        "troubleshooting_section": "If something goes wrong, check the logs and verify your configuration.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_url": "null",
        "target_path": "null",
        "analysis_hash": "none",
        "primary_platform": "claude-code",
    }

    # Overlay analysis data
    if analysis:
        variables["target_url"] = analysis.get("target_url", "null")
        variables["target_path"] = analysis.get("target_path", "null")
        caps = analysis.get("capabilities", [])
        if caps:
            lines = []
            for cap in caps[:10]:
                lines.append(f"- **{cap.get('name', '')}**: {cap.get('description', '')}")
            variables["examples_section"] = "\n".join(lines)

    # Overlay architecture data
    if architecture:
        variables["primary_platform"] = architecture.get("primary_platform", "claude-code")
        sections = architecture.get("structure", {}).get("sections", [])
        variables["sections"] = sections
        variables["scripts"] = architecture.get("structure", {}).get("scripts", [])
        variables["references"] = architecture.get("structure", {}).get("references", [])
        variables["platforms"] = architecture.get("platforms", ["claude-code"])

    return variables


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------

def scaffold(
    skill_name: str,
    template_type: str,
    output_dir: str,
    analysis: dict | None = None,
    architecture: dict | None = None,
) -> Path:
    """Create the skill directory and return its path."""
    variables = _build_variables(skill_name, template_type, analysis, architecture)

    skill_dir = Path(output_dir) / skill_name
    subdirs = ["scripts", "references", "evals"]
    for d in subdirs:
        (skill_dir / d).mkdir(parents=True, exist_ok=True)

    # SKILL.md
    tmpl = _load_template("SKILL.md.tmpl")
    if tmpl:
        rendered = _render(tmpl, variables)
    else:
        rendered = f"# {variables['title']}\n\n{variables['overview']}\n\n## Usage\n\n{variables['usage_section']}\n"
    (skill_dir / "SKILL.md").write_text(rendered)

    # config.yaml
    tmpl = _load_template("config.yaml.tmpl")
    if tmpl:
        rendered = _render(tmpl, variables)
    else:
        rendered = (
            f"skill_name: {skill_name}\nversion: \"1.0.0\"\n"
            f"target: {variables['target_name']}\ntarget_type: {variables['target_type']}\n"
            f"generated_by: SkillAnything v1.0.0\ngenerated_at: {variables['generated_at']}\n"
        )
    (skill_dir / "config.yaml").write_text(rendered)

    # evals placeholder
    evals_tmpl = _load_template("evals/evals.json.tmpl")
    if evals_tmpl:
        rendered = _render(evals_tmpl, variables)
    else:
        rendered = json.dumps({"version": "1.0", "skill_name": skill_name, "test_cases": []}, indent=2)
    (skill_dir / "evals" / "evals.json").write_text(rendered + "\n")

    # .gitkeep in empty dirs
    for d in subdirs:
        gitkeep = skill_dir / d / ".gitkeep"
        if not any((skill_dir / d).iterdir()) or not any(
            f for f in (skill_dir / d).iterdir() if f.name != ".gitkeep"
        ):
            gitkeep.touch()

    return skill_dir


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a skill directory from templates.",
    )
    parser.add_argument("skill_name", help="Name of the skill (kebab-case recommended).")
    parser.add_argument(
        "--template",
        choices=["cli", "api", "library", "workflow", "service", "generic"],
        default="generic",
        help="Template type (default: generic).",
    )
    parser.add_argument("--output", default=".", help="Parent directory for the skill (default: cwd).")
    parser.add_argument("--analysis", default=None, help="Path to analysis.json for auto-filling.")
    parser.add_argument("--architecture", default=None, help="Path to architecture.json for auto-filling.")
    args = parser.parse_args()

    analysis = None
    architecture = None

    if args.analysis:
        p = Path(args.analysis)
        if not p.is_file():
            print(f"Error: analysis file not found: {p}", file=sys.stderr)
            sys.exit(1)
        analysis = json.loads(p.read_text())

    if args.architecture:
        p = Path(args.architecture)
        if not p.is_file():
            print(f"Error: architecture file not found: {p}", file=sys.stderr)
            sys.exit(1)
        architecture = json.loads(p.read_text())

    skill_dir = scaffold(
        skill_name=args.skill_name,
        template_type=args.template,
        output_dir=args.output,
        analysis=analysis,
        architecture=architecture,
    )

    # Print summary
    created = sorted(skill_dir.rglob("*"))
    print(f"\nSkill scaffolded at: {skill_dir}\n")
    print("Created files:")
    for f in created:
        if f.is_file():
            rel = f.relative_to(skill_dir)
            print(f"  {rel}")
    print(f"\nTotal: {sum(1 for f in created if f.is_file())} files")


if __name__ == "__main__":
    main()
