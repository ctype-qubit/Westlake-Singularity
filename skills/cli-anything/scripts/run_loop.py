# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Eval + improve loop: iteratively improve skill descriptions using eval feedback."""
import json
import random
import sys
from pathlib import Path
from typing import Any

from scripts.improve_description import improve_description
from scripts.run_eval import run_eval
from scripts.utils import parse_skill_md


def _split_queries(
    queries: list[dict[str, Any]],
    train_ratio: float = 0.6,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split queries into train and test sets."""
    rng = random.Random(seed)
    shuffled = list(queries)
    rng.shuffle(shuffled)
    split_idx = int(len(shuffled) * train_ratio)
    return shuffled[:split_idx], shuffled[split_idx:]


def run_loop(
    skill_path: Path,
    queries: list[dict[str, Any]],
    max_iterations: int = 5,
    train_ratio: float = 0.6,
    model: str | None = None,
    improvement_model: str = "claude-sonnet-4-20250514",
    max_workers: int = 4,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the eval + improve loop.

    Args:
        skill_path: Path to the skill directory.
        queries: All eval queries.
        max_iterations: Maximum improvement iterations.
        train_ratio: Fraction of queries used for training (rest for test).
        model: Model for eval runs.
        improvement_model: Model for description improvement.
        max_workers: Max parallel workers for eval.
        output_dir: Directory for output files (reports, etc.).

    Returns:
        Dict with 'history' (list of iteration results) and 'best' info.
    """
    name, current_description, content = parse_skill_md(skill_path)

    train_queries, test_queries = _split_queries(queries, train_ratio)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    history: list[dict[str, Any]] = []
    best_iteration = -1
    best_test_score = -1.0

    for iteration in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"Iteration {iteration + 1}/{max_iterations}")
        print(f"Description: {current_description[:80]}...")
        print(f"{'='*60}")

        # Run eval on train set
        print("\nRunning train eval...")
        train_results = run_eval(
            queries=train_queries,
            skill_name=name,
            skill_description=current_description,
            model=model,
            max_workers=max_workers,
        )
        train_score = train_results["summary"]["pass_rate"]
        print(f"Train score: {train_score:.1%}")

        # Run eval on test set
        print("Running test eval...")
        test_results = run_eval(
            queries=test_queries,
            skill_name=name,
            skill_description=current_description,
            model=model,
            max_workers=max_workers,
        )
        test_score = test_results["summary"]["pass_rate"]
        print(f"Test score: {test_score:.1%}")

        iteration_data = {
            "iteration": iteration + 1,
            "description": current_description,
            "train_results": train_results,
            "test_results": test_results,
            "train_score": train_score,
            "test_score": test_score,
        }
        history.append(iteration_data)

        # Track best by test score
        if test_score > best_test_score:
            best_test_score = test_score
            best_iteration = iteration

        # Generate live HTML report
        if output_dir:
            _generate_live_report(history, train_queries, test_queries, output_dir)

        # If perfect on train, stop early
        if train_score == 1.0:
            print("Perfect train score! Stopping early.")
            break

        # Improve description based on train results
        print("\nImproving description...")
        improvement = improve_description(
            current_description=current_description,
            eval_results=train_results,
            history=[
                {"description": h["description"], "score": h["train_score"]}
                for h in history
            ],
            model=improvement_model,
        )
        current_description = improvement["description"]
        print(f"New description: {current_description[:80]}...")

    # Find best iteration by test score
    best = history[best_iteration]

    result = {
        "history": history,
        "best": {
            "iteration": best["iteration"],
            "description": best["description"],
            "train_score": best["train_score"],
            "test_score": best["test_score"],
        },
        "train_queries": train_queries,
        "test_queries": test_queries,
    }

    if output_dir:
        (output_dir / "run_loop_results.json").write_text(json.dumps(result, indent=2))

    return result


def _generate_live_report(
    history: list[dict[str, Any]],
    train_queries: list[dict[str, Any]],
    test_queries: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Generate a live HTML report of the loop progress."""
    from scripts.generate_report import generate_report

    report_data = {
        "history": history,
        "train_queries": train_queries,
        "test_queries": test_queries,
    }
    generate_report(report_data, output_dir / "report.html")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run eval + improve loop")
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument("--eval-file", type=Path, required=True, help="Path to evals.json")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--improvement-model", type=str, default="claude-sonnet-4-20250514")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    with open(args.eval_file) as f:
        queries = json.load(f)

    result = run_loop(
        skill_path=args.skill_path,
        queries=queries,
        max_iterations=args.max_iterations,
        train_ratio=args.train_ratio,
        model=args.model,
        improvement_model=args.improvement_model,
        max_workers=args.max_workers,
        output_dir=args.output_dir,
    )

    best = result["best"]
    print(f"\nBest iteration: {best['iteration']}")
    print(f"Best description: {best['description']}")
    print(f"Best test score: {best['test_score']:.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
