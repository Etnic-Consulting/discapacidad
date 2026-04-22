#!/usr/bin/env bash
# Launch SMT-ONIC framework API on :8096
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
exec python -m uvicorn server:app --host 127.0.0.1 --port 8096 --reload
