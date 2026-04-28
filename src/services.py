"""
Service helpers for the Study Planner app.

This module prepares subject and task data for display in the Streamlit UI.
It also calculates dashboard metrics, subject progress, upcoming deadlines,
and a special list of important academic due dates.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd


def normalize_subjects_df(subjects: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert raw subject records into a clean pandas DataFrame.

    Data coming from SQLite is returned as dictionaries. Before using it in
    charts, tables, or calculations, we normalize the types so the rest of
    the app can work with predictable values.
    """
    df = pd.DataFrame(subjects)

    # Return an empty DataFrame with known columns so later code
    # can still safely reference these column names.
    if df.empty:
        return pd.DataFrame(
            columns=["id", "name", "exam_date", "target_hours", "difficulty", "created_at"]
        )

    # Convert subject IDs to integers so joins/lookups work reliably.
    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)

    # Convert target study hours to numeric values so they can be summed or charted.
    if "target_hours" in df.columns:
        df["target_hours"] = pd.to_numeric(df["target_hours"], errors="coerce").fillna(0.0)

    # Convert exam dates into Python date objects for deadline comparisons.
    if "exam_date" in df.columns:
        df["exam_date"] = pd.to_datetime(df["exam_date"], errors="coerce").dt.date

    # Convert created_at into datetime for possible sorting or future analysis.
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    return df


def normalize_tasks_df(tasks: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert raw task records into a clean pandas DataFrame.

    The dashboard, filters, charts, and tables all depend on task data having
    consistent types. This function makes sure IDs are integers, dates are real
    dates, numbers are numeric, and text fields are safe to search.
    """
    df = pd.DataFrame(tasks)

    # Return an empty DataFrame with expected columns so the UI
    # can still render without crashing when there are no tasks.
    if df.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "subject_id",
                "title",
                "description",
                "topic",
                "status",
                "priority",
                "deadline",
                "estimated_hours",
                "actual_hours",
                "created_at",
                "updated_at",
            ]
        )

    # IDs should be integers for comparisons and subject/task matching.
    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)

    if "subject_id" in df.columns:
        df["subject_id"] = pd.to_numeric(df["subject_id"], errors="coerce").fillna(0).astype(int)

    # estimated hours should be numeric so totals and remaining workload
    # can be calculated correctly.
    if "estimated_hours" in df.columns:
        df["estimated_hours"] = pd.to_numeric(df["estimated_hours"], errors="coerce").fillna(0.0)

    # actual_hours is still normalized because it may exist in the database
    # even if it is not heavily used in the current UI.
    if "actual_hours" in df.columns:
        df["actual_hours"] = pd.to_numeric(df["actual_hours"], errors="coerce").fillna(0.0)

    # Deadlines are converted to date objects so we can compare them to today.
    if "deadline" in df.columns:
        df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce").dt.date

    # these fields are converted to datetime to support recent-task sorting.
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    if "updated_at" in df.columns:
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    # Text columns are forced into safe strings so searching and filtering
    # do not fail because of None values.
    for column in ["title", "description", "topic", "status", "priority"]:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str)

    return df


def build_dashboard_metrics(tasks: list[dict[str, Any]]) -> dict[str, float | int]:
    """
    Calculate the main dashboard summary metrics.

    Returns:
    - total number of tasks
    - number of completed tasks
    - number of overdue tasks
    - total estimated hours left for unfinished tasks
    """
    df = normalize_tasks_df(tasks)

    # When there are no tasks, return default zero values

    if df.empty:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "hours_left": 0.0,
        }

    today = date.today()

    total_tasks = len(df)

    # Completed tasks are tasks whose status is exactly "Done".
    completed_tasks = len(df[df["status"] == "Done"])

    # Overdue tasks are unfinished tasks whose deadline has already passed.
    overdue_tasks = len(df[(df["status"] != "Done") & (df["deadline"] < today)])

    # Hours left are based on unfinished tasks only.
    hours_left = df[df["status"] != "Done"]["estimated_hours"].sum()

    return {
        "total_tasks": int(total_tasks),
        "completed_tasks": int(completed_tasks),
        "overdue_tasks": int(overdue_tasks),
        "hours_left": float(hours_left),
    }


def build_subject_progress(subjects: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Build progress percentages for each subject.

    Progress is calculated as:
    completed subject tasks / total subject tasks * 100
    """
    subject_df = normalize_subjects_df(subjects)
    task_df = normalize_tasks_df(tasks)

    rows: list[dict[str, Any]] = []

    # Loop through each subject and calculate how much of its work is done.
    for _, subject in subject_df.iterrows():
        subject_tasks = task_df[task_df["subject_id"] == subject["id"]]
        total_tasks = len(subject_tasks)

        # If a subject has no tasks yet, progress is 0%.
        if total_tasks == 0:
            progress_percent = 0.0
        else:
            done_tasks = len(subject_tasks[subject_tasks["status"] == "Done"])
            progress_percent = round((done_tasks / total_tasks) * 100, 1)

        rows.append(
            {
                "subject_id": int(subject["id"]),
                "subject_name": str(subject["name"]),
                "progress_percent": progress_percent,
            }
        )

    return pd.DataFrame(rows)


def get_upcoming_deadlines(tasks: list[dict[str, Any]], days: int = 7) -> pd.DataFrame:
    """
    Return unfinished tasks due within the next given number of days.

    Default window:
    7 days
    """
    df = normalize_tasks_df(tasks)

    if df.empty:
        return pd.DataFrame(columns=["Task", "Status", "Priority", "Deadline", "Days Left"])

    today = date.today()
    end_date = today + timedelta(days=days)

    # Keep only tasks that:
    # - are not completed
    # - have a valid deadline
    # - are due between today and the end of the selected window
    df = df[
        (df["status"] != "Done")
        & (df["deadline"].notna())
        & (df["deadline"] >= today)
        & (df["deadline"] <= end_date)
    ].copy()

    if df.empty:
        return pd.DataFrame(columns=["Task", "Status", "Priority", "Deadline", "Days Left"])

    # Days Left helps users quickly see urgency.
    df["Days Left"] = df["deadline"].apply(lambda x: (x - today).days)

    # Sort by nearest deadline first.
    df = df.sort_values("deadline")

    result = df[["title", "status", "priority", "deadline", "Days Left"]].copy()
    result.columns = ["Task", "Status", "Priority", "Deadline", "Days Left"]
    return result


def build_important_due_dates(
    subjects: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    days: int = 30,
) -> pd.DataFrame:
    """
    Build a combined list of important academic due dates.

    This section combines:
    - subject exam dates
    - tasks whose text suggests they are major academic items
      such as quizzes, assignments, projects, labs, or finals

    The result is sorted by urgency and priority.
    """
    subject_df = normalize_subjects_df(subjects)
    task_df = normalize_tasks_df(tasks)

    today = date.today()
    end_date = today + timedelta(days=days)

    rows: list[dict[str, Any]] = []

    # Create a quick lookup from subject_id to subject_name so task rows
    # can display a readable subject name in the final table.
    subject_map: dict[int, str] = {}
    for _, subject in subject_df.iterrows():
        subject_map[int(subject["id"])] = str(subject["name"])

    # Add upcoming exam dates from the subjects table.
    if not subject_df.empty:
        exam_rows = subject_df[
            subject_df["exam_date"].notna()
            & (subject_df["exam_date"] >= today)
            & (subject_df["exam_date"] <= end_date)
        ]

        for _, row in exam_rows.iterrows():
            due_date = row["exam_date"]
            rows.append(
                {
                    "Type": "Exam",
                    "Subject": str(row["name"]),
                    "Title": f'{row["name"]} exam',
                    "Due Date": due_date,
                    "Priority": "High",
                    "Days Left": (due_date - today).days,
                }
            )

    # Add important task deadlines based on academic keywords.
    if not task_df.empty:
        keywords = r"exam|midterm|final|quiz|assignment|homework|project|lab|report|presentation"

        # Combine multiple text fields so a task can be detected as important
        # even if the keyword appears in the description or topic instead of title.
        text_to_search = (
            task_df["title"].fillna("")
            + " "
            + task_df["topic"].fillna("")
            + " "
            + task_df["description"].fillna("")
        )

        important_tasks = task_df[
            task_df["deadline"].notna()
            & (task_df["deadline"] >= today)
            & (task_df["deadline"] <= end_date)
            & text_to_search.str.contains(keywords, case=False, regex=True)
        ]

        for _, row in important_tasks.iterrows():
            due_date = row["deadline"]
            rows.append(
                {
                    "Type": "Task",
                    "Subject": subject_map.get(int(row["subject_id"]), "Unknown"),
                    "Title": str(row["title"]),
                    "Due Date": due_date,
                    "Priority": str(row["priority"]),
                    "Days Left": (due_date - today).days,
                }
            )

    # Return an empty but correctly structured table if nothing matched.
    if not rows:
        return pd.DataFrame(columns=["Type", "Subject", "Title", "Due Date", "Priority", "Days Left"])

    result = pd.DataFrame(rows)

    # Lower rank means higher importance in sorting.
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    result["priority_rank"] = result["Priority"].map(priority_order).fillna(3)

    # Sort by closest due date first, then by priority, then by title.
    result = result.sort_values(["Days Left", "priority_rank", "Title"])
    result = result.drop(columns=["priority_rank"])

    return result[["Type", "Subject", "Title", "Due Date", "Priority", "Days Left"]]