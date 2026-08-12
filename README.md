# University Application Command Center

A local-first university application tracker with a **Ruflo live-research bridge**.

## What it does now

- Tracks universities, deadlines, scholarships, documents, and application status
- Queues specialized Ruflo research tasks per university
- Exposes application state through both HTTP and MCP
- Lets agents claim queued research work
- Lets agents submit sourced deadline/scholarship proposals automatically
- Keeps a human approval gate before researched facts become trusted data
- Stores source URL, evidence, checked date, confidence, and agent identity

## Live research flow

1. Add a university.
2. Click **Research with Ruflo**.
3. Ruflo/Claude agents claim queued tasks through `mcp_server.py`.
4. Agents research official university sources.
5. Findings appear under **Research Review**.
6. Approve or reject each finding.
7. Approved deadlines and scholarships are written into the main tracker.

## Run the dashboard

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

## Windows Ruflo setup

After activating your virtual environment:

```powershell
.\setup-ruflo.ps1
```

Or manually:

```powershell
npx ruflo@latest init wizard
npx ruflo@latest doctor
claude mcp add uacc -- python mcp_server.py
```

Then read `ruflo/WORKFLOW.md` and paste its research swarm prompt into Claude Code.

## Agent team

| Agent | Job |
|---|---|
| `research-scout` | Official admissions deadlines and application links |
| `scholarship-analyst` | Scholarships, forms, eligibility, deadlines |
| `requirements-auditor` | School-by-school document checklist |
| `essay-critic` | Essay feedback without replacing student voice |
| `deadline-planner` | Internal schedule and collision detection |
| `verification-lead` | Final factual QA and conflict detection |

## MCP tools exposed to agents

- `get_application_context`
- `claim_task`
- `submit_university_fact`
- `submit_scholarship`
- `complete_task`
- `fail_task`

Agents cannot approve their own research through MCP. Approval stays in the dashboard.

## API endpoints

- `GET /api/context`
- `POST /api/agent-tasks/claim`
- `POST /api/agent-tasks/{id}/complete`
- `POST /api/agent-tasks/{id}/fail`
- `GET /api/proposals`
- `POST /api/proposals`

## Safety / accuracy model

Admissions and scholarship information changes annually and can differ for international applicants, specific colleges, and entry cycles. The system therefore separates **agent-proposed research** from **human-approved application data**.
