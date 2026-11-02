#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo 'Install Python 3.11 or newer first.'; exit 1; fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo 'Created .env. Add OPENAI_API_KEY if you want live AI extraction.'; fi
echo 'Open http://localhost:8000 in your browser.'
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
