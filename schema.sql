CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL
        CHECK (length(trim(title)) BETWEEN 1 AND 500),
    created_at TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    ),
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_open
ON tasks(completed_at, id);