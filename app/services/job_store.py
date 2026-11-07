"""SQLite storage (free, no server needed): saved jobs + their embeddings, and a cache of AI results.
Each visitor's jobs are kept separate by an anonymous browser id (`owner`)."""
import json
import sqlite3
import threading
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    def __init__(self, db_path: str = "jobs.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.conn.executescript(
            """CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                description TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_cache (
                key TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            );"""
        )
        # Upgrade databases made before jobs had an owner.
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(jobs)")}
        if "owner" not in cols:
            self.conn.execute("ALTER TABLE jobs ADD COLUMN owner TEXT NOT NULL DEFAULT 'public'")
        self.conn.commit()

    # --- jobs ---
    def add(self, owner: str, title: str, company: str, description: str, embedding: list[float]) -> int:
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO jobs (owner, title, company, description, embedding, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (owner, title, company, description, json.dumps(embedding), _now()),
            )
            self.conn.commit()
            return cur.lastrowid

    def list_all(self, owner: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, company, description, created_at FROM jobs WHERE owner = ? ORDER BY id DESC", (owner,)
        )
        return [dict(r) for r in rows]

    def all_with_embeddings(self, owner: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, company, description, embedding FROM jobs WHERE owner = ?", (owner,)
        )
        return [{**dict(r), "embedding": json.loads(r["embedding"])} for r in rows]

    def delete(self, owner: str, job_id: int) -> bool:
        with self.lock:
            cur = self.conn.execute("DELETE FROM jobs WHERE id = ? AND owner = ?", (job_id, owner))
            self.conn.commit()
            return cur.rowcount > 0

    # --- AI result cache (saves free-tier quota) ---
    def cache_get(self, key: str) -> dict | None:
        row = self.conn.execute("SELECT result FROM ai_cache WHERE key = ?", (key,)).fetchone()
        return json.loads(row["result"]) if row else None

    def cache_set(self, key: str, result: dict) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO ai_cache (key, result, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(result), _now()),
            )
            self.conn.commit()
