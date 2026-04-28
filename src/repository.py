"""
Database access functions for the Study Planner app.

This module is responsible for reading and writing subject and task data.
It acts as a small data layer between the Streamlit UI and the SQLite database.
"""

from __future__ import annotations

from typing import Any, Optional

from src.database import get_connection


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    """
    Convert SQLite row objects into normal Python dictionaries.

    SQLite returns Row objects, but the rest of the app is handled as plain dictionaries.
    """
    return [dict(row) for row in rows]


def add_subject(name: str, exam_date: Optional[str], target_hours: float, difficulty: str) -> None:
    """
    Insert a new subject into the database.

    The subject stores the core planning information needed for the app:
    name, exam date, target study hours, and difficulty.
    """
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
    """
    Retrieve all subjects from the database.

    Subjects are ordered alphabetically by name so they appear in a clean,
    predictable order in dropdowns, tables, and the dashboard.
    """
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
    """
    Retrieve a single subject by its database ID.

    Returns:
    - the subject as a dictionary if found
    - None if the subject does not exist
    """
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
) -> None:
    """
    Insert a single task into the database.
    """
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
                0.0,
            ),
        )
        conn.commit()


def bulk_add_tasks(subject_id: int, tasks: list[dict[str, Any]]) -> None:
    """
    Insert multiple AI-generated tasks at once.

    This is used by the AI Study Assistant after it creates a study plan.
    Each generated study item becomes a normal task linked to the selected subject.
    """
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO tasks (
                subject_id, title, description, topic, status, priority,
                deadline, estimated_hours, actual_hours
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    subject_id,
                    str(task["title"]),
                    str(task.get("description", "")),
                    str(task.get("topic", "")),
                    str(task.get("status", "Planned")),
                    str(task.get("priority", "Medium")),
                    str(task["deadline"]),
                    float(task.get("estimated_hours", 1.0)),
                    0.0,
                )
                for task in tasks
            ],
        )
        conn.commit()


def fetch_tasks() -> list[dict[str, Any]]:
    """
    Retrieve all tasks from the database.

    Tasks are ordered by:
    1. nearest deadline first
    2. most recently created tasks first when deadlines are the same

    """
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


def get_task_by_id(task_id: int) -> Optional[dict[str, Any]]:
    """

    This is mainly used when the user selects a task to edit.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, subject_id, title, description, topic, status, priority,
                deadline, estimated_hours, actual_hours, created_at, updated_at
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()

    return dict(row) if row else None


def update_task(
    task_id: int,
    subject_id: int,
    title: str,
    description: str,
    topic: str,
    status: str,
    priority: str,
    deadline: str,
    estimated_hours: float,
) -> None:
    """
    Update an existing task.

    updated_at is refreshed automatically so the database records when
    the task was last changed.
    """
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET
                subject_id = ?,
                title = ?,
                description = ?,
                topic = ?,
                status = ?,
                priority = ?,
                deadline = ?,
                estimated_hours = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
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
                task_id,
            ),
        )
        conn.commit()


def update_task_status(task_id: int, status: str) -> None:
    """
    Update only the status of a task.

    This is used for quick status changes in the UI without editing the full task.
    """
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
    """
    Delete a task from the database.

    This permanently removes the selected task, so the UI should call this
    only when the user confirms deletion.
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()