# Ruflo workflow for the University Application Command Center

This project separates **application state** (the FastAPI/SQLite app) from **agent execution** (Ruflo + Claude Code/Codex).

## Recommended swarm

- `research-scout`: gathers official admissions facts
- `scholarship-analyst`: maps scholarship eligibility and forms
- `requirements-auditor`: builds per-school checklists
- `essay-critic`: critiques essays while preserving student voice
- `deadline-planner`: generates internal action dates
- `verification-lead`: validates claims before they are trusted

## Full Ruflo install

From the repository root:

```bash
npx ruflo init
```

Ruflo's full install provides the MCP server, hooks, memory, agent infrastructure and swarm capabilities. After initialization, copy the role prompts in `ruflo/agents/` into whatever agent-definition location the generated Ruflo/Claude setup expects for the installed version.

## Suggested orchestration prompt

```text
Create a hierarchical swarm for university-application operations.
Coordinator: verification-lead.
Workers: research-scout, scholarship-analyst, requirements-auditor, essay-critic, deadline-planner.
Read current application state from http://127.0.0.1:8000/api/context.
Never treat admissions facts as verified unless they come from official university sources.
For research tasks, store source URL and date checked.
Return proposed database changes as structured JSON for human review before writing them.
```

## Operating loop

1. Add universities and tasks in the dashboard.
2. Start the app: `uvicorn app:app --reload`.
3. Initialize Ruflo: `npx ruflo init`.
4. Ask the swarm to process queued tasks.
5. Verify results with `verification-lead`.
6. Enter approved facts into the dashboard.
7. Run `deadline-planner` weekly or after any deadline change.

## Why proposed changes are review-first
Admissions and scholarship information is high-impact and changes annually. The MVP deliberately does not let an autonomous agent overwrite trusted deadline data without review.
