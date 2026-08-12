CREATE TABLE IF NOT EXISTS universities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  country TEXT NOT NULL DEFAULT 'United States',
  application_deadline TEXT,
  scholarship_deadline TEXT,
  application_url TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'researching',
  notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS scholarships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  university_id INTEGER,
  name TEXT NOT NULL,
  deadline TEXT,
  amount TEXT DEFAULT '',
  form_url TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'to_check',
  FOREIGN KEY(university_id) REFERENCES universities(id)
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'missing',
  notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS essays (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  university_id INTEGER,
  prompt TEXT NOT NULL,
  draft TEXT DEFAULT '',
  feedback TEXT DEFAULT '',
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(university_id) REFERENCES universities(id)
);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent TEXT NOT NULL,
  objective TEXT NOT NULL,
  payload TEXT DEFAULT '',
  result TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER,
  university_id INTEGER,
  proposal_type TEXT NOT NULL CHECK (proposal_type IN ('university_field','scholarship')),
  field_name TEXT DEFAULT '',
  proposed_value TEXT DEFAULT '',
  scholarship_name TEXT DEFAULT '',
  deadline TEXT,
  amount TEXT DEFAULT '',
  form_url TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  source_url TEXT NOT NULL,
  evidence TEXT DEFAULT '',
  checked_at TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.8,
  submitted_by TEXT NOT NULL DEFAULT 'ruflo-agent',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TEXT,
  FOREIGN KEY(task_id) REFERENCES agent_tasks(id),
  FOREIGN KEY(university_id) REFERENCES universities(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_status_agent ON agent_tasks(status, agent, created_at);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON research_proposals(status, created_at);

INSERT OR IGNORE INTO documents(name,status,notes) VALUES
('Passport','missing','Identity document'),
('School transcript','missing','Latest official/unofficial transcript'),
('Predicted grades','missing','If required by university'),
('English proficiency proof','missing','Check waiver/requirements'),
('Recommendation letters','missing','Track teacher/counselor requests'),
('Activities list / résumé','missing','Master activity bank'),
('Financial aid documents','missing','If applying for need-based aid');
