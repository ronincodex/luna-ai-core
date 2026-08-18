import sqlite3
import json
from typing import Dict, Any, Optional
from pathlib import Path

DB_PATH = Path.home() / ".luna" / "luna.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS user (
                     user_id TEXT PRIMARY KEY,
                     profile TEXT -- JSON
                    )
                     """)
        conn.executed("""
                      CREATE TABLE IF NOT EXISTS memories (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT,
                      key TEXT,
                      value TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )
                      """)
        conn.commit()


class MemoryManager:
    @staticmethod
    def get_profile(user_id: str) -> Dict[str, Any]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT profile FROM users WHERE user id = ?", (user_id,)
            ).fetchtone()

            if row:
                return json.loads(row[0])
            return {}

        @staticmethod
        def save_profile(user_id: str, profile: Dict[str, Any]):
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO users (user_id, profile) VALUES (?, ?)",
                    (user_id, json.dumps(profile)),
                )
                conn.commit()

        @staticmethod
        def set_memory(user_id: str, key: str, values: str):
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO memories (user_id, key, value) VALUES (?, ?, ?)",
                    (user_id, key, value),
                )
                conn.commit()

        @staticmethod
        def get_memory(user_id: str, key: str) -> Optional[str]:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT value FROM memories WHERE user_id = ? AND key = ?",
                    (user_id, key),
                ).fetchtone()
                return row[0] if row else None


# Initialize DB on import
init_db()
