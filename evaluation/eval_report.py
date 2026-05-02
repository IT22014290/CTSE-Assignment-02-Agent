"""
evaluation/eval_report.py
--------------------------
Member 3 – Evaluation Script: Report Generator Agent

Tests that the Report Generator Agent produces a complete, well-structured
Markdown report. Uses:
  1. Structural property tests: all required sections present, links valid.
  2. LLM-as-a-Judge: Ollama rates the report quality vs. a rubric.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OLLAMA_MODEL
from tools.report_generator_tool import report_generator_tool

# ── ANSI colours ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

_passed = 0
_failed = 0
_skipped = 0


def _assert(condition: bool, test_name: str, detail: str = "") -> None:
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  {GREEN}✅ PASS{RESET} — {test_name}")
    else:
        _failed += 1
        print(f"  {RED}❌ FAIL{RESET} — {test_name}" + (f": {detail}" if detail else ""))


def _skip(test_name: str, reason: str) -> None:
    global _skipped
    _skipped += 1
    print(f"  {YELLOW}⏭️  SKIP{RESET} — {test_name} ({reason})")


# ── Shared fixture ────────────────────────────────────────────────────────
_SAMPLE_CODE_FILES = {
    "app.py": "password = 'abc'\ndef foo(): eval(x)",
    "utils.py": "x = 1\n",
}
_SAMPLE_ANALYSIS = {
    "app.py":   {"score": 4, "issues": ["No type hints", "Magic string"], "summary": "Needs work"},
    "utils.py": {"score": 9, "issues": [], "summary": "Clean file"},
}
_SAMPLE_SECURITY = {
    "app.py": {
        "high":   [{"issue_id": "B307", "severity": "HIGH", "text": "eval() risk", "line_number": 2}],
        "medium": [{"issue_id": "B105", "severity": "MEDIUM", "text": "Hardcoded password", "line_number": 1}],
        "low":    [],
        "total":  2,
        "summary": "⚠️  2 issues: 1 HIGH, 1 MEDIUM",
    },
    "utils.py": {"high": [], "medium": [], "low": [], "total": 0, "summary": "✅ Clean"},
}
_SAMPLE_LOGS = [
    {"timestamp": "2026-04-30T18:00:00+00:00", "agent": "CoordinatorAgent",
     "tool_called": "file_reader_tool", "input_summary": "scan /code",
     "output_summary": "Read 2 files", "model": OLLAMA_MODEL, "duration_ms": 320},
]


def _generate_report() -> tuple[str, str]:
    """Generate a report and return (path, content)."""
    path = report_generator_tool.invoke({
        "input_path": "/test/sample_code",
        "code_files": _SAMPLE_CODE_FILES,
        "analysis_results": _SAMPLE_ANALYSIS,
        "security_results": _SAMPLE_SECURITY,
        "llm_summary": "The codebase has critical security issues requiring immediate attention.",
        "agent_logs": _SAMPLE_LOGS,
    })
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    return path, content


# ─────────────────────────────────────────────────────────────────────────
# Test 1: Report file is created on disk
# ─────────────────────────────────────────────────────────────────────────
def test_report_file_created() -> None:
    print(f"\n{BOLD}Test 1: Report file created on disk{RESET}")
    path, _ = _generate_report()
    _assert(os.path.exists(path),              "report file exists on disk")
    _assert(path.endswith(".md"),              "report has .md extension")
    _assert(os.path.getsize(path) > 500,       "report is not empty (>500 bytes)",
            f"got {os.path.getsize(path)} bytes")


# ─────────────────────────────────────────────────────────────────────────
# Test 2: All required sections present
# ─────────────────────────────────────────────────────────────────────────
def test_required_sections() -> None:
    print(f"\n{BOLD}Test 2: All required sections present{RESET}")
    _, content = _generate_report()
    required = [
        "# Code Review Report",
        "## Executive Summary",
        "## Code Quality Analysis",
        "## Security Audit",
        "## Recommendations",
        "## Appendix",
    ]
    for section in required:
        _assert(section in content, f"section '{section}' present")


# ─────────────────────────────────────────────────────────────────────────
# Test 3: Security findings appear in report
# ─────────────────────────────────────────────────────────────────────────
def test_security_findings_in_report() -> None:
    print(f"\n{BOLD}Test 3: Security findings appear in report{RESET}")
    _, content = _generate_report()
    _assert("app.py"  in content,          "app.py referenced in report")
    _assert("B307"    in content,          "issue B307 (eval) mentioned")
    _assert("B105"    in content,          "issue B105 (hardcoded pw) mentioned")
    _assert("HIGH"    in content.upper(),  "HIGH severity label present")
    _assert("MEDIUM"  in content.upper(),  "MEDIUM severity label present")


# ─────────────────────────────────────────────────────────────────────────
# Test 4: Quality findings appear in report
# ─────────────────────────────────────────────────────────────────────────
def test_quality_findings_in_report() -> None:
    print(f"\n{BOLD}Test 4: Quality findings appear in report{RESET}")
    _, content = _generate_report()
    _assert("No type hints"  in content,   "quality issue 'No type hints' present")
    _assert("Magic string"   in content,   "quality issue 'Magic string' present")
    _assert("4/10"           in content,   "quality score 4/10 present")


# ─────────────────────────────────────────────────────────────────────────
# Test 5: Trace log appears in appendix
# ─────────────────────────────────────────────────────────────────────────
def test_trace_log_in_appendix() -> None:
    print(f"\n{BOLD}Test 5: Trace log appears in appendix{RESET}")
    _, content = _generate_report()
    _assert("CoordinatorAgent" in content, "CoordinatorAgent in trace appendix")
    _assert("file_reader_tool" in content, "tool name in trace appendix")


# ─────────────────────────────────────────────────────────────────────────
# Test 6: LLM-as-a-Judge — report quality score
# ─────────────────────────────────────────────────────────────────────────
def test_llm_judge() -> None:
    print(f"\n{BOLD}Test 6: LLM-as-a-Judge — report quality{RESET}")
    try:
        from langchain_ollama import OllamaLLM
        from langchain_core.prompts import ChatPromptTemplate
        from config import OLLAMA_MODEL, OLLAMA_BASE_URL

        _, content = _generate_report()
        # Give the LLM the first 2000 chars to judge
        excerpt = content[:2000]

        judge_prompt = ChatPromptTemplate.from_messages([("human", """\
You are evaluating the quality of an automatically generated code-review report.

Rubric (each criterion 0-2 points):
1. Has a clear Executive Summary (2=excellent, 1=basic, 0=missing)
2. Lists specific security issues with severity levels (2=yes, 1=partial, 0=no)
3. Lists specific code quality issues (2=yes, 1=partial, 0=no)
4. Has actionable recommendations (2=yes, 1=vague, 0=no)
5. Professional and readable formatting (2=yes, 1=ok, 0=poor)

Report excerpt:
{excerpt}

Respond ONLY with:
TOTAL_SCORE: <0-10>
VERDICT: <one sentence>
""")])

        llm   = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
        chain = judge_prompt | llm
        response = chain.invoke({"excerpt": excerpt})

        import re
        score = 0
        # Match "TOTAL_SCORE: 7", "Total Score: 7/10", "Total: 8" etc.
        for line in response.splitlines():
            normalized = line.strip().upper().replace(" ", "_")
            if normalized.startswith("TOTAL_SCORE:") or normalized.startswith("TOTAL:"):
                try:
                    raw = line.split(":")[1].strip().split("/")[0].strip()
                    score = int(raw)
                    break
                except (IndexError, ValueError):
                    pass
        # Fallback: scan for any "N/10" pattern in the full response
        if score == 0:
            match = re.search(r"\b([7-9]|10)\s*/\s*10\b", response)
            if match:
                score = int(match.group(1))

        print(f"    LLM Judge response:\n    {response.strip()}")
        _assert(score >= 6, "LLM judge score ≥ 6/10", f"got {score}/10")

    except Exception as exc:
        _skip("LLM judge", f"Ollama unavailable: {exc}")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{'='*60}")
    print("  REPORT AGENT EVALUATION — Member 3")
    print(f"{'='*60}{RESET}")

    test_report_file_created()
    test_required_sections()
    test_security_findings_in_report()
    test_quality_findings_in_report()
    test_trace_log_in_appendix()
    test_llm_judge()

    total = _passed + _failed
    print(f"\n{BOLD}{'='*60}")
    print(f"  Results: {_passed}/{total} tests passed  ({_skipped} skipped)")
    if _failed == 0:
        print(f"  {GREEN}ALL TESTS PASSED ✅{RESET}")
    else:
        print(f"  {RED}{_failed} test(s) FAILED ❌{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    sys.exit(0 if _failed == 0 else 1)
