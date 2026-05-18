# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Aggregate benchmark results from multiple runs into summary statistics."""
import json
import math
import sys
from pathlib import Path
from typing import Any


def _load_grading_results(run_dirs: list[Path]) -> list[dict[str, Any]]:
    """Load grading.json from each run directory.

    Supports both workspace layout (run_dir/grading.json) and
    legacy layout (run_dir/outputs/grading.json).
    """
    results = []
    for run_dir in run_dirs:
        # Try workspace layout first
        grading_path = run_dir / "grading.json"
        if not grading_path.exists():
            # Try legacy layout
            grading_path = run_dir / "outputs" / "grading.json"
        if not grading_path.exists():
            print(f"Warning: No grading.json found in {run_dir}", file=sys.stderr)
            continue

        with open(grading_path) as f:
            data = json.load(f)
        data["_run_dir"] = str(run_dir)
        results.append(data)

    return results


def _calculate_stats(values: list[float]) -> dict[str, float]:
    """Calculate mean, stddev, min, max for a list of values."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "count": 0}

    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": mean,
        "stddev": stddev,
        "min": min(values),
        "max": max(values),
        "count": n,
    }


def aggregate_benchmark(
    workspace_dir: Path | None = None,
    run_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    """Aggregate benchmark results from multiple runs.

    Args:
        workspace_dir: Directory containing run_* subdirectories.
        run_dirs: Explicit list of run directories.

    Returns:
        Dict with aggregated statistics.
    """
    if run_dirs is None and workspace_dir is not None:
        # Discover run directories
        run_dirs = sorted(
            d for d in workspace_dir.iterdir()
            if d.is_dir() and d.name.startswith("run_")
        )

    if not run_dirs:
        return {"error": "No run directories found", "stats": {}}

    results = _load_grading_results(run_dirs)

    if not results:
        return {"error": "No grading results found", "stats": {}}

    # Aggregate scores
    all_scores: dict[str, list[float]] = {}

    for result in results:
        scores = result.get("scores", {})
        for metric, value in scores.items():
            if isinstance(value, (int, float)):
                all_scores.setdefault(metric, []).append(float(value))

        # Also handle flat score field
        if "score" in result and isinstance(result["score"], (int, float)):
            all_scores.setdefault("overall", []).append(float(result["score"]))

    # Calculate stats per metric
    stats = {}
    for metric, values in all_scores.items():
        stats[metric] = _calculate_stats(values)

    benchmark = {
        "num_runs": len(results),
        "stats": stats,
        "runs": [
            {
                "run_dir": r.get("_run_dir", "unknown"),
                "scores": {
                    k: v for k, v in r.items()
                    if k not in ("_run_dir",) and isinstance(v, (int, float))
                },
            }
            for r in results
        ],
    }

    return benchmark


def generate_benchmark_report(
    benchmark: dict[str, Any], output_dir: Path
) -> None:
    """Generate benchmark.json and benchmark.md from aggregated results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    json_path = output_dir / "benchmark.json"
    json_path.write_text(json.dumps(benchmark, indent=2))
    print(f"Written: {json_path}")

    # Write Markdown report
    md_lines = [
        "# Benchmark Results",
        "",
        f"**Runs:** {benchmark.get('num_runs', 0)}",
        "",
        "## Statistics",
        "",
        "| Metric | Mean | Std Dev | Min | Max | Count |",
        "|--------|------|---------|-----|-----|-------|",
    ]

    for metric, stat in benchmark.get("stats", {}).items():
        md_lines.append(
            f"| {metric} | {stat['mean']:.3f} | {stat['stddev']:.3f} | "
            f"{stat['min']:.3f} | {stat['max']:.3f} | {stat['count']} |"
        )

    md_lines.append("")

    md_path = output_dir / "benchmark.md"
    md_path.write_text("\n".join(md_lines))
    print(f"Written: {md_path}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    benchmark = aggregate_benchmark(workspace_dir=args.workspace_dir)

    if "error" in benchmark and not benchmark.get("stats"):
        print(f"Error: {benchmark['error']}", file=sys.stderr)
        return 1

    output_dir = args.output_dir or args.workspace_dir
    generate_benchmark_report(benchmark, output_dir)

    # Print summary
    print(f"\nBenchmark Summary ({benchmark.get('num_runs', 0)} runs):")
    for metric, stat in benchmark.get("stats", {}).items():
        print(f"  {metric}: {stat['mean']:.3f} +/- {stat['stddev']:.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
