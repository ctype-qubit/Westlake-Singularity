# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Package a skill directory into a .skill zip file."""
import sys
import zipfile
from pathlib import Path

from scripts.quick_validate import validate_skill
from scripts.utils import parse_skill_md

# Patterns to exclude from the package
EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git"}
EXCLUDE_FILES = {"*.pyc", ".DS_Store"}
# evals/ directory excluded only at root level
EXCLUDE_ROOT_DIRS = {"evals"}


def _should_exclude_file(file_path: Path, root: Path) -> bool:
    """Check if a file should be excluded from the package."""
    for part in file_path.relative_to(root).parts:
        if part in EXCLUDE_DIRS:
            return True

    # Exclude root-level evals/ directory
    rel = file_path.relative_to(root)
    if rel.parts and rel.parts[0] in EXCLUDE_ROOT_DIRS:
        return True

    name = file_path.name
    if name.endswith(".pyc") or name == ".DS_Store":
        return True

    return False


def package_skill(skill_path: Path, output_dir: Path | None = None) -> Path:
    """Package a skill directory into a .skill zip file.

    Args:
        skill_path: Path to the skill directory containing SKILL.md.
        output_dir: Optional output directory. Defaults to skill_path parent.

    Returns:
        Path to the created .skill file.

    Raises:
        ValueError: If validation fails.
    """
    skill_path = skill_path.resolve()

    # Validate first
    errors = validate_skill(skill_path)
    if errors:
        raise ValueError(
            f"Skill validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    name, description, _ = parse_skill_md(skill_path)

    if output_dir is None:
        output_dir = skill_path.parent
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{name}.skill"

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(skill_path.rglob("*")):
            if file_path.is_dir():
                continue
            if _should_exclude_file(file_path, skill_path):
                continue
            arcname = file_path.relative_to(skill_path)
            zf.write(file_path, arcname)

    print(f"Packaged skill '{name}' -> {output_file}")
    return output_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.package_skill <skill_path> [output_dir]")
        return 1

    skill_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        output_file = package_skill(skill_path, output_dir)
        print(f"Success: {output_file}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
