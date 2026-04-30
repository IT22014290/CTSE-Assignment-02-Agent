"""
graph/workflow_parallel.py
--------------------------
LangGraph StateGraph with PARALLEL pipeline support.

This version allows code_analysis and security_audit to run in PARALLEL
after the coordinator completes, improving performance.

Graph topology (PARALLEL):
    START → coordinator → ┐
                          ├─→ (parallel) code_analysis
                          ├─→ (parallel) security_audit
                          └─→ report_generator → END

vs Sequential (original):
    START → coordinator → code_analysis → security_audit → report_generator → END
"""

from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import StateGraph, START, END

from state import SharedState
from logger.trace_logger import TraceLogger
from agents.coordinator_agent import run_coordinator
from agents.code_analysis_agent import run_code_analysis
from agents.security_agent import run_security_audit
from agents.report_agent import run_report_generator


def _route_after_coordinator(state: SharedState) -> list[str]:
    """
    Routing function: route to both analysis agents in parallel.

    Returns
    -------
    list[str]
        Node names for both analysis agents to run in parallel.
    """
    if state["status"] == "error":
        return [END]
    # Return both nodes to run in parallel
    return ["code_analysis", "security_audit"]


def _merge_analysis_results(state: SharedState) -> SharedState:
    """
    Merge results from both analysis agents (called after both complete).
    
    This is a no-op in terms of state transformation but ensures
    both analyses are complete before moving to report generation.
    """
    # Both analyses have already updated the state
    # Just ensure status is still good
    if state.get("status") != "error":
        state["status"] = "ready_for_report"
    return state


def build_graph_parallel(logger: TraceLogger) -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph with PARALLEL execution.

    Code Analysis and Security Audit run in PARALLEL after Coordinator.

    Parameters
    ----------
    logger : TraceLogger
        The single shared LLMOps trace logger for this pipeline run.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph StateGraph with parallel support.
    """
    graph = StateGraph(SharedState)

    # ── Register agent nodes ──────────────────────────────────────────────
    graph.add_node(
        "coordinator",
        lambda state: run_coordinator(state, logger),
    )
    graph.add_node(
        "code_analysis",
        lambda state: run_code_analysis(state, logger),
    )
    graph.add_node(
        "security_audit",
        lambda state: run_security_audit(state, logger),
    )
    graph.add_node(
        "merge_results",
        lambda state: _merge_analysis_results(state),
    )
    graph.add_node(
        "report_generator",
        lambda state: run_report_generator(state, logger),
    )

    # ── Define edges (routing) ────────────────────────────────────────────
    graph.add_edge(START, "coordinator")

    # After coordinator, both analyses run in PARALLEL
    graph.add_conditional_edges(
        "coordinator",
        _route_after_coordinator,
        {
            "code_analysis": "code_analysis",
            "security_audit": "security_audit",
            END: END,
        },
    )

    # Both analyses converge at merge_results
    graph.add_edge("code_analysis", "merge_results")
    graph.add_edge("security_audit", "merge_results")

    # After merge, generate report
    graph.add_edge("merge_results", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()
