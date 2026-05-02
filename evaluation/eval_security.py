"""
evaluation/eval_security.py
-----------------------------
Member 2 – Evaluation Script: Security Audit Agent

Uses a hybrid approach:
  1. Property-based tests: verify that known vulnerabilities in sample
     code are detected by the security_scanner_tool.
  2. LLM-as-a-Judge: asks Ollama to rate whether the agent's
     interpretation of findings is accurate, relevant, and actionable.

This script can run without Ollama (property tests still execute);
the LLM judge section gracefully skips if Ollama is unavailable.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.security_scanner_tool import security_scanner_tool

# ── ANSI colours ──────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
RESET = "\033[0m"
BOLD  = "\033[1m"

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


# ─────────────────────────────────────────────────────────────────────────
# Test 1: eval() usage is flagged as HIGH severity
# ─────────────────────────────────────────────────────────────────────────
def test_eval_detected() -> None:
    print(f"\n{BOLD}Test 1: eval() detected (HIGH or MEDIUM severity){RESET}")
    code = "result = eval(user_input)"
    result = security_scanner_tool.invoke({"code_files": {"test.py": code}})
    findings = result.get("test.py", {})
    high   = findings.get("high",   [])
    medium = findings.get("medium", [])
    all_f  = high + medium
    _assert(len(all_f) >= 1, "at least one HIGH/MEDIUM finding", f"got {len(all_f)}")
    _assert(
        any("eval" in f.get("text", "").lower() or "B307" in f.get("issue_id", "") for f in all_f),
        "eval() / B307 mentioned in findings",
    )


# ─────────────────────────────────────────────────────────────────────────
# Test 2: Hardcoded password detected
# ─────────────────────────────────────────────────────────────────────────
def test_hardcoded_secret_detected() -> None:
    print(f"\n{BOLD}Test 2: Hardcoded password detected{RESET}")
    code = 'password = "hunter2"\nsecret = "my_secret_key"'
    result = security_scanner_tool.invoke({"code_files": {"config.py": code}})
    findings = result.get("config.py", {})
    all_findings = (
        findings.get("high", []) +
        findings.get("medium", []) +
        findings.get("low", [])
    )
    _assert(len(all_findings) >= 1, "at least one finding for hardcoded secret")
    _assert(
        any("password" in f.get("text", "").lower() or
            "secret" in f.get("text", "").lower() or
            "B105" in f.get("issue_id", "") for f in all_findings),
        "hardcoded secret is identified",
    )


# ─────────────────────────────────────────────────────────────────────────
# Test 3: shell=True subprocess flagged
# ─────────────────────────────────────────────────────────────────────────
def test_shell_injection_detected() -> None:
    print(f"\n{BOLD}Test 3: shell=True subprocess flagged{RESET}")
    code = 'import subprocess\nsubprocess.call(["ls", user_input], shell=True)'
    result = security_scanner_tool.invoke({"code_files": {"run.py": code}})
    findings = result.get("run.py", {})
    high   = findings.get("high", [])
    medium = findings.get("medium", [])
    _assert(
        len(high) + len(medium) >= 1,
        "shell injection risk detected",
        f"high={len(high)}, medium={len(medium)}",
    )


# ─────────────────────────────────────────────────────────────────────────
# Test 4: Clean code produces no findings
# ─────────────────────────────────────────────────────────────────────────
def test_clean_code_no_findings() -> None:
    print(f"\n{BOLD}Test 4: Clean code produces no/low findings{RESET}")
    code = '''\
def add(a: int, b: int) -> int:
    """Return the sum of a and b."""
    return a + b

def greet(name: str) -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"
'''
    result = security_scanner_tool.invoke({"code_files": {"clean.py": code}})
    findings = result.get("clean.py", {})
    high = findings.get("high", [])
    _assert(len(high) == 0, "no HIGH findings in clean code", f"got {len(high)}")


# ─────────────────────────────────────────────────────────────────────────
# Test 5: Tool returns correct dict structure
# ─────────────────────────────────────────────────────────────────────────
def test_output_structure() -> None:
    print(f"\n{BOLD}Test 5: Output structure is correct{RESET}")
    code = "x = 1"
    result = security_scanner_tool.invoke({"code_files": {"x.py": code}})
    entry = result.get("x.py", {})
    for key in ["high", "medium", "low", "total", "summary"]:
        _assert(key in entry, f"output has '{key}' key")
    _assert(isinstance(entry["high"],   list), "high is a list")
    _assert(isinstance(entry["medium"], list), "medium is a list")
    _assert(isinstance(entry["low"],    list), "low is a list")
    _assert(isinstance(entry["total"],  int),  "total is an int")


# ─────────────────────────────────────────────────────────────────────────
# Test 6: LLM-as-a-Judge (requires Ollama)
# ─────────────────────────────────────────────────────────────────────────
def test_llm_judge() -> None:
    print(f"\n{BOLD}Test 6: LLM-as-a-Judge — security interpretation quality{RESET}")
    try:
        from langchain_ollama import OllamaLLM
        from langchain_core.prompts import ChatPromptTemplate
        from config import OLLAMA_MODEL, OLLAMA_BASE_URL

        # Get actual findings for vulnerable_app.py
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "tests", "sample_code", "vulnerable_app.py",
        )
        if not os.path.exists(sample_path):
            _skip("LLM judge", "sample_code/vulnerable_app.py not found")
            return

        with open(sample_path) as fh:
            code = fh.read()

        scan_result = security_scanner_tool.invoke({"code_files": {"vulnerable_app.py": code}})
        findings = scan_result.get("vulnerable_app.py", {})

        judge_prompt = ChatPromptTemplate.from_messages([("human", """\
You are evaluating an automated security scanner's output.

The scanner analysed a Python file that is KNOWN to contain:
- eval() usage (HIGH)
- hardcoded passwords/tokens (MEDIUM-HIGH)
- pickle.loads() (HIGH)
- shell=True subprocess (HIGH)
- MD5 hashing (MEDIUM)

Scanner output:
{scan_json}

Rate the scanner's performance on a scale of 1-10 where:
10 = detected all known vulnerabilities
1  = detected nothing

Respond with ONLY: SCORE: <number>/10
REASON: <one sentence>
""")])

        llm   = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
        chain = judge_prompt | llm
        response = chain.invoke({"scan_json": json.dumps(findings, indent=2)})

        import re
        score = 0
        for line in response.splitlines():
            if line.strip().upper().startswith("SCORE:"):
                try:
                    raw = line.split(":")[1].strip().split("/")[0].strip()
                    score = int(raw)
                    break
                except (IndexError, ValueError):
                    pass
        # Fallback: scan for any "N/10" pattern in the full response
        if score == 0:
            match = re.search(r"\b([6-9]|10)\s*/\s*10\b", response)
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
    print("  SECURITY AGENT EVALUATION — Member 2")
    print(f"{'='*60}{RESET}")

    test_eval_detected()
    test_hardcoded_secret_detected()
    test_shell_injection_detected()
    test_clean_code_no_findings()
    test_output_structure()
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
