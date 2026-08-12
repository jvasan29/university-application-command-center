# University Application Command Center

A local-first application tracker designed to work with a **Ruflo multi-agent swarm**.

## What it does

- Tracks universities, application deadlines, status, and official links
- Tracks scholarships separately from admissions deadlines
- Tracks core application documents
- Queues tasks for specialized AI agents
- Exposes application state at `GET /api/context` for agent workflows
- Includes six Ruflo-oriented agent role prompts and a verification-first workflow

## Agent team

| Agent | Job |
|---|---|
| `research-scout` | Official admissions research |
| `scholarship-analyst` | Scholarships, forms, eligibility, deadlines |
| `requirements-auditor` | School-by-school document checklist |
| `essay-critic` | Essay feedback without replacing student voice |
| `deadline-planner` | Internal schedule and collision detection |
| `verification-lead` | Final factual QA gate |

## Run the dashboard

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

Optional demo data:

```bash
python scripts/seed_demo.py
```

## Initialize Ruflo

Install Node.js first, then from this repository:

```bash
npx ruflo init
```

Read `ruflo/WORKFLOW.md` for the recommended swarm and orchestration prompt.

## Important design choice

The MVP uses a **verification gate**. Agents can research and propose facts, but deadlines and eligibility should be checked against official university pages before you rely on them. Admissions rules change by entry year and applicant type.

## Next upgrades

1. OAuth and multi-user profiles
2. Essay version history UI
3. Direct Common App / email / calendar integrations where permitted
4. Source-citation table and automatic stale-source alerts
5. Ruflo worker that consumes `agent_tasks` and writes results into a review queue
6. Notifications for 14/30/60-day deadlines
