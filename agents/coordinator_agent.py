"""
agents/coordinator_agent.py
----------------------------
Member 1 – Coordinator Agent

The Coordinator is the entry point of the LangGraph pipeline.  Its
responsibilities are:
  1. Validate that the input path exists and contains Python files.
  2. Invoke the file_reader_tool to populate code_files in SharedState.
  3. Set status flags to drive the graph routing.
  4. Log every action via TraceLogger.

Persona / System Prompt
-----------------------
You are the Coordinator of an automated code-review team.  Your job is
to accept a directory path, validate it, read all source files, and
delegate review tasks to the specialist agents.  Be precise, concise, and
never hallucinate file contents.  If validation fails, set the error field
and return immediately.
"""

from __future__ import annotations

import os

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from state import SharedState
from logger.trace_logger import TraceLogger
from tools.file_reader_tool import file_reader_tool, summarise_code_files

# ── System prompt ─────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are the Coordinator Agent of an automated code-review pipeline.
Your responsibilities:
1. Confirm the target directory exists and contains Python source files.
2. Report a concise summary of what was found (number of files, total lines).
3. If no files are found or the path is invalid, clearly state the problem.
4. Do NOT invent or assume file contents — only describe what the tool returns.
Respond in 2-4 sentences. Be precise and factual.
"""

_HUMAN_PROMPT = """\
The file reader tool has scanned the directory '{input_path}'.
Here is what it found:

{file_summary}

Provide a brief coordinator status update confirming the scan is complete
and the analysis agents can proceed.
"""


def run_coordinator(state: SharedState, logger: TraceLogger) -> SharedState:
    """
    Execute the Coordinator Agent node.

    Validates the input directory, reads all source files via the
    file_reader_tool, and populates *state* with the discovered code files.

    Parameters
    ----------
    state : SharedState
        The current pipeline state (mutated in place and returned).
    logger : TraceLogger
        LLMOps trace logger shared across all agents.

    Returns
    -------
    SharedState
        Updated state with ``code_files`` populated and
        ``status`` set to ``"analyzing"`` (or ``"error"``).
    """
    t0 = logger.start_timer()
    agent_name = "CoordinatorAgent"
    input_path = state["input_path"]

    print(f"\n{'='*60}")
    print(f"🤖 COORDINATOR AGENT — scanning: {input_path}")
    print(f"{'='*60}")

    # ── 1. Validate path ──────────────────────────────────────────────────
    if not os.path.exists(input_path) or not os.path.isdir(input_path):
        err = f"Invalid path: '{input_path}' does not exist or is not a directory."
        state["error"]  = err
        state["status"] = "error"
        logger.log(agent_name, None, input_path, err, logger.stop_timer(t0))
        return state

    # ── 2. Read files using the custom tool ───────────────────────────────
    t_tool = logger.start_timer()
    try:
        code_files: dict[str, str] = file_reader_tool.invoke(
            {"directory_path": input_path}
        )
    except Exception as exc:
        state["error"]  = f"file_reader_tool failed: {exc}"
        state["status"] = "error"
        logger.log(agent_name, "file_reader_tool", input_path,
                   state["error"], logger.stop_timer(t0))
        return state

    tool_ms = logger.stop_timer(t_tool)
    logger.log(agent_name, "file_reader_tool",
               f"Scanning {input_path}",
               f"Read {len(code_files)} file(s)",
               tool_ms, OLLAMA_MODEL)

    if not code_files:
        state["error"]  = f"No supported files found in '{input_path}'."
        state["status"] = "error"
        logger.log(agent_name, None, input_path, state["error"],
                   logger.stop_timer(t0))
        return state

    state["code_files"] = code_files
    file_summary = summarise_code_files(code_files)

    # ── 3. LLM coordinator status message ─────────────────────────────────
    t_llm = logger.start_timer()
    try:
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", _HUMAN_PROMPT),
        ])
        chain  = prompt | llm
        status_msg: str = chain.invoke({
            "input_path": input_path,
            "file_summary": file_summary,
        })
    except Exception as exc:
        # LLM is optional for the coordinator — continue even if it fails
        status_msg = f"[LLM unavailable: {exc}] — {file_summary}"

    llm_ms = logger.stop_timer(t_llm)
    print(f"\n  💬 Coordinator says:\n  {status_msg.strip()}\n")

    logger.log(agent_name, None,
               f"LLM status update for {len(code_files)} file(s)",
               status_msg.strip()[:120],
               llm_ms, OLLAMA_MODEL)

    # ── 4. Update state ───────────────────────────────────────────────────
    state["status"]     = "analyzing"
    state["agent_logs"] = logger.get_entries()
    return state
