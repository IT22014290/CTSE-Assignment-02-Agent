"""
graph/workflow.py
-----------------
LangGraph StateGraph definition for the MAS Code Review Pipeline.

Defines the directed graph of agent nodes and the routing logic that
determines which node executes next based on the current SharedState.

Graph topology:
    START → coordinator → code_analysis → security_audit → report_generator → END
                                  ↓ (on error)
                                 END
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from state import SharedState
from logger.trace_logger import TraceLogger
from agents.coordinator_agent import run_coordinator
from agents.code_analysis_agent import run_code_analysis
from agents.security_agent import run_security_audit
from agents.report_agent import run_report_generator


def _route_after_coordinator(state: SharedState) -> str:
    """
    Routing function: decide next node after the Coordinator.

    Parameters
    ----------
    state : SharedState
        Current pipeline state.

    Returns
    -------
    str
        Node name: ``"code_analysis"`` on success, ``"__end__"`` on error.
    """
    if state["status"] == "error":
        return END
    return "code_analysis"


def _route_after_code_analysis(state: SharedState) -> str:
    """
    Routing function: decide next node after Code Analysis.

    Returns
    -------
    str
        Node name: ``"security_audit"`` on success, ``"__end__"`` on error.
    """
    if state["status"] == "error":
        return END
    return "security_audit"


def _route_after_security(state: SharedState) -> str:
    """
    Routing function: decide next node after Security Audit.

    Returns
    -------
    str
        Always routes to ``"report_generator"`` (errors are non-fatal here).
    """
    return "report_generator"


def build_graph(logger: TraceLogger) -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph for the pipeline.

    Each node is a thin wrapper that injects the shared *logger* instance
    into the corresponding agent function.

    Parameters
    ----------
    logger : TraceLogger
        The single shared LLMOps trace logger for this pipeline run.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph StateGraph ready to invoke.
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
        "report_generator",
        lambda state: run_report_generator(state, logger),
    )

    # ── Define edges (routing) ────────────────────────────────────────────
    graph.add_edge(START, "coordinator")

    graph.add_conditional_edges(
        "coordinator",
        _route_after_coordinator,
        {"code_analysis": "code_analysis", END: END},
    )
    graph.add_conditional_edges(
        "code_analysis",
        _route_after_code_analysis,
        {"security_audit": "security_audit", END: END},
    )
    graph.add_conditional_edges(
        "security_audit",
        _route_after_security,
        {"report_generator": "report_generator"},
    )
    graph.add_edge("report_generator", END)

    return graph.compile()
