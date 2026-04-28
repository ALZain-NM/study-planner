# =========================
# File: src/services.py
# =========================
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd


def build_task_dataframe(tasks: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(tasks)
    if df.empty:
        return df
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    return df


def build_dashboard_metrics(tasks: list[dict[str, Any]]) -> dict[str, float]:
    today = date.today()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task["status"] == "Done")
    overdue_tasks = sum(
        1
        for task in tasks
        if task["status"] != "Done" and datetime.fromisoformat(task["deadline"]).date() < today
    )
    hours_left = sum(max(float(task["estimated_hours"]) - float(task["actual_hours"]), 0.0) for task in tasks)

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "hours_left": hours_left,
    }


def build_subject_progress(subjects: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for subject in subjects:
        subject_tasks = [task for task in tasks if task["subject_id"] == subject["id"]]
        total = len(subject_tasks)
        done = sum(1 for task in subject_tasks if task["status"] == "Done")
        progress = round((done / total) * 100, 1) if total else 0.0
        rows.append(
            {
                "subject_id": subject["id"],
                "subject_name": subject["name"],
                "total_tasks": total,
                "completed_tasks": done,
                "progress_percent": progress,
            }
        )

    return pd.DataFrame(rows)


def get_upcoming_deadlines(tasks: list[dict[str, Any]]) -> pd.DataFrame:
    today = date.today()
    limit = today + timedelta(days=7)

    rows: list[dict[str, Any]] = []
    for task in tasks:
        deadline = datetime.fromisoformat(task["deadline"]).date()
        if today <= deadline <= limit and task["status"] != "Done":
            rows.append(
                {
                    "Task": task["title"],
                    "Status": task["status"],
                    "Priority": task["priority"],
                    "Deadline": deadline.isoformat(),
                }
            )

    return pd.DataFrame(rows)
