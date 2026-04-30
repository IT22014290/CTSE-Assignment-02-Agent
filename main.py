"""
main.py
-------
CLI entry point for the MAS Code Review Pipeline.

Usage:
    python main.py --input <path_to_code_directory>
    python main.py --input tests/sample_code/
    python main.py --input tests/sample_code/ --model phi3
"""

from __future__ import annotations

import argparse
import os
import sys

# ── Load config first so REPORTS_DIR / LOGS_DIR get created ──────────────
import config  # noqa: F401

from state import initial_state
from logger.trace_logger import TraceLogger
from graph.workflow import build_graph


BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║       MAS CODE REVIEW PIPELINE  — CTSE Assignment 2     ║
║   Powered by LangGraph + Ollama (100%% local, zero cost) ║
╚══════════════════════════════════════════════════════════╝
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MAS Code Review Pipeline — CTSE Assignment 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the directory containing Python source files to review.",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Ollama model to use (overrides config.py). e.g. phi3, mistral",
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the full MAS pipeline and return an exit code.

    Returns
    -------
    int
        0 on success, 1 on error.
    """
    print(BANNER)
    args = parse_args()

    # Allow model override from CLI
    if args.model:
        config.OLLAMA_MODEL = args.model
        print(f"ℹ️  Using model: {config.OLLAMA_MODEL}\n")
    else:
        print(f"ℹ️  Using model: {config.OLLAMA_MODEL}  (change in config.py or --model)\n")

    input_path = os.path.abspath(args.input)
    print(f"📁 Input directory: {input_path}\n")

    # ── Initialise shared state and logger ────────────────────────────────
    state  = initial_state(input_path)
    logger = TraceLogger()

    # ── Build and run the LangGraph pipeline ─────────────────────────────
    pipeline = build_graph(logger)

    print("🚀 Starting pipeline...\n")
    try:
        final_state = pipeline.invoke(state)
    except Exception as exc:
        print(f"\n❌ Pipeline crashed unexpectedly: {exc}", file=sys.stderr)
        return 1

    # ── Save trace log ────────────────────────────────────────────────────
    log_path = logger.save()

    # ── Final summary ─────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  PIPELINE COMPLETE")
    print("="*60)

    if final_state["status"] == "error":
        print(f"\n❌ Error: {final_state['error']}")
        return 1

    report_path = final_state.get("report_path", "")
    num_files   = len(final_state.get("code_files", {}))
    sec_results = final_state.get("security_results", {})
    q_results   = final_state.get("analysis_results", {})

    total_high   = sum(len(v.get("high",   [])) for v in sec_results.values())
    total_medium = sum(len(v.get("medium", [])) for v in sec_results.values())
    total_q      = sum(len(v.get("issues", [])) for v in q_results.values())
    avg_score    = (
        sum(v.get("score", 0) for v in q_results.values()) / max(len(q_results), 1)
    )

    print(f"\n  Files reviewed      : {num_files}")
    print(f"  Avg quality score   : {avg_score:.1f}/10")
    print(f"  Security issues     : {total_high} HIGH, {total_medium} MEDIUM")
    print(f"  Quality issues      : {total_q}")
    print(f"\n  📋 Report → {report_path}")
    print(f"  📄 Trace  → {log_path}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
