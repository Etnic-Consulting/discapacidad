#!/usr/bin/env bash
# Launch SMT-ONIC framework dashboard on :8097
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
exec streamlit run dashboard.py --server.port 8097 --server.headless true --server.address 127.0.0.1
