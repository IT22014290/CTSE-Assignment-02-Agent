# MAS Code Review Pipeline
### SE4010 CTSE – Assignment 2 | Multi-Agent System

> A locally-hosted, zero-cost Multi-Agent System that automatically reviews Python code for **quality issues** and **security vulnerabilities**, powered by [LangGraph](https://github.com/langchain-ai/langgraph) + [Ollama](https://ollama.com).

---

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Team Members & Contributions](#team-members--contributions)
- [Setup](#setup)
- [Usage](#usage)
- [Running Evaluations](#running-evaluations)
- [Project Structure](#project-structure)
- [State Management](#state-management)
- [Observability](#observability)

---

## Overview

| Item | Detail |
|------|--------|
| **Course** | SE4010 – Cloud Technologies in Software Engineering (CTSE) |
| **Assignment** | Assignment 2 – Machine Learning / MAS |
| **Framework** | LangGraph (StateGraph) |
| **LLM Engine** | Ollama (local SLMs — no cloud API keys) |
| **Language** | Python 3.9+ |

### What it does

1. 📁 **Reads** all Python files from a local directory
2. 🔍 **Analyses** code quality — style, complexity, naming, smells (via LLM)
3. 🔒 **Audits** security — `eval()`, hardcoded secrets, SQL injection, shell injection, weak hashes (via bandit + LLM)
4. 📋 **Generates** a structured Markdown report with findings, scores, and recommendations
5. 📄 **Logs** every agent action to a JSON trace file (LLMOps observability)

---

## Architecture

```
User Input (local folder path)
         │
         ▼
┌─────────────────────────────────────────────┐
│          COORDINATOR AGENT (Member 1)        │
│  Validates path → reads files → delegates   │
└──────────┬──────────────────────────────────┘
           │ LangGraph StateGraph edge
    ┌──────┴──────┐
    ▼             ▼  (parallel concept, sequential in graph)
┌──────────┐  ┌──────────────┐
│  CODE    │  │  SECURITY    │
│ ANALYSIS │  │    AUDIT     │
│ (Mbr 1)  │  │  (Mbr 2)    │
└──────────┘  └──────────────┘
         │           │
         └─────┬─────┘
               ▼
    ┌─────────────────┐
    │ REPORT GENERATOR│
    │   (Member 3)    │
    └─────────────────┘
               │
               ▼
    outputs/reports/report_*.md
    outputs/logs/trace_*.json
```

**LangGraph routing:** `START → coordinator → code_analysis → security_audit → report_generator → END`
Conditional edges route to `END` immediately if the coordinator detects an error.

---

## Team Members & Contributions

### Member 1 — **Samishka H T** (IT22014290)
| Component | File |
|-----------|------|
| **Agent** | `agents/coordinator_agent.py` — Validates input, reads files, drives pipeline |
| **Agent** | `agents/code_analysis_agent.py` — LLM-based code quality reviewer |
| **Tool** | `tools/file_reader_tool.py` — Reads Python files from directory |
| **Eval** | `evaluation/eval_coordinator.py` — Property-based tests |

### Member 2 — **Pandithasundara N B** (IT22248244)
| Component | File |
|-----------|------|
| **Agent** | `agents/security_agent.py` — Runs bandit scan + LLM security interpretation |
| **Tool** | `tools/security_scanner_tool.py` — bandit wrapper + pattern-based fallback |
| **Eval** | `evaluation/eval_security.py` — Property tests + LLM-as-a-Judge |

### Member 3 — **Wijerathne C G T N** (IT22333148)
| Component | File |
|-----------|------|
| **Agent** | `agents/report_agent.py` — Synthesises findings, writes executive summary |
| **Tool** | `tools/report_generator_tool.py` — Generates structured Markdown report |
| **Eval** | `evaluation/eval_report.py` — Structural tests + LLM-as-a-Judge |

---

## Setup

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com) installed and running
- At least one model pulled: `ollama pull llama3:8b` _(or `phi3`, `mistral`)_

### Quick Setup (recommended)

```bash
cd mas-code-review
bash setup.sh
source .venv/bin/activate
```

### Manual Setup

```bash
cd mas-code-review
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Change the Ollama model

Edit `config.py`:
```python
OLLAMA_MODEL: str = "phi3"    # or "mistral", "qwen2", etc.
```
Or pass it as a CLI argument: `python main.py --input ... --model phi3`

---

## Usage

```bash
# Activate the venv first
source .venv/bin/activate

# Review the included sample code (recommended first run)
python main.py --input tests/sample_code/

# Review any local Python project
python main.py --input /path/to/your/project/

# Use a different model
python main.py --input tests/sample_code/ --model phi3
```

**Expected output:**
```
🤖 COORDINATOR AGENT — scanning: .../tests/sample_code
  🔧 [CoordinatorAgent] Read 3 file(s)  (45 ms)

🤖 CODE ANALYSIS AGENT — reviewing 3 file(s)
  🔍 Analysing: vulnerable_app.py
  🤖 [CodeAnalysisAgent] Score 3/10, 5 issues  (8240 ms)
  ...

🤖 SECURITY AGENT — auditing 3 file(s)
  🔧 [SecurityAgent] Found 12 issue(s) across all files  (120 ms)
  ...

🤖 REPORT AGENT — generating final report
  ✅ Report saved → outputs/reports/report_20260430_180000.md

📄 Trace log saved → outputs/logs/trace_20260430_180000.json
```

---

## Running Evaluations

Each evaluation script can run **without** Ollama (property tests always run). The LLM-as-a-Judge section is automatically skipped if Ollama is unavailable.

```bash
# Member 1 — Coordinator evaluation
python evaluation/eval_coordinator.py

# Member 2 — Security evaluation
python evaluation/eval_security.py

# Member 3 — Report evaluation
python evaluation/eval_report.py
```

---

## Project Structure

```
mas-code-review/
├── README.md
├── requirements.txt
├── setup.sh
├── main.py                          # CLI entry point
├── config.py                        # Ollama model, paths, settings
├── state.py                         # LangGraph SharedState TypedDict
│
├── agents/
│   ├── coordinator_agent.py         # Member 1: Coordinator
│   ├── code_analysis_agent.py       # Member 1: Code Quality Reviewer
│   ├── security_agent.py            # Member 2: Security Auditor
│   └── report_agent.py              # Member 3: Report Generator
│
├── tools/
│   ├── file_reader_tool.py          # Member 1: reads code files
│   ├── security_scanner_tool.py     # Member 2: bandit security scanner
│   └── report_generator_tool.py    # Member 3: Markdown report builder
│
├── graph/
│   └── workflow.py                  # LangGraph StateGraph
│
├── logger/
│   └── trace_logger.py              # LLMOps JSON trace logger
│
├── evaluation/
│   ├── eval_coordinator.py          # Member 1 evaluation
│   ├── eval_security.py             # Member 2 evaluation
│   └── eval_report.py               # Member 3 evaluation
│
├── tests/
│   └── sample_code/
│       ├── vulnerable_app.py        # Security test: HIGH vulnerabilities
│       ├── bad_quality_code.py      # Quality test: style/complexity issues
│       └── mixed_issues.py          # End-to-end test: both types of issues
│
└── outputs/
    ├── logs/                        # trace_<timestamp>.json files
    └── reports/                     # report_<timestamp>.md files
```

---

## State Management

The `SharedState` TypedDict in `state.py` is the single source of truth passed through the LangGraph graph. Each agent receives the full state, enriches it, and returns it.

```python
class SharedState(TypedDict):
    input_path: str          # Directory path to review
    code_files: dict         # {filename: source_code}       ← set by Coordinator
    analysis_results: dict   # {filename: quality_findings}  ← set by CodeAnalysis
    security_results: dict   # {filename: security_findings} ← set by Security
    report_path: str         # Path to generated .md file    ← set by ReportAgent
    agent_logs: list         # LLMOps trace entries          ← appended by all
    status: str              # Pipeline lifecycle status
    error: str               # Error message (empty = OK)
```

**Flow:** `initial_state()` → Coordinator enriches `code_files` → CodeAnalysis enriches `analysis_results` → Security enriches `security_results` → ReportAgent writes `report_path`.

---

## Observability

Every agent call is logged to `outputs/logs/trace_<timestamp>.json`:

```json
{
  "run_id": "20260430_180000",
  "total_entries": 8,
  "entries": [
    {
      "timestamp": "2026-04-30T18:00:01.234Z",
      "agent": "CoordinatorAgent",
      "tool_called": "file_reader_tool",
      "input_summary": "Scanning /tests/sample_code",
      "output_summary": "Read 3 file(s)",
      "model": "llama3:8b",
      "duration_ms": 45.3
    }
  ]
}
```

---

## Technical Constraints Compliance

| Requirement | Status |
|-------------|--------|
| Local LLM only (Ollama) | ✅ |
| No paid API keys | ✅ |
| LangGraph orchestration | ✅ |
| 3–4 distinct agents | ✅ (4 agents) |
| Custom Python tools | ✅ (3 tools) |
| State management | ✅ (SharedState TypedDict) |
| LLMOps / Observability | ✅ (JSON trace logger) |
| Each student: 1 agent + 1 tool + 1 eval | ✅ |

---

## 🎨 Modern Web Frontend (NEW!)

### Start the Web Interface

```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend API
source .venv/bin/activate
python -m uvicorn api:app --reload

# Terminal 3: Frontend
cd frontend
npm install && npm run dev
```

Visit **http://localhost:3000** for the stunning web UI!

### Features
- 🎯 **Review Tab**: Submit directories for analysis
- 📊 **Monitor Tab**: Real-time pipeline progress tracking
- 📋 **History Tab**: Browse all reports and trace logs
- 🎨 **Beautiful Design**: Modern dark theme with gradient accents
- 📱 **Responsive**: Works on desktop, tablet, mobile

See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) for detailed documentation.

---

## 🔌 REST API (NEW!)

The FastAPI backend provides a complete REST interface:

```bash
# Start the API
python -m uvicorn api:app --reload
```

### Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Check backend health |
| POST | `/api/review` | Start a new review |
| GET | `/api/status/{run_id}` | Get pipeline status |
| GET | `/api/result/{run_id}` | Get pipeline results |
| GET | `/api/reports` | List all reports |
| GET | `/api/report/{filename}` | Download a report |
| GET | `/api/logs` | List all trace logs |
| GET | `/api/log/{filename}` | Download a trace log |
| GET | `/api/config` | Get pipeline config |

### Example: Start a Review via API

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "tests/sample_code",
    "model": "phi3"
  }'
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for API examples and documentation.

---

## ⚡ Parallel Pipeline Execution (NEW!)

### Sequential Mode (Default)

```bash
python main.py --input tests/sample_code/
```

Execution: `Coordinator → Code Analysis → Security Audit → Report`

### Parallel Mode (Faster)

```bash
python main.py --input tests/sample_code/ --parallel
```

Execution: `Coordinator → (Code Analysis ∥ Security Audit) → Report`

**Performance**: ~30-35% faster on typical projects

- Member 1's agents (Coordinator) sequentially validate and dispatch
- Member 2's agent (Security) and Member 1's agent (Code Analysis) run in **parallel**
- Member 3's agent (Report) waits for both to complete

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for more details.

---

## 🐳 Docker Deployment (NEW!)

### Full Stack with Docker Compose

```bash
# Start all services (API, Frontend, Ollama)
docker-compose up
```

Services:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Ollama: http://localhost:11434

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## 📚 Documentation

- **[README.md](README.md)** — This file; architecture and overview
- **[SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)** — Complete solution overview with all changes
- **[FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)** — React frontend setup and development
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** — Complete deployment and API reference
- **[requirements.txt](requirements.txt)** — Python dependencies

---

## 🎯 Project Highlights

✅ **All Requirements Met**
- Multi-agent system with 4 agents (Coordinator, Code Analysis, Security, Report)
- Custom Python tools for each agent with type hints and docstrings
- State management via SharedState TypedDict
- JSON-based observability with trace logging
- Individual evaluations for each team member

✨ **Bonus Features**
- Modern React web frontend with real-time monitoring
- FastAPI REST backend with full integration
- Parallel pipeline execution (30% performance improvement)
- Docker containerization for easy deployment
- Comprehensive documentation and guides

---

## 📞 Next Steps

1. **Try the CLI**: `python main.py --input tests/sample_code/`
2. **Try with Frontend**: `npm run dev` and visit http://localhost:3000
3. **Deploy**: `docker-compose up` for production
4. **Evaluate**: Run individual eval scripts for each member
5. **Review**: Check outputs/reports/ and outputs/logs/
