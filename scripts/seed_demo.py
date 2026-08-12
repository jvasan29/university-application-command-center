from contextlib import closing
from app import db, init_db


def main():
    init_db()
    with closing(db()) as conn:
        examples = [
            ("Example University A", "United States", None, None, "", "researching"),
            ("Example University B", "United States", None, None, "", "drafting"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO universities(name,country,application_deadline,scholarship_deadline,application_url,status) VALUES(?,?,?,?,?,?)",
            examples,
        )
        conn.execute(
            "INSERT INTO agent_tasks(agent,objective,payload,status) VALUES(?,?,?,?)",
            ("research-scout", "Find and verify the first-year application deadline for Example University A.", "Use official admissions sources only.", "queued"),
        )
        conn.commit()
    print("Demo data seeded.")


if __name__ == "__main__":
    main()
