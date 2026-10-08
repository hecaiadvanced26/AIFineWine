#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
    echo "Create .env using .env.example and add your API key."
    exit 1
fi

set -a
source .env
set +a

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -q -r requirements.txt
if [[ "${1:-}" == "--cli" ]]; then
    exec python main.py
fi
cd frontend
npm install --no-audit --no-fund
npm run build
cd ..
exec python server.py
