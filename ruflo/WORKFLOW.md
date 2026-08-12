# Ruflo live-research workflow

The dashboard now has a **review-first live research bridge**. Ruflo/Claude agents can claim queued tasks, research official university pages, and submit structured findings directly into the dashboard without directly overwriting trusted data.

## Architecture

```text
Dashboard button
  -> SQLite agent_tasks
  -> Ruflo/Claude agent claims task via UACC MCP
  -> agent researches official university sources
  -> agent calls submit_university_fact / submit_scholarship
  -> research_proposals review queue
  -> human Approve / Reject
  -> approved fact is written to universities/scholarships
```

## 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 2. Start the dashboard

```bash
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

## 3. Initialize Ruflo

```bash
npx ruflo@latest init wizard
npx ruflo@latest doctor
```

Ruflo's full init gives Claude Code the swarm/MCP/hooks infrastructure. After init you can use Claude Code normally while Ruflo coordinates agents.

## 4. Register the dashboard MCP bridge

From the repository root:

```bash
claude mcp add uacc -- python mcp_server.py
```

If `python` does not point to your virtual environment, use the full interpreter path.

## 5. Queue research

In the dashboard, add a university and click **Research with Ruflo**. This queues:

- `research-scout`: application deadlines, scholarship consideration deadline, official application link
- `scholarship-analyst`: international-undergraduate scholarship opportunities
- `verification-lead`: conflict/staleness QA

## 6. Run the research swarm

Use this prompt in Claude Code after Ruflo is initialized:

```text
Use Ruflo to process University Application Command Center research tasks.

Create a hierarchical research swarm with research-scout, scholarship-analyst, and verification-lead roles.
Use the UACC MCP tools.

For each worker role:
1. Call claim_task with the role name.
2. If no task exists, report that role idle.
3. Parse the task payload to identify the university_id and university.
4. Research the task using official university-controlled websites only for factual admissions/scholarship claims.
5. For each supported university fact, call submit_university_fact with the exact source URL and concise evidence.
6. For each scholarship, call submit_scholarship with deadline, amount, form URL, eligibility/application notes, source URL, and evidence.
7. Never submit a deadline unless the official page clearly applies to the relevant undergraduate entry cycle/applicant type. If ambiguous, do not guess; describe the ambiguity in the task result.
8. When finished, call complete_task.

Do not directly edit the SQLite database or application source. All researched facts must enter through UACC MCP proposal tools so they require human approval.
```

## Human approval gate

Open **Research Review** in the dashboard. Every proposal contains university, proposed field/scholarship, official source URL, evidence, checked date, and agent confidence.

**Approve** applies it to the trusted application data. **Reject** preserves the audit trail but does not change application data.

## Supported automatic proposals

University fields: `application_deadline`, `scholarship_deadline`, `application_url`, `notes`.

Scholarships are added as verified records only after approval.
