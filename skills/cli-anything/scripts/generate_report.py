# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Generate HTML reports from run_loop output."""
import json
import sys
from pathlib import Path
from typing import Any


def generate_report(
    loop_results: dict[str, Any],
    output_path: Path,
) -> None:
    """Generate an HTML report from run_loop results.

    Shows iterations with check/x marks per query, distinguishes
    train/test queries, and highlights the best iteration.

    Args:
        loop_results: Output from run_loop containing history, train/test queries.
        output_path: Path to write the HTML report.
    """
    history = loop_results.get("history", [])
    train_queries = loop_results.get("train_queries", [])
    test_queries = loop_results.get("test_queries", [])

    # Find best iteration by test score
    best_idx = 0
    best_test_score = -1.0
    for i, h in enumerate(history):
        if h.get("test_score", 0) > best_test_score:
            best_test_score = h["test_score"]
            best_idx = i

    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<title>Skill Eval Report</title>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2em; background: #f8f9fa; }",
        "h1 { color: #1a1a2e; }",
        "h2 { color: #16213e; margin-top: 2em; }",
        ".iteration { background: white; border-radius: 8px; padding: 1.5em; margin: 1em 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }",
        ".iteration.best { border: 2px solid #2ecc71; }",
        ".best-badge { background: #2ecc71; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px; }",
        ".description { background: #f0f0f0; padding: 0.8em; border-radius: 4px; font-family: monospace; font-size: 0.9em; margin: 0.5em 0; white-space: pre-wrap; word-break: break-word; }",
        ".scores { display: flex; gap: 2em; margin: 0.5em 0; }",
        ".score { font-size: 1.2em; font-weight: bold; }",
        ".score.good { color: #2ecc71; }",
        ".score.bad { color: #e74c3c; }",
        ".score.ok { color: #f39c12; }",
        "table { border-collapse: collapse; width: 100%; margin: 1em 0; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background: #f4f4f4; }",
        ".pass { color: #2ecc71; font-weight: bold; }",
        ".fail { color: #e74c3c; font-weight: bold; }",
        ".train-tag { background: #3498db; color: white; padding: 1px 6px; border-radius: 3px; font-size: 0.75em; }",
        ".test-tag { background: #9b59b6; color: white; padding: 1px 6px; border-radius: 3px; font-size: 0.75em; }",
        "</style>",
        "</head><body>",
        "<h1>Skill Trigger Eval Report</h1>",
    ]

    # Summary
    if history:
        html_parts.append("<h2>Summary</h2>")
        html_parts.append(f"<p>Iterations: {len(history)} | "
                          f"Best test score: {best_test_score:.1%} (iteration {best_idx + 1})</p>")

    # Iteration details
    for i, h in enumerate(history):
        is_best = i == best_idx
        cls = "iteration best" if is_best else "iteration"
        badge = '<span class="best-badge">BEST</span>' if is_best else ""

        train_score = h.get("train_score", 0)
        test_score = h.get("test_score", 0)
        train_cls = "good" if train_score >= 0.9 else ("ok" if train_score >= 0.7 else "bad")
        test_cls = "good" if test_score >= 0.9 else ("ok" if test_score >= 0.7 else "bad")

        html_parts.append(f'<div class="{cls}">')
        html_parts.append(f"<h2>Iteration {h['iteration']}{badge}</h2>")
        html_parts.append(f'<div class="description">{_escape_html(h["description"])}</div>')
        html_parts.append('<div class="scores">')
        html_parts.append(f'<div>Train: <span class="score {train_cls}">{train_score:.1%}</span></div>')
        html_parts.append(f'<div>Test: <span class="score {test_cls}">{test_score:.1%}</span></div>')
        html_parts.append("</div>")

        # Results table
        html_parts.append("<table>")
        html_parts.append("<tr><th>Set</th><th>Query</th><th>Should Trigger</th><th>Triggered</th><th>Result</th></tr>")

        # Train results
        for r in h.get("train_results", {}).get("results", []):
            tag = '<span class="train-tag">train</span>'
            result_cls = "pass" if r["passed"] else "fail"
            result_mark = "PASS" if r["passed"] else "FAIL"
            html_parts.append(
                f"<tr><td>{tag}</td>"
                f"<td>{_escape_html(r['query'])}</td>"
                f"<td>{r['should_trigger']}</td>"
                f"<td>{r['triggered']}</td>"
                f'<td class="{result_cls}">{result_mark}</td></tr>'
            )

        # Test results
        for r in h.get("test_results", {}).get("results", []):
            tag = '<span class="test-tag">test</span>'
            result_cls = "pass" if r["passed"] else "fail"
            result_mark = "PASS" if r["passed"] else "FAIL"
            html_parts.append(
                f"<tr><td>{tag}</td>"
                f"<td>{_escape_html(r['query'])}</td>"
                f"<td>{r['should_trigger']}</td>"
                f"<td>{r['triggered']}</td>"
                f'<td class="{result_cls}">{result_mark}</td></tr>'
            )

        html_parts.append("</table>")
        html_parts.append("</div>")

    html_parts.extend(["</body></html>"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(html_parts))
    print(f"Report written to {output_path}")


def _escape_html(text: str) -> str:
    """Basic HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate eval report")
    parser.add_argument("--input", type=Path, required=True, help="Path to run_loop_results.json")
    parser.add_argument("--output", type=Path, required=True, help="Output HTML path")
    args = parser.parse_args()

    with open(args.input) as f:
        loop_results = json.load(f)

    generate_report(loop_results, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
