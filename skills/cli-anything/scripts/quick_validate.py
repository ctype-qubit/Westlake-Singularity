# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Quick validation of SKILL.md files."""
import re
import sys
from pathlib import Path

from scripts.utils import parse_skill_md

ALLOWED_PROPERTIES = frozenset(
    {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
)

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(skill_path: Path) -> list[str]:
    """Validate a SKILL.md file and return a list of error messages (empty = valid)."""
    errors: list[str] = []
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return ["SKILL.md not found"]

    try:
        name, description, content = parse_skill_md(skill_path)
    except ValueError as e:
        return [str(e)]

    # Parse frontmatter lines to check allowed properties
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is not None:
        frontmatter_lines = lines[1:end_idx]
        for line in frontmatter_lines:
            if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                key = line.split(":", 1)[0].strip()
                if key and key not in ALLOWED_PROPERTIES:
                    errors.append(
                        f"Unknown frontmatter property: '{key}'. "
                        f"Allowed: {', '.join(sorted(ALLOWED_PROPERTIES))}"
                    )

    # Required fields
    if not name:
        errors.append("Missing required field: name")
    if not description:
        errors.append("Missing required field: description")

    # Name validation: kebab-case, max 64 chars
    if name:
        if len(name) > 64:
            errors.append(f"Name too long ({len(name)} chars, max 64)")
        if not KEBAB_RE.match(name):
            errors.append(
                f"Name '{name}' is not valid kebab-case "
                "(lowercase alphanumeric with hyphens)"
            )

    # Description validation: max 1024 chars, no angle brackets
    if description:
        if len(description) > 1024:
            errors.append(
                f"Description too long ({len(description)} chars, max 1024)"
            )
        if "<" in description or ">" in description:
            errors.append("Description must not contain angle brackets (< or >)")

    # Optional compatibility field
    compatibility = ""
    if end_idx is not None:
        for line in lines[1:end_idx]:
            if line.startswith("compatibility:"):
                compatibility = line[len("compatibility:"):].strip().strip('"').strip("'")
                break
    if compatibility and len(compatibility) > 500:
        errors.append(
            f"Compatibility too long ({len(compatibility)} chars, max 500)"
        )

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.quick_validate <skill_path>")
        return 1

    skill_path = Path(sys.argv[1])
    errors = validate_skill(skill_path)

    if errors:
        print(f"Validation FAILED for {skill_path}:")
        for err in errors:
            print(f"  - {err}")
        return 1
    else:
        print(f"Validation PASSED for {skill_path}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
