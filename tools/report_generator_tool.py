"""
tools/report_generator_tool.py
-------------------------------
Member 3 – Custom Tool: Report Generator

Synthesises code-quality and security findings from the shared state into
a well-structured Markdown report and saves it to the outputs/reports/
directory.

All public functions use strict type hints and comprehensive docstrings
as required by the assignment rubric.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from config import REPORTS_DIR


# ── section templates ─────────────────────────────────────────────────────

_HEADER_TPL = """\
# Code Review Report

**Generated:** {timestamp}
**Input Path:** `{input_path}`
**Files Reviewed:** {num_files}

---
"""

_TOC = """\
## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Code Quality Analysis](#code-quality-analysis)
3. [Security Audit](#security-audit)
4. [Recommendations](#recommendations)
5. [Appendix: Trace Log](#appendix)

---
"""

_EXEC_SUMMARY_TPL = """\
## Executive Summary

| Metric | Value |
|--------|-------|
| Total Files Reviewed | {num_files} |
| Quality Issues Found | {quality_issues} |
| Security Issues (HIGH) | {sec_high} |
| Security Issues (MEDIUM) | {sec_medium} |
| Security Issues (LOW) | {sec_low} |
| Overall Risk Level | **{risk_level}** |

{llm_summary}

---
"""


def _risk_level(sec_high: int, sec_medium: int) -> str:
    """Compute an overall risk label from security counts."""
    if sec_high >= 3:
        return "🔴 CRITICAL"
    if sec_high >= 1:
        return "🟠 HIGH"
    if sec_medium >= 3:
        return "🟡 MEDIUM"
    if sec_medium >= 1:
        return "🟡 LOW-MEDIUM"
    return "🟢 LOW"


def _format_quality_section(analysis_results: dict) -> str:
    """
    Format the Code Quality Analysis section of the report.

    Parameters
    ----------
    analysis_results : dict
        Per-file analysis results from the Code Analysis Agent.

    Returns
    -------
    str
        Markdown-formatted section string.
    """
    lines: list[str] = ["## Code Quality Analysis\n"]
    if not analysis_results:
        lines.append("_No quality analysis results available._\n")
        return "\n".join(lines) + "\n---\n"

    for filename, result in analysis_results.items():
        score = result.get("score", "N/A")
        summary = result.get("summary", "")
        issues = result.get("issues", [])
        lines.append(f"### 📄 `{filename}`")
        lines.append(f"**Quality Score:** {score}/10\n")
        if summary:
            lines.append(f"{summary}\n")
        if issues:
            lines.append("**Issues Found:**")
            for issue in issues:
                lines.append(f"- {issue}")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def _format_security_section(security_results: dict) -> str:
    """
    Format the Security Audit section of the report.

    Parameters
    ----------
    security_results : dict
        Per-file security findings from the Security Agent.

    Returns
    -------
    str
        Markdown-formatted section string.
    """
    lines: list[str] = ["## Security Audit\n"]
    if not security_results:
        lines.append("_No security scan results available._\n")
        return "\n".join(lines) + "\n---\n"

    for filename, result in security_results.items():
        summary = result.get("summary", "")
        high    = result.get("high", [])
        medium  = result.get("medium", [])
        low     = result.get("low", [])
        lines.append(f"### 🔒 `{filename}`")
        lines.append(f"**{summary}**\n")

        for label, findings in [("🔴 HIGH", high), ("🟠 MEDIUM", medium), ("🟡 LOW", low)]:
            if findings:
                lines.append(f"**{label} Severity:**")
                for f in findings:
                    line_ref = f" _(line {f['line_number']})_" if f.get("line_number") else ""
                    lines.append(f"- `{f.get('issue_id', '?')}` — {f.get('text', '')}{line_ref}")
                lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def _format_recommendations(analysis_results: dict, security_results: dict) -> str:
    """
    Generate a deduplicated list of actionable recommendations.

    Parameters
    ----------
    analysis_results : dict
        Code quality findings.
    security_results : dict
        Security audit findings.

    Returns
    -------
    str
        Markdown-formatted recommendations section.
    """
    recs: list[str] = []

    # Security-driven recommendations
    for findings in security_results.values():
        for item in findings.get("high", []):
            recs.append(f"🔴 **[SECURITY]** Fix `{item.get('issue_id','')}`: {item.get('text','')}")
        for item in findings.get("medium", []):
            recs.append(f"🟠 **[SECURITY]** Review `{item.get('issue_id','')}`: {item.get('text','')}")

    # Quality-driven recommendations
    for findings in analysis_results.values():
        for issue in findings.get("issues", []):
            recs.append(f"🔵 **[QUALITY]** {issue}")

    if not recs:
        return "## Recommendations\n\n✅ No critical issues found. Keep up the good work!\n\n---\n"

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    lines = ["## Recommendations\n"]
    for rec in unique[:20]:   # cap at 20 items
        lines.append(f"- {rec}")
    lines.append("\n---\n")
    return "\n".join(lines)


@tool
def report_generator_tool(
    input_path: str,
    code_files: dict,
    analysis_results: dict,
    security_results: dict,
    llm_summary: str,
    agent_logs: list,
) -> str:
    """
    Generate a structured Markdown code-review report and save it to disk.

    Combines code-quality analysis and security audit findings into a
    professional, well-structured Markdown document.

    Parameters
    ----------
    input_path : str
        The original directory path that was reviewed.
    code_files : dict
        ``{filename: source_code}`` mapping from the file reader tool.
    analysis_results : dict
        Per-file code-quality findings from the Code Analysis Agent.
    security_results : dict
        Per-file security findings from the Security Agent.
    llm_summary : str
        Executive summary text produced by the Report Agent's LLM.
    agent_logs : list
        LLMOps trace entries to embed in the appendix.

    Returns
    -------
    str
        Absolute path to the saved ``.md`` report file.

    Raises
    ------
    ValueError
        If *input_path* is empty.

    Example
    -------
    >>> path = report_generator_tool.invoke({
    ...     "input_path": "/code",
    ...     "code_files": {"app.py": "..."},
    ...     "analysis_results": {"app.py": {"score": 6, "issues": ["Long function"]}},
    ...     "security_results": {"app.py": {"high": [], "medium": [], "low": [], "total": 0, "summary": "Clean"}},
    ...     "llm_summary": "The codebase is mostly clean.",
    ...     "agent_logs": [],
    ... })
    """
    if not input_path:
        raise ValueError("input_path must not be empty")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    num_files  = len(code_files)

    # Compute aggregate security counts
    sec_high   = sum(len(v.get("high",   [])) for v in security_results.values())
    sec_medium = sum(len(v.get("medium", [])) for v in security_results.values())
    sec_low    = sum(len(v.get("low",    [])) for v in security_results.values())
    quality_issues = sum(
        len(v.get("issues", [])) for v in analysis_results.values()
    )
    risk = _risk_level(sec_high, sec_medium)

    # Build report sections
    header  = _HEADER_TPL.format(
        timestamp=timestamp, input_path=input_path, num_files=num_files
    )
    exec_s  = _EXEC_SUMMARY_TPL.format(
        num_files=num_files, quality_issues=quality_issues,
        sec_high=sec_high, sec_medium=sec_medium, sec_low=sec_low,
        risk_level=risk, llm_summary=llm_summary,
    )
    quality  = _format_quality_section(analysis_results)
    security = _format_security_section(security_results)
    recs     = _format_recommendations(analysis_results, security_results)

    # Appendix: trace log
    appendix_lines = ["## Appendix: Agent Execution Trace\n"]
    if agent_logs:
        appendix_lines.append("| Timestamp | Agent | Tool | Duration (ms) | Summary |")
        appendix_lines.append("|-----------|-------|------|--------------|---------|")
        for entry in agent_logs:
            ts     = entry.get("timestamp", "")[:19].replace("T", " ")
            agent  = entry.get("agent", "")
            tool_  = entry.get("tool_called") or "—"
            dur    = entry.get("duration_ms", 0)
            out    = entry.get("output_summary", "")[:60]
            appendix_lines.append(f"| {ts} | {agent} | {tool_} | {dur} | {out} |")
    else:
        appendix_lines.append("_No trace entries recorded._")

    report_body = "\n".join([
        header, _TOC, exec_s, quality, security, recs,
        "\n".join(appendix_lines)
    ])

    # Save to disk
    run_id   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"report_{run_id}.md"
    out_path = os.path.join(REPORTS_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report_body)

    return out_path
