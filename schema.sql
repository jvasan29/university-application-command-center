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

INSERT OR IGNORE INTO documents(name,status,notes) VALUES
('Passport','missing','Identity document'),
('School transcript','missing','Latest official/unofficial transcript'),
('Predicted grades','missing','If required by university'),
('English proficiency proof','missing','Check waiver/requirements'),
('Recommendation letters','missing','Track teacher/counselor requests'),
('Activities list / résumé','missing','Master activity bank'),
('Financial aid documents','missing','If applying for need-based aid');
