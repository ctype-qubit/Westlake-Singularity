# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Run trigger evaluation: test whether a skill description triggers Claude for test queries."""
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def _run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    should_trigger: bool,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a single trigger test query against Claude.

    Creates a temporary command file in .claude/commands/ and invokes
    `claude -p` with --output-format stream-json to detect triggering.

    Returns a dict with query, expected, actual, and pass/fail.
    """
    # Create temporary command file
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Use a unique temp file name
    cmd_file = claude_dir / f"_eval_trigger_{os.getpid()}_{id(query)}.md"

    try:
        # Write the skill command file
        cmd_file.write_text(
            f"---\n"
            f"name: {skill_name}\n"
            f"description: {skill_description}\n"
            f"---\n\n"
            f"This is a test skill for evaluation.\n"
        )

        # Build claude command
        cmd = ["claude", "-p", query, "--output-format", "stream-json"]
        if model:
            cmd.extend(["--model", model])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Parse stream-json output to detect triggering
        triggered = False
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "content_block_start":
                    # Check if the content block references our skill
                    content_block = event.get("content_block", {})
                    if content_block.get("type") == "tool_use":
                        tool_name = content_block.get("name", "")
                        if skill_name in tool_name:
                            triggered = True
                            break
            except json.JSONDecodeError:
                continue

        passed = triggered == should_trigger

        return {
            "query": query,
            "should_trigger": should_trigger,
            "triggered": triggered,
            "passed": passed,
        }

    finally:
        # Clean up temp command file
        if cmd_file.exists():
            cmd_file.unlink()


def run_eval(
    queries: list[dict[str, Any]],
    skill_name: str,
    skill_description: str,
    model: str | None = None,
    max_workers: int = 4,
) -> dict[str, Any]:
    """Run trigger evaluation for a list of queries.

    Args:
        queries: List of dicts with 'query' and 'should_trigger' keys.
        skill_name: Name of the skill being tested.
        skill_description: Description of the skill.
        model: Optional model override.
        max_workers: Max parallel workers.

    Returns:
        Dict with 'results' list and 'summary' stats.
    """
    results: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for q in queries:
            future = executor.submit(
                _run_single_query,
                query=q["query"],
                skill_name=skill_name,
                skill_description=skill_description,
                should_trigger=q["should_trigger"],
                model=model,
            )
            futures[future] = q

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                q = futures[future]
                results.append(
                    {
                        "query": q["query"],
                        "should_trigger": q["should_trigger"],
                        "triggered": False,
                        "passed": False,
                        "error": str(e),
                    }
                )

    # Calculate summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    # Breakdown by trigger type
    should_trigger_results = [r for r in results if r["should_trigger"]]
    should_not_trigger_results = [r for r in results if not r["should_trigger"]]

    true_positives = sum(1 for r in should_trigger_results if r["triggered"])
    false_negatives = sum(1 for r in should_trigger_results if not r["triggered"])
    true_negatives = sum(1 for r in should_not_trigger_results if not r["triggered"])
    false_positives = sum(1 for r in should_not_trigger_results if r["triggered"])

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
    }

    return {"results": results, "summary": summary}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run trigger evaluation")
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument("--eval-file", type=Path, required=True, help="Path to evals.json")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    from scripts.utils import parse_skill_md

    name, description, _ = parse_skill_md(args.skill_path)

    with open(args.eval_file) as f:
        queries = json.load(f)

    output = run_eval(
        queries=queries,
        skill_name=name,
        skill_description=description,
        model=args.model,
        max_workers=args.max_workers,
    )

    output_json = json.dumps(output, indent=2)

    if args.output:
        args.output.write_text(output_json)
        print(f"Results written to {args.output}")
    else:
        print(output_json)

    # Print summary
    s = output["summary"]
    print(f"\nSummary: {s['passed']}/{s['total']} passed ({s['pass_rate']:.1%})")
    print(f"  TP={s['true_positives']} FN={s['false_negatives']} "
          f"TN={s['true_negatives']} FP={s['false_positives']}")

    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
