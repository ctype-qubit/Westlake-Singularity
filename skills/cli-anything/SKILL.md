---
name: skill-anything
description: >
  Automatically generate production-ready Skills for any software, API, CLI tool, library, workflow,
  or service. Use this skill whenever the user wants to create a skill from scratch for a target
  application, convert an existing tool into an agent-native skill, generate skills for multiple
  platforms (Claude Code, OpenClaw, Codex), or automate the full skill creation pipeline including
  analysis, design, implementation, testing, optimization, and multi-platform packaging. Also use
  when the user mentions "skill-anything", "generate a skill for", "make a skill from", "skillify",
  or wants to turn any software into an agent-ready skill. Even if they just say "create a skill
  for X" where X is any tool or API, this skill should trigger.
---

# SkillAnything

Automatically generate production-ready Skills for any target — software, API, CLI tool, library,
workflow, or web service. SkillAnything runs a 7-phase pipeline that analyzes your target, designs
the skill architecture, implements it, generates test cases, benchmarks performance, optimizes the
description, and packages for multiple agent platforms.

## Quick Start

**Fully automated** (one command):
```
Give SkillAnything a target and it handles everything:
- "Create a skill for the jq CLI tool"
- "Generate a skill for the Stripe API"
- "Turn this workflow into a multi-platform skill"
```

The pipeline runs all 7 phases automatically. Results land in `sa-workspace/`.

## The 7-Phase Pipeline

```
Phase 1: Analyze    → Detect target type, extract capabilities     → analysis.json
Phase 2: Design     → Map capabilities to skill architecture       → architecture.json
Phase 3: Implement  → Generate SKILL.md + scripts + references     → complete skill directory
Phase 4: Test Plan  → Auto-generate eval cases + trigger queries   → evals.json
Phase 5: Evaluate   → Benchmark with/without skill, grade results  → benchmark.json
Phase 6: Optimize   → Improve description via train/test loop      → optimized SKILL.md
Phase 7: Package    → Multi-platform distribution packages         → dist/
```

See `METHODOLOGY.md` for the full pipeline specification.

## Usage Modes

### Auto Mode (default)
Runs all 7 phases end-to-end. Provide the target and SkillAnything does the rest:
```
Target: "the httpie CLI tool"
→ Analyzes httpie --help output, designs command structure, generates skill,
  creates tests, benchmarks, optimizes, packages for 4 platforms
```

### Interactive Mode
Set `auto_mode: false` in `config.yaml`. SkillAnything pauses after each phase for review:
- Phase 1 → "Here's what I found about the target. Look right?"
- Phase 2 → "Here's the proposed skill architecture. Any changes?"
- Phase 3 → "Draft skill ready for review."
- ...continues with user feedback at each step

### Single Phase Mode
Run any phase independently:
```bash
python -m scripts.analyze_target --target "jq" --output analysis.json
python -m scripts.design_skill --analysis analysis.json --output architecture.json
python -m scripts.init_skill my-skill --template cli --output ./out
python -m scripts.generate_tests --analysis analysis.json --skill-path ./out/my-skill
python -m scripts.run_eval --eval-set evals.json --skill-path ./out/my-skill
python -m scripts.run_loop --eval-set trigger-evals.json --skill-path ./out/my-skill --model <model>
python -m scripts.package_multiplatform ./out/my-skill --platforms claude-code,openclaw,codex
```

## Configuration

Edit `config.yaml` to customize the pipeline. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `pipeline.auto_mode` | `true` | Run all phases or pause for review |
| `target.type` | `auto` | Force target type: api, cli, library, workflow, service |
| `platforms.enabled` | all 4 | Which platforms to package for |
| `platforms.primary` | claude-code | Primary output platform |
| `eval.max_optimization_iterations` | 5 | Max description optimization rounds |
| `obfuscation.enabled` | `false` | Obfuscate original scripts with PyArmor |

See `references/schemas.md` for the complete configuration schema.

## Platform Output

| Platform | Install Path | Package Format |
|----------|-------------|----------------|
| Claude Code | `~/.claude/skills/<name>/` | Directory |
| OpenClaw | `~/.openclaw/skills/<name>/` | Directory |
| Codex | `~/.codex/skills/<name>/` | Directory + openai.yaml |
| Generic | anywhere | `.skill` zip |

See `references/platform-formats.md` for platform-specific format details.

## Evaluation and Benchmarking

SkillAnything uses the same eval system as the Anthropic skill-creator:

1. **Test cases** with assertions → graded by `agents/grader.md`
2. **Benchmark** comparing with-skill vs baseline → `benchmark.json`
3. **Description optimization** with train/test split → prevents overfitting
4. **Interactive viewer** via `eval-viewer/generate_review.py`

The eval loop is optional (`skip_eval: true` in config) for rapid prototyping.

## Scripts Reference

| Script | Phase | Purpose |
|--------|-------|---------|
| `analyze_target.py` | 1 | Auto-detect and analyze target |
| `design_skill.py` | 2 | Generate skill architecture from analysis |
| `init_skill.py` | 3 | Scaffold skill directory from templates |
| `generate_tests.py` | 4 | Auto-generate test cases and trigger queries |
| `run_eval.py` | 5 | Test description triggering accuracy |
| `aggregate_benchmark.py` | 5 | Aggregate benchmark statistics |
| `generate_report.py` | 5-6 | Generate HTML optimization report |
| `improve_description.py` | 6 | AI-powered description improvement |
| `run_loop.py` | 6 | Full eval + improve optimization loop |
| `quick_validate.py` | 7 | Validate SKILL.md structure |
| `package_skill.py` | 7 | Package for single platform |
| `package_multiplatform.py` | 7 | Package for all enabled platforms |
| `obfuscate.py` | - | PyArmor wrapper for code protection |

## Agents

Read these when spawning specialized subagents:

| Agent | Purpose |
|-------|---------|
| `agents/analyzer.md` | Phase 1: Target analysis instructions |
| `agents/designer.md` | Phase 2: Skill architecture design |
| `agents/implementer.md` | Phase 3: Skill content writing |
| `agents/grader.md` | Phase 5: Eval assertion grading |
| `agents/comparator.md` | Phase 5: Blind A/B output comparison |
| `agents/optimizer.md` | Phase 6: Description optimization orchestration |
| `agents/packager.md` | Phase 7: Multi-platform packaging instructions |

## Target Types

SkillAnything auto-detects the target type and adapts its analysis:

| Type | Detection | Analysis Method |
|------|-----------|-----------------|
| API | URL with /api, OpenAPI spec, swagger | Fetch spec, extract endpoints |
| CLI | Executable name, --help output | Run help, parse subcommands |
| Library | Package name, import path | Read docs, parse public API |
| Workflow | Step descriptions, sequence | Parse steps, map data flow |
| Service | URL, web interface | Scrape docs, identify actions |

## Troubleshooting

- **Phase 1 fails**: Target not found or inaccessible → provide `--target-type` override
- **Low eval scores**: Description too vague → run Phase 6 optimization
- **Platform packaging errors**: Missing required fields → check `references/platform-formats.md`
- **PyArmor not found**: Install with `pip install pyarmor`

## License

MIT License. See `NOTICE` for third-party attributions (CLI-Anything, Dazhuang Skill Creator,
Anthropic Skill Creator).
