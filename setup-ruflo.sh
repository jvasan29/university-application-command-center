#!/usr/bin/env bash
set -euo pipefail
command -v node >/dev/null || { echo "Node.js 20+ is required."; exit 1; }
command -v npx >/dev/null || { echo "npx is required."; exit 1; }
command -v python >/dev/null || { echo "Python is required."; exit 1; }

python -m pip install -r requirements.txt
npx ruflo@latest init wizard
npx ruflo@latest doctor

if command -v claude >/dev/null; then
  claude mcp add uacc -- python mcp_server.py
  echo "Registered MCP bridge as 'uacc'."
else
  echo "Claude Code CLI not found. Later run: claude mcp add uacc -- python mcp_server.py"
fi

echo "Start dashboard: uvicorn app:app --reload"
echo "Then follow ruflo/WORKFLOW.md."
