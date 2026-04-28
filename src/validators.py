# =========================
# File: src/validators.py
# =========================
from __future__ import annotations


def validate_subject_input(name: str, target_hours: float) -> list[str]:
    errors: list[str] = []

    if not name or not name.strip():
        errors.append("Subject name is required.")

    if target_hours < 0:
        errors.append("Target study hours cannot be negative.")

    return errors


def validate_task_input(title: str, estimated_hours: float, actual_hours: float) -> list[str]:
    errors: list[str] = []

    if not title or not title.strip():
        errors.append("Task title is required.")

    if estimated_hours < 0:
        errors.append("Estimated hours cannot be negative.")

    if actual_hours < 0:
        errors.append("Actual hours cannot be negative.")

    if actual_hours > estimated_hours and estimated_hours > 0:
        errors.append("Actual hours should not exceed estimated hours for a new task.")

    return errors