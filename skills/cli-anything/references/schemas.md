# Data Schemas Reference

JSON and YAML schemas for all data structures produced and consumed by the SkillAnything pipeline.

---

## analysis.json (Phase 1 Output)

Produced by `scripts/analyze_target.py`. Contains everything discovered about the target.

```json
{
  "target_name": "string — canonical name of the target (e.g., 'jq', 'stripe-api')",
  "target_type": "string — one of: api, cli, library, workflow, service",
  "confidence": "number — 0.0 to 1.0, how confident the classifier is in target_type",
  "capabilities": [
    {
      "name": "string — capability identifier (e.g., 'filter', 'create-customer')",
      "description": "string — what this capability does",
      "complexity": "string — one of: core, intermediate, advanced"
    }
  ],
  "inputs": ["string — description of each input the target accepts"],
  "outputs": ["string — description of each output the target produces"],
  "auth_requirements": "string | null — auth mechanism (e.g., 'API key in header', 'OAuth2', null)",
  "dependencies": ["string — required tools or packages with version constraints"],
  "error_patterns": ["string — common error messages or failure modes"],
  "raw_help": "string — raw help text, API spec, or documentation captured during analysis",
  "documentation_urls": ["string — URLs to official docs discovered during analysis"],
  "metadata": {
    "analyzed_at": "string — ISO 8601 timestamp",
    "analyzer_version": "string — SkillAnything version that produced this",
    "source": "string — what was provided as input (URL, command name, path, etc.)"
  }
}
```

### Field Notes

- `confidence` below 0.7 triggers interactive mode to ask the user for clarification
- `capabilities` are ordered by priority: core capabilities first
- `raw_help` is truncated to 50,000 characters to avoid context overflow
- `auth_requirements` is null when no auth is needed

---

## architecture.json (Phase 2 Output)

Produced by `scripts/design_skill.py`. Defines the skill's structure before implementation.

```json
{
  "skill_name": "string — kebab-case skill name (e.g., 'jq-helper')",
  "skill_type": "string — one of: tool-augmentation, workflow-automation, knowledge-base, hybrid",
  "structure": {
    "skill_md_sections": ["string — ordered list of sections to include in SKILL.md"],
    "scripts": ["string — filenames of helper scripts to generate"],
    "references": ["string — filenames of reference docs to generate"],
    "assets": ["string — filenames of static assets to include"]
  },
  "triggers": ["string — phrases that should activate this skill"],
  "platforms": {
    "claude-code": {
      "hooks": [
        {
          "event": "string — one of: UserPromptSubmit, PreToolUse, PostToolUse, Stop",
          "command": "string — shell command to run"
        }
      ],
      "allowed_tools": ["string — tool names"]
    },
    "openclaw": {
      "settings_hooks": [
        {
          "event": "string — hook event name",
          "command": "string — shell command"
        }
      ]
    },
    "codex": {
      "interface": {
        "display_name": "string",
        "short_description": "string",
        "brand_color": "string — hex color",
        "default_prompt": "string"
      }
    }
  },
  "writing_guidelines": {
    "tone": "string — e.g., 'direct', 'conversational'",
    "max_skill_md_lines": "number — target line count for SKILL.md",
    "progressive_disclosure": "boolean — whether to use progressive detail levels"
  }
}
```

### Field Notes

- `skill_type` determines the overall architecture pattern
- `structure.skill_md_sections` typically includes: overview, usage, examples, advanced, troubleshooting
- Platform entries are only populated for platforms listed in `config.yaml platforms.enabled`

---

## evals.json (Phase 4 Output — Functional Evals)

Produced by `scripts/generate_tests.py`. Contains functional test cases.

```json
{
  "version": "1.0",
  "skill_name": "string — skill being tested",
  "test_cases": [
    {
      "id": "string — unique test case identifier (e.g., 'tc-001')",
      "name": "string — short descriptive name",
      "prompt": "string — the user prompt to send to the agent",
      "context": {
        "files": {
          "string (path)": "string (content) — files to pre-create before the test"
        },
        "env": {
          "string (var name)": "string (value) — environment variables to set"
        }
      },
      "assertions": [
        {
          "type": "string — one of: contains, not_contains, file_exists, file_contains, exit_code, regex",
          "target": "string — what to check (response, file path, etc.)",
          "value": "string — expected value or pattern",
          "weight": "number — 0.0 to 1.0, importance of this assertion"
        }
      ],
      "expected_behavior": "string — natural language description of what should happen",
      "tags": ["string — categorization tags (e.g., 'core', 'edge-case', 'error-handling')"]
    }
  ]
}
```

### Assertion Types

| Type | Target | Value | Checks |
|------|--------|-------|--------|
| `contains` | response | substring | Agent response contains the value |
| `not_contains` | response | substring | Agent response does not contain the value |
| `file_exists` | file path | — | File was created at the given path |
| `file_contains` | file path | substring | File at path contains the value |
| `exit_code` | command | number (as string) | Command exited with this code |
| `regex` | response | regex pattern | Agent response matches the pattern |

---

## trigger-evals.json (Phase 4 Output — Trigger Evals)

Produced by `scripts/generate_tests.py`. Used for description optimization.

```json
{
  "version": "1.0",
  "skill_name": "string",
  "queries": [
    {
      "id": "string — unique query identifier (e.g., 'tq-001')",
      "prompt": "string — realistic user prompt",
      "should_trigger": "boolean — true if the skill should activate for this prompt",
      "reasoning": "string — why this should or should not trigger",
      "difficulty": "string — one of: easy, medium, hard",
      "split": "string — one of: train, test (assigned during optimization)"
    }
  ]
}
```

### Quality Standards for Queries

- Should-trigger queries: realistic, varied in length and formality, include abbreviations and typos
- Should-not-trigger queries: near-misses that a naive description might wrongly match
- Minimum 10 should-trigger + 10 should-not-trigger
- Difficulty distribution: ~30% easy, ~40% medium, ~30% hard

---

## grading.json (Phase 5 Output — Per-Run Grading)

Produced by `agents/grader.md` for each eval run.

```json
{
  "run_id": "string — unique run identifier",
  "test_case_id": "string — which test case was run",
  "skill_name": "string",
  "mode": "string — one of: with-skill, baseline",
  "timestamp": "string — ISO 8601",
  "assertions": [
    {
      "type": "string — assertion type from evals.json",
      "target": "string",
      "value": "string",
      "passed": "boolean",
      "actual": "string — what was actually observed",
      "weight": "number"
    }
  ],
  "score": "number — 0.0 to 1.0, weighted assertion pass rate",
  "qualitative": {
    "correctness": "number — 1 to 5",
    "completeness": "number — 1 to 5",
    "efficiency": "number — 1 to 5",
    "notes": "string — grader commentary"
  },
  "agent_output": "string — truncated agent response",
  "duration_seconds": "number"
}
```

---

## benchmark.json (Phase 5 Output — Aggregated Results)

Produced by `scripts/aggregate_benchmark.py`.

```json
{
  "skill_name": "string",
  "timestamp": "string — ISO 8601",
  "config": {
    "num_test_cases": "number",
    "runs_per_config": "number",
    "model": "string — model used for evaluation"
  },
  "results": {
    "with_skill": {
      "mean_score": "number — 0.0 to 1.0",
      "median_score": "number",
      "std_dev": "number",
      "min_score": "number",
      "max_score": "number",
      "pass_rate": "number — fraction of runs scoring above 0.5",
      "per_test_case": {
        "string (test case id)": {
          "mean_score": "number",
          "scores": ["number — score from each run"]
        }
      }
    },
    "baseline": {
      "mean_score": "number",
      "median_score": "number",
      "std_dev": "number",
      "min_score": "number",
      "max_score": "number",
      "pass_rate": "number",
      "per_test_case": {
        "string (test case id)": {
          "mean_score": "number",
          "scores": ["number"]
        }
      }
    }
  },
  "improvement": {
    "mean_delta": "number — with_skill.mean - baseline.mean",
    "pass_rate_delta": "number",
    "significant": "boolean — whether delta is statistically meaningful"
  },
  "trigger_accuracy": {
    "overall": "number — 0.0 to 1.0",
    "true_positive_rate": "number",
    "true_negative_rate": "number",
    "false_positive_rate": "number",
    "false_negative_rate": "number"
  }
}
```

---

## comparison.json (Phase 5 Output — Blind Comparator)

Produced by `agents/comparator.md` for side-by-side evaluation.

```json
{
  "test_case_id": "string",
  "comparison_id": "string — unique identifier",
  "response_a": {
    "mode": "string — with-skill or baseline (hidden from comparator)",
    "truncated_output": "string"
  },
  "response_b": {
    "mode": "string",
    "truncated_output": "string"
  },
  "winner": "string — one of: a, b, tie",
  "reasoning": "string — why the comparator chose this winner",
  "dimensions": {
    "correctness": "string — a, b, or tie",
    "completeness": "string — a, b, or tie",
    "clarity": "string — a, b, or tie",
    "efficiency": "string — a, b, or tie"
  }
}
```

---

## manifest.json (Phase 7 Output)

Produced by `scripts/package_multiplatform.py`. Describes the packaged distribution.

```json
{
  "skill_name": "string",
  "version": "string — semver",
  "generated_by": "string — SkillAnything version",
  "generated_at": "string — ISO 8601",
  "source": {
    "target_name": "string",
    "target_type": "string",
    "analysis_hash": "string — SHA-256 of analysis.json"
  },
  "platforms": {
    "claude-code": {
      "path": "string — relative path in dist/",
      "files": ["string — list of files in the package"],
      "install_path": "~/.claude/skills/<name>/"
    },
    "openclaw": {
      "path": "string",
      "files": ["string"],
      "install_path": "~/.openclaw/skills/<name>/"
    },
    "codex": {
      "path": "string",
      "files": ["string"],
      "install_path": "~/.codex/skills/<name>/"
    },
    "generic": {
      "path": "string — path to .skill file",
      "files": ["string"],
      "install_path": "anywhere"
    }
  },
  "benchmark_summary": {
    "with_skill_mean": "number",
    "baseline_mean": "number",
    "improvement": "number",
    "trigger_accuracy": "number"
  },
  "checksums": {
    "string (file path)": "string (SHA-256 hash)"
  }
}
```

---

## config.yaml (Pipeline Configuration)

The main configuration file. Located at the project root.

```yaml
# Pipeline version
version: "string — semver (e.g., '1.0.0')"

pipeline:
  # Run all phases automatically or pause for review after each
  auto_mode: "boolean (default: true)"
  # Which phases to run (1-7). Omit phases to skip them.
  phases: "list of integers (default: [1, 2, 3, 4, 5, 6, 7])"
  # Working directory for intermediate outputs
  workspace: "string — path (default: './sa-workspace')"
  # Skip evaluation phases (4-6) for rapid prototyping
  skip_eval: "boolean (default: false)"

target:
  # Force a target type instead of auto-detecting
  type: "string — one of: auto, api, cli, library, workflow, service (default: 'auto')"
  # URL for API or service targets
  url: "string | null"
  # File system path for local targets
  path: "string | null"
  # Target name (for CLI tools or packages)
  name: "string | null"
  # Additional documentation URLs to include in analysis
  extra_docs: "list of strings (default: [])"

platforms:
  # Which platforms to generate packages for
  enabled: "list of strings (default: [claude-code, openclaw, codex, generic])"
  # Primary platform — gets priority in design decisions
  primary: "string (default: 'claude-code')"

eval:
  # Number of functional test cases to generate
  num_test_cases: "integer (default: 5)"
  # Number of trigger eval queries to generate
  num_trigger_queries: "integer (default: 20)"
  # How many times to run each query for statistical stability
  runs_per_query: "integer (default: 3)"
  # How many times to run each eval config
  runs_per_config: "integer (default: 3)"
  # Maximum description optimization iterations
  max_optimization_iterations: "integer (default: 5)"
  # Parallel workers for eval runs
  num_workers: "integer (default: 10)"
  # Timeout per eval run in seconds
  timeout: "integer (default: 30)"
  # Minimum trigger accuracy to accept
  trigger_threshold: "number (default: 0.5)"
  # Fraction of trigger evals held out for test
  holdout: "number (default: 0.4)"
  # Model override for evaluation (null = use default)
  model: "string | null"

obfuscation:
  # Whether to obfuscate SkillAnything scripts in the distribution
  enabled: "boolean (default: false)"
  # Obfuscation tool
  tool: "string (default: 'pyarmor')"
  # Which scripts to obfuscate (only SkillAnything originals)
  protect_scripts: "list of strings"

output:
  # Override the auto-generated skill name
  skill_name: "string | null"
  # Description writing style
  description_style: "string — one of: pushy, neutral, conservative (default: 'pushy')"
  # Include eval artifacts in the distribution
  include_evals: "boolean (default: false)"
  # Output directory for final packages
  dist_dir: "string — path (default: './dist')"
```
