"""
agents/report_agent.py
-----------------------
Member 3 – Report Generator Agent

Synthesises all findings from the SharedState into a professional,
actionable code-review report.

Responsibilities:
  1. Ask the Ollama LLM to write an executive summary from the raw findings.
  2. Call the report_generator_tool to produce the full Markdown document.
  3. Print the report path and update SharedState.

Persona / System Prompt
-----------------------
You are a Senior Technical Writer and Engineering Lead.  Your job is to
write a clear, concise executive summary for a code-review report.  You
synthesise input from code-quality and security specialists, highlight the
most critical issues, and recommend a clear remediation priority.  You write
for a developer audience — be specific, avoid filler phrases, and never
repeat the same point twice.
"""

from __future__ import annotations

import json

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from state import SharedState
from logger.trace_logger import TraceLogger
from tools.report_generator_tool import report_generator_tool

# ── System prompt ─────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a Senior Technical Writer and Engineering Lead writing an executive
summary for an automated code-review report.

Given a JSON summary of:
  - code quality findings (per file: score, issues list)
  - security findings (per file: HIGH/MEDIUM/LOW counts, scanner summary)

Write a clear 3-5 sentence executive summary that:
1. States the overall health of the codebase (good / needs improvement / critical).
2. Calls out the most severe security issue (if any).
3. Identifies the most important quality improvement needed.
4. Recommends the single highest-priority action the team should take.

Write in present tense. Be specific. Do NOT use phrases like "it appears"
or "it seems". Do NOT invent findings not present in the data.
"""

_HUMAN_PROMPT = """\
Quality findings summary:
{quality_summary}

Security findings summary:
{security_summary}

Write the executive summary now.
"""


def _build_quality_summary(analysis_results: dict) -> str:
    """Produce a compact JSON-like summary of quality findings for the LLM."""
    summary = {}
    for fname, result in analysis_results.items():
        summary[fname] = {
            "score": result.get("score", "?"),
            "num_issues": len(result.get("issues", [])),
            "top_issues": result.get("issues", [])[:3],
        }
    return json.dumps(summary, indent=2)


def _build_security_summary(security_results: dict) -> str:
    """Produce a compact JSON-like summary of security findings for the LLM."""
    summary = {}
    for fname, result in security_results.items():
        summary[fname] = {
            "total": result.get("total", 0),
            "high_count": len(result.get("high", [])),
            "medium_count": len(result.get("medium", [])),
            "scanner_summary": result.get("summary", ""),
        }
    return json.dumps(summary, indent=2)


def run_report_generator(state: SharedState, logger: TraceLogger) -> SharedState:
    """
    Execute the Report Generator Agent node.

    Calls the Ollama LLM to write an executive summary, then invokes the
    report_generator_tool to assemble and save the full Markdown report.

    Parameters
    ----------
    state : SharedState
        Current pipeline state (analysis_results + security_results must
        be populated).
    logger : TraceLogger
        Shared LLMOps trace logger.

    Returns
    -------
    SharedState
        Updated state with ``report_path`` set and ``status`` = ``"done"``.
    """
    agent_name        = "ReportAgent"
    analysis_results  = state.get("analysis_results", {})
    security_results  = state.get("security_results", {})
    agent_logs        = state.get("agent_logs", [])

    print(f"\n{'='*60}")
    print(f"🤖 REPORT AGENT — generating final report")
    print(f"{'='*60}")

    # ── Stage 1: LLM executive summary ───────────────────────────────────
    t_llm = logger.start_timer()
    quality_summary  = _build_quality_summary(analysis_results)
    security_summary = _build_security_summary(security_results)

    try:
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.2,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", _HUMAN_PROMPT),
        ])
        chain = prompt | llm
        exec_summary: str = chain.invoke({
            "quality_summary":  quality_summary,
            "security_summary": security_summary,
        })
    except Exception as exc:
        exec_summary = (
            f"[Executive summary unavailable — LLM error: {exc}]\n"
            "Please review the detailed sections below for findings."
        )

    llm_ms = logger.stop_timer(t_llm)
    logger.log(
        agent_name, None,
        "Generating executive summary",
        exec_summary.strip()[:120],
        llm_ms, OLLAMA_MODEL,
    )

    # ── Stage 2: Generate report via custom tool ──────────────────────────
    t_tool = logger.start_timer()
    try:
        report_path: str = report_generator_tool.invoke({
            "input_path":        state["input_path"],
            "code_files":        state.get("code_files", {}),
            "analysis_results":  analysis_results,
            "security_results":  security_results,
            "llm_summary":       exec_summary.strip(),
            "agent_logs":        logger.get_entries(),
        })
    except Exception as exc:
        state["error"]  = f"report_generator_tool failed: {exc}"
        state["status"] = "error"
        logger.log(agent_name, "report_generator_tool",
                   "Generating report", state["error"],
                   logger.stop_timer(t_tool))
        state["agent_logs"] = logger.get_entries()
        return state

    tool_ms = logger.stop_timer(t_tool)
    logger.log(
        agent_name, "report_generator_tool",
        "Assembling Markdown report",
        f"Report saved to {report_path}",
        tool_ms, OLLAMA_MODEL,
    )

    state["report_path"] = report_path
    state["status"]      = "done"
    state["agent_logs"]  = logger.get_entries()

    print(f"\n✅ Report saved → {report_path}\n")
    return state
