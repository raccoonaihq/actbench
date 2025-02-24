DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS api_keys;

CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    agent TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    latency_ms INTEGER,
    response TEXT
);

CREATE TABLE api_keys (
    agent TEXT PRIMARY KEY,
    key TEXT NOT NULL
);