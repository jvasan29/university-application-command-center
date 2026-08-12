from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "university_apps.sqlite3"

app = FastAPI(title="University Application Command Center", version="0.2.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

ALLOWED_UNIVERSITY_FIELDS = {
    "application_deadline",
    "scholarship_deadline",
    "application_url",
    "notes",
}


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with closing(db()) as conn:
        conn.executescript(schema)
        conn.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_deadline(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def deadline_status(value: str | None) -> dict:
    d = parse_deadline(value)
    if d is None:
        return {"label": "No date", "class": "muted", "days": None}
    days = (d - date.today()).days
    if days < 0:
        return {"label": f"{abs(days)}d overdue", "class": "danger", "days": days}
    if days <= 14:
        return {"label": f"{days}d left", "class": "danger", "days": days}
    if days <= 45:
        return {"label": f"{days}d left", "class": "warning", "days": days}
    return {"label": f"{days}d left", "class": "success", "days": days}


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def get_university(university_id: int) -> dict | None:
    with closing(db()) as conn:
        row = conn.execute("SELECT * FROM universities WHERE id=?", (university_id,)).fetchone()
    return dict(row) if row else None


def queue_research_bundle(university_id: int) -> int:
    university = get_university(university_id)
    if not university:
        raise ValueError("University not found")

    payload = json.dumps(
        {
            "university_id": university_id,
            "university": university["name"],
            "country": university["country"],
            "entry_cycle": "next undergraduate entry cycle",
            "verification_policy": "official university sources only",
        }
    )
    tasks = [
        (
            "research-scout",
            f"Research official undergraduate application deadline(s), scholarship consideration deadline, and official application URL for {university['name']}.",
            payload,
        ),
        (
            "scholarship-analyst",
            f"Find scholarships at {university['name']} relevant to international undergraduate applicants. Capture automatic vs separate application, deadline, amount, and official URL.",
            payload,
        ),
        (
            "verification-lead",
            f"Review proposals submitted for {university['name']} and flag conflicts, stale pages, or applicant-type ambiguity.",
            payload,
        ),
    ]
    with closing(db()) as conn:
        conn.executemany(
            "INSERT INTO agent_tasks(agent,objective,payload,status,created_at) VALUES(?,?,?,?,datetime('now'))",
            [(agent, objective, payload, "queued") for agent, objective, payload in tasks],
        )
        conn.commit()
    return len(tasks)


def claim_next_task(agent: str) -> dict | None:
    """Atomically claim the oldest queued task for an agent."""
    with closing(db()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM agent_tasks WHERE agent=? AND status='queued' ORDER BY created_at, id LIMIT 1",
            (agent,),
        ).fetchone()
        if not row:
            conn.commit()
            return None
        conn.execute("UPDATE agent_tasks SET status='running' WHERE id=?", (row["id"],))
        conn.commit()
    result = dict(row)
    result["status"] = "running"
    return result


def finish_task(task_id: int, result: str, status: str = "complete") -> dict:
    if status not in {"complete", "failed"}:
        raise ValueError("Invalid task status")
    with closing(db()) as conn:
        row = conn.execute("SELECT * FROM agent_tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise ValueError("Task not found")
        conn.execute(
            "UPDATE agent_tasks SET result=?, status=? WHERE id=?",
            (result, status, task_id),
        )
        conn.commit()
    return {"task_id": task_id, "status": status}


def create_proposal(
    *,
    proposal_type: str,
    source_url: str,
    evidence: str,
    submitted_by: str,
    university_id: int | None = None,
    task_id: int | None = None,
    field_name: str = "",
    proposed_value: str = "",
    scholarship_name: str = "",
    deadline: str = "",
    amount: str = "",
    form_url: str = "",
    notes: str = "",
    checked_at: str = "",
    confidence: float = 0.8,
) -> dict:
    if proposal_type not in {"university_field", "scholarship"}:
        raise ValueError("proposal_type must be university_field or scholarship")
    if not valid_http_url(source_url):
        raise ValueError("source_url must be an http(s) URL")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if university_id is not None and not get_university(university_id):
        raise ValueError("University not found")
    if proposal_type == "university_field":
        if field_name not in ALLOWED_UNIVERSITY_FIELDS:
            raise ValueError(f"Unsupported field: {field_name}")
        if not proposed_value.strip():
            raise ValueError("proposed_value is required")
        if field_name.endswith("deadline") and parse_deadline(proposed_value) is None:
            raise ValueError("Deadline values must use YYYY-MM-DD")
    if proposal_type == "scholarship":
        if university_id is None:
            raise ValueError("Scholarship proposals require university_id")
        if not scholarship_name.strip():
            raise ValueError("scholarship_name is required")
        if deadline and parse_deadline(deadline) is None:
            raise ValueError("Scholarship deadline must use YYYY-MM-DD")
        if form_url and not valid_http_url(form_url):
            raise ValueError("form_url must be an http(s) URL")

    checked = checked_at.strip() or now_iso()
    with closing(db()) as conn:
        cur = conn.execute(
            """
            INSERT INTO research_proposals(
                task_id, university_id, proposal_type, field_name, proposed_value,
                scholarship_name, deadline, amount, form_url, notes, source_url,
                evidence, checked_at, confidence, submitted_by, status, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            """,
            (
                task_id,
                university_id,
                proposal_type,
                field_name.strip(),
                proposed_value.strip(),
                scholarship_name.strip(),
                deadline or None,
                amount.strip(),
                form_url.strip(),
                notes.strip(),
                source_url.strip(),
                evidence.strip(),
                checked,
                confidence,
                submitted_by.strip() or "ruflo-agent",
                "pending",
            ),
        )
        proposal_id = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM research_proposals WHERE id=?", (proposal_id,)).fetchone()
    return dict(row)


def review_proposal(proposal_id: int, decision: str) -> dict:
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")

    with closing(db()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM research_proposals WHERE id=?", (proposal_id,)).fetchone()
        if not row:
            conn.rollback()
            raise ValueError("Proposal not found")
        if row["status"] != "pending":
            conn.rollback()
            raise ValueError("Proposal has already been reviewed")

        if decision == "approved":
            if row["proposal_type"] == "university_field":
                field = row["field_name"]
                if field not in ALLOWED_UNIVERSITY_FIELDS:
                    conn.rollback()
                    raise ValueError("Unsupported university field")
                conn.execute(
                    f"UPDATE universities SET {field}=? WHERE id=?",
                    (row["proposed_value"], row["university_id"]),
                )
            elif row["proposal_type"] == "scholarship":
                conn.execute(
                    """
                    INSERT INTO scholarships(university_id,name,deadline,amount,form_url,notes,status)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        row["university_id"],
                        row["scholarship_name"],
                        row["deadline"],
                        row["amount"],
                        row["form_url"] or row["source_url"],
                        row["notes"],
                        "verified",
                    ),
                )

        conn.execute(
            "UPDATE research_proposals SET status=?, reviewed_at=datetime('now') WHERE id=?",
            (decision, proposal_id),
        )
        conn.commit()
    return {"proposal_id": proposal_id, "status": decision}


class ClaimRequest(BaseModel):
    agent: str = Field(min_length=1, max_length=80)


class TaskFinishRequest(BaseModel):
    result: str = ""


class ProposalRequest(BaseModel):
    proposal_type: str
    source_url: str
    evidence: str = ""
    submitted_by: str = "ruflo-agent"
    university_id: int | None = None
    task_id: int | None = None
    field_name: str = ""
    proposed_value: str = ""
    scholarship_name: str = ""
    deadline: str = ""
    amount: str = ""
    form_url: str = ""
    notes: str = ""
    checked_at: str = ""
    confidence: float = 0.8


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with closing(db()) as conn:
        universities = conn.execute(
            "SELECT * FROM universities ORDER BY COALESCE(application_deadline, '9999-12-31')"
        ).fetchall()
        scholarships = conn.execute(
            "SELECT s.*, u.name AS university_name FROM scholarships s LEFT JOIN universities u ON u.id=s.university_id ORDER BY COALESCE(s.deadline, '9999-12-31')"
        ).fetchall()
        documents = conn.execute("SELECT * FROM documents ORDER BY name").fetchall()
        tasks = conn.execute(
            "SELECT * FROM agent_tasks ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'queued' THEN 1 ELSE 2 END, created_at DESC"
        ).fetchall()
        proposals = conn.execute(
            """
            SELECT p.*, u.name AS university_name
            FROM research_proposals p
            LEFT JOIN universities u ON u.id=p.university_id
            ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END, p.created_at DESC
            """
        ).fetchall()

    enriched_universities = []
    for row in universities:
        item = dict(row)
        item["deadline_meta"] = deadline_status(item["application_deadline"])
        enriched_universities.append(item)

    enriched_scholarships = []
    for row in scholarships:
        item = dict(row)
        item["deadline_meta"] = deadline_status(item["deadline"])
        enriched_scholarships.append(item)

    stats = {
        "universities": len(universities),
        "applications_ready": sum(1 for x in universities if x["status"] in {"ready", "submitted"}),
        "scholarships": len(scholarships),
        "documents_complete": sum(1 for x in documents if x["status"] == "complete"),
        "documents_total": len(documents),
        "pending_proposals": sum(1 for x in proposals if x["status"] == "pending"),
    }
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "universities": enriched_universities,
            "scholarships": enriched_scholarships,
            "documents": documents,
            "tasks": tasks,
            "proposals": proposals,
        },
    )


@app.post("/universities")
def add_university(
    name: str = Form(...),
    country: str = Form("United States"),
    application_deadline: str = Form(""),
    scholarship_deadline: str = Form(""),
    application_url: str = Form(""),
):
    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO universities(name,country,application_deadline,scholarship_deadline,application_url,status) VALUES(?,?,?,?,?,?)",
            (name.strip(), country.strip(), application_deadline or None, scholarship_deadline or None, application_url.strip(), "researching"),
        )
        conn.commit()
    return RedirectResponse("/#universities", status_code=303)


@app.post("/universities/{university_id}/research")
def research_university(university_id: int):
    try:
        queue_research_bundle(university_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse("/#agents", status_code=303)


@app.post("/universities/{university_id}/status")
def update_university_status(university_id: int, status: str = Form(...)):
    allowed = {"researching", "drafting", "ready", "submitted", "decision"}
    if status in allowed:
        with closing(db()) as conn:
            conn.execute("UPDATE universities SET status=? WHERE id=?", (status, university_id))
            conn.commit()
    return RedirectResponse("/#universities", status_code=303)


@app.post("/scholarships")
def add_scholarship(
    university_id: Optional[int] = Form(None),
    name: str = Form(...),
    deadline: str = Form(""),
    amount: str = Form(""),
    form_url: str = Form(""),
    notes: str = Form(""),
):
    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO scholarships(university_id,name,deadline,amount,form_url,notes,status) VALUES(?,?,?,?,?,?,?)",
            (university_id, name.strip(), deadline or None, amount.strip(), form_url.strip(), notes.strip(), "to_check"),
        )
        conn.commit()
    return RedirectResponse("/#scholarships", status_code=303)


@app.post("/documents/{document_id}/toggle")
def toggle_document(document_id: int):
    with closing(db()) as conn:
        row = conn.execute("SELECT status FROM documents WHERE id=?", (document_id,)).fetchone()
        if row:
            next_status = "complete" if row["status"] != "complete" else "missing"
            conn.execute("UPDATE documents SET status=? WHERE id=?", (next_status, document_id))
            conn.commit()
    return RedirectResponse("/#documents", status_code=303)


@app.post("/agent-tasks")
def add_agent_task(agent: str = Form(...), objective: str = Form(...), payload: str = Form("")):
    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO agent_tasks(agent,objective,payload,status,created_at) VALUES(?,?,?,?,datetime('now'))",
            (agent.strip(), objective.strip(), payload.strip(), "queued"),
        )
        conn.commit()
    return RedirectResponse("/#agents", status_code=303)


@app.post("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: int):
    try:
        review_proposal(proposal_id, "approved")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/#proposals", status_code=303)


@app.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: int):
    try:
        review_proposal(proposal_id, "rejected")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/#proposals", status_code=303)


@app.get("/api/context")
def export_context():
    """Machine-readable application state for Ruflo/Codex/Claude agents."""
    with closing(db()) as conn:
        universities = [dict(x) for x in conn.execute("SELECT * FROM universities").fetchall()]
        scholarships = [dict(x) for x in conn.execute("SELECT * FROM scholarships").fetchall()]
        documents = [dict(x) for x in conn.execute("SELECT * FROM documents").fetchall()]
        tasks = [dict(x) for x in conn.execute("SELECT * FROM agent_tasks").fetchall()]
        proposals = [dict(x) for x in conn.execute("SELECT * FROM research_proposals").fetchall()]
    return {
        "generated_at": now_iso(),
        "universities": universities,
        "scholarships": scholarships,
        "documents": documents,
        "agent_tasks": tasks,
        "research_proposals": proposals,
    }


@app.post("/api/agent-tasks/claim")
def api_claim_task(body: ClaimRequest):
    return {"task": claim_next_task(body.agent)}


@app.post("/api/agent-tasks/{task_id}/complete")
def api_complete_task(task_id: int, body: TaskFinishRequest):
    try:
        return finish_task(task_id, body.result, "complete")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/agent-tasks/{task_id}/fail")
def api_fail_task(task_id: int, body: TaskFinishRequest):
    try:
        return finish_task(task_id, body.result, "failed")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/proposals")
def api_list_proposals(status: str = "pending"):
    with closing(db()) as conn:
        if status == "all":
            rows = conn.execute("SELECT * FROM research_proposals ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM research_proposals WHERE status=? ORDER BY created_at DESC", (status,)
            ).fetchall()
    return {"proposals": [dict(x) for x in rows]}


@app.post("/api/proposals")
def api_create_proposal(body: ProposalRequest):
    try:
        proposal = create_proposal(**body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"proposal": proposal}


@app.get("/health")
def health():
    return {"ok": True, "version": app.version}
