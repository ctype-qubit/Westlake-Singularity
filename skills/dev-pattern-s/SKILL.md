---
name: pattern-s-collaboration
description: "Pattern S — Parallel multi-agent collaboration workflow. Jupiter decomposes tasks, then simultaneously launches Mars/Venus/Saturn as independent background processes, then Jupiter validates and merges results."
version: 1.0.0
author: Jupiter
---

# Pattern S — Parallel Multi-Agent Collaboration

## Core Principle

**Jupiter decomposes → Agents parallel execute → Jupiter validates and merges.**

This is the opposite of serial delegation. Pattern S is for **real parallel work** — multiple agents working simultaneously on independent subtasks.

## When to Use

- Multiple independent subtasks that can run in parallel
- Large engineering work that would overwhelm a single agent's context
- Tasks requiring different agent specializations (e.g., Mars for layout code, Venus for writing, Saturn for literature)

## Workflow

### Step 1: Jupiter Decomposes

Jupiter breaks the user's request into independent subtasks and writes a task file for each:

```
/tmp/task_mars_xxx.md  — layout code generation
/tmp/task_venus_xxx.md — paper/LaTeX writing
/tmp/task_saturn_xxx.md — literature research
```

Each task file is **self-contained** with: goal, input specs, output path, constraints.

### Step 2: Jupiter Launches All Agents Simultaneously

Using `terminal(background=true, notify_on_complete=true)`:

```python
# Launch all agents in parallel — they're independent OS processes
terminal("hermes --profile mars run --prompt-file /tmp/task_mars_xxx.md", background=True, notify_on_complete=True)
terminal("hermes --profile venus run --prompt-file /tmp/task_venus_xxx.md", background=True, notify_on_complete=True)
terminal("hermes --profile saturn run --prompt-file /tmp/task_saturn_xxx.md", background=True, notify_on_complete=True)
```

Each agent:
- Uses its **own profile** (Mars, Venus, Saturn) with its own config, API keys, and persona
- Has its **own terminal session** (isolated cwd)
- Outputs to a **fixed path** and exits
- **notify_on_complete=true** — Jupiter gets notified when each finishes

### Step 3: Jupiter Validates & Merges

After all agents complete (wait for all notifications):
1. Read each agent's output file
2. Validate correctness and completeness
3. Merge into a final result for the user
4. Report what each agent did

## What NOT to Do

❌ **Serial delegation** — `delegate_task → wait → delegate_task → wait` wastes parallelism
❌ **Jupiter doing everything** — defeats the purpose of having a team
❌ **Using `delegate_task` for large work** — `delegate_task` is synchronous and runs inside Jupiter's context; use background processes instead for long-running work

## When to Use `delegate_task` Instead

`delegate_task` is still the right tool for:
- **Short pure-computation tasks** (Mercury code review, file parsing, small analysis)
- Tasks that don't need their own profile/persona
- Tasks that need sequential processing with Jupiter's context

## Pitfalls

- **Task files must be self-contained** — agents have no access to conversation history
- **Output paths must be unique** — avoid file conflicts between agents
- **`hermes run` does NOT exist** — use `hermes chat` as subcommand, not `run`
- **`hermes chat -z "$(cat file)"` fails with `#` in prompt** — shell treats `#` as comment. Workaround: pipe via stdin, BUT...
- **`hermes chat < file` says "Input is not a terminal"** — `chat` mode requires a TTY. Piped input via stdin does NOT work for background agent launch.
- **`delegate_task` model name format** — delegation config uses `provider/model` format, but some APIs (e.g. DeepSeek) expect bare model names. Check provider requirements before using delegate_task.
- **When all launch methods fail**, Jupiter handles work directly with web_search + file writes. Serial execution is slower but reliable.
- **Monitor via `process(action="poll")`** — check progress of any agent if needed
- ⚠️ **hermes run is not a valid subcommand** — use `hermes chat` instead. `hermes run --prompt-file` will fail with exit code 2.
- ⚠️ **hermes chat does not accept piped input** — `hermes chat < task.md` exits immediately with "Input is not a terminal (fd=0)". 
- ⚠️ **hermes chat -z has shell quoting issues** — `-z "$(cat file.md)"` fails when file contains `#` (shell comment). Use `hermes chat` without args and type/paste the prompt.
- ⚠️ **delegate_task model naming**: delegation model in config.yaml must NOT have `provider/` prefix. Use `deepseek-v4-pro` not `deepseek/deepseek-v4-pro`. Even after `hermes config set`, verify the config file directly.
- **Fallback**: when background processes fail, use `execute_code` to write task files and handle all research angles sequentially within Jupiter's own context. This is slower but reliable.
