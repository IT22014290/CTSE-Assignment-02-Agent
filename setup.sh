#!/usr/bin/env bash
# setup.sh
# One-command setup for the MAS Code Review Pipeline.
# Run: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       MAS Code Review — Environment Setup               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Check Python 3.9+ ──────────────────────────────────────────────────
PYTHON=$(which python3 || which python)
PY_VER=$($PYTHON -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
if [ "$PY_VER" -lt 39 ]; then
  echo "❌ Python 3.9+ is required. Found: $($PYTHON --version)"
  exit 1
fi
echo "✅ Python: $($PYTHON --version)"

# ── 2. Create virtual environment ─────────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "📦 Creating virtual environment..."
  $PYTHON -m venv .venv
fi
echo "✅ Virtual environment ready"

# ── 3. Activate and install dependencies ──────────────────────────────────
source .venv/bin/activate
echo "📦 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# ── 4. Check Ollama ───────────────────────────────────────────────────────
echo ""
echo "🔍 Checking Ollama..."
if command -v ollama &> /dev/null; then
  echo "✅ Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
  echo ""
  echo "📋 Available models:"
  ollama list 2>/dev/null || echo "  (run 'ollama list' to see models)"
  echo ""
  echo "ℹ️  If you don't have llama3:8b, run:  ollama pull llama3:8b"
  echo "   Or use phi3 (smaller):             ollama pull phi3"
  echo "   Then update OLLAMA_MODEL in config.py"
else
  echo "⚠️  Ollama not found. Install from: https://ollama.com"
  echo "   After installing, run:  ollama pull llama3:8b"
fi

# ── 5. Create output directories ─────────────────────────────────────────
mkdir -p outputs/reports outputs/logs
echo "✅ Output directories created"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Setup complete! To run the pipeline:                   ║"
echo "║                                                          ║"
echo "║  source .venv/bin/activate                              ║"
echo "║  python main.py --input tests/sample_code/              ║"
echo "║                                                          ║"
echo "║  To run evaluations:                                     ║"
echo "║  python evaluation/eval_coordinator.py                  ║"
echo "║  python evaluation/eval_security.py                     ║"
echo "║  python evaluation/eval_report.py                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
