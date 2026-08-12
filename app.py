from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "university_apps.sqlite3"

app = FastAPI(title="University Application Command Center", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with closing(db()) as conn:
        conn.executescript(schema)
        conn.commit()


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


@app.get("/api/context")
def export_context():
    """Machine-readable application state for Ruflo/Codex/Claude agents."""
    with closing(db()) as conn:
        universities = [dict(x) for x in conn.execute("SELECT * FROM universities").fetchall()]
        scholarships = [dict(x) for x in conn.execute("SELECT * FROM scholarships").fetchall()]
        documents = [dict(x) for x in conn.execute("SELECT * FROM documents").fetchall()]
        tasks = [dict(x) for x in conn.execute("SELECT * FROM agent_tasks").fetchall()]
    return {
        "generated_at": datetime.now().isoformat(),
        "universities": universities,
        "scholarships": scholarships,
        "documents": documents,
        "agent_tasks": tasks,
    }


@app.get("/health")
def health():
    return {"ok": True}
