"""
api.py
------
FastAPI server for the MAS Code Review Pipeline.

Provides REST endpoints for:
  - Running code review pipelines (sequentially or in parallel)
  - Retrieving pipeline results
  - Listing reports and logs
  - Real-time pipeline monitoring
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import REPORTS_DIR, LOGS_DIR, OLLAMA_MODEL
from state import initial_state
from logger.trace_logger import TraceLogger
from graph.workflow import build_graph


# ─────────────────────────────────────────────────────────────────────────
# FastAPI Setup
# ─────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MAS Code Review Pipeline API",
    description="Multi-Agent System for Python Code Review (Quality + Security)",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running pipelines asynchronously
executor = ThreadPoolExecutor(max_workers=3)

# ─────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────


class ReviewRequest(BaseModel):
    """Request to run a code review."""
    input_path: str
    model: Optional[str] = None


class PipelineStatus(BaseModel):
    """Pipeline execution status."""
    run_id: str
    status: str  # "pending", "running", "completed", "error"
    progress: float  # 0.0 to 1.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ReviewResult(BaseModel):
    """Result of a code review."""
    run_id: str
    status: str
    input_path: str
    files_analyzed: int
    report_path: Optional[str] = None
    trace_log_path: Optional[str] = None
    summary: Optional[str] = None
    timestamp: str


class ReportMetadata(BaseModel):
    """Metadata about a report file."""
    filename: str
    path: str
    created_at: str
    size: int


# ─────────────────────────────────────────────────────────────────────────
# In-Memory Pipeline State
# ─────────────────────────────────────────────────────────────────────────

pipeline_runs: dict[str, dict] = {}


def generate_run_id() -> str:
    """Generate a unique run ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]


def run_pipeline_sync(input_path: str, run_id: str, model: Optional[str] = None) -> dict:
    """
    Execute the code review pipeline synchronously.

    Parameters
    ----------
    input_path : str
        Path to directory containing Python files.
    run_id : str
        Unique identifier for this run.
    model : Optional[str]
        Override Ollama model.

    Returns
    -------
    dict
        Pipeline execution result.
    """
    try:
        # Update status
        pipeline_runs[run_id]["status"] = "running"
        pipeline_runs[run_id]["started_at"] = datetime.now().isoformat()

        # Initialize logger
        logger = TraceLogger(run_id=run_id)

        # Override model if provided
        os.environ["OLLAMA_MODEL"] = model or OLLAMA_MODEL

        # Build and execute graph
        graph = build_graph(logger)
        compiled_graph = graph.compile()

        state = initial_state(input_path)
        result = compiled_graph.invoke(state)

        # Extract results
        files_analyzed = len(result.get("code_files", {}))
        report_path = result.get("report_path")
        trace_log_path = logger.log_file

        # Get report summary (first 500 chars)
        summary = None
        if report_path and os.path.exists(report_path):
            with open(report_path, "r") as f:
                summary = f.read()[:500]

        pipeline_runs[run_id]["status"] = "completed"
        pipeline_runs[run_id]["completed_at"] = datetime.now().isoformat()
        pipeline_runs[run_id]["progress"] = 1.0
        pipeline_runs[run_id]["result"] = {
            "files_analyzed": files_analyzed,
            "report_path": report_path,
            "trace_log_path": trace_log_path,
            "summary": summary,
        }

        return {
            "run_id": run_id,
            "status": "completed",
            "input_path": input_path,
            "files_analyzed": files_analyzed,
            "report_path": report_path,
            "trace_log_path": trace_log_path,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        pipeline_runs[run_id]["status"] = "error"
        pipeline_runs[run_id]["completed_at"] = datetime.now().isoformat()
        pipeline_runs[run_id]["error"] = str(e)
        raise


# ─────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": OLLAMA_MODEL,
    }


@app.post("/api/review")
async def start_review(request: ReviewRequest, background_tasks: BackgroundTasks):
    """
    Start a code review pipeline run.

    Parameters
    ----------
    request : ReviewRequest
        Review request with input path and optional model.
    background_tasks : BackgroundTasks
        FastAPI background tasks.

    Returns
    -------
    dict
        Pipeline metadata with run ID.
    """
    # Validate input path
    if not os.path.isdir(request.input_path):
        raise HTTPException(status_code=400, detail="Invalid input path")

    # Check for Python files
    py_files = list(Path(request.input_path).rglob("*.py"))
    if not py_files:
        raise HTTPException(
            status_code=400, detail="No Python files found in directory"
        )

    # Generate run ID and create entry
    run_id = generate_run_id()
    pipeline_runs[run_id] = {
        "status": "pending",
        "progress": 0.0,
        "started_at": None,
        "completed_at": None,
        "error": None,
    }

    # Run pipeline in background
    background_tasks.add_task(run_pipeline_sync, request.input_path, run_id, request.model)

    return {
        "run_id": run_id,
        "status": "pending",
        "message": "Pipeline started",
    }


@app.get("/api/status/{run_id}")
async def get_pipeline_status(run_id: str):
    """Get the status of a pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run_info = pipeline_runs[run_id]
    return PipelineStatus(
        run_id=run_id,
        status=run_info["status"],
        progress=run_info.get("progress", 0.0),
        started_at=run_info.get("started_at"),
        completed_at=run_info.get("completed_at"),
        error=run_info.get("error"),
    )


@app.get("/api/result/{run_id}")
async def get_pipeline_result(run_id: str):
    """Get the result of a completed pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run_info = pipeline_runs[run_id]

    if run_info["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"Pipeline still {run_info['status']}"
        )

    result = run_info.get("result", {})
    return ReviewResult(
        run_id=run_id,
        status="completed",
        input_path=result.get("input_path", ""),
        files_analyzed=result.get("files_analyzed", 0),
        report_path=result.get("report_path"),
        trace_log_path=result.get("trace_log_path"),
        summary=result.get("summary"),
        timestamp=run_info.get("completed_at", ""),
    )


@app.get("/api/reports")
async def list_reports():
    """List all available reports."""
    try:
        reports = []
        if os.path.exists(REPORTS_DIR):
            for filename in sorted(os.listdir(REPORTS_DIR), reverse=True):
                filepath = os.path.join(REPORTS_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append(
                        ReportMetadata(
                            filename=filename,
                            path=filepath,
                            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            size=stat.st_size,
                        ).model_dump()
                    )
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/{filename}")
async def download_report(filename: str):
    """Download a report file."""
    filepath = os.path.join(REPORTS_DIR, filename)

    # Security: prevent directory traversal
    if not os.path.abspath(filepath).startswith(os.path.abspath(REPORTS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(filepath, filename=filename)


@app.get("/api/logs")
async def list_logs():
    """List all available trace logs."""
    try:
        logs = []
        if os.path.exists(LOGS_DIR):
            for filename in sorted(os.listdir(LOGS_DIR), reverse=True):
                filepath = os.path.join(LOGS_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    logs.append(
                        {
                            "filename": filename,
                            "path": filepath,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "size": stat.st_size,
                        }
                    )
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/log/{filename}")
async def download_log(filename: str):
    """Download a trace log file."""
    filepath = os.path.join(LOGS_DIR, filename)

    # Security: prevent directory traversal
    if not os.path.abspath(filepath).startswith(os.path.abspath(LOGS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log not found")

    return FileResponse(filepath, filename=filename)


@app.get("/api/config")
async def get_config():
    """Get pipeline configuration."""
    return {
        "ollama_model": OLLAMA_MODEL,
        "reports_dir": REPORTS_DIR,
        "logs_dir": LOGS_DIR,
    }


# Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "build")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir, html=True), name="static")


@app.get("/")
async def root():
    """Serve the frontend index.html"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not built yet. Run: npm run build in frontend/"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
