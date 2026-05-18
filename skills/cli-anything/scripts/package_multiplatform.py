#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 6 -- Multi-platform packaging.

Copies and adapts a skill for each target platform (claude-code, openclaw,
codex, generic), generates platform-specific SKILL.md files, and produces a
dist/manifest.json.

Usage:
    python package_multiplatform.py ./my-skill \
        [--platforms claude-code,openclaw,codex,generic] \
        [--output-dir ./dist] [--config config.yaml]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADAPTER_DIR = _PROJECT_ROOT / "templates" / "platform-adapters"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """Load YAML with pyyaml or naive fallback."""
    try:
        import yaml  # type: ignore[import-untyped]
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
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


def _sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _render_template(template_text: str, variables: dict) -> str:
    """Simple Jinja2-style template rendering (no jinja2 dependency)."""
    def _replace(m: re.Match) -> str:
        key = m.group(1).strip().split("|")[0].strip()
        return str(variables.get(key, m.group(0)))

    text = re.sub(r"\{\{\s*(.+?)\s*\}\}", _replace, template_text)
    text = re.sub(r"\{%.*?%\}", "", text)
    text = re.sub(r"\{#.*?#\}", "", text)
    return text


def _read_skill_md(skill_path: Path) -> tuple[dict, str]:
    """Read SKILL.md and split into frontmatter dict and body text."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return {}, ""

    content = skill_md.read_text()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            body = parts[2].strip()
            # Parse frontmatter (simple key: value)
            fm: dict = {}
            current_key = None
            for line in frontmatter_text.splitlines():
                if line and not line[0].isspace() and ":" in line:
                    key, _, val = line.partition(":")
                    val = val.strip()
                    current_key = key.strip()
                    fm[current_key] = val
                elif current_key and line.strip().startswith("- "):
                    existing = fm.get(current_key, "")
                    if isinstance(existing, str) and not existing:
                        fm[current_key] = [line.strip()[2:]]
                    elif isinstance(existing, list):
                        existing.append(line.strip()[2:])
                    else:
                        fm[current_key] = [existing, line.strip()[2:]]
            return fm, body
    return {}, content


# ---------------------------------------------------------------------------
# Platform packagers
# ---------------------------------------------------------------------------

def _copy_skill_base(skill_path: Path, dest: Path) -> None:
    """Copy the entire skill directory to dest."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill_path, dest, dirs_exist_ok=False)


def _package_platform(
    skill_path: Path,
    skill_name: str,
    platform: str,
    output_dir: Path,
    config: dict,
) -> dict:
    """Package for a single platform. Returns manifest entry."""
    dest = output_dir / platform / skill_name
    _copy_skill_base(skill_path, dest)

    frontmatter, body = _read_skill_md(skill_path)

    # Load platform adapter template if available
    adapter_path = _ADAPTER_DIR / f"{platform}.md.tmpl"
    if adapter_path.is_file():
        adapter_tmpl = adapter_path.read_text()
        variables = {
            "skill_name": skill_name,
            "description": frontmatter.get("description", f"AI skill for {skill_name}"),
            "skill_body": body,
            "short_description": (frontmatter.get("description", "") or "")[:80],
            "display_name": skill_name.replace("-", " ").title(),
        }

        # Merge any allowed_tools, hooks, metadata from frontmatter
        if "allowed-tools" in frontmatter:
            tools = frontmatter["allowed-tools"]
            if isinstance(tools, str):
                tools = [tools]
            variables["allowed_tools"] = tools

        rendered = _render_template(adapter_tmpl, variables)
        (dest / "SKILL.md").write_text(rendered)

    # Codex: also generate agents/openai.yaml
    if platform == "codex":
        agents_dir = dest / "agents"
        agents_dir.mkdir(exist_ok=True)
        openai_yaml = (
            f'interface:\n'
            f'  display_name: "{skill_name.replace("-", " ").title()}"\n'
            f'  short_description: "{(frontmatter.get("description", "") or "")[:80]}"\n'
            f'  brand_color: "#2C3E50"\n'
            f'  default_prompt: "Help me with {skill_name.replace("-", " ")}"\n'
            f'\n'
            f'dependencies:\n'
            f'  tools:\n'
            f'    - bash\n'
            f'    - file_read\n'
            f'    - file_write\n'
            f'\n'
            f'policy:\n'
            f'  allow_implicit_invocation: true\n'
        )
        (agents_dir / "openai.yaml").write_text(openai_yaml)

    # Compute format and checksum
    fmt = "directory"
    checksum = ""
    if platform == "generic":
        # Create a .skill zip
        zip_path = output_dir / platform / f"{skill_name}.skill"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(dest):
                for fname in files:
                    fpath = Path(root) / fname
                    arcname = fpath.relative_to(dest)
                    zf.write(fpath, arcname)
        fmt = "zip"
        checksum = _sha256(zip_path)
    else:
        # Checksum the SKILL.md
        skill_md = dest / "SKILL.md"
        if skill_md.is_file():
            checksum = _sha256(skill_md)

    return {
        "platform": platform,
        "path": str(dest.relative_to(output_dir)),
        "format": fmt,
        "checksum": checksum,
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_platform(dest: Path, platform: str) -> list[str]:
    """Quick validation of a packaged platform output."""
    issues: list[str] = []
    skill_md = dest / "SKILL.md"
    if not skill_md.is_file():
        issues.append(f"[{platform}] Missing SKILL.md")
    else:
        content = skill_md.read_text()
        if not content.startswith("---"):
            issues.append(f"[{platform}] SKILL.md missing YAML frontmatter")
        if len(content) < 50:
            issues.append(f"[{platform}] SKILL.md is suspiciously short ({len(content)} chars)")

    if platform == "codex":
        openai_yaml = dest / "agents" / "openai.yaml"
        if not openai_yaml.is_file():
            issues.append(f"[{platform}] Missing agents/openai.yaml")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def package(
    skill_path: str,
    platforms: list[str],
    output_dir: str,
    config: dict | None = None,
) -> dict:
    """Package a skill for multiple platforms. Returns the manifest dict."""
    config = config or {}
    skill_p = Path(skill_path)
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    skill_name = skill_p.name

    # Read version from skill config if available
    skill_config_path = skill_p / "config.yaml"
    version = "1.0.0"
    if skill_config_path.is_file():
        sc = _load_yaml(str(skill_config_path))
        version = sc.get("version", version) or version

    platform_entries = []
    all_issues: list[str] = []

    for platform in platforms:
        entry = _package_platform(skill_p, skill_name, platform, out_p, config)
        platform_entries.append(entry)

        # Validate
        dest = out_p / platform / skill_name
        if dest.is_dir():
            issues = _validate_platform(dest, platform)
            all_issues.extend(issues)

    manifest = {
        "skill_name": skill_name,
        "version": str(version),
        "packaged_at": datetime.now(timezone.utc).isoformat(),
        "platforms": platform_entries,
    }

    manifest_path = out_p / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # Print summary
    print(f"\nPackaging complete: {skill_name}")
    print(f"Output directory:  {out_p}")
    print(f"Manifest:          {manifest_path}")
    print(f"\nPlatforms packaged ({len(platform_entries)}):")
    for entry in platform_entries:
        print(f"  - {entry['platform']}: {entry['path']} ({entry['format']})")

    if all_issues:
        print(f"\nValidation warnings ({len(all_issues)}):")
        for issue in all_issues:
            print(f"  ! {issue}")
    else:
        print("\nAll platform outputs validated successfully.")

    return manifest


def main() -> None:
    all_platforms = ["claude-code", "openclaw", "codex", "generic"]

    parser = argparse.ArgumentParser(
        description="Package a skill for multiple platforms.",
    )
    parser.add_argument("skill_path", help="Path to the skill directory.")
    parser.add_argument(
        "--platforms",
        default=",".join(all_platforms),
        help=f"Comma-separated platforms (default: {','.join(all_platforms)}).",
    )
    parser.add_argument("--output-dir", default="./dist", help="Output directory (default: ./dist).")
    parser.add_argument("--config", default=None, help="Path to config.yaml (optional).")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not skill_path.is_dir():
        print(f"Error: skill directory not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    config = _load_yaml(args.config) if args.config else {}

    package(
        skill_path=str(skill_path),
        platforms=platforms,
        output_dir=args.output_dir,
        config=config,
    )


if __name__ == "__main__":
    main()
