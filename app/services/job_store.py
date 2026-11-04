"""Stores job posts and their embeddings in SQLite (free, no server needed).
Later this can be swapped for pgvector/ChromaDB without changing the API."""
import json
import sqlite3
from datetime import datetime, timezone


class JobStore:
    def __init__(self, db_path: str = "jobs.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                description TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        self.conn.commit()

    def add(self, title: str, company: str, description: str, embedding: list[float]) -> int:
        cur = self.conn.execute(
            "INSERT INTO jobs (title, company, description, embedding, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, company, description, json.dumps(embedding), datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_all(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, title, company, description, created_at FROM jobs ORDER BY id DESC")
        return [dict(r) for r in rows]

    def all_with_embeddings(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, title, company, description, embedding FROM jobs")
        return [{**dict(r), "embedding": json.loads(r["embedding"])} for r in rows]

    def delete(self, job_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        self.conn.commit()
        return cur.rowcount > 0
