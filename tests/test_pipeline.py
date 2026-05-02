"""
tests/test_pipeline.py
-----------------------
Pytest-compatible test suite for the MAS Code Review Pipeline.

Covers core logic without requiring Ollama to be running:
  - SharedState structure and initialisation
  - file_reader_tool behaviour (valid dir, empty dir, skips non-.py)
  - security_scanner_tool structure and pattern detection
  - report_generator_tool produces a valid Markdown file
  - TraceLogger records entries and saves JSON

Each test is standalone (no external network calls).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

# Allow imports from project root regardless of how pytest is invoked
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from state import initial_state
from logger.trace_logger import TraceLogger
from tools.file_reader_tool import file_reader_tool
from tools.security_scanner_tool import security_scanner_tool
from tools.report_generator_tool import report_generator_tool


# ═══════════════════════════════════════════════════════════════
# State tests
# ═══════════════════════════════════════════════════════════════

def test_initial_state_has_all_keys() -> None:
    state = initial_state("/tmp/test")
    required = ["input_path", "code_files", "analysis_results",
                "security_results", "report_path", "agent_logs", "status", "error"]
    for key in required:
        assert key in state, f"Missing key: {key}"


def test_initial_state_defaults() -> None:
    state = initial_state("/tmp/test")
    assert state["input_path"] == "/tmp/test"
    assert state["status"] == "pending"
    assert state["error"] == ""
    assert state["code_files"] == {}
    assert state["analysis_results"] == {}
    assert state["security_results"] == {}
    assert state["agent_logs"] == []


# ═══════════════════════════════════════════════════════════════
# file_reader_tool tests
# ═══════════════════════════════════════════════════════════════

def test_file_reader_reads_python_files() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        (open(os.path.join(tmpdir, "a.py"), "w")).write("x = 1\n")
        (open(os.path.join(tmpdir, "b.py"), "w")).write("y = 2\n")
        result = file_reader_tool.invoke({"directory_path": tmpdir})
        assert len(result) == 2
        assert "a.py" in result
        assert "b.py" in result


def test_file_reader_skips_non_python_files() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        (open(os.path.join(tmpdir, "notes.txt"),  "w")).write("ignore me\n")
        (open(os.path.join(tmpdir, "script.py"),  "w")).write("pass\n")
        result = file_reader_tool.invoke({"directory_path": tmpdir})
        assert "script.py" in result
        assert "notes.txt" not in result


def test_file_reader_empty_directory_returns_empty_dict() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = file_reader_tool.invoke({"directory_path": tmpdir})
        assert result == {}


def test_file_reader_preserves_content() -> None:
    content = "def hello():\n    return 42\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "fn.py"), "w") as fh:
            fh.write(content)
        result = file_reader_tool.invoke({"directory_path": tmpdir})
        assert result["fn.py"] == content


def test_file_reader_invalid_path_returns_empty_or_raises() -> None:
    try:
        result = file_reader_tool.invoke({"directory_path": "/no/such/path/xyz_abc"})
        assert isinstance(result, dict)
    except Exception:
        pass  # also acceptable — tool may raise on invalid path


# ═══════════════════════════════════════════════════════════════
# security_scanner_tool tests
# ═══════════════════════════════════════════════════════════════

def test_security_scanner_output_structure() -> None:
    result = security_scanner_tool.invoke({"code_files": {"x.py": "x = 1\n"}})
    entry = result["x.py"]
    for key in ["high", "medium", "low", "total", "summary"]:
        assert key in entry
    assert isinstance(entry["high"],   list)
    assert isinstance(entry["medium"], list)
    assert isinstance(entry["low"],    list)
    assert isinstance(entry["total"],  int)


def test_security_scanner_detects_eval() -> None:
    result = security_scanner_tool.invoke({"code_files": {"t.py": "eval(user_input)"}})
    all_findings = result["t.py"]["high"] + result["t.py"]["medium"]
    assert len(all_findings) >= 1


def test_security_scanner_detects_hardcoded_password() -> None:
    code = 'password = "s3cr3t"\n'
    result = security_scanner_tool.invoke({"code_files": {"cfg.py": code}})
    all_f = (result["cfg.py"]["high"] +
             result["cfg.py"]["medium"] +
             result["cfg.py"]["low"])
    assert len(all_f) >= 1


def test_security_scanner_clean_code_no_high_findings() -> None:
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    result = security_scanner_tool.invoke({"code_files": {"clean.py": code}})
    assert result["clean.py"]["high"] == []


def test_security_scanner_wrong_type_raises() -> None:
    with pytest.raises(Exception):  # TypeError from tool or ValidationError from Pydantic
        security_scanner_tool.invoke({"code_files": "not a dict"})


def test_security_scanner_shell_true_flagged() -> None:
    code = "import subprocess\nsubprocess.call(['ls'], shell=True)\n"
    result = security_scanner_tool.invoke({"code_files": {"run.py": code}})
    high = result["run.py"]["high"]
    medium = result["run.py"]["medium"]
    assert len(high) + len(medium) >= 1


# ═══════════════════════════════════════════════════════════════
# report_generator_tool tests
# ═══════════════════════════════════════════════════════════════

_REPORT_CODE   = {"app.py": "password='x'\ndef foo(): eval(x)"}
_REPORT_QUAL   = {"app.py": {"score": 4, "issues": ["No type hints"], "summary": "Needs work"}}
_REPORT_SEC    = {
    "app.py": {
        "high":   [{"issue_id": "B307", "severity": "HIGH", "text": "eval risk", "line_number": 2}],
        "medium": [{"issue_id": "B105", "severity": "MEDIUM", "text": "Hardcoded password", "line_number": 1}],
        "low":    [],
        "total":  2,
        "summary": "2 issues: 1 HIGH, 1 MEDIUM",
    }
}
_REPORT_LOGS   = [
    {"timestamp": "2026-01-01T00:00:00+00:00", "agent": "CoordinatorAgent",
     "tool_called": "file_reader_tool", "input_summary": "scan",
     "output_summary": "Read 1 file", "model": "llama3.2:3b", "duration_ms": 100},
]


def test_report_file_created() -> None:
    path = report_generator_tool.invoke({
        "input_path": "/test",
        "code_files": _REPORT_CODE,
        "analysis_results": _REPORT_QUAL,
        "security_results": _REPORT_SEC,
        "llm_summary": "Critical issues found.",
        "agent_logs": _REPORT_LOGS,
    })
    assert os.path.exists(path)
    assert path.endswith(".md")
    assert os.path.getsize(path) > 200


def test_report_required_sections() -> None:
    path = report_generator_tool.invoke({
        "input_path": "/test",
        "code_files": _REPORT_CODE,
        "analysis_results": _REPORT_QUAL,
        "security_results": _REPORT_SEC,
        "llm_summary": "Critical issues found.",
        "agent_logs": _REPORT_LOGS,
    })
    content = open(path, encoding="utf-8").read()
    for section in ["# Code Review Report", "## Executive Summary",
                    "## Code Quality Analysis", "## Security Audit",
                    "## Recommendations", "## Appendix"]:
        assert section in content, f"Missing section: {section}"


def test_report_contains_findings() -> None:
    path = report_generator_tool.invoke({
        "input_path": "/test",
        "code_files": _REPORT_CODE,
        "analysis_results": _REPORT_QUAL,
        "security_results": _REPORT_SEC,
        "llm_summary": "Critical issues found.",
        "agent_logs": _REPORT_LOGS,
    })
    content = open(path, encoding="utf-8").read()
    assert "B307" in content
    assert "No type hints" in content
    assert "CoordinatorAgent" in content


# ═══════════════════════════════════════════════════════════════
# TraceLogger tests
# ═══════════════════════════════════════════════════════════════

def test_trace_logger_records_entries() -> None:
    logger = TraceLogger()
    t = logger.start_timer()
    logger.log("AgentX", "toolY", "input", "output", logger.stop_timer(t))
    entries = logger.get_entries()
    assert len(entries) == 1
    assert entries[0]["agent"] == "AgentX"
    assert entries[0]["tool_called"] == "toolY"


def test_trace_logger_saves_json(tmp_path) -> None:
    logger = TraceLogger()
    t = logger.start_timer()
    logger.log("TestAgent", None, "in", "out", logger.stop_timer(t))
    path = logger.save()
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert "entries" in data
    assert data["total_entries"] == 1


def test_trace_logger_entry_has_required_keys() -> None:
    logger = TraceLogger()
    t = logger.start_timer()
    entry = logger.log("A", "B", "in", "out", logger.stop_timer(t))
    for key in ["timestamp", "agent", "tool_called", "input_summary",
                "output_summary", "model", "duration_ms"]:
        assert key in entry
