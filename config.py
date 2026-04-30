"""
config.py
---------
Central configuration for the MAS Code Review System.
Change OLLAMA_MODEL to match whatever model you have pulled locally.
"""

import os

# ── Ollama ─────────────────────────────────────────────────────────────────
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── LLM generation settings ─────────────────────────────────────────────────
LLM_TEMPERATURE: float = 0.1        # Low temperature = more deterministic reviews
LLM_NUM_CTX: int = 4096             # Context window

# ── File scanning ────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS: list[str] = [".py"]  # Extend to [".py", ".js"] if needed
MAX_FILE_SIZE_BYTES: int = 100_000         # Skip files larger than 100 KB

# ── Output paths ─────────────────────────────────────────────────────────────
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR: str = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR: str = os.path.join(OUTPUTS_DIR, "reports")
LOGS_DIR: str = os.path.join(OUTPUTS_DIR, "logs")

# ── Ensure output dirs exist ──────────────────────────────────────────────────
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
