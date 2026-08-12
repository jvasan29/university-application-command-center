import app as app_module


def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test.sqlite3"
    monkeypatch.setattr(app_module, "DB_PATH", test_db)
    app_module.init_db()
    with app_module.db() as conn:
        cur = conn.execute(
            "INSERT INTO universities(name,country,status) VALUES(?,?,?)",
            ("Example University", "United States", "researching"),
        )
        university_id = cur.lastrowid
        conn.commit()
    return university_id


def test_queue_and_claim_research_task(tmp_path, monkeypatch):
    university_id = setup_test_db(tmp_path, monkeypatch)
    assert app_module.queue_research_bundle(university_id) == 3

    task = app_module.claim_next_task("research-scout")
    assert task is not None
    assert task["status"] == "running"
    assert "Example University" in task["objective"]

    assert app_module.claim_next_task("research-scout") is None


def test_approve_university_deadline_proposal(tmp_path, monkeypatch):
    university_id = setup_test_db(tmp_path, monkeypatch)
    proposal = app_module.create_proposal(
        proposal_type="university_field",
        university_id=university_id,
        field_name="application_deadline",
        proposed_value="2027-01-05",
        source_url="https://example.edu/admissions/deadlines",
        evidence="Official admissions deadline table.",
        submitted_by="research-scout",
        confidence=0.95,
    )

    assert proposal["status"] == "pending"
    app_module.review_proposal(proposal["id"], "approved")

    with app_module.db() as conn:
        university = conn.execute("SELECT * FROM universities WHERE id=?", (university_id,)).fetchone()
        reviewed = conn.execute("SELECT * FROM research_proposals WHERE id=?", (proposal["id"],)).fetchone()

    assert university["application_deadline"] == "2027-01-05"
    assert reviewed["status"] == "approved"


def test_approve_scholarship_proposal(tmp_path, monkeypatch):
    university_id = setup_test_db(tmp_path, monkeypatch)
    proposal = app_module.create_proposal(
        proposal_type="scholarship",
        university_id=university_id,
        scholarship_name="International Merit Award",
        deadline="2026-12-01",
        amount="Up to $20,000",
        form_url="https://example.edu/scholarships/apply",
        notes="Separate application required.",
        source_url="https://example.edu/scholarships/international",
        evidence="Official scholarship page lists award and deadline.",
        submitted_by="scholarship-analyst",
        confidence=0.9,
    )

    app_module.review_proposal(proposal["id"], "approved")
    with app_module.db() as conn:
        scholarship = conn.execute(
            "SELECT * FROM scholarships WHERE university_id=? AND name=?",
            (university_id, "International Merit Award"),
        ).fetchone()

    assert scholarship is not None
    assert scholarship["status"] == "verified"
    assert scholarship["deadline"] == "2026-12-01"


def test_reject_does_not_apply(tmp_path, monkeypatch):
    university_id = setup_test_db(tmp_path, monkeypatch)
    proposal = app_module.create_proposal(
        proposal_type="university_field",
        university_id=university_id,
        field_name="application_deadline",
        proposed_value="2027-02-01",
        source_url="https://example.edu/admissions",
        evidence="Candidate fact.",
        submitted_by="research-scout",
    )
    app_module.review_proposal(proposal["id"], "rejected")

    with app_module.db() as conn:
        university = conn.execute("SELECT * FROM universities WHERE id=?", (university_id,)).fetchone()
    assert university["application_deadline"] is None
