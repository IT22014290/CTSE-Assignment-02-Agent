"""
logger/trace_logger.py
----------------------
LLMOps / AgentOps observability logger.

Records every agent invocation — including tool calls, inputs, outputs,
and timing — to a structured JSON trace file in outputs/logs/.

Member contribution: shared infrastructure (used by all agents).
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

from config import LOGS_DIR, OLLAMA_MODEL


class TraceLogger:
    """
    Thread-safe JSON trace logger for the MAS pipeline.

    Each call to :meth:`log` appends an :class:`AgentLog` entry to an
    in-memory list.  Call :meth:`save` at the end of the run to persist
    the full trace to disk.

    Example
    -------
    >>> logger = TraceLogger()
    >>> t = logger.start_timer()
    >>> logger.log("CoordinatorAgent", "file_reader_tool",
    ...            "Scanning /code", "Read 3 files", logger.stop_timer(t))
    >>> logger.save()
    """

    def __init__(self, run_id: Optional[str] = None) -> None:
        self._entries: list[dict] = []
        self._run_id: str = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # ── Timer helpers ──────────────────────────────────────────────────────
    def start_timer(self) -> float:
        """Return a monotonic start timestamp (seconds)."""
        return time.monotonic()

    def stop_timer(self, start: float) -> float:
        """Return elapsed milliseconds since *start*."""
        return round((time.monotonic() - start) * 1000, 2)

    # ── Core log method ────────────────────────────────────────────────────
    def log(
        self,
        agent: str,
        tool_called: Optional[str],
        input_summary: str,
        output_summary: str,
        duration_ms: float,
        model: str = OLLAMA_MODEL,
    ) -> dict:
        """
        Record one agent invocation trace entry.

        Parameters
        ----------
        agent : str
            Name of the agent that produced this entry.
        tool_called : str | None
            Name of the custom tool invoked, or None if no tool was used.
        input_summary : str
            Brief description of what the agent received.
        output_summary : str
            Brief description of what the agent produced.
        duration_ms : float
            Wall-clock time in milliseconds for this invocation.
        model : str
            Ollama model identifier used for the LLM call.

        Returns
        -------
        dict
            The trace entry that was appended.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "tool_called": tool_called,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "model": model,
            "duration_ms": duration_ms,
        }
        self._entries.append(entry)
        # Also print to stdout so the user sees live progress
        icon = "🔧" if tool_called else "🤖"
        print(f"  {icon} [{agent}] {output_summary}  ({duration_ms:.0f} ms)")
        return entry

    def get_entries(self) -> list[dict]:
        """Return all trace entries accumulated so far."""
        return list(self._entries)

    # ── Persistence ────────────────────────────────────────────────────────
    def save(self) -> str:
        """
        Write the full trace to a JSON file in the logs directory.

        Returns
        -------
        str
            Absolute path to the saved log file.
        """
        filename = f"trace_{self._run_id}.json"
        path = os.path.join(LOGS_DIR, filename)
        payload = {
            "run_id": self._run_id,
            "total_entries": len(self._entries),
            "entries": self._entries,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print(f"\n📄 Trace log saved → {path}")
        return path
