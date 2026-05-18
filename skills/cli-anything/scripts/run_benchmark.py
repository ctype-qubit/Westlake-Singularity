# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Benchmark orchestration wrapper for SkillAnything.

Runs with-skill and without-skill evaluations, grades results,
and aggregates into benchmark statistics.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from scripts.aggregate_benchmark import aggregate_benchmark, generate_benchmark_report
from scripts.utils import parse_skill_md


def _run_single_benchmark(
    eval_case: dict[str, Any],
    skill_path: Path | None,
    workspace_dir: Path,
    run_id: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a single benchmark case (with or without skill).

    Args:
        eval_case: Dict with 'query' and 'grader_instructions'.
        skill_path: Path to skill directory, or None for without-skill.
        workspace_dir: Directory for outputs.
        run_id: Unique run identifier.
        model: Optional model override.

    Returns:
        Dict with run results and grading.
    """
    run_dir = workspace_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    query = eval_case["query"]

    # Build claude command
    cmd = ["claude", "-p", query, "--output-format", "json"]
    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        response = result.stdout.strip()

        # Save raw output
        (outputs_dir / "response.txt").write_text(response)
        (outputs_dir / "stderr.txt").write_text(result.stderr)

    except subprocess.TimeoutExpired:
        response = ""
        (outputs_dir / "response.txt").write_text("")
        (outputs_dir / "stderr.txt").write_text("TIMEOUT")

    # Grade using grader instructions
    grading = _grade_response(
        query=query,
        response=response,
        grader_instructions=eval_case.get("grader_instructions", ""),
        model=model,
    )

    # Save grading
    (run_dir / "grading.json").write_text(json.dumps(grading, indent=2))

    return {
        "run_id": run_id,
        "query": query,
        "with_skill": skill_path is not None,
        "grading": grading,
    }


def _grade_response(
    query: str,
    response: str,
    grader_instructions: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Grade a response using Claude as grader agent.

    Args:
        query: The original query.
        response: The model's response.
        grader_instructions: Instructions for the grader.
        model: Optional model override.

    Returns:
        Dict with score and reasoning.
    """
    grader_prompt = (
        f"You are a grading agent. Evaluate the following response.\n\n"
        f"## Original Query\n{query}\n\n"
        f"## Response\n{response}\n\n"
        f"## Grading Instructions\n{grader_instructions}\n\n"
        f"Return a JSON object with:\n"
        f'- "score": a float from 0.0 to 1.0\n'
        f'- "reasoning": brief explanation\n'
        f"Return ONLY the JSON object."
    )

    cmd = ["claude", "-p", grader_prompt, "--output-format", "json"]
    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            grading = json.loads(result.stdout.strip())
            if "score" not in grading:
                grading = {"score": 0.0, "reasoning": "Failed to parse grader output"}
        except json.JSONDecodeError:
            grading = {"score": 0.0, "reasoning": "Grader output not valid JSON"}
    except subprocess.TimeoutExpired:
        grading = {"score": 0.0, "reasoning": "Grader timed out"}

    return grading


def run_benchmark(
    skill_path: Path,
    eval_set_path: Path,
    workspace_dir: Path,
    runs_per_config: int = 3,
    model: str | None = None,
) -> dict[str, Any]:
    """Run full benchmark: with-skill and without-skill evaluations.

    Args:
        skill_path: Path to the skill directory.
        eval_set_path: Path to evals.json with benchmark cases.
        workspace_dir: Directory for all run outputs.
        runs_per_config: Number of runs per configuration.
        model: Optional model override.

    Returns:
        Dict with benchmark results and aggregated statistics.
    """
    workspace_dir.mkdir(parents=True, exist_ok=True)

    with open(eval_set_path) as f:
        eval_cases = json.load(f)

    name, description, _ = parse_skill_md(skill_path)

    all_results: list[dict[str, Any]] = []

    # Run with-skill evaluations
    print(f"\nRunning WITH-SKILL evaluations ({runs_per_config} runs per case)...")
    with_skill_dir = workspace_dir / "with_skill"
    with_skill_dir.mkdir(exist_ok=True)

    for case_idx, case in enumerate(eval_cases):
        for run_idx in range(runs_per_config):
            run_id = f"run_{case_idx:03d}_{run_idx:02d}_with"
            print(f"  {run_id}: {case['query'][:60]}...")
            result = _run_single_benchmark(
                eval_case=case,
                skill_path=skill_path,
                workspace_dir=with_skill_dir,
                run_id=run_id,
                model=model,
            )
            all_results.append(result)

    # Run without-skill evaluations
    print(f"\nRunning WITHOUT-SKILL evaluations ({runs_per_config} runs per case)...")
    without_skill_dir = workspace_dir / "without_skill"
    without_skill_dir.mkdir(exist_ok=True)

    for case_idx, case in enumerate(eval_cases):
        for run_idx in range(runs_per_config):
            run_id = f"run_{case_idx:03d}_{run_idx:02d}_without"
            print(f"  {run_id}: {case['query'][:60]}...")
            result = _run_single_benchmark(
                eval_case=case,
                skill_path=None,
                workspace_dir=without_skill_dir,
                run_id=run_id,
                model=model,
            )
            all_results.append(result)

    # Aggregate results
    print("\nAggregating results...")
    with_benchmark = aggregate_benchmark(workspace_dir=with_skill_dir)
    without_benchmark = aggregate_benchmark(workspace_dir=without_skill_dir)

    generate_benchmark_report(with_benchmark, with_skill_dir)
    generate_benchmark_report(without_benchmark, without_skill_dir)

    # Combined summary
    summary = {
        "skill_name": name,
        "eval_cases": len(eval_cases),
        "runs_per_config": runs_per_config,
        "with_skill": with_benchmark.get("stats", {}),
        "without_skill": without_benchmark.get("stats", {}),
        "all_results": all_results,
    }

    (workspace_dir / "benchmark.json").write_text(json.dumps(summary, indent=2))

    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run SkillAnything benchmark")
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument("--eval-set", type=Path, required=True, help="Path to evals.json")
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--runs-per-config", type=int, default=3)
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    summary = run_benchmark(
        skill_path=args.skill_path,
        eval_set_path=args.eval_set,
        workspace_dir=args.workspace_dir,
        runs_per_config=args.runs_per_config,
        model=args.model,
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"Benchmark Complete: {summary['skill_name']}")
    print(f"{'='*60}")
    print(f"Eval cases: {summary['eval_cases']}")
    print(f"Runs per config: {summary['runs_per_config']}")

    for config_name in ("with_skill", "without_skill"):
        stats = summary.get(config_name, {})
        print(f"\n{config_name}:")
        for metric, stat in stats.items():
            if isinstance(stat, dict) and "mean" in stat:
                print(f"  {metric}: {stat['mean']:.3f} +/- {stat['stddev']:.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
