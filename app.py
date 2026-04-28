# =========================
# File: app.py
# =========================
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ai_service import generate_study_plan
from src.database import init_db
from src.repository import (
    add_subject,
    add_task,
    delete_task,
    fetch_subjects,
    fetch_tasks,
    get_subject_by_id,
    update_task_status,
)
from src.services import (
    build_dashboard_metrics,
    build_subject_progress,
    build_task_dataframe,
    get_upcoming_deadlines,
)
from src.validators import validate_subject_input, validate_task_input


st.set_page_config(page_title="Study Planner", layout="wide")


def _init() -> None:
    init_db()


def render_sidebar() -> str:
    st.sidebar.title("Study Planner")
    return st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Add Subject", "Add Task", "Manage Tasks", "AI Study Assistant"],
    )


def render_dashboard() -> None:
    st.title("Study Planner Dashboard")

    subjects = fetch_subjects()
    tasks = fetch_tasks()

    metrics = build_dashboard_metrics(tasks)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tasks", metrics["total_tasks"])
    c2.metric("Completed", metrics["completed_tasks"])
    c3.metric("Overdue", metrics["overdue_tasks"])
    c4.metric("Hours Left", f'{metrics["hours_left"]:.1f}')

    if not tasks:
        st.info("No tasks yet. Add a subject, then add tasks.")
        return

    task_df = build_task_dataframe(tasks)

    col1, col2 = st.columns(2)

    with col1:
        status_counts = task_df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count", title="Tasks by Status")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        subject_progress = build_subject_progress(subjects, tasks)
        if not subject_progress.empty:
            fig = px.bar(
                subject_progress,
                x="subject_name",
                y="progress_percent",
                title="Progress by Subject",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Upcoming Deadlines")
    upcoming = get_upcoming_deadlines(tasks)
    if upcoming.empty:
        st.success("No upcoming deadlines in the next 7 days.")
    else:
        st.dataframe(upcoming, use_container_width=True, hide_index=True)


def render_add_subject() -> None:
    st.title("Add Subject")

    with st.form("add_subject_form", clear_on_submit=True):
        name = st.text_input("Subject Name")
        exam_date = st.date_input("Exam Date", value=None)
        target_hours = st.number_input("Target Study Hours", min_value=0.0, step=1.0)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        submitted = st.form_submit_button("Add Subject")

        if submitted:
            errors = validate_subject_input(name=name, target_hours=target_hours)
            if errors:
                for error in errors:
                    st.error(error)
                return

            add_subject(
                name=name.strip(),
                exam_date=exam_date.isoformat() if exam_date else None,
                target_hours=target_hours,
                difficulty=difficulty,
            )
            st.success("Subject added successfully.")


def render_add_task() -> None:
    st.title("Add Task")

    subjects = fetch_subjects()
    if not subjects:
        st.warning("Add at least one subject before adding tasks.")
        return

    subject_options = {f'{s["name"]} (ID {s["id"]})': s["id"] for s in subjects}

    with st.form("add_task_form", clear_on_submit=True):
        subject_label = st.selectbox("Subject", list(subject_options.keys()))
        title = st.text_input("Task Title")
        description = st.text_area("Description")
        topic = st.text_input("Topic")
        status = st.selectbox("Status", ["Planned", "In Progress", "Done"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        deadline = st.date_input("Deadline", value=date.today())
        estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5)
        actual_hours = st.number_input("Actual Hours", min_value=0.0, step=0.5)

        submitted = st.form_submit_button("Add Task")

        if submitted:
            errors = validate_task_input(
                title=title,
                estimated_hours=estimated_hours,
                actual_hours=actual_hours,
            )
            if errors:
                for error in errors:
                    st.error(error)
                return

            subject_id = subject_options[subject_label]
            add_task(
                subject_id=subject_id,
                title=title.strip(),
                description=description.strip(),
                topic=topic.strip(),
                status=status,
                priority=priority,
                deadline=deadline.isoformat(),
                estimated_hours=estimated_hours,
                actual_hours=actual_hours,
            )
            st.success("Task added successfully.")


def render_manage_tasks() -> None:
    st.title("Manage Tasks")

    subjects = fetch_subjects()
    tasks = fetch_tasks()

    if not tasks:
        st.info("No tasks found.")
        return

    subject_map = {s["id"]: s["name"] for s in subjects}
    df = build_task_dataframe(tasks)
    df["subject_name"] = df["subject_id"].map(subject_map)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        search = st.text_input("Search")
    with c2:
        subject_filter = st.selectbox("Subject", ["All"] + sorted(df["subject_name"].dropna().unique().tolist()))
    with c3:
        status_filter = st.selectbox("Status", ["All"] + sorted(df["status"].dropna().unique().tolist()))
    with c4:
        sort_by = st.selectbox("Sort By", ["deadline", "priority", "title", "status"])

    filtered = df.copy()

    if search:
        mask = (
            filtered["title"].str.contains(search, case=False, na=False)
            | filtered["description"].str.contains(search, case=False, na=False)
            | filtered["topic"].str.contains(search, case=False, na=False)
            | filtered["subject_name"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    if subject_filter != "All":
        filtered = filtered[filtered["subject_name"] == subject_filter]

    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    if sort_by == "priority":
        filtered = filtered.assign(priority_rank=filtered["priority"].map(priority_order)).sort_values("priority_rank")
        filtered = filtered.drop(columns=["priority_rank"])
    else:
        filtered = filtered.sort_values(sort_by)

    st.dataframe(
        filtered[
            [
                "id",
                "subject_name",
                "title",
                "topic",
                "status",
                "priority",
                "deadline",
                "estimated_hours",
                "actual_hours",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Update Task Status")
    task_ids = filtered["id"].tolist()

    if task_ids:
        col1, col2 = st.columns([2, 2])
        with col1:
            selected_task_id = st.selectbox("Task ID", task_ids)
        with col2:
            new_status = st.selectbox("New Status", ["Planned", "In Progress", "Done"])

        if st.button("Update Status"):
            update_task_status(selected_task_id, new_status)
            st.success("Task status updated.")
            st.rerun()

        st.subheader("Delete Task")
        delete_id = st.selectbox("Select Task ID to Delete", task_ids, key="delete_task_id")
        if st.button("Delete Selected Task"):
            delete_task(delete_id)
            st.success("Task deleted.")
            st.rerun()


def render_ai_assistant() -> None:
    st.title("AI Study Assistant")

    subjects = fetch_subjects()
    if not subjects:
        st.warning("Add at least one subject first.")
        return

    subject_labels = {f'{s["name"]} (ID {s["id"]})': s["id"] for s in subjects}
    selected_label = st.selectbox("Choose Subject", list(subject_labels.keys()))
    subject_id = subject_labels[selected_label]
    subject = get_subject_by_id(subject_id)

    weak_topics = st.text_area("Weak Topics", placeholder="e.g. recursion, linked lists, sorting")
    weekly_hours = st.number_input("Available Study Hours Per Week", min_value=1.0, step=1.0, value=6.0)
    extra_notes = st.text_area("Extra Notes", placeholder="Anything else the planner should consider?")

    if st.button("Generate Study Plan"):
        if subject is None:
            st.error("Subject not found.")
            return

        result = generate_study_plan(
            subject_name=subject["name"],
            exam_date=subject["exam_date"],
            difficulty=subject["difficulty"],
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
        )
        st.markdown(result)


def main() -> None:
    _init()
    page = render_sidebar()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Add Subject":
        render_add_subject()
    elif page == "Add Task":
        render_add_task()
    elif page == "Manage Tasks":
        render_manage_tasks()
    elif page == "AI Study Assistant":
        render_ai_assistant()


if __name__ == "__main__":
    main()














