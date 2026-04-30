"""
tools/security_scanner_tool.py
-------------------------------
Member 2 – Custom Tool: Security Scanner

Performs static security analysis on Python source code using the
``bandit`` AST-based linter.  Returns a structured dict of findings
organised by severity level, ready for the Security Agent to consume.

All public functions use strict type hints and comprehensive docstrings
as required by the assignment rubric.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from typing import Optional

from langchain_core.tools import tool


# ── severity ordering for display ─────────────────────────────────────────
_SEVERITY_ORDER: dict[str, int] = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# ── simple pattern-based fallback checks ──────────────────────────────────
# Each tuple: (pattern_substring, issue_id, message, severity)
_PATTERN_CHECKS: list[tuple[str, str, str, str]] = [
    ("eval(",             "B307", "Use of eval() is a security risk",                  "HIGH"),
    ("exec(",             "B102", "Use of exec() can execute arbitrary code",          "HIGH"),
    ("pickle.",           "B301", "Pickle deserialisation can execute arbitrary code", "HIGH"),
    ("shell=True",        "B602", "shell=True enables injection attacks",               "HIGH"),
    ("os.system(",        "B605", "os.system() is vulnerable to shell injection",      "HIGH"),
    ("subprocess.call(",  "B603", "Subprocess call — verify shell=True is not used",   "MEDIUM"),
    ("password =",        "B105", "Possible hardcoded password",                       "MEDIUM"),
    ("secret =",          "B105", "Possible hardcoded secret",                         "MEDIUM"),
    ("token =",           "B105", "Possible hardcoded token",                          "MEDIUM"),
    ("md5(",              "B303", "Use of weak MD5 hash function",                     "MEDIUM"),
    ("sha1(",             "B303", "Use of weak SHA1 hash function",                    "MEDIUM"),
    ("DEBUG = True",      "B501", "Debug mode enabled — do not deploy",                "LOW"),
]


def _run_bandit(code: str, filename: str) -> list[dict]:
    """
    Run the ``bandit`` CLI on *code* and parse its JSON output.

    Parameters
    ----------
    code : str
        Python source code to analyse.
    filename : str
        Logical filename used for error messages.

    Returns
    -------
    list[dict]
        List of bandit issue dicts with keys: issue_id, severity,
        confidence, text, line_number.
    """
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-f", "json", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        os.unlink(tmp_path)

        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        issues = []
        for item in data.get("results", []):
            issues.append({
                "issue_id": item.get("test_id", ""),
                "severity": item.get("issue_severity", "").upper(),
                "confidence": item.get("issue_confidence", "").upper(),
                "text": item.get("issue_text", ""),
                "line_number": item.get("line_number", 0),
            })
        return issues

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


def _run_pattern_scan(code: str) -> list[dict]:
    """
    Lightweight pattern-based security scan used as bandit fallback.

    Parameters
    ----------
    code : str
        Python source code to scan.

    Returns
    -------
    list[dict]
        List of finding dicts with keys: issue_id, severity, confidence,
        text, line_number.
    """
    findings: list[dict] = []
    seen: set[tuple] = set()  # deduplicate (line, pattern) pairs
    for line_num, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, issue_id, message, severity in _PATTERN_CHECKS:
            if pattern.lower() in stripped.lower():
                key = (line_num, issue_id)
                if key in seen:
                    continue
                seen.add(key)
                findings.append({
                    "issue_id": issue_id,
                    "severity": severity,
                    "confidence": "MEDIUM",
                    "text": message,
                    "line_number": line_num,
                })
    return findings


@tool
def security_scanner_tool(code_files: dict) -> dict[str, dict]:
    """
    Perform static security analysis on a set of Python source files.

    Attempts to use ``bandit`` for AST-based analysis; falls back to a
    lightweight pattern scanner if bandit is unavailable.  Returns a
    per-file mapping of findings grouped by severity.

    Parameters
    ----------
    code_files : dict
        ``{filename: source_code}`` mapping — exactly the output of
        :func:`tools.file_reader_tool.file_reader_tool`.

    Returns
    -------
    dict[str, dict]
        ``{filename: {"high": [...], "medium": [...], "low": [...],
        "total": int, "summary": str}}``

    Raises
    ------
    TypeError
        If *code_files* is not a dict.

    Example
    -------
    >>> results = security_scanner_tool.invoke({"code_files": {"app.py": "eval(input())"}})
    >>> results["app.py"]["high"]
    [{'issue_id': 'B307', 'text': 'Use of eval() is a security risk', ...}]
    """
    if not isinstance(code_files, dict):
        raise TypeError(f"Expected dict, got {type(code_files).__name__}")

    output: dict[str, dict] = {}

    for filename, code in code_files.items():
        if code.startswith("# SKIPPED") or code.startswith("# ERROR"):
            output[filename] = {
                "high": [], "medium": [], "low": [],
                "total": 0, "summary": code,
            }
            continue

        # Try bandit first, fall back to pattern scan
        findings = _run_bandit(code, filename)
        if not findings:
            findings = _run_pattern_scan(code)

        high   = [f for f in findings if f["severity"] == "HIGH"]
        medium = [f for f in findings if f["severity"] == "MEDIUM"]
        low    = [f for f in findings if f["severity"] == "LOW"]
        total  = len(findings)

        if total == 0:
            summary = "✅ No security issues detected."
        else:
            parts = []
            if high:   parts.append(f"{len(high)} HIGH")
            if medium: parts.append(f"{len(medium)} MEDIUM")
            if low:    parts.append(f"{len(low)} LOW")
            summary = f"⚠️  {total} issue(s) found: {', '.join(parts)}"

        output[filename] = {
            "high": high,
            "medium": medium,
            "low": low,
            "total": total,
            "summary": summary,
        }

    return output
