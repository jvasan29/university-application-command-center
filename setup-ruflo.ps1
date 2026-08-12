$ErrorActionPreference = "Stop"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js 20+ is required." }
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { throw "npx is required." }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python is required." }

Write-Host "Installing Python dependencies..."
python -m pip install -r requirements.txt

Write-Host "Initializing Ruflo..."
npx ruflo@latest init wizard
npx ruflo@latest doctor

if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "Registering University Application Command Center MCP bridge..."
    claude mcp add uacc -- python mcp_server.py
    Write-Host "MCP bridge registered as 'uacc'."
} else {
    Write-Warning "Claude Code CLI was not found. Install/configure Claude Code, then run: claude mcp add uacc -- python mcp_server.py"
}

Write-Host "Done. Start the dashboard with: uvicorn app:app --reload"
Write-Host "Then read ruflo/WORKFLOW.md and use its research prompt in Claude Code."
