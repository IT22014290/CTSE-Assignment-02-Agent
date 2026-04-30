# Deployment & Execution Guide

## 🚀 Complete Deployment Instructions

This guide covers all methods to run the MAS Code Review Pipeline with the new frontend and API.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Parallel Pipeline Execution](#parallel-pipeline-execution)
4. [CLI Usage](#cli-usage)
5. [API Usage](#api-usage)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Setup Environment

```bash
# Clone/navigate to project
cd CTSE-Assignment-02-Agent

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama service (in a separate terminal)
ollama serve

# Pull a model (if not already pulled)
ollama pull phi3  # or llama3, mistral, etc.
```

### Run CLI (No Frontend)

Traditional command-line usage:

```bash
# Sequential mode (default)
python main.py --input tests/sample_code/

# Parallel mode (faster)
python main.py --input tests/sample_code/ --parallel

# Custom model
python main.py --input /path/to/project --model mistral

# All options together
python main.py -i tests/sample_code -m llama3 -p
```

### Run with Frontend

Run both backend API and frontend:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Backend API
source .venv/bin/activate
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Start Frontend
cd frontend
npm install  # First time only
npm run dev
```

Visit `http://localhost:3000` to access the UI.

---

## Docker Deployment

### Prerequisites
- Docker and docker-compose installed
- Docker daemon running

### Option 1: Docker Compose (Recommended)

Start all services at once:

```bash
# Pull Ollama models first (optional, saves time)
docker run -d --name ollama ollama/ollama:latest
docker exec ollama ollama pull phi3

# Start all services
docker-compose up

# In background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services will be available at:
- **Frontend**: `http://localhost:3000`
- **API**: `http://localhost:8000`
- **Ollama**: `http://localhost:11434`

### Option 2: Individual Docker Containers

```bash
# Build images
docker build -t mas-api:latest .
docker build -t mas-frontend:latest ./frontend

# Run Ollama
docker run -d -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  --name ollama-service \
  ollama/ollama:latest

# Pull a model
docker exec ollama-service ollama pull phi3

# Run API
docker run -d -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=phi3 \
  -v $(pwd)/outputs:/app/outputs \
  --name mas-api \
  mas-api:latest

# Run Frontend
docker run -d -p 3000:3000 \
  -e REACT_APP_API_URL=http://localhost:8000/api \
  --name mas-frontend \
  mas-frontend:latest
```

---

## Parallel Pipeline Execution

The pipeline can run code analysis and security audit in **PARALLEL** for improved performance.

### CLI Usage

```bash
# Enable parallel mode
python main.py --input tests/sample_code/ --parallel

# Or short form
python main.py -i tests/sample_code -p
```

### Execution Flow

**Sequential (default):**
```
Coordinator → Code Analysis → Security Audit → Report
```

**Parallel (with --parallel):**
```
Coordinator → ┌─ Code Analysis ─┐
              └─ Security Audit ─┘ → Report
```

### Performance Comparison

On a typical project:
- **Sequential**: ~45-60 seconds
- **Parallel**: ~30-40 seconds (25-35% faster)

### Via API

The parallel mode is automatically used when creating reviews through the API.

---

## CLI Usage

### Basic Commands

```bash
# Help
python main.py --help

# Analyze sample code
python main.py --input tests/sample_code/

# Analyze custom project
python main.py --input /path/to/your/project

# Choose Ollama model
python main.py --input tests/sample_code/ --model llama3
```

### Available Models

Install any of these via: `ollama pull <model_name>`

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| phi3 | ~2GB | ⚡ Fast | ⭐⭐⭐ |
| mistral | ~5GB | ⭐⭐ Medium | ⭐⭐⭐⭐ |
| llama3 | ~8GB | ⭐ Slow | ⭐⭐⭐⭐⭐ |
| qwen2 | ~4GB | ⭐⭐ Medium | ⭐⭐⭐⭐ |

### Output Files

Results are saved to:
- **Reports**: `outputs/reports/report_YYYYMMDD_HHMMSS.md`
- **Trace Logs**: `outputs/logs/trace_YYYYMMDD_HHMMSS.json`

---

## API Usage

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Start a Review

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "tests/sample_code",
    "model": "phi3"
  }'

# Response:
{
  "run_id": "20260501_120000_000000",
  "status": "pending",
  "message": "Pipeline started"
}
```

### Get Pipeline Status

```bash
curl http://localhost:8000/api/status/20260501_120000_000000

# Response:
{
  "run_id": "20260501_120000_000000",
  "status": "running",
  "progress": 0.45,
  "started_at": "2026-05-01T12:00:00",
  "completed_at": null,
  "error": null
}
```

### Get Results

```bash
curl http://localhost:8000/api/result/20260501_120000_000000
```

### List Reports

```bash
curl http://localhost:8000/api/reports
```

### Download Report

```bash
curl -O http://localhost:8000/api/report/report_20260501_120000.md
```

---

## Configuration

### Ollama Settings

Edit `config.py`:

```python
OLLAMA_MODEL = "phi3"              # Model to use
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama service URL
```

### API Settings

Edit `config.py`:

```python
REPORTS_DIR = "outputs/reports"    # Report output directory
LOGS_DIR = "outputs/logs"          # Log output directory
```

### Environment Variables

```bash
# Backend
export OLLAMA_MODEL=phi3
export OLLAMA_BASE_URL=http://localhost:11434

# Frontend
export REACT_APP_API_URL=http://localhost:8000/api
```

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Or with Docker
docker run -d -p 11434:11434 ollama/ollama:latest
```

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull phi3

# Remove and re-pull
ollama rm phi3
ollama pull phi3
```

### Connection Refused

```bash
# Check if services are running
lsof -i :8000      # API port
lsof -i :3000      # Frontend port
lsof -i :11434     # Ollama port

# Restart services if needed
docker-compose restart
```

### Out of Memory

Reduce model size or increase system resources:

```bash
# Use smaller, faster model
ollama pull phi3

# Or configure memory limits
docker update --memory 4gb ollama-service
```

### Frontend Can't Connect

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS is enabled in `api.py`
3. Verify `REACT_APP_API_URL` in environment

---

## Performance Tuning

### For Faster Analysis

```bash
# Use faster model + parallel mode
python main.py -i tests/sample_code -m phi3 --parallel

# Or via API with parallel (automatic)
curl -X POST http://localhost:8000/api/review \
  -d '{
    "input_path": "tests/sample_code",
    "model": "phi3"
  }'
```

### For Better Quality

```bash
# Use larger, more capable model
python main.py -i tests/sample_code -m llama3

# Use sequential mode for stability
python main.py -i tests/sample_code -m llama3
```

### Docker Memory Settings

```yaml
# In docker-compose.yml
ollama:
  mem_limit: 8gb      # Increase if available
  memswap_limit: 10gb
```

---

## Next Steps

1. **Try the Sample**: `python main.py -i tests/sample_code`
2. **Run Frontend**: `npm run dev` in `frontend/`
3. **Deploy**: `docker-compose up` for production
4. **Monitor**: Check `outputs/reports/` and `outputs/logs/` for results

Enjoy the pipeline! 🚀
