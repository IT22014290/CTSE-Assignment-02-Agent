"""
agents/security_agent.py
-------------------------
Member 2 – Security Audit Agent

Performs a two-stage security audit:
  1. Static analysis via the security_scanner_tool (bandit / pattern scan).
  2. LLM-based interpretation: the agent reasons about the raw findings,
     explains the risks in plain English, and suggests concrete fixes.

Persona / System Prompt
-----------------------
You are a Cybersecurity Expert specialising in Python application security.
You analyse static-analysis scan results and explain each vulnerability
clearly to a developer audience.  You prioritise findings by severity,
explain the real-world risk, and propose specific code-level fixes.
You NEVER fabricate vulnerabilities not present in the scan data.
"""

from __future__ import annotations

import json

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from state import SharedState
from logger.trace_logger import TraceLogger
from tools.security_scanner_tool import security_scanner_tool

# ── System prompt ─────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a Cybersecurity Expert specialising in Python application security.
Given the output of a static security scanner for a Python file, you must:
1. Confirm the severity of each finding.
2. Explain the real-world risk in 1-2 sentences per issue.
3. Suggest a specific code-level fix for each HIGH/MEDIUM issue.
4. End with a one-sentence overall verdict.

IMPORTANT: Only reference issues present in the scan data. Do NOT invent findings.
Keep your response concise and developer-friendly.
"""

_HUMAN_PROMPT = """\
File: {filename}
Scanner findings (JSON):
{scan_json}

Provide your security interpretation and recommended fixes.
"""


def run_security_audit(state: SharedState, logger: TraceLogger) -> SharedState:
    """
    Execute the Security Audit Agent node.

    Calls the security_scanner_tool on all code files, then asks the LLM
    to interpret and explain each finding.  Stores enriched results in
    ``state["security_results"]``.

    Parameters
    ----------
    state : SharedState
        Current pipeline state (must have ``code_files`` populated).
    logger : TraceLogger
        Shared LLMOps trace logger.

    Returns
    -------
    SharedState
        Updated state with ``security_results`` populated and
        ``status`` set to ``"reporting"``.
    """
    agent_name = "SecurityAgent"
    code_files = state.get("code_files", {})

    print(f"\n{'='*60}")
    print(f"🤖 SECURITY AGENT — auditing {len(code_files)} file(s)")
    print(f"{'='*60}")

    # ── Stage 1: Run the scanner tool ─────────────────────────────────────
    t_tool = logger.start_timer()
    try:
        raw_scan: dict = security_scanner_tool.invoke({"code_files": code_files})
    except Exception as exc:
        state["error"]          = f"security_scanner_tool failed: {exc}"
        state["security_results"] = {}
        state["status"]         = "reporting"   # Continue to report even on error
        logger.log(agent_name, "security_scanner_tool",
                   "Scanning all files", state["error"],
                   logger.stop_timer(t_tool))
        state["agent_logs"] = logger.get_entries()
        return state

    tool_ms = logger.stop_timer(t_tool)
    total_issues = sum(v.get("total", 0) for v in raw_scan.values())
    logger.log(agent_name, "security_scanner_tool",
               f"Scanning {len(code_files)} file(s)",
               f"Found {total_issues} issue(s) across all files",
               tool_ms, OLLAMA_MODEL)

    # ── Stage 2: LLM interpretation per file ─────────────────────────────
    llm = OllamaLLM(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", _HUMAN_PROMPT),
    ])
    chain = prompt | llm

    enriched: dict = {}
    for filename, scan_data in raw_scan.items():
        t0 = logger.start_timer()
        print(f"  🔒 Auditing: {filename} — {scan_data.get('summary', '')}")

        # Enrich with LLM interpretation if there are findings
        llm_interpretation = ""
        if scan_data.get("total", 0) > 0:
            scan_json = json.dumps({
                "high":   scan_data.get("high",   []),
                "medium": scan_data.get("medium", []),
                "low":    scan_data.get("low",    []),
            }, indent=2)

            try:
                llm_interpretation = chain.invoke({
                    "filename": filename,
                    "scan_json": scan_json,
                })
            except Exception as exc:
                llm_interpretation = f"[LLM unavailable: {exc}]"
        else:
            llm_interpretation = "✅ No security issues were detected in this file."

        enriched[filename] = {
            **scan_data,
            "llm_interpretation": llm_interpretation.strip(),
        }

        dur = logger.stop_timer(t0)
        logger.log(
            agent_name, None,
            f"LLM interpreting {filename}",
            llm_interpretation.strip()[:100],
            dur, OLLAMA_MODEL,
        )

    state["security_results"] = enriched
    state["status"]            = "reporting"
    state["agent_logs"]        = logger.get_entries()
    return state
