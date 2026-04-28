# =========================
# File: src/repository.py
# =========================
from __future__ import annotations

from typing import Any, Optional

from src.database import get_connection


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def add_subject(name: str, exam_date: Optional[str], target_hours: float, difficulty: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO subjects (name, exam_date, target_hours, difficulty)
            VALUES (?, ?, ?, ?)
            """,
            (name, exam_date, target_hours, difficulty),
        )
        conn.commit()


def fetch_subjects() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, exam_date, target_hours, difficulty, created_at
            FROM subjects
            ORDER BY name ASC
            """
        ).fetchall()
    return _rows_to_dicts(rows)


def get_subject_by_id(subject_id: int) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, exam_date, target_hours, difficulty, created_at
            FROM subjects
            WHERE id = ?
            """,
            (subject_id,),
        ).fetchone()
    return dict(row) if row else None


def add_task(
    subject_id: int,
    title: str,
    description: str,
    topic: str,
    status: str,
    priority: str,
    deadline: str,
    estimated_hours: float,
    actual_hours: float,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks (
                subject_id, title, description, topic, status, priority,
                deadline, estimated_hours, actual_hours
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subject_id,
                title,
                description,
                topic,
                status,
                priority,
                deadline,
                estimated_hours,
                actual_hours,
            ),
        )
        conn.commit()


def fetch_tasks() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, subject_id, title, description, topic, status, priority,
                deadline, estimated_hours, actual_hours, created_at, updated_at
            FROM tasks
            ORDER BY deadline ASC, created_at DESC
            """
        ).fetchall()
    return _rows_to_dicts(rows)


def update_task_status(task_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, task_id),
        )
        conn.commit()


def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
