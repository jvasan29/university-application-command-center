"""MCP bridge that lets Ruflo/Claude agents read and write the dashboard review queue."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app import (
    claim_next_task,
    create_proposal,
    export_context,
    finish_task,
    init_db,
)

init_db()

mcp = FastMCP(
    "University Application Command Center",
    instructions=(
        "Use these tools to process university research tasks. Only submit admissions facts from "
        "official university sources. Submit findings as proposals; never bypass human approval."
    ),
)


@mcp.tool()
def get_application_context() -> dict:
    """Read universities, scholarships, queued agent tasks, documents, and research proposals."""
    return export_context()


@mcp.tool()
def claim_task(agent: str) -> dict:
    """Claim the oldest queued dashboard task assigned to this agent role."""
    task = claim_next_task(agent)
    return {"task": task}


@mcp.tool()
def submit_university_fact(
    university_id: int,
    field_name: str,
    proposed_value: str,
    source_url: str,
    evidence: str,
    task_id: int | None = None,
    checked_at: str = "",
    confidence: float = 0.8,
    submitted_by: str = "research-scout",
) -> dict:
    """Submit a sourced deadline/link/note as a human-review proposal."""
    return create_proposal(
        proposal_type="university_field",
        university_id=university_id,
        task_id=task_id,
        field_name=field_name,
        proposed_value=proposed_value,
        source_url=source_url,
        evidence=evidence,
        checked_at=checked_at,
        confidence=confidence,
        submitted_by=submitted_by,
    )


@mcp.tool()
def submit_scholarship(
    university_id: int,
    scholarship_name: str,
    source_url: str,
    evidence: str,
    task_id: int | None = None,
    deadline: str = "",
    amount: str = "",
    form_url: str = "",
    notes: str = "",
    checked_at: str = "",
    confidence: float = 0.8,
    submitted_by: str = "scholarship-analyst",
) -> dict:
    """Submit a sourced scholarship as a human-review proposal."""
    return create_proposal(
        proposal_type="scholarship",
        university_id=university_id,
        task_id=task_id,
        scholarship_name=scholarship_name,
        deadline=deadline,
        amount=amount,
        form_url=form_url,
        notes=notes,
        source_url=source_url,
        evidence=evidence,
        checked_at=checked_at,
        confidence=confidence,
        submitted_by=submitted_by,
    )


@mcp.tool()
def complete_task(task_id: int, result: str) -> dict:
    """Mark a claimed task complete after its proposals have been submitted."""
    return finish_task(task_id, result, "complete")


@mcp.tool()
def fail_task(task_id: int, reason: str) -> dict:
    """Mark a claimed task failed and save a useful reason."""
    return finish_task(task_id, reason, "failed")


if __name__ == "__main__":
    mcp.run()
