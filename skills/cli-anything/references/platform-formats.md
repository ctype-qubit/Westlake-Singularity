# Platform-Specific SKILL.md Formats

Reference for the SKILL.md format expected by each supported agent platform.

All platforms share a common base: a Markdown file named `SKILL.md` with YAML frontmatter delimited
by `---`. The body contains instructions for the agent. Each platform extends this base with its own
frontmatter fields, directory layout, and configuration mechanisms.

---

## Claude Code

Claude Code skills live in `~/.claude/skills/<name>/` (global) or `<project>/.claude/skills/<name>/`
(project-scoped). Project skills take precedence over global skills.

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | yes | string | Skill identifier (kebab-case) |
| `description` | yes | string | Trigger description for the agent harness |
| `allowed-tools` | no | list | Tools the skill is allowed to use |
| `hooks` | no | object | Lifecycle hooks (see below) |
| `metadata` | no | object | Arbitrary key-value pairs |

### Hooks

Claude Code supports lifecycle hooks defined directly in the frontmatter YAML. Each hook fires at a
specific point in the agent interaction cycle.

| Hook | Fires When |
|------|-----------|
| `UserPromptSubmit` | After the user submits a prompt, before processing |
| `PreToolUse` | Before the agent invokes any tool |
| `PostToolUse` | After a tool invocation completes |
| `Stop` | When the agent finishes its response |

Hook values are shell commands. Script paths are relative to the skill directory.

### Example

```markdown
---
name: jq-helper
description: >
  Help users write and debug jq expressions for JSON filtering and transformation.
  Trigger when the user mentions jq, JSON filtering, JSON transformation, or needs
  to parse complex JSON structures from the command line.
allowed-tools:
  - Bash
  - Read
  - Write
hooks:
  PreToolUse: python scripts/validate_jq.py
  PostToolUse: python scripts/check_output.py
metadata:
  author: SkillAnything
  version: "1.0.0"
---

# jq Helper

Help users write correct jq expressions for JSON processing tasks.

## Usage
...
```

### Directory Layout

```
~/.claude/skills/jq-helper/
  SKILL.md
  scripts/
    validate_jq.py
    check_output.py
  references/
    jq-patterns.md
  assets/
```

---

## OpenClaw

OpenClaw skills live in `~/.openclaw/skills/<name>/` (global) or `<workspace>/skills/<name>/`
(workspace-scoped). Workspace skills take priority over global skills when names collide.

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | yes | string | Skill identifier (kebab-case) |
| `description` | yes | string | Trigger description |

OpenClaw uses a minimal frontmatter. Additional configuration (hooks, allowed tools, metadata) is
managed externally through the `settings.json` file in the workspace or global config directory.

### Hooks

Hooks are not defined in SKILL.md. Instead, configure them in `settings.json`:

```json
{
  "skills": {
    "jq-helper": {
      "hooks": {
        "pre_tool_use": "python scripts/validate_jq.py",
        "post_tool_use": "python scripts/check_output.py"
      },
      "allowed_tools": ["bash", "read", "write"]
    }
  }
}
```

### Example

```markdown
---
name: jq-helper
description: >
  Help users write and debug jq expressions for JSON filtering and transformation.
  Trigger when the user mentions jq, JSON filtering, JSON transformation, or needs
  to parse complex JSON structures from the command line.
---

# jq Helper

Help users write correct jq expressions for JSON processing tasks.

## Usage
...
```

### Directory Layout

```
~/.openclaw/skills/jq-helper/
  SKILL.md
  scripts/
    validate_jq.py
  references/
    jq-patterns.md
```

or workspace-scoped:

```
<workspace>/skills/jq-helper/
  SKILL.md
  scripts/
  references/
```

---

## Codex (OpenAI)

Codex skills live in `~/.codex/skills/<name>/`. They require an additional `agents/openai.yaml`
configuration file alongside the SKILL.md.

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | yes | string | Skill identifier (kebab-case) |
| `description` | yes | string | Trigger description |
| `metadata.short-description` | no | string | Brief one-liner for UI display |

### openai.yaml

The `agents/openai.yaml` file defines the Codex-specific interface and policy configuration:

```yaml
interface:
  display_name: "jq Helper"
  short_description: "Write and debug jq expressions"
  icon_small: "assets/icon-16.png"
  icon_large: "assets/icon-64.png"
  brand_color: "#2C3E50"
  default_prompt: "Help me with jq"

dependencies:
  tools:
    - bash
    - file_read
    - file_write

policy:
  allow_implicit_invocation: true
```

| Interface Field | Description |
|----------------|-------------|
| `display_name` | Human-readable name shown in UI |
| `short_description` | One-liner under the display name |
| `icon_small` | 16x16 icon path (relative to skill dir) |
| `icon_large` | 64x64 icon path (relative to skill dir) |
| `brand_color` | Hex color for UI theming |
| `default_prompt` | Placeholder text in the skill input |

| Dependencies Field | Description |
|-------------------|-------------|
| `tools` | List of tool identifiers the skill requires |

| Policy Field | Description |
|-------------|-------------|
| `allow_implicit_invocation` | Whether the agent can invoke this skill without explicit user request |

### Example

```markdown
---
name: jq-helper
description: >
  Help users write and debug jq expressions for JSON filtering and transformation.
  Trigger when the user mentions jq, JSON filtering, JSON transformation, or needs
  to parse complex JSON structures from the command line.
metadata:
  short-description: Write and debug jq expressions for JSON processing
---

# jq Helper

Help users write correct jq expressions for JSON processing tasks.

## Usage
...
```

### Directory Layout

```
~/.codex/skills/jq-helper/
  SKILL.md
  agents/
    openai.yaml
  scripts/
    validate_jq.py
  references/
    jq-patterns.md
  assets/
    icon-16.png
    icon-64.png
```

---

## Generic

The generic format is platform-agnostic and designed for portability. Skills are packaged as `.skill`
zip files that can be installed on any compliant agent platform.

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | yes | string | Skill identifier (kebab-case) |
| `description` | yes | string | Trigger description |

Only the two core fields are used. No hooks, metadata, or platform-specific configuration.

### Packaging

Generic skills are distributed as `.skill` files, which are standard zip archives with the extension
renamed:

```bash
cd my-skill/
zip -r ../my-skill.skill SKILL.md scripts/ references/ assets/
```

The archive must contain `SKILL.md` at its root. All script paths in the SKILL.md body must be
relative to the skill directory root.

### Example

```markdown
---
name: jq-helper
description: >
  Help users write and debug jq expressions for JSON filtering and transformation.
  Trigger when the user mentions jq, JSON filtering, JSON transformation, or needs
  to parse complex JSON structures from the command line.
---

# jq Helper

Help users write correct jq expressions for JSON processing tasks.

## Usage
...
```

### Directory Layout (before packaging)

```
jq-helper/
  SKILL.md
  scripts/
    validate_jq.py
  references/
    jq-patterns.md
```

### Resulting Package

```
jq-helper.skill   (zip archive)
```

---

## Cross-Platform Compatibility Matrix

| Feature | Claude Code | OpenClaw | Codex | Generic |
|---------|------------|----------|-------|---------|
| SKILL.md frontmatter | yes | yes | yes | yes |
| Hooks in frontmatter | yes | no | no | no |
| External hooks config | no | yes (settings.json) | no | no |
| Extra config files | no | no | yes (openai.yaml) | no |
| Icon assets | no | no | yes | no |
| Zip packaging | no | no | no | yes |
| Workspace scoping | yes (project) | yes (workspace) | no | n/a |
| Global install | yes | yes | yes | n/a |

---

## Description Guidelines

The `description` field is critical for skill triggering. Regardless of platform, follow these
guidelines:

1. Lead with the primary use case in plain language
2. Include specific trigger phrases the user might say
3. Mention the target tool or service by name
4. Keep under 1024 characters
5. Avoid generic phrases like "helps with coding" that would match too broadly
6. Include near-miss exclusions if needed ("do not trigger for raw SQL queries")
