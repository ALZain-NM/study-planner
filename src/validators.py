"""
Validation helpers for the Study Planner app.

This module checks user input before subjects or tasks are saved to the database.
It returns a list of user-friendly error messages so the UI can display them clearly.
"""

from __future__ import annotations


def validate_subject_input(name: str, target_hours: float) -> list[str]:
    """Validate subject form input and return any errors found."""
    errors: list[str] = []

    # A subject must have a visible, non-empty name.
    if not name or not name.strip():
        errors.append("Subject name is required.")

    # Negative study hours do not make sense for planning.
    if target_hours < 0:
        errors.append("Target study hours cannot be negative.")

    return errors


def validate_task_input(title: str, estimated_hours: float) -> list[str]:
    """Validate task form input and return any errors found."""
    errors: list[str] = []

    # A task should always have a name so it can be identified in the planner.
    if not title or not title.strip():
        errors.append("Task title is required.")

    # Estimated hours should represent planned work, so they cannot be negative.
    if estimated_hours < 0:
        errors.append("Estimated hours cannot be negative.")

    return errors