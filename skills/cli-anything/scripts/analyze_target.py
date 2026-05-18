#!/usr/bin/env python3
from __future__ import annotations

"""SkillAnything Phase 1 -- Auto-detect and analyze any target.

Accepts a target (name, URL, or file path), determines what it is, extracts
its capabilities, and writes a structured analysis.json that downstream
pipeline scripts consume.

Usage:
    python analyze_target.py --target <name|url|path> [--target-type <type>] \
        [--output analysis.json] [--verbose]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Target-type detection
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _is_url(target: str) -> bool:
    return bool(_URL_RE.match(target))


def _detect_target_type(target: str, verbose: bool = False) -> str:
    """Return one of: api, cli, library, workflow, service, file, unknown."""
    if _is_url(target):
        if verbose:
            print(f"[detect] Target looks like a URL: {target}")
        return _classify_url(target, verbose)

    if shutil.which(target):
        if verbose:
            print(f"[detect] Found executable in PATH: {target}")
        return "cli"

    if os.path.exists(target):
        if verbose:
            print(f"[detect] Target is an existing file/dir: {target}")
        return _classify_path(target, verbose)

    if verbose:
        print(f"[detect] Could not auto-detect target type for: {target}")
    return "unknown"


def _classify_url(url: str, verbose: bool = False) -> str:
    """Fetch a URL and decide whether it is an API (OpenAPI/Swagger) or generic service."""
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "SkillAnything/1.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read(64 * 1024).decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        if verbose:
            print(f"[detect] URL fetch failed: {exc}")
        return "service"

    openapi_signals = ["openapi", "swagger", '"paths"', '"info"', "operationId"]
    hits = sum(1 for s in openapi_signals if s.lower() in body.lower())
    if hits >= 2 or "application/json" in content_type and hits >= 1:
        if verbose:
            print(f"[detect] URL appears to be an OpenAPI/Swagger spec ({hits} signals)")
        return "api"
    return "service"


def _classify_path(path: str, verbose: bool = False) -> str:
    """Read a local file/dir and guess its category."""
    p = Path(path)
    if p.is_dir():
        return "library"
    try:
        text = p.read_text(errors="replace")[:32_000]
    except OSError:
        return "unknown"

    if any(kw in text.lower() for kw in ["openapi", "swagger", "operationid"]):
        return "api"
    if any(kw in text.lower() for kw in ["import ", "def ", "class ", "function "]):
        return "library"
    if any(kw in text.lower() for kw in ["step ", "workflow", "pipeline", "stage"]):
        return "workflow"
    return "file"


# ---------------------------------------------------------------------------
# Analyzers -- one per target type
# ---------------------------------------------------------------------------

def _analyze_cli(target: str, verbose: bool = False) -> dict:
    """Run ``<tool> --help`` and parse the output."""
    raw_help = ""
    for flag in ("--help", "-h", "help"):
        try:
            result = subprocess.run(
                [target, flag],
                capture_output=True,
                text=True,
                timeout=15,
            )
            raw_help = result.stdout or result.stderr
            if raw_help.strip():
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    if not raw_help.strip():
        return {
            "capabilities": [],
            "inputs": [],
            "outputs": [],
            "dependencies": [],
            "error_patterns": [],
            "raw_help": "(no help output captured)",
        }

    capabilities = _parse_cli_capabilities(raw_help)
    inputs = _parse_cli_inputs(raw_help)

    return {
        "capabilities": capabilities,
        "inputs": inputs,
        "outputs": ["stdout", "stderr"],
        "dependencies": [target],
        "error_patterns": _extract_error_patterns(raw_help),
        "raw_help": raw_help[:16_000],
    }


def _parse_cli_capabilities(help_text: str) -> list:
    """Extract subcommands / high-level capabilities from help text."""
    caps: list[dict] = []

    # Look for "commands:" or "subcommands:" sections
    section_re = re.compile(
        r"(?:commands|subcommands|available commands)[:\s]*\n((?:[ \t]+\S.*\n?)+)",
        re.IGNORECASE,
    )
    m = section_re.search(help_text)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            parts = re.split(r"\s{2,}", line, maxsplit=1)
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            if name and not name.startswith("-"):
                caps.append({"name": name, "description": desc, "type": "subcommand"})

    # If nothing found, describe the tool as a single capability
    if not caps:
        first_line = help_text.strip().splitlines()[0] if help_text.strip() else ""
        caps.append({
            "name": "main",
            "description": first_line[:200],
            "type": "primary",
        })

    return caps


def _parse_cli_inputs(help_text: str) -> list:
    """Extract flags / options from help text."""
    inputs: list[dict] = []
    flag_re = re.compile(r"^\s*(--?\S+)(?:\s+(\S+))?\s{2,}(.+)", re.MULTILINE)
    for m in flag_re.finditer(help_text):
        inputs.append({
            "flag": m.group(1),
            "metavar": m.group(2) or None,
            "description": m.group(3).strip(),
        })
    return inputs


def _extract_error_patterns(text: str) -> list:
    """Pull out common error-related phrases."""
    patterns = []
    for line in text.splitlines():
        low = line.lower().strip()
        if any(kw in low for kw in ("error", "fail", "invalid", "not found", "permission denied")):
            patterns.append(line.strip()[:200])
    return patterns[:10]


def _analyze_api(target: str, verbose: bool = False) -> dict:
    """Fetch an API spec (URL or file) and extract capabilities."""
    body = ""
    if _is_url(target):
        try:
            req = urllib.request.Request(target, method="GET")
            req.add_header("User-Agent", "SkillAnything/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read(256 * 1024).decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError) as exc:
            if verbose:
                print(f"[api] Fetch failed: {exc}")
    elif os.path.isfile(target):
        body = Path(target).read_text(errors="replace")[:256_000]

    capabilities = []
    endpoints: list[dict] = []
    try:
        spec = json.loads(body)
        info = spec.get("info", {})
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, detail in methods.items():
                if method.startswith("x-") or method == "parameters":
                    continue
                summary = ""
                if isinstance(detail, dict):
                    summary = detail.get("summary", detail.get("description", ""))[:120]
                endpoints.append({"path": path, "method": method.upper(), "summary": summary})
                capabilities.append({
                    "name": f"{method.upper()} {path}",
                    "description": summary,
                    "type": "endpoint",
                })
    except (json.JSONDecodeError, AttributeError):
        if verbose:
            print("[api] Response is not valid JSON; treating as raw docs.")
        capabilities.append({
            "name": "api",
            "description": body[:300].strip(),
            "type": "raw_docs",
        })

    return {
        "capabilities": capabilities,
        "inputs": endpoints,
        "outputs": ["json_response"],
        "dependencies": [],
        "error_patterns": [],
        "raw_docs": body[:16_000],
    }


def _analyze_file(target: str, verbose: bool = False) -> dict:
    """Read a local file and extract whatever information we can."""
    p = Path(target)
    try:
        text = p.read_text(errors="replace")[:64_000]
    except OSError as exc:
        return {"error": str(exc)}

    return {
        "capabilities": [{"name": p.stem, "description": text[:300].strip(), "type": "file_content"}],
        "inputs": [{"path": str(p)}],
        "outputs": [],
        "dependencies": [],
        "error_patterns": [],
        "raw_docs": text[:16_000],
    }


def _analyze_library(target: str, verbose: bool = False) -> dict:
    """Analyse a library directory or source file."""
    p = Path(target)
    files = list(p.rglob("*.py"))[:50] if p.is_dir() else [p]
    capabilities = []
    for f in files:
        try:
            src = f.read_text(errors="replace")[:16_000]
        except OSError:
            continue
        for m in re.finditer(r"^(?:def|class)\s+(\w+)", src, re.MULTILINE):
            capabilities.append({"name": m.group(1), "description": "", "type": "symbol"})

    return {
        "capabilities": capabilities[:100],
        "inputs": [str(f) for f in files],
        "outputs": [],
        "dependencies": [],
        "error_patterns": [],
        "raw_docs": "",
    }


_ANALYZERS = {
    "cli": _analyze_cli,
    "api": _analyze_api,
    "service": _analyze_api,
    "file": _analyze_file,
    "library": _analyze_library,
    "workflow": _analyze_file,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(target: str, target_type: str | None = None, verbose: bool = False) -> dict:
    """Run full analysis and return a dict suitable for writing as JSON."""
    detected_type = target_type or _detect_target_type(target, verbose)
    confidence = 0.9 if target_type else 0.7

    if detected_type == "unknown":
        confidence = 0.3
        print(
            f"Warning: Could not auto-detect target type for '{target}'.\n"
            "Consider specifying --target-type explicitly.",
            file=sys.stderr,
        )

    analyzer = _ANALYZERS.get(detected_type, _analyze_file)
    if verbose:
        print(f"[analyze] Using analyzer for type={detected_type}")
    details = analyzer(target, verbose)

    return {
        "target_name": Path(target).stem if os.path.exists(target) else target,
        "target_type": detected_type,
        "confidence": confidence,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        **details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-detect and analyze any target for SkillAnything.",
    )
    parser.add_argument("--target", required=True, help="Name, URL, or file path of the target.")
    parser.add_argument(
        "--target-type",
        choices=["api", "cli", "library", "workflow", "service"],
        default=None,
        help="Override auto-detection with an explicit type.",
    )
    parser.add_argument("--output", default="analysis.json", help="Output JSON path (default: analysis.json).")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostic messages.")
    args = parser.parse_args()

    result = analyze(args.target, args.target_type, args.verbose)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Analysis written to {out_path}")
    if args.verbose:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
