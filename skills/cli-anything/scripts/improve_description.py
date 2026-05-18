# Adapted from Anthropic Skill Creator (Apache 2.0) - see NOTICE
"""Use Claude API with extended thinking to improve skill descriptions based on eval results."""
import json
import sys
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

MAX_DESCRIPTION_LENGTH = 1024


def _build_improvement_prompt(
    current_description: str,
    failed_triggers: list[dict[str, Any]],
    false_positives: list[dict[str, Any]],
    history: list[dict[str, Any]] | None = None,
) -> str:
    """Build the prompt for Claude to improve the description."""
    parts = [
        "You are an expert at writing skill descriptions that trigger correctly.",
        "",
        "## Current Description",
        current_description,
        "",
    ]

    if failed_triggers:
        parts.append("## Failed Triggers (should have triggered but didn't)")
        for ft in failed_triggers:
            parts.append(f"- Query: {ft['query']}")
        parts.append("")

    if false_positives:
        parts.append("## False Positives (triggered but shouldn't have)")
        for fp in false_positives:
            parts.append(f"- Query: {fp['query']}")
        parts.append("")

    if history:
        parts.append("## Previous Attempts")
        for h in history:
            parts.append(f"- Description: {h.get('description', 'N/A')}")
            parts.append(f"  Score: {h.get('score', 'N/A')}")
        parts.append("")

    parts.extend(
        [
            "## Instructions",
            f"Write an improved description (max {MAX_DESCRIPTION_LENGTH} chars) that:",
            "1. Triggers for all the failed trigger queries above",
            "2. Does NOT trigger for the false positive queries",
            "3. Is specific and clear about what the skill does",
            "4. Uses keywords that match the trigger queries naturally",
            "5. Does not contain angle brackets (< or >)",
            "",
            "Return ONLY a JSON object with a single key 'description' containing the new text.",
            "Do not include any other text or explanation.",
        ]
    )

    return "\n".join(parts)


def improve_description(
    current_description: str,
    eval_results: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, Any]:
    """Use Claude API to improve a skill description based on eval results.

    Args:
        current_description: The current skill description.
        eval_results: Output from run_eval containing results and summary.
        history: Optional list of previous improvement attempts.
        model: Model to use for improvement.

    Returns:
        Dict with 'description' (new description) and 'reasoning' (if available).
    """
    if anthropic is None:
        raise ImportError(
            "anthropic package required. Install with: pip install anthropic"
        )

    # Extract failed triggers and false positives
    results = eval_results.get("results", [])
    failed_triggers = [
        r for r in results if r["should_trigger"] and not r["triggered"]
    ]
    false_positives = [
        r for r in results if not r["should_trigger"] and r["triggered"]
    ]

    if not failed_triggers and not false_positives:
        return {
            "description": current_description,
            "reasoning": "No improvements needed - all queries passed.",
        }

    prompt = _build_improvement_prompt(
        current_description, failed_triggers, false_positives, history
    )

    client = anthropic.Anthropic()

    # Use extended thinking for better reasoning
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 10000,
        },
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract thinking and text blocks
    reasoning = ""
    text_content = ""

    for block in response.content:
        if block.type == "thinking":
            reasoning = block.thinking
        elif block.type == "text":
            text_content = block.text

    # Parse the JSON response
    try:
        # Try to extract JSON from the response
        json_str = text_content.strip()
        if json_str.startswith("```"):
            # Strip code fences
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])
        result = json.loads(json_str)
        new_description = result["description"]
    except (json.JSONDecodeError, KeyError):
        # Fallback: use the raw text as description
        new_description = text_content.strip()

    # Auto-shorten if exceeds max length
    if len(new_description) > MAX_DESCRIPTION_LENGTH:
        # Truncate at last complete sentence within limit
        truncated = new_description[:MAX_DESCRIPTION_LENGTH]
        last_period = truncated.rfind(".")
        if last_period > MAX_DESCRIPTION_LENGTH // 2:
            new_description = truncated[: last_period + 1]
        else:
            new_description = truncated.rstrip()

    return {
        "description": new_description,
        "reasoning": reasoning,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Improve skill description")
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument(
        "--eval-results", type=Path, required=True, help="Path to eval results JSON"
    )
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    from scripts.utils import parse_skill_md

    _, current_description, _ = parse_skill_md(args.skill_path)

    with open(args.eval_results) as f:
        eval_results = json.load(f)

    result = improve_description(
        current_description=current_description,
        eval_results=eval_results,
        model=args.model,
    )

    output_json = json.dumps(result, indent=2)

    if args.output:
        args.output.write_text(output_json)
        print(f"Result written to {args.output}")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
