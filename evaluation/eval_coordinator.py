"""
evaluation/eval_coordinator.py
--------------------------------
Member 1 – Evaluation Script: Coordinator Agent

Tests that the Coordinator Agent correctly:
  1. Validates the input directory and rejects invalid paths.
  2. Populates code_files in SharedState from a real directory.
  3. Sets the correct status transitions.
  4. Produces a trace log entry for each action.
  5. Handles edge cases (empty directory, non-existent path).

Approach: property-based / scenario-based testing (no LLM-as-judge needed
for the coordinator since its outputs are deterministic and verifiable).
"""

from __future__ import annotations

import os
import sys
import tempfile

# Allow importing from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import initial_state
from logger.trace_logger import TraceLogger
from agents.coordinator_agent import run_coordinator


# ── ANSI colours for terminal output ─────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"
BOLD  = "\033[1m"

_passed = 0
_failed = 0


def _assert(condition: bool, test_name: str, detail: str = "") -> None:
    """Print pass/fail for a single assertion."""
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  {GREEN}✅ PASS{RESET} — {test_name}")
    else:
        _failed += 1
        print(f"  {RED}❌ FAIL{RESET} — {test_name}" + (f": {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────
# Test 1: Rejects invalid (non-existent) path
# ─────────────────────────────────────────────────────────────────────────
def test_invalid_path() -> None:
    print(f"\n{BOLD}Test 1: Invalid path rejected{RESET}")
    state  = initial_state("/this/path/does/not/exist_xyz_abc")
    logger = TraceLogger()
    result = run_coordinator(state, logger)
    _assert(result["status"] == "error",       "status set to 'error'")
    _assert(bool(result["error"]),             "error message is non-empty")
    _assert(result["code_files"] == {},        "code_files remains empty")


# ─────────────────────────────────────────────────────────────────────────
# Test 2: Empty directory handled gracefully
# ─────────────────────────────────────────────────────────────────────────
def test_empty_directory() -> None:
    print(f"\n{BOLD}Test 2: Empty directory handled gracefully{RESET}")
    with tempfile.TemporaryDirectory() as tmpdir:
        state  = initial_state(tmpdir)
        logger = TraceLogger()
        result = run_coordinator(state, logger)
        _assert(result["status"] == "error",   "status set to 'error'")
        _assert("No supported files" in result["error"], "error mentions no files found")


# ─────────────────────────────────────────────────────────────────────────
# Test 3: Valid directory with Python files
# ─────────────────────────────────────────────────────────────────────────
def test_valid_directory() -> None:
    print(f"\n{BOLD}Test 3: Valid directory with Python files{RESET}")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two dummy Python files
        for name, content in [
            ("hello.py", "def hello():\n    print('hello')\n"),
            ("utils.py", "x = 1\n"),
        ]:
            with open(os.path.join(tmpdir, name), "w") as fh:
                fh.write(content)

        state  = initial_state(tmpdir)
        logger = TraceLogger()
        result = run_coordinator(state, logger)

        _assert(result["status"] == "analyzing",        "status set to 'analyzing'")
        _assert(len(result["code_files"]) == 2,         "code_files has 2 entries",
                f"got {len(result['code_files'])}")
        _assert("hello.py" in result["code_files"],     "hello.py in code_files")
        _assert("utils.py" in result["code_files"],     "utils.py in code_files")
        _assert(result["error"] == "",                  "no error message")


# ─────────────────────────────────────────────────────────────────────────
# Test 4: File contents are preserved accurately
# ─────────────────────────────────────────────────────────────────────────
def test_file_contents_preserved() -> None:
    print(f"\n{BOLD}Test 4: File contents are preserved{RESET}")
    content = "# Test file\ndef foo():\n    return 42\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.py")
        with open(path, "w") as fh:
            fh.write(content)

        state  = initial_state(tmpdir)
        logger = TraceLogger()
        result = run_coordinator(state, logger)

        stored = result["code_files"].get("test.py", "")
        _assert(stored == content, "file content matches exactly",
                f"expected {repr(content[:30])}, got {repr(stored[:30])}")


# ─────────────────────────────────────────────────────────────────────────
# Test 5: Trace log entries are recorded
# ─────────────────────────────────────────────────────────────────────────
def test_trace_logging() -> None:
    print(f"\n{BOLD}Test 5: Trace log entries recorded{RESET}")
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "app.py"), "w") as fh:
            fh.write("x = 1\n")

        state  = initial_state(tmpdir)
        logger = TraceLogger()
        run_coordinator(state, logger)

        logs = logger.get_entries()
        _assert(len(logs) >= 1,                    "at least 1 log entry")
        _assert(
            any(e["agent"] == "CoordinatorAgent" for e in logs),
            "CoordinatorAgent appears in logs",
        )
        _assert(
            any(e.get("tool_called") == "file_reader_tool" for e in logs),
            "file_reader_tool usage is logged",
        )


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{'='*60}")
    print("  COORDINATOR AGENT EVALUATION — Member 1")
    print(f"{'='*60}{RESET}")

    test_invalid_path()
    test_empty_directory()
    test_valid_directory()
    test_file_contents_preserved()
    test_trace_logging()

    total = _passed + _failed
    print(f"\n{BOLD}{'='*60}")
    print(f"  Results: {_passed}/{total} tests passed")
    if _failed == 0:
        print(f"  {GREEN}ALL TESTS PASSED ✅{RESET}")
    else:
        print(f"  {RED}{_failed} test(s) FAILED ❌{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    sys.exit(0 if _failed == 0 else 1)
