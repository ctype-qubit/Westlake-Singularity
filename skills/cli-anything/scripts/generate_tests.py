#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 4 -- Auto-generate eval test cases from analysis.json.

Produces two JSON files:
  * Functional evals  (evals.json)   -- realistic user prompts per capability
  * Trigger evals     (trigger-evals.json) -- should-trigger / should-not-trigger queries

Usage:
    python generate_tests.py --analysis analysis.json \
        [--skill-path ./my-skill] \
        [--num-functional 5] [--num-trigger 20] \
        [--output-functional evals.json] \
        [--output-trigger trigger-evals.json]
"""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Prompt templates for functional evals
# ---------------------------------------------------------------------------

_FUNCTIONAL_TEMPLATES = {
    "cli": [
        "Can you run {tool} {cap} and show me the output?",
        "I need to use {tool} to {desc}. Walk me through it.",
        "What happens if I run {tool} {cap} with invalid arguments?",
        "Help me figure out the right flags for {tool} {cap}.",
        "I'm getting an error when running {tool} {cap}. Can you debug it?",
        "Show me how to use {tool} {cap} for a real-world scenario.",
        "I need to automate {tool} {cap} in a shell script.",
        "Compare the output of {tool} {cap} with and without the verbose flag.",
    ],
    "api": [
        "Make a request to {cap} and explain the response.",
        "How do I authenticate before calling {cap}?",
        "I'm getting a 403 when calling {cap}. What could be wrong?",
        "Show me how to paginate through {cap} results.",
        "Can you call {cap} with these parameters: {desc}",
        "What's the rate limit for {cap}?",
        "Help me build a script that calls {cap} periodically.",
        "Parse the JSON response from {cap} and extract the key fields.",
    ],
    "library": [
        "Show me how to use {cap} from the {tool} library.",
        "What parameters does {cap} accept?",
        "Write a short example using {cap} to {desc}.",
        "I'm getting a TypeError when calling {cap}. Help me fix it.",
        "How do I combine {cap} with other functions in {tool}?",
        "What's the return type of {cap}?",
    ],
    "workflow": [
        "Walk me through the {cap} step of the workflow.",
        "What happens after {cap} completes?",
        "I'm stuck at the {cap} stage. What should I check?",
        "Can I skip {cap} and go straight to the next step?",
        "How long does {cap} typically take?",
    ],
    "service": [
        "Connect to {tool} and run {cap}.",
        "How do I set up credentials for {tool}?",
        "Show me the result of {cap} on the service.",
        "What permissions do I need for {cap}?",
        "Troubleshoot a connection failure when trying {cap}.",
    ],
}

_GENERIC_TEMPLATES = [
    "Help me use {tool} to {desc}.",
    "What can {tool} do?",
    "I need to {desc} using {tool}. How?",
    "Show me an example of using {tool} for {cap}.",
    "Explain what {cap} does in {tool}.",
]


def _generate_functional_cases(
    analysis: dict,
    num: int,
) -> list[dict]:
    """Create functional eval cases from analysis capabilities."""
    target = analysis.get("target_name", "tool")
    target_type = analysis.get("target_type", "generic")
    capabilities = analysis.get("capabilities", [])

    if not capabilities:
        capabilities = [{"name": "main", "description": "use the tool", "type": "primary"}]

    templates = _FUNCTIONAL_TEMPLATES.get(target_type, _GENERIC_TEMPLATES)
    cases: list[dict] = []

    for i in range(num):
        cap = capabilities[i % len(capabilities)]
        cap_name = cap.get("name", "main")
        cap_desc = cap.get("description", "perform an action") or "perform an action"
        tmpl = templates[i % len(templates)]

        prompt = tmpl.format(tool=target, cap=cap_name, desc=cap_desc)

        case_id = f"func-{i+1:03d}-{hashlib.md5(prompt.encode()).hexdigest()[:6]}"
        cases.append({
            "id": case_id,
            "name": f"Test {cap_name} ({target_type})",
            "prompt": prompt,
            "context": {"files": {}, "env": {}},
            "assertions": [
                {
                    "type": "contains_keyword",
                    "target": "response",
                    "value": cap_name,
                    "weight": 1.0,
                },
                {
                    "type": "no_error",
                    "target": "execution",
                    "value": "true",
                    "weight": 0.5,
                },
            ],
            "expected_behavior": f"The agent should correctly invoke or explain {cap_name} from {target}.",
            "tags": [target_type, cap_name],
        })

    return cases


# ---------------------------------------------------------------------------
# Trigger eval generation
# ---------------------------------------------------------------------------

_SHOULD_TRIGGER_PATTERNS = [
    "I need to {verb} using {tool}",
    "Can you help me with {tool}?",
    "How do I {verb} in {tool}?",
    "Use {tool} to {verb} for me",
    "{tool} {cap} please",
    "Run {tool} and show me {cap}",
    "I'm trying to {verb} with {tool} but it's not working",
    "Show me how {tool} handles {cap}",
    "I want to {verb}. I think {tool} can do that.",
    "Help me set up {tool} for {cap}",
    "What's the best way to {verb} using {tool}?",
    "I have a project that needs {tool} for {cap}",
    "My boss asked me to {verb} and I think {tool} is the right tool",
    "Can {tool} do {cap}? I need it for a deadline tomorrow",
    "I've been manually doing {cap} -- can {tool} automate it?",
]

_SHOULD_NOT_TRIGGER_PATTERNS = [
    "I need to {verb} but I want to use a different tool",
    "What's a good alternative to {tool}?",
    "Compare {tool} with {similar}",
    "I don't want to use {tool}, suggest something else",
    "Help me uninstall {tool}",
    "Write a blog post about {generic_topic}",
    "What's the weather like today?",
    "Help me write a Python script to sort a list",
    "I need to schedule a meeting for tomorrow",
    "Can you explain how DNS works?",
    "Review this pull request for me",
    "Help me debug a CSS layout issue",
    "What's the best database for my app?",
    "I need to {verb} but without any external tools",
    "Tell me about the history of {generic_topic}",
]


def _generate_trigger_cases(
    analysis: dict,
    num_should: int,
    num_should_not: int,
) -> list[dict]:
    """Generate trigger eval queries."""
    target = analysis.get("target_name", "tool")
    capabilities = analysis.get("capabilities", [])

    cap_names = [c.get("name", "main") for c in capabilities[:5]] or ["main"]
    verbs = []
    for c in capabilities:
        desc = c.get("description", "")
        if desc:
            # Extract a verb-like phrase
            words = desc.split()[:4]
            verbs.append(" ".join(words).lower().rstrip("."))
    if not verbs:
        verbs = ["process data", "run commands", "manage resources"]

    similar_tools = [f"alternative-to-{target}", "other-tool", "competitor"]
    generic_topics = ["machine learning", "web development", "containerization", "networking"]

    cases: list[dict] = []

    # Should-trigger
    for i in range(num_should):
        tmpl = _SHOULD_TRIGGER_PATTERNS[i % len(_SHOULD_TRIGGER_PATTERNS)]
        query = tmpl.format(
            tool=target,
            cap=cap_names[i % len(cap_names)],
            verb=verbs[i % len(verbs)],
        )
        cases.append({
            "id": f"trig-yes-{i+1:03d}",
            "query": query,
            "should_trigger": True,
            "reasoning": f"Directly references {target} and its capabilities.",
        })

    # Should-not-trigger
    for i in range(num_should_not):
        tmpl = _SHOULD_NOT_TRIGGER_PATTERNS[i % len(_SHOULD_NOT_TRIGGER_PATTERNS)]
        query = tmpl.format(
            tool=target,
            cap=cap_names[i % len(cap_names)],
            verb=verbs[i % len(verbs)],
            similar=similar_tools[i % len(similar_tools)],
            generic_topic=generic_topics[i % len(generic_topics)],
        )
        cases.append({
            "id": f"trig-no-{i+1:03d}",
            "query": query,
            "should_trigger": False,
            "reasoning": "Does not require invoking the target skill.",
        })

    return cases


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(
    analysis: dict,
    num_functional: int = 5,
    num_trigger: int = 20,
) -> tuple[dict, dict]:
    """Return (functional_evals, trigger_evals) dicts."""
    target = analysis.get("target_name", "unnamed")

    functional_cases = _generate_functional_cases(analysis, num_functional)
    functional_evals = {
        "version": "1.0",
        "skill_name": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_cases": functional_cases,
    }

    num_should = num_trigger // 2
    num_should_not = num_trigger - num_should
    trigger_cases = _generate_trigger_cases(analysis, num_should, num_should_not)
    trigger_evals = {
        "version": "1.0",
        "skill_name": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trigger_queries": trigger_cases,
    }

    return functional_evals, trigger_evals


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-generate eval test cases from analysis.json.",
    )
    parser.add_argument("--analysis", required=True, help="Path to analysis.json.")
    parser.add_argument("--skill-path", default=None, help="Path to generated skill directory (optional).")
    parser.add_argument("--num-functional", type=int, default=5, help="Number of functional test cases.")
    parser.add_argument("--num-trigger", type=int, default=20, help="Number of trigger eval queries.")
    parser.add_argument("--output-functional", default="evals.json", help="Output path for functional evals.")
    parser.add_argument("--output-trigger", default="trigger-evals.json", help="Output path for trigger evals.")
    args = parser.parse_args()

    analysis_path = Path(args.analysis)
    if not analysis_path.is_file():
        print(f"Error: analysis file not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    analysis = json.loads(analysis_path.read_text())

    functional_evals, trigger_evals = generate(
        analysis,
        num_functional=args.num_functional,
        num_trigger=args.num_trigger,
    )

    # If skill-path is given, write into its evals/ directory
    if args.skill_path:
        evals_dir = Path(args.skill_path) / "evals"
        evals_dir.mkdir(parents=True, exist_ok=True)
        func_path = evals_dir / Path(args.output_functional).name
        trig_path = evals_dir / Path(args.output_trigger).name
    else:
        func_path = Path(args.output_functional)
        trig_path = Path(args.output_trigger)

    func_path.parent.mkdir(parents=True, exist_ok=True)
    trig_path.parent.mkdir(parents=True, exist_ok=True)

    func_path.write_text(json.dumps(functional_evals, indent=2, ensure_ascii=False) + "\n")
    trig_path.write_text(json.dumps(trigger_evals, indent=2, ensure_ascii=False) + "\n")

    print(f"Functional evals ({len(functional_evals['test_cases'])} cases) -> {func_path}")
    print(f"Trigger evals ({len(trigger_evals['trigger_queries'])} queries) -> {trig_path}")


if __name__ == "__main__":
    main()
