"""
agents/code_analysis_agent.py
------------------------------
Member 1 – Code Analysis Agent

Analyses each Python source file for code quality issues including:
  • PEP 8 style violations (identified by LLM)
  • Cognitive complexity & long functions
  • Code smells: magic numbers, bare except, etc.
  • Overall maintainability score (1-10)

Persona / System Prompt
-----------------------
You are a Senior Python Code Reviewer with 10 years of experience.  You
review code for style (PEP 8), complexity, naming, and maintainability.
You are strict but constructive.  You NEVER invent issues that are not
present in the code.  You always provide a numeric quality score (1-10)
and a bullet list of specific, actionable issues.
"""

from __future__ import annotations

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from state import SharedState
from logger.trace_logger import TraceLogger

# ── System prompt ─────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a Senior Python Code Reviewer with 10+ years of experience.
Your task: review Python source code for quality issues.

You MUST:
- Assign a quality score from 1 (terrible) to 10 (excellent).
- List specific, actionable issues found (not generic advice).
- Be concise — each issue in one sentence.
- Never invent issues not present in the actual code shown.

Output format (use EXACTLY this structure):
SCORE: <number>/10
ISSUES:
- <issue 1>
- <issue 2>
SUMMARY: <one paragraph overall assessment>
"""

_HUMAN_PROMPT = """\
Review the following Python file for code quality.

File: {filename}
```python
{code}
```

Provide your structured review now.
"""


def _parse_llm_output(raw: str) -> dict:
    """
    Parse the structured LLM output into a typed dict.

    Parameters
    ----------
    raw : str
        Raw LLM response text.

    Returns
    -------
    dict
        ``{"score": int, "issues": list[str], "summary": str}``
    """
    score   = 5
    issues: list[str] = []
    summary = ""
    mode    = None

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("SCORE:"):
            try:
                score = int(stripped.split(":")[1].split("/")[0].strip())
            except (IndexError, ValueError):
                pass
        elif stripped.upper() == "ISSUES:":
            mode = "issues"
        elif stripped.upper().startswith("SUMMARY:"):
            mode    = "summary"
            summary = stripped[len("SUMMARY:"):].strip()
        elif mode == "issues" and stripped.startswith("-"):
            issues.append(stripped[1:].strip())
        elif mode == "summary" and stripped:
            summary += " " + stripped

    return {"score": score, "issues": issues, "summary": summary.strip()}


def run_code_analysis(state: SharedState, logger: TraceLogger) -> SharedState:
    """
    Execute the Code Analysis Agent node.

    Iterates over all files in ``state["code_files"]``, calls the Ollama
    LLM with a structured review prompt, and stores results in
    ``state["analysis_results"]``.

    Parameters
    ----------
    state : SharedState
        Current pipeline state.
    logger : TraceLogger
        Shared LLMOps trace logger.

    Returns
    -------
    SharedState
        Updated state with ``analysis_results`` populated.
    """
    agent_name  = "CodeAnalysisAgent"
    code_files  = state.get("code_files", {})
    results: dict = {}

    print(f"\n{'='*60}")
    print(f"🤖 CODE ANALYSIS AGENT — reviewing {len(code_files)} file(s)")
    print(f"{'='*60}")

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

    for filename, code in code_files.items():
        t0 = logger.start_timer()
        print(f"  🔍 Analysing: {filename}")

        if code.startswith("# SKIPPED") or code.startswith("# ERROR"):
            results[filename] = {
                "score": 0, "issues": [code], "summary": code
            }
            continue

        # Truncate very long files to avoid context overflow
        code_snippet = code[:3500] + ("\n# ... (truncated)" if len(code) > 3500 else "")

        try:
            raw = chain.invoke({"filename": filename, "code": code_snippet})
            parsed = _parse_llm_output(raw)
        except Exception as exc:
            parsed = {
                "score": 0,
                "issues": [f"LLM analysis failed: {exc}"],
                "summary": "Analysis could not be completed.",
            }

        results[filename] = parsed
        dur = logger.stop_timer(t0)
        logger.log(
            agent_name, None,
            f"Analysing {filename}",
            f"Score {parsed['score']}/10, {len(parsed['issues'])} issues",
            dur, OLLAMA_MODEL,
        )

    state["analysis_results"] = results
    state["status"]            = "auditing"
    state["agent_logs"]        = logger.get_entries()
    return state
