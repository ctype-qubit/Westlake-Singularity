# Pipeline Phases Reference

Detailed specification for each of the 7 phases in the SkillAnything pipeline.

---

## Phase 1: Analyze Target

**Purpose:** Discover what the target is and extract its capabilities, inputs, outputs, and
error patterns.

### Input

- Target identifier: one of URL, executable name, package name, file path, or free-text description
- `config.yaml` settings: `target.type`, `target.url`, `target.path`, `target.name`, `target.extra_docs`

### Output

- `sa-workspace/analysis.json` (see `references/schemas.md` for full schema)

### Script

```bash
python -m scripts.analyze_target --target "<identifier>" --output sa-workspace/analysis.json
```

### Agent

`agents/analyzer.md` -- spawned for ambiguous cases where the script cannot confidently classify
the target (confidence < 0.7) or when the target requires intelligent interpretation (e.g.,
scraping unstructured documentation).

### Success Criteria

- `analysis.json` is valid JSON matching the schema
- `target_type` is one of: api, cli, library, workflow, service
- `confidence` >= 0.7 (or user confirmed in interactive mode)
- At least 1 capability extracted
- `raw_help` is non-empty

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| Target not found | CLI tool not in PATH, URL unreachable | Install the tool or check the URL. Provide `target.path` explicitly. |
| Low confidence (< 0.7) | Ambiguous target type | Set `target.type` in config.yaml to override auto-detection. |
| Empty capabilities | Docs inaccessible, tool has no --help | Provide `target.extra_docs` URLs pointing to documentation. |
| Timeout | Large API spec, slow network | Increase timeout. For large specs, provide a local copy via `target.path`. |
| Wrong target type | Heuristics misclassified | Override with `target.type: cli` (or api, library, etc.) in config. |

---

## Phase 2: Design Skill Architecture

**Purpose:** Transform the raw analysis into a structured skill design: what sections the SKILL.md
needs, which scripts to generate, what hooks to configure, and how to adapt per platform.

### Input

- `sa-workspace/analysis.json` (Phase 1 output)
- `config.yaml` settings: `platforms.enabled`, `platforms.primary`

### Output

- `sa-workspace/architecture.json` (see `references/schemas.md`)

### Script

```bash
python -m scripts.design_skill --analysis sa-workspace/analysis.json --output sa-workspace/architecture.json
```

### Agent

`agents/designer.md` -- makes architectural decisions: skill type selection, section ordering,
hook design, and cross-platform adaptation strategy.

### Success Criteria

- `architecture.json` is valid JSON matching the schema
- `skill_name` is non-empty kebab-case
- `structure.skill_md_sections` has at least 3 entries
- `triggers` list has at least 3 entries
- All enabled platforms have corresponding entries in `platforms`

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| Generic architecture | Analysis too shallow | Re-run Phase 1 with `extra_docs` for richer analysis. |
| Missing platform config | Platform not in analysis | Ensure `platforms.enabled` in config matches desired targets. |
| Too many scripts planned | Over-engineering | The designer should prefer inline instructions over scripts. Reduce `capabilities` count in analysis. |
| No triggers | Description field empty in analysis | Manually add trigger phrases or re-run analysis. |

---

## Phase 3: Implement

**Purpose:** Generate the complete skill directory: SKILL.md with proper frontmatter and body,
helper scripts, reference files, and configuration defaults.

### Input

- `sa-workspace/architecture.json` (Phase 2 output)
- `sa-workspace/analysis.json` (Phase 1 output)
- Templates from `templates/skill-scaffold/`

### Output

- Complete skill directory at `sa-workspace/<skill-name>/`
  - `SKILL.md`
  - `scripts/` (if any helper scripts were designed)
  - `references/` (if any reference docs were designed)
  - `assets/` (if any static assets were designed)

### Script

```bash
python -m scripts.init_skill <skill-name> --template <target-type> --output sa-workspace/
```

The script handles scaffolding (directory creation, template rendering). The agent handles
content writing (SKILL.md body, script logic, reference content).

### Agent

`agents/implementer.md` -- writes the actual skill content following these principles:
- Explain the WHY, not just the WHAT
- Use imperative form in instructions
- Avoid heavy-handed MUSTs; rely on theory of mind
- Keep SKILL.md lean with progressive disclosure
- Bundle repeated deterministic work as scripts

### Success Criteria

- `SKILL.md` exists and has valid YAML frontmatter
- `name` and `description` fields are present in frontmatter
- SKILL.md body is under 500 lines
- Description is under 1024 characters
- All scripts referenced in SKILL.md body exist in `scripts/`
- All references mentioned in SKILL.md body exist in `references/`

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| SKILL.md too long | Trying to cover every capability | Focus on core capabilities. Move advanced content to references/. |
| Missing scripts | Architecture referenced scripts not created | Re-run implementation or create stubs manually. |
| Invalid frontmatter | YAML syntax error | Validate YAML before writing. Common issue: unquoted special chars. |
| Description too long | Trying to cover all trigger cases | Focus on primary use case. Rely on Phase 6 optimization for trigger accuracy. |
| Broken script references | Path mismatch | Ensure all paths in SKILL.md use relative paths from the skill root. |

---

## Phase 4: Test Planning

**Purpose:** Auto-generate test cases for functional evaluation and trigger queries for
description optimization.

### Input

- `sa-workspace/analysis.json` (Phase 1 output)
- Generated skill at `sa-workspace/<skill-name>/`

### Output

- `sa-workspace/<skill-name>/evals/evals.json` (functional test cases)
- `sa-workspace/<skill-name>/evals/trigger-evals.json` (trigger queries)

### Script

```bash
python -m scripts.generate_tests --analysis sa-workspace/analysis.json --skill-path sa-workspace/<skill-name>
```

### Agent

No dedicated agent. The script uses the model directly with structured output to generate
test cases matching the schemas.

### Success Criteria

- `evals.json` has at least `eval.num_test_cases` entries (default: 5)
- Each test case has at least 1 assertion
- `trigger-evals.json` has at least `eval.num_trigger_queries` entries (default: 20)
- At least 50% should-trigger and 50% should-not-trigger queries
- Trigger queries include a mix of easy, medium, and hard difficulty
- Should-not-trigger queries are near-misses, not obviously unrelated

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| Generic test cases | Analysis lacked concrete examples | Add realistic usage examples to the analysis or architecture. |
| All-easy trigger queries | Description too specific or too vague | Ensure description covers edge cases. Adjust difficulty distribution. |
| Missing assertions | Model generated prompts without verification criteria | Re-run with explicit instruction to include assertions. |
| Duplicate queries | Small target surface area | Reduce `num_trigger_queries` in config. |

---

## Phase 5: Evaluate and Benchmark

**Purpose:** Run the skill against test cases, grade results, compare with-skill vs baseline
performance, and present findings.

### Input

- Generated skill at `sa-workspace/<skill-name>/`
- `evals/evals.json` (functional test cases)
- `evals/trigger-evals.json` (trigger queries)

### Output

- `sa-workspace/<skill-name>/evals/grading/` -- per-run grading files
- `sa-workspace/<skill-name>/evals/benchmark.json` -- aggregated statistics
- `sa-workspace/<skill-name>/evals/comparison.json` -- blind comparisons
- HTML report via `eval-viewer/`

### Scripts

```bash
# Run eval suite
python -m scripts.run_eval --eval-set sa-workspace/<skill-name>/evals/evals.json \
  --skill-path sa-workspace/<skill-name>

# Aggregate results
python -m scripts.aggregate_benchmark --grading-dir sa-workspace/<skill-name>/evals/grading/ \
  --output sa-workspace/<skill-name>/evals/benchmark.json

# Generate HTML report
python -m scripts.generate_report --benchmark sa-workspace/<skill-name>/evals/benchmark.json
```

### Agents

- `agents/grader.md` -- grades each eval run against assertions and provides qualitative scores
- `agents/comparator.md` -- performs blind A/B comparison of with-skill vs baseline outputs

### Success Criteria

- All test cases have been run `runs_per_config` times in both modes
- `benchmark.json` is populated with statistics
- With-skill mean score > baseline mean score
- With-skill pass rate > 80%
- Trigger accuracy > `eval.trigger_threshold` (default: 0.5)

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| All runs fail | Skill references unavailable tools | Check `allowed-tools` and dependency availability. |
| No improvement over baseline | Skill adds no value for these prompts | Review test cases for relevance. The skill may need redesign (back to Phase 2). |
| High variance | Too few runs | Increase `runs_per_config`. |
| Low trigger accuracy | Description poorly tuned | Proceed to Phase 6 optimization. |
| Timeout on eval runs | Complex test cases | Increase `eval.timeout` in config. |

---

## Phase 6: Optimize

**Purpose:** Improve the skill description for trigger accuracy using a train/test split
optimization loop. Optionally improve skill content based on functional eval feedback.

### Input

- Generated skill at `sa-workspace/<skill-name>/`
- `evals/trigger-evals.json` with train/test split
- `evals/benchmark.json` (feedback from Phase 5)

### Output

- Optimized `SKILL.md` with improved description
- `sa-workspace/<skill-name>/evals/optimization-log.json` (history of iterations)

### Scripts

```bash
# Full optimization loop
python -m scripts.run_loop --eval-set sa-workspace/<skill-name>/evals/trigger-evals.json \
  --skill-path sa-workspace/<skill-name> --model <model>

# Single description improvement iteration
python -m scripts.improve_description --skill-path sa-workspace/<skill-name> \
  --eval-results sa-workspace/<skill-name>/evals/grading/
```

### Agent

`agents/optimizer.md` -- orchestrates the optimization loop:
1. Split trigger evals: 60% train / 40% test (configurable via `eval.holdout`)
2. Evaluate current description (3 runs per query on train set)
3. Call Claude with extended thinking to propose description improvements
4. Re-evaluate proposed description on both train and test sets
5. Accept improvement only if test score improves (prevents overfitting)
6. Repeat up to `max_optimization_iterations` times
7. Select the description with the best test score

### Success Criteria

- Trigger accuracy on test set improves over baseline
- Description remains under 1024 characters
- No overfitting: test score does not diverge significantly from train score
- Optimization completes within `max_optimization_iterations`

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| No improvement after iterations | Description already near-optimal, or queries too hard | Accept current description. Review query quality. |
| Overfitting (train >> test) | Too few test queries | Increase `num_trigger_queries` and `holdout` ratio. |
| Description keeps growing | Optimizer adding too many trigger phrases | Add max-length constraint. Use `description_style: conservative`. |
| Oscillating scores | High eval variance | Increase `runs_per_query` for more stable measurements. |

---

## Phase 7: Multi-Platform Packaging

**Purpose:** Take the optimized skill and produce platform-specific packages for all enabled
platforms. Generate a distribution manifest.

### Input

- Optimized skill at `sa-workspace/<skill-name>/`
- `config.yaml` settings: `platforms.enabled`, `obfuscation.enabled`
- `evals/benchmark.json` (for manifest summary)

### Output

- `dist/claude-code/<skill-name>/` -- Claude Code package
- `dist/openclaw/<skill-name>/` -- OpenClaw package
- `dist/codex/<skill-name>/` -- Codex package with agents/openai.yaml
- `dist/generic/<skill-name>.skill` -- Generic zip package
- `dist/manifest.json` -- distribution manifest

### Script

```bash
python -m scripts.package_multiplatform sa-workspace/<skill-name> \
  --platforms claude-code,openclaw,codex,generic \
  --output dist/
```

### Agent

`agents/packager.md` -- handles platform-specific adaptations:
- Claude Code: embed hooks in SKILL.md frontmatter
- OpenClaw: strip hooks from frontmatter, generate settings.json fragment
- Codex: generate agents/openai.yaml with interface configuration
- Generic: create .skill zip archive

### Success Criteria

- All enabled platforms have a valid package in `dist/`
- Each package's SKILL.md has valid frontmatter for its platform
- `manifest.json` lists all files with correct checksums
- Codex package includes `agents/openai.yaml`
- Generic package is a valid zip with SKILL.md at root
- All script paths in each package resolve correctly
- If obfuscation is enabled, specified scripts are obfuscated

### Common Failure Modes

| Problem | Cause | Fix |
|---------|-------|-----|
| Missing openai.yaml | Codex platform enabled but interface config empty | Ensure Phase 2 populated `platforms.codex.interface`. |
| Broken script paths | Path rewriting error during packaging | Verify all paths are relative to skill root before packaging. |
| Zip creation fails | Permission error or missing files | Check file permissions. Ensure all referenced files exist. |
| Obfuscation fails | PyArmor not installed or license issue | Install PyArmor: `pip install pyarmor`. See `references/obfuscation-guide.md`. |
| Large package size | Bundled raw_help or large assets | Exclude raw analysis artifacts. Compress assets. |
| Checksum mismatch | File modified after packaging | Re-run packaging. Do not modify files in dist/ after generation. |
