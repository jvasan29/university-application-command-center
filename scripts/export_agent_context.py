import json
from contextlib import closing
from datetime import datetime
from pathlib import Path
from app import db, init_db

OUT = Path("agent-context.json")


def main():
    init_db()
    with closing(db()) as conn:
        payload = {
            "generated_at": datetime.now().isoformat(),
            "universities": [dict(x) for x in conn.execute("SELECT * FROM universities").fetchall()],
            "scholarships": [dict(x) for x in conn.execute("SELECT * FROM scholarships").fetchall()],
            "documents": [dict(x) for x in conn.execute("SELECT * FROM documents").fetchall()],
            "agent_tasks": [dict(x) for x in conn.execute("SELECT * FROM agent_tasks").fetchall()],
        }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
