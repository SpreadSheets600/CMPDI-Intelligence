#!/usr/bin/env bash
# CMPDI Intelligence: one-command setup and run.
#
#   ./run.sh              setup + start the app (first run also ingests the demo corpus)
#   ./run.sh --fresh      wipe data/, re-ingest the demo corpus, start the app
#   ./run.sh --no-llm     skip Ollama entirely; the app runs in extractive mode
#
# Environment overrides: OLLAMA_MODEL (default gemma4:31b-cloud), PORT (default 5000).

set -euo pipefail

cd "$(dirname "$0")"

PORT="${PORT:-5000}"
OLLAMA_MODEL="${OLLAMA_MODEL:-gemma4:31b-cloud}"
FRESH=0
NO_LLM=0

for arg in "$@"; do
  case "$arg" in
    --fresh) FRESH=1 ;;
    --no-llm) NO_LLM=1 ;;
    *) echo "Unknown option: $arg (use --fresh or --no-llm)"; exit 1 ;;
  esac
done

info() { printf '\033[1;33m[run]\033[0m %s\n' "$1"; }
ok()   { printf '\033[1;32m[ok]\033[0m  %s\n' "$1"; }
warn() { printf '\033[1;31m[!!]\033[0m %s\n' "$1"; }

# ---------------------------------------------------------------- dependencies

if [ ! -d .venv ]; then
  info "Creating virtual environment"
  if command -v uv >/dev/null 2>&1; then
    uv venv --system-site-packages .venv
  else
    python3 -m venv .venv
  fi
fi
PY=.venv/bin/python

info "Installing Python dependencies"
if command -v uv >/dev/null 2>&1; then
  uv pip install -q -e . || uv pip install -q -r pyproject.toml
else
  .venv/bin/pip install -q -e .
fi
ok "Dependencies ready"

# ---------------------------------------------------------------- ollama

OLLAMA_PID=""
setup_ollama() {
  if ! command -v ollama >/dev/null 2>&1; then
    info "Ollama not found, installing"
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      curl -fsSL https://ollama.com/install.sh | sudo bash || { warn "Ollama install failed; continuing without it"; return 1; }
    else
      warn "Cannot install Ollama without passwordless sudo; install it manually (https://ollama.com)"
      warn "The app will use extractive mode until then."
      return 1
    fi
  fi

  # Start the server if nothing answers on the default port
  if ! curl -s --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    info "Starting ollama serve in the background"
    nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    OLLAMA_PID=$!
    for _ in $(seq 1 30); do
      curl -s --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
      sleep 1
    done
    curl -s --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1 || { warn "ollama serve did not come up; continuing without it"; return 1; }
  fi
  ok "Ollama is running"

  if ! ollama list 2>/dev/null | grep -q "^${OLLAMA_MODEL%%:*}"; then
    info "Pulling model $OLLAMA_MODEL (this can take a while)"
    ollama pull "$OLLAMA_MODEL" || { warn "Model pull failed; continuing in extractive mode"; return 1; }
  fi
  ok "Model $OLLAMA_MODEL available"
  return 0
}

if [ "$NO_LLM" -eq 1 ]; then
  warn "Skipping Ollama (--no-llm); answers will use extractive mode"
else
  setup_ollama || true
fi

# ---------------------------------------------------------------- data

if [ "$FRESH" -eq 1 ] && [ -d data ]; then
  info "Wiping data/ (--fresh)"
  rm -rf data
fi

"$PY" -m backend.scripts.init_system

DOC_COUNT=$("$PY" -c "
from backend.db import database as db
db.init_db()
print(len(db.q('SELECT id FROM documents')))
" 2>/dev/null || echo 0)

if [ "$DOC_COUNT" -eq 0 ]; then
  info "No documents yet; generating and ingesting the demo corpus"
  "$PY" -m backend.scripts.make_demo_corpus
  "$PY" -m backend.scripts.ingest data/demo_corpus
  ok "Demo corpus ingested"
else
  ok "Library already has $DOC_COUNT documents"
fi

# ---------------------------------------------------------------- frontend

if ! command -v npm >/dev/null 2>&1; then
  warn "npm not found; skipping frontend build (install Node.js, then run: cd frontend && npm install && npm run build)"
elif [ ! -f frontend/dist/index.html ]; then
  info "Building frontend (first run)"
  (cd frontend && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund) && npm run build)
  ok "Frontend built"
elif [ -z "$(find frontend/src frontend/package.json -newer frontend/dist/index.html -print -quit 2>/dev/null)" ]; then
  ok "Frontend already built and up to date"
else
  info "Rebuilding frontend (sources changed)"
  (cd frontend && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund) && npm run build)
  ok "Frontend rebuilt"
fi

# ---------------------------------------------------------------- run

if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  warn "Port $PORT is busy; killing the stale listener"
  lsof -tiTCP:"$PORT" -sTCP:LISTEN | xargs -r kill
  sleep 1
fi

cleanup() {
  [ -n "$OLLAMA_PID" ] && kill "$OLLAMA_PID" 2>/dev/null || true
}
trap cleanup EXIT

info "Starting CMPDI Intelligence on http://127.0.0.1:${PORT} (Ctrl+C to stop)"
"$PY" -c "
from backend.app import create_app
create_app().run(host='127.0.0.1', port=${PORT}, debug=False)
"
