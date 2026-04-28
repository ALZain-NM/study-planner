
# =========================
# File: src/database.py
# =========================
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path("data")
DB_PATH = DB_DIR / "study_planner.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                exam_date TEXT,
                target_hours REAL NOT NULL DEFAULT 0,
                difficulty TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                topic TEXT DEFAULT '',
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                deadline TEXT NOT NULL,
                estimated_hours REAL NOT NULL DEFAULT 0,
                actual_hours REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects (id)
            )
            """
        )
        conn.commit()