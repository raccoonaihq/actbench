import sqlite3
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from .base import BaseDatabase


class SQLiteDatabase(BaseDatabase):
    def __init__(self, db_path: str = "./results.db"):
        self.db_path = Path(db_path)
        self.conn = None
        self.schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        if self.conn is None:
            self.connect()
        assert self.conn is not None, "Database is not connected. Call connect() first."
        return self.conn.execute(query, params)

    def _commit(self):
        if self.conn is None:
            self.connect()
        assert self.conn is not None
        self.conn.commit()

    def init_db(self) -> None:
        if self.conn is None:
            self.connect()
        with open(self.schema_path, 'r') as f:
            self.conn.executescript(f.read())
        self.close()

    def insert_result(self, task_id: str, agent: str, success: bool, latency_ms: int, response: str = None) -> None:
        self._execute(
            "INSERT INTO results (task_id, agent, success, latency_ms, response) VALUES (?, ?, ?, ?, ?)",
            (task_id, agent, success, latency_ms, response),
        )
        self._commit()

    def get_all_results(self) -> List[Dict[str, Any]]:
        cursor = self._execute("SELECT * FROM results ORDER BY timestamp DESC")
        return [dict(row) for row in cursor.fetchall()]

    def clear_results(self) -> None:
        self._execute("DELETE FROM results")
        self._commit()

    def insert_api_key(self, agent: str, key: str) -> None:
        self._execute("INSERT OR REPLACE INTO api_keys (agent, key) VALUES (?, ?)", (agent, key))
        self._commit()

    def get_api_key(self, agent: str) -> Optional[str]:
        cursor = self._execute("SELECT key FROM api_keys WHERE agent = ?", (agent,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_api_keys(self) -> Dict[str, str]:
        cursor = self._execute("SELECT agent, key FROM api_keys")
        return {row['agent']: row['key'] for row in cursor.fetchall()}

    def delete_api_key(self, agent: str) -> None:
        self._execute("DELETE FROM api_keys WHERE agent = ?", (agent,))
        self._commit()


_DB_INSTANCE = SQLiteDatabase()
if not _DB_INSTANCE.db_path.exists():
    _DB_INSTANCE.init_db()
