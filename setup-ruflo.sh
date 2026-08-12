#!/usr/bin/env bash
set -euo pipefail
command -v node >/dev/null || { echo "Node.js is required."; exit 1; }
command -v npx >/dev/null || { echo "npx is required."; exit 1; }
echo "Initializing Ruflo in this repository..."
npx ruflo init
echo "Ruflo initialized. Next: read ruflo/WORKFLOW.md and adapt the role prompts under ruflo/agents/."
