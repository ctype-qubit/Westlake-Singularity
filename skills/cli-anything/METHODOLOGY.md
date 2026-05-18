# SkillAnything Methodology

The complete 7-phase pipeline specification for automated skill generation.

Adapted from CLI-Anything's HARNESS.md methodology for skill generation rather than CLI generation.

## Philosophy

Three non-negotiable principles:

1. **Use the real target — don't approximate.** When analyzing a CLI tool, actually run `--help`.
   When analyzing an API, fetch the real spec. Never guess at capabilities.

2. **Verify outputs programmatically.** Don't assume a generated SKILL.md is correct because the
   generation succeeded. Validate structure, run trigger evals, benchmark against baselines.

3. **Fail with clear messages.** When analysis can't determine the target type, when a required
   dependency is missing, when packaging fails — provide actionable error messages that enable
   self-correction.

## Target Classification

### Detection Strategy

SkillAnything auto-detects the target type using these heuristics (in order):

1. **URL with OpenAPI/Swagger indicators** → API
2. **Executable found in PATH** → CLI tool
3. **Package name resolvable via pip/npm** → Library
4. **File with step-by-step structure** → Workflow
5. **URL with web interface** → Service
6. **Free-text description** → Ask user to clarify

When confidence < 0.7, fall back to interactive mode and ask the user.

### Per-Type Analysis

**API targets:**
- Fetch OpenAPI spec (or scrape REST docs)
- Extract: endpoints, methods, auth patterns, request/response schemas, error codes
- Identify: CRUD patterns, resource relationships, pagination
- Priority: most-used endpoints, unique capabilities

**CLI targets:**
- Run: `<tool> --help`, `<tool> <subcommand> --help`, `man <tool>`
- Parse: subcommands, flags, options, output formats
- Identify: stateful vs stateless operations, piping patterns
- Priority: most common operations, unique capabilities

**Library targets:**
- Read: README, API docs, docstrings, type hints
- Parse: public functions, classes, configuration options
- Identify: initialization patterns, common workflows
- Priority: frequently imported functions, core capabilities

**Workflow targets:**
- Parse: step descriptions, tool references, data flow
- Identify: sequential vs parallel steps, decision points, error handling
- Map: inputs → transformations → outputs at each step
- Priority: critical path steps, error-prone steps

**Service targets:**
- Scrape: documentation, getting started guides, API reference
- Identify: authentication, core actions, webhooks/events
- Map: user journey → API calls → outcomes
- Priority: onboarding flow, most-used features

## Phase Specifications

### Phase 1: Analyze Target

**Input:** Target identifier (URL, name, path, or description)
**Output:** `analysis.json`

```json
{
  "target_name": "jq",
  "target_type": "cli",
  "confidence": 0.95,
  "capabilities": [
    {"name": "filter", "description": "Filter JSON with expressions", "complexity": "core"},
    {"name": "transform", "description": "Transform JSON structure", "complexity": "core"}
  ],
  "inputs": ["JSON from stdin", "JSON files"],
  "outputs": ["Filtered/transformed JSON"],
  "auth_requirements": null,
  "dependencies": ["jq >= 1.6"],
  "error_patterns": ["parse error", "null output"],
  "raw_help": "...",
  "documentation_urls": []
}
```

**Script:** `scripts/analyze_target.py`
**Agent:** `agents/analyzer.md` — handles ambiguous cases requiring intelligence

### Phase 2: Design Skill Architecture

**Input:** `analysis.json`
**Output:** `architecture.json`

```json
{
  "skill_name": "jq-helper",
  "skill_type": "tool-augmentation",
  "structure": {
    "skill_md_sections": ["overview", "usage", "examples", "advanced"],
    "scripts": ["validate_jq.py"],
    "references": ["jq-patterns.md"],
    "assets": []
  },
  "triggers": ["jq", "json filter", "json transform", "parse json"],
  "platforms": {
    "claude-code": {"hooks": []},
    "openclaw": {},
    "codex": {"interface": {"display_name": "jq Helper"}}
  }
}
```

**Script:** `scripts/design_skill.py`
**Agent:** `agents/designer.md` — makes architectural decisions

### Phase 3: Implement

**Input:** `architecture.json` + `analysis.json`
**Output:** Complete skill directory

The implementer generates:
- `SKILL.md` with proper frontmatter and instructions (< 500 lines)
- Helper scripts for deterministic operations
- Reference files for detailed documentation
- Configuration defaults

**Script:** `scripts/init_skill.py` (scaffolding) + `agents/implementer.md` (content)

**Writing principles** (from Anthropic skill-creator):
- Explain the WHY, not just the WHAT
- Use imperative form in instructions
- Avoid heavy-handed MUSTs — use theory of mind
- Keep SKILL.md lean with progressive disclosure
- Bundle repeated work as scripts

### Phase 4: Test Planning

**Input:** `analysis.json` + generated skill
**Output:** `evals/evals.json` + `trigger-evals.json`

Generates two types of test cases:

1. **Functional evals** (5-8 cases): Realistic user prompts with expected outcomes and assertions
2. **Trigger evals** (20 cases): 10 should-trigger + 10 should-not-trigger for description optimization

Quality standards for trigger evals (from Anthropic):
- Realistic, detailed, with file paths and personal context
- Mix of lengths, formality levels, and phrasings
- Include abbreviations, typos, casual speech
- Focus on edge cases over clear-cut cases
- Should-not-trigger cases are near-misses, not obviously irrelevant

**Script:** `scripts/generate_tests.py`

### Phase 5: Evaluate and Benchmark

**Input:** Generated skill + eval cases
**Output:** `benchmark.json`, `grading.json` per run, HTML viewer

Full evaluation flow:
1. Spawn with-skill and baseline runs in parallel
2. Grade each run with `agents/grader.md`
3. Aggregate into benchmark statistics
4. Run analyst pass with `agents/analyzer.md`
5. Launch eval-viewer for user review
6. Collect feedback

**Scripts:** `run_eval.py`, `aggregate_benchmark.py`, `generate_report.py`
**Viewer:** `eval-viewer/generate_review.py`

### Phase 6: Optimize

**Input:** Eval results + feedback
**Output:** Optimized SKILL.md

Two optimization loops:
1. **Content optimization**: Improve skill instructions based on functional eval feedback
2. **Description optimization**: Improve triggering accuracy via train/test split loop

Description optimization process:
- Split trigger evals 60% train / 40% test
- Evaluate current description (3 runs per query)
- Call Claude with extended thinking to propose improvements
- Re-evaluate on train + test
- Iterate up to 5 times
- Select best by TEST score (not train) to prevent overfitting

**Scripts:** `improve_description.py`, `run_loop.py`
**Agent:** `agents/optimizer.md`

### Phase 7: Multi-Platform Packaging

**Input:** Optimized skill
**Output:** Platform-specific packages in `dist/`

```
dist/
├── claude-code/<skill-name>/
│   ├── SKILL.md (with hooks in frontmatter)
│   └── scripts/, references/, assets/
├── openclaw/<skill-name>/
│   ├── SKILL.md
│   └── scripts/, references/, assets/
├── codex/<skill-name>/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── scripts/, references/, assets/
├── generic/<skill-name>.skill
└── manifest.json
```

**Script:** `scripts/package_multiplatform.py`
**Agent:** `agents/packager.md`

## Quality Standards

A well-generated skill should:
- Pass >80% of functional eval assertions
- Trigger correctly for >90% of trigger eval queries
- Have a description under 1024 characters
- Have SKILL.md under 500 lines
- Include at least 3 functional test cases
- Work on all enabled target platforms
- Properly attribute any bundled third-party content
