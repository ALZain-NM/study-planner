"""
Main Streamlit app for the Study Planner project.

This file is the main entry point of the application.
It is responsible for:
- setting up the Streamlit page
- showing the sidebar navigation
- loading data from the database
- displaying dashboard charts and tables
- handling subject and task forms
- handling AI study plan generation
"""

from __future__ import annotations

# date is used when we need a default date value, for example in task deadlines.
from datetime import date

# pandas is used for working with tables of data.
import pandas as pd

# plotly is used for charts in the dashboard.
import plotly.express as px

# streamlit is the framework used to build the app UI.
import streamlit as st

# option_menu is used to create the styled sidebar navigation.
from streamlit_option_menu import option_menu

# AI helper functions:
# - generate_study_plan creates the plan text
# - build_plan_tasks converts the plan into task records
from src.ai_service import build_plan_tasks, generate_study_plan

# init_db creates the database tables if they do not already exist.
from src.database import init_db

# Repository functions are used to read and write data in the database.
from src.repository import (
    add_subject,
    add_task,
    bulk_add_tasks,
    delete_task,
    fetch_subjects,
    fetch_tasks,
    get_subject_by_id,
    get_task_by_id,
    update_task,
    update_task_status,
)

# Service functions are used for calculations, table formatting, and dashboard logic.
from src.services import (
    build_dashboard_metrics,
    build_important_due_dates,
    build_subject_progress,
    get_upcoming_deadlines,
    normalize_subjects_df,
    normalize_tasks_df,
)

# Validation functions check user input before saving it.
from src.validators import validate_subject_input, validate_task_input

# This sets the browser tab title, page icon, and layout width.
st.set_page_config(page_title="Study Planner", page_icon="📘", layout="wide")

# This makes sure the database file and tables exist before the app starts running.
init_db()

# Streamlit reruns the script many times.
# session_state lets us keep values between reruns.
# We use it here to keep the AI-generated study plan visible after the user clicks buttons.

# This will store the generated markdown study plan text.
if "generated_plan_markdown" not in st.session_state:
    st.session_state["generated_plan_markdown"] = ""

# This will store the generated tasks created from the AI plan.
if "generated_plan_tasks" not in st.session_state:
    st.session_state["generated_plan_tasks"] = []

# This will store which subject the generated AI plan belongs to.
if "generated_plan_subject_id" not in st.session_state:
    st.session_state["generated_plan_subject_id"] = None


def apply_custom_css() -> None:
    """
    Add custom CSS styling to the app.

    Streamlit has default styling, but this function improves the look of:
    - page spacing
    - sidebar background
    - metric size
    - card layout
    """
    st.markdown(
        """
        <style>
        /* Add spacing around the main page content */
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1220px;
        }

        /* Change the sidebar background */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        /* Make dashboard metric numbers larger */
        div[data-testid="stMetricValue"] {
            font-size: 2.2rem;
        }

        /* Style for card-like sections on the page */
        .section-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            padding: 1rem 1rem 0.65rem 1rem;
            margin-bottom: 1rem;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }

        /* Style for the app title box in the sidebar */
        .sidebar-brand {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 1rem 1rem 0.9rem 1rem;
            border-radius: 18px;
            margin-bottom: 1rem;
        }

        /* Sidebar title text */
        .sidebar-brand h2 {
            margin: 0;
            font-size: 1.55rem;
        }

        /* Sidebar subtitle text */
        .sidebar-brand p {
            margin: 0.35rem 0 0 0;
            color: rgba(255,255,255,0.88);
            font-size: 0.92rem;
        }

        /* Grid layout for sidebar stats */
        .sidebar-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.6rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        /* Each small stat box in the sidebar */
        .sidebar-stat-box {
            background: white;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 14px;
            padding: 0.75rem 0.8rem;
            text-align: center;
        }

        /* Large number inside the stat box */
        .sidebar-stat-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111827;
            line-height: 1.1;
        }

        /* Label under the stat number */
        .sidebar-stat-label {
            font-size: 0.82rem;
            color: #6b7280;
            margin-top: 0.18rem;
        }

        /* Small tip box at the bottom of the sidebar */
        .sidebar-tip {
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 14px;
            padding: 0.9rem;
            margin-top: 1rem;
            color: #475569;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(subjects: list[dict], tasks: list[dict]) -> str:
    """
    Show the sidebar and return the selected page.

    Parameters:
    - subjects: list of subject records from the database
    - tasks: list of task records from the database

    Returns:
    - the name of the page the user selected
    """
    # st.sidebar means everything inside this block appears in the sidebar.
    with st.sidebar:
        # Show app branding at the top of the sidebar.
        st.markdown(
            """
            <div class="sidebar-brand">
                <h2>📘 Study Planner</h2>
                <p>Plan smarter. Track progress. Stay ready.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show quick counts so the user can see how much data is in the app.
        st.markdown(
            f"""
            <div class="sidebar-stats">
                <div class="sidebar-stat-box">
                    <div class="sidebar-stat-value">{len(subjects)}</div>
                    <div class="sidebar-stat-label">Subjects</div>
                </div>
                <div class="sidebar-stat-box">
                    <div class="sidebar-stat-value">{len(tasks)}</div>
                    <div class="sidebar-stat-label">Tasks</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # option_menu creates the navigation menu in the sidebar.
        selected = option_menu(
            menu_title="Navigation",
            options=[
                "Dashboard",
                "Subjects",
                "Add Subject",
                "Add Task",
                "Manage Tasks",
                "AI Study Assistant",
            ],
            icons=[
                "speedometer2",
                "collection",
                "bookmark-plus",
                "plus-square",
                "check2-square",
                "robot",
            ],
            menu_icon="list",
            default_index=0,
            styles={
                # Style the menu container
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent",
                },
                # Style the icons
                "icon": {
                    "color": "#2563eb",
                    "font-size": "17px",
                },
                # Style normal menu items
                "nav-link": {
                    "font-size": "16px",
                    "font-weight": "600",
                    "text-align": "left",
                    "margin": "6px 0",
                    "padding": "12px 14px",
                    "border-radius": "12px",
                    "--hover-color": "#dbeafe",
                    "color": "#1f2937",
                },
                # Style the selected menu item
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, #2563eb 0%, #7c3aed 100%)",
                    "color": "white",
                },
                # Style the menu title
                "menu-title": {
                    "font-size": "16px",
                    "font-weight": "700",
                    "color": "#334155",
                },
            },
        )

        # Show a helpful tip below the navigation.
        st.markdown(
            """
            <div class="sidebar-tip">
                <strong>Tip:</strong><br>
                Generate a study plan, then add it as tasks in one click.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Return the selected page so the main function knows which page to show.
    return selected


def dashboard_page(subjects: list[dict], tasks: list[dict]) -> None:
    """
    Show the main dashboard page.

    This page gives the user a summary of all study data.
    """
    # Page title at the top.
    st.title("Study Planner Dashboard")

    # Clean the raw subject and task data.
    # This makes it easier to use in tables and charts.
    subject_df = normalize_subjects_df(subjects)
    task_df = normalize_tasks_df(tasks)

    # Build the summary numbers for the top metric cards.
    metrics = build_dashboard_metrics(tasks)

    # Create 4 columns for the 4 main metrics.
    c1, c2, c3, c4 = st.columns(4)

    # Show the metric cards.
    c1.metric("Total Tasks", metrics["total_tasks"])
    c2.metric("Completed", metrics["completed_tasks"])
    c3.metric("Overdue", metrics["overdue_tasks"])
    c4.metric("Hours Left", f'{metrics["hours_left"]:.1f}')

    # Create two columns for overview sections.
    top1, top2 = st.columns([1.4, 1.2])

    with top1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Overview")

        # If there are no subjects, show a message.
        if subject_df.empty:
            st.info("No subjects yet. Start by adding a subject.")
        else:
            # Pick only a few useful columns for display.
            overview_df = subject_df[["name", "difficulty", "exam_date", "target_hours"]].copy()

            # Rename columns to nicer labels.
            overview_df.columns = ["Subject", "Difficulty", "Exam Date", "Target Hours"]

            # Show the subject table.
            st.dataframe(overview_df, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with top2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Quick Stats")

        # Count tasks by status using generator expressions.
        st.write(f"**Subjects:** {len(subjects)}")
        st.write(f"**Planned Tasks:** {sum(1 for task in tasks if task['status'] == 'Planned')}")
        st.write(f"**In Progress:** {sum(1 for task in tasks if task['status'] == 'In Progress')}")
        st.write(f"**Done:** {sum(1 for task in tasks if task['status'] == 'Done')}")

        st.markdown("</div>", unsafe_allow_html=True)

    # Important due dates section.
    # This is useful for showing exams, quizzes, assignments, etc.
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Important Due Dates")

    # Get important due dates for the next 30 days.
    important_df = build_important_due_dates(subjects, tasks, days=30)

    # Show a message if no important deadlines were found.
    if important_df.empty:
        st.info("No important exams, midterms, quizzes, or assignments due in the next 30 days.")
    else:
        # Show the table of important due dates.
        st.dataframe(important_df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # If there are no tasks yet, do not try to make charts.
    if task_df.empty:
        st.info("No tasks yet. Add a subject, then add tasks.")
        return

    # Create 2 columns for the first row of charts.
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Tasks by Status")

        # Count how many tasks belong to each status.
        status_counts = task_df["status"].value_counts().reset_index()

        # Rename columns for the chart.
        status_counts.columns = ["status", "count"]

        # Create a pie chart.
        fig = px.pie(status_counts, names="status", values="count")

        # Show the chart.
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Progress by Subject")

        # Calculate the progress percentage for each subject.
        progress_df = build_subject_progress(subjects, tasks)

        # If there is no data, show a message.
        if progress_df.empty:
            st.info("No progress data yet.")
        else:
            # Create a bar chart.
            fig = px.bar(progress_df, x="subject_name", y="progress_percent")

            # Show the chart.
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Create 2 columns for the lower row.
    lower1, lower2 = st.columns(2)

    with lower1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Upcoming Deadlines")

        # Get tasks due soon.
        upcoming_df = get_upcoming_deadlines(tasks)

        # If no tasks are due soon, show a message.
        if upcoming_df.empty:
            st.success("No upcoming deadlines in the next 7 days.")
        else:
            # Show the table.
            st.dataframe(upcoming_df, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with lower2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Recent Tasks")

        # Sort tasks so the newest ones appear first.
        recent_df = task_df.sort_values(["created_at", "deadline"], ascending=[False, True]).head(5)

        # If no recent tasks exist, show a message.
        if recent_df.empty:
            st.info("No recent tasks.")
        else:
            # Keep only the columns we want to show.
            recent_df = recent_df[["title", "status", "priority", "deadline"]].copy()

            # Rename columns.
            recent_df.columns = ["Task", "Status", "Priority", "Deadline"]

            # Show the table.
            st.dataframe(recent_df, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)


def subjects_page(subjects: list[dict], tasks: list[dict]) -> None:
    """
    Show the subjects page.

    This page lists all subjects and shows progress for each one.
    """
    st.title("Subjects")

    # If there are no subjects, show a message and stop.
    if not subjects:
        st.info("No subjects yet. Add your first subject.")
        return

    # Build progress data for all subjects.
    progress_df = build_subject_progress(subjects, tasks)

    # This dictionary will map subject IDs to progress percentages.
    progress_map: dict[int, float] = {}

    # Fill the progress map if data exists.
    if not progress_df.empty:
        for _, row in progress_df.iterrows():
            progress_map[int(row["subject_id"])] = float(row["progress_percent"])

    # Clean subject data.
    subject_df = normalize_subjects_df(subjects)

    # Add a new column for subject progress.
    subject_df["progress_percent"] = subject_df["id"].map(progress_map).fillna(0.0)

    # Select columns for display.
    display_df = subject_df[["name", "difficulty", "exam_date", "target_hours", "progress_percent"]].copy()

    # Rename columns.
    display_df.columns = ["Subject", "Difficulty", "Exam Date", "Target Hours", "Progress %"]

    # Create 2 columns: one for the table and one for the chart.
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("All Subjects")

        # Show all subjects in a table.
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Target Hours by Subject")

        # Create a bar chart showing target hours for each subject.
        fig = px.bar(subject_df, x="name", y="target_hours")

        # Show the chart.
        st.plotly_chart(fig, use_container_width=True)


def add_subject_page() -> None:
    """
    Show the page for adding a new subject.
    """
    st.title("Add Subject")

    # Create a Streamlit form for subject input.
    with st.form("add_subject_form", clear_on_submit=True):
        # Use columns to place inputs side by side.
        col1, col2 = st.columns(2)

        with col1:
            # Subject name text input.
            name = st.text_input("Subject Name")

            # Target study hours number input.
            target_hours = st.number_input("Target Study Hours", min_value=0.0, step=1.0)

        with col2:
            # Exam date input.
            exam_date = st.date_input("Exam Date", value=None)

            # Difficulty dropdown.
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        # Form submit button.
        submitted = st.form_submit_button("Add Subject")

        # Only run this block if the form is submitted.
        if submitted:
            # Check the user input first.
            errors = validate_subject_input(name=name, target_hours=target_hours)

            # If there are validation errors, show them.
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save the subject to the database.
                add_subject(
                    name=name.strip(),
                    exam_date=exam_date.isoformat() if exam_date else None,
                    target_hours=target_hours,
                    difficulty=difficulty,
                )

                # Show success message.
                st.success("Subject added successfully.")

                # Rerun so the page updates immediately.
                st.rerun()


def add_task_page(subjects: list[dict]) -> None:
    """
    Show the page for adding a new task.
    """
    st.title("Add Task")

    # A task must belong to a subject.
    # If there are no subjects, stop here.
    if not subjects:
        st.warning("Add at least one subject before adding tasks.")
        return

    # Build a dropdown dictionary:
    # key = label shown to user
    # value = subject id
    subject_options = {f'{subject["name"]} (ID {subject["id"]})': subject["id"] for subject in subjects}

    # Create the task form.
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # Subject selection.
            subject_label = st.selectbox("Subject", list(subject_options.keys()))

            # Task title input.
            title = st.text_input("Task Title")

            # Topic input.
            topic = st.text_input("Topic")

            # Estimated hours input.
            estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5)

        with col2:
            # Status dropdown.
            status = st.selectbox("Status", ["Planned", "In Progress", "Done"])

            # Priority dropdown.
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])

            # Deadline date input.
            deadline = st.date_input("Deadline", value=date.today())

        # Description box under the columns.
        description = st.text_area("Description")

        # Submit button.
        submitted = st.form_submit_button("Add Task")

        if submitted:
            # Validate the task data before saving it.
            errors = validate_task_input(title=title, estimated_hours=estimated_hours)

            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save the task to the database.
                add_task(
                    subject_id=subject_options[subject_label],
                    title=title.strip(),
                    description=description.strip(),
                    topic=topic.strip(),
                    status=status,
                    priority=priority,
                    deadline=deadline.isoformat(),
                    estimated_hours=estimated_hours,
                )

                # Show success message.
                st.success("Task added successfully.")

                # Refresh the page.
                st.rerun()


def manage_tasks_page(subjects: list[dict], tasks: list[dict]) -> None:
    """
    Show the page for managing tasks.

    This page allows the user to:
    - search tasks
    - filter tasks
    - sort tasks
    - edit tasks
    - update task status
    - delete tasks
    """
    st.title("Manage Tasks")

    # If there are no tasks, show a message and stop.
    if not tasks:
        st.info("No tasks found.")
        return

    # Create a map from subject_id to subject name.
    subject_map = {int(subject["id"]): subject["name"] for subject in subjects}

    # Clean the task data and add subject names.
    task_df = normalize_tasks_df(tasks)
    task_df["subject_name"] = task_df["subject_id"].map(subject_map)

    # Create 4 columns for search/filter/sort controls.
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        search = st.text_input("Search")

    with f2:
        subject_filter = st.selectbox(
            "Subject",
            ["All"] + sorted(task_df["subject_name"].dropna().unique().tolist()),
        )

    with f3:
        status_filter = st.selectbox(
            "Status",
            ["All"] + sorted(task_df["status"].dropna().unique().tolist()),
        )

    with f4:
        sort_by = st.selectbox("Sort By", ["deadline", "priority", "title", "status"])

    # Start with a full copy of the task data.
    filtered_df = task_df.copy()

    # Search across title, description, topic, and subject name.
    if search:
        mask = (
            filtered_df["title"].astype(str).str.contains(search, case=False, na=False)
            | filtered_df["description"].astype(str).str.contains(search, case=False, na=False)
            | filtered_df["topic"].astype(str).str.contains(search, case=False, na=False)
            | filtered_df["subject_name"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    # Filter by subject if chosen.
    if subject_filter != "All":
        filtered_df = filtered_df[filtered_df["subject_name"] == subject_filter]

    # Filter by status if chosen.
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    # Custom sorting order for priority.
    priority_order = {"High": 0, "Medium": 1, "Low": 2}

    if sort_by == "priority":
        # Add a helper column for sorting priority.
        filtered_df = filtered_df.assign(priority_rank=filtered_df["priority"].map(priority_order))

        # Sort using the helper column.
        filtered_df = filtered_df.sort_values("priority_rank")

        # Remove the helper column after sorting.
        filtered_df = filtered_df.drop(columns=["priority_rank"])
    else:
        # Normal sorting for other columns.
        filtered_df = filtered_df.sort_values(sort_by)

    st.subheader("Task List")

    # Select only the columns we want to show.
    display_df = filtered_df[
        [
            "id",
            "subject_name",
            "title",
            "topic",
            "status",
            "priority",
            "deadline",
            "estimated_hours",
        ]
    ].copy()

    # Rename columns to nicer labels.
    display_df.columns = [
        "ID",
        "Subject",
        "Title",
        "Topic",
        "Status",
        "Priority",
        "Deadline",
        "Est. Hours",
    ]

    # Show the task table.
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Save the IDs of visible tasks.
    task_ids = filtered_df["id"].tolist()

    # If nothing matched the filters, stop here.
    if not task_ids:
        st.warning("No tasks match the current filters.")
        return

    st.subheader("Edit Task")

    # Let the user select which task to edit.
    selected_task_id = st.selectbox("Select Task ID", task_ids, key="edit_task_id")

    # Load the selected task from the database.
    task = get_task_by_id(int(selected_task_id))

    if task:
        # Create subject dropdown options for the edit form.
        subject_options = {f'{subject["name"]} (ID {subject["id"]})': int(subject["id"]) for subject in subjects}

        # Find the current subject label of this task.
        current_subject_label = next(
            label for label, value in subject_options.items() if value == int(task["subject_id"])
        )

        # Create the edit form.
        with st.form("edit_task_form"):
            col1, col2 = st.columns(2)

            with col1:
                edited_subject_label = st.selectbox(
                    "Subject",
                    list(subject_options.keys()),
                    index=list(subject_options.keys()).index(current_subject_label),
                )
                edited_title = st.text_input("Task Title", value=str(task["title"]))
                edited_topic = st.text_input("Topic", value=str(task["topic"] or ""))
                edited_estimated_hours = st.number_input(
                    "Estimated Hours",
                    min_value=0.0,
                    step=0.5,
                    value=float(task["estimated_hours"]),
                )

            with col2:
                edited_status = st.selectbox(
                    "Status",
                    ["Planned", "In Progress", "Done"],
                    index=["Planned", "In Progress", "Done"].index(task["status"]),
                )
                edited_priority = st.selectbox(
                    "Priority",
                    ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(task["priority"]),
                )
                edited_deadline = st.date_input(
                    "Deadline",
                    value=pd.to_datetime(task["deadline"]).date(),
                )

            # Description field below the columns.
            edited_description = st.text_area("Description", value=str(task["description"] or ""))

            # Submit button for saving task changes.
            save_changes = st.form_submit_button("Save Changes")

            if save_changes:
                # Validate the edited task before updating it.
                errors = validate_task_input(
                    title=edited_title,
                    estimated_hours=edited_estimated_hours,
                )

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Save the updated task.
                    update_task(
                        task_id=int(selected_task_id),
                        subject_id=subject_options[edited_subject_label],
                        title=edited_title.strip(),
                        description=edited_description.strip(),
                        topic=edited_topic.strip(),
                        status=edited_status,
                        priority=edited_priority,
                        deadline=edited_deadline.isoformat(),
                        estimated_hours=edited_estimated_hours,
                    )

                    # Show success message.
                    st.success("Task updated successfully.")

                    # Refresh the page.
                    st.rerun()

    st.subheader("Quick Status Update")

    # This section lets the user change only the status quickly.
    quick_task_id = st.selectbox("Task ID", task_ids, key="quick_status_task_id")
    quick_status = st.selectbox("New Status", ["Planned", "In Progress", "Done"])

    if st.button("Update Status"):
        update_task_status(int(quick_task_id), quick_status)
        st.success("Task status updated.")
        st.rerun()

    st.subheader("Delete Task")

    # This section deletes a chosen task.
    delete_task_id = st.selectbox("Task ID to Delete", task_ids, key="delete_task_id")

    if st.button("Delete Task"):
        delete_task(int(delete_task_id))
        st.success("Task deleted.")
        st.rerun()


def ai_study_assistant_page(subjects: list[dict]) -> None:
    """
    Show the AI Study Assistant page.

    This page lets the user generate a study plan and save it as tasks.
    """
    st.title("AI Study Assistant")
    st.write("Generate a study plan and add it as tasks automatically.")

    # The AI plan must be linked to a subject.
    if not subjects:
        st.warning("Add at least one subject first.")
        return

    # Create subject options for the dropdown.
    subject_options = {f'{subject["name"]} (ID {subject["id"]})': int(subject["id"]) for subject in subjects}

    # Let the user choose the subject.
    selected_label = st.selectbox("Choose Subject", list(subject_options.keys()))
    subject_id = subject_options[selected_label]

    # Get the full subject record from the database.
    subject = get_subject_by_id(subject_id)

    # Create 2 columns for input fields.
    col1, col2 = st.columns(2)

    with col1:
        # Topics the user finds difficult.
        weak_topics = st.text_area("Weak Topics", placeholder="e.g. recursion, linked lists, joins")

        # How many hours per week the user can study.
        weekly_hours = st.number_input(
            "Available Study Hours Per Week",
            min_value=1.0,
            step=1.0,
            value=6.0,
        )

    with col2:
        # How many weeks of plan to create.
        plan_weeks = st.number_input(
            "How many weeks to generate",
            min_value=1,
            max_value=12,
            value=4,
            step=1,
        )

        # Extra notes that may affect the plan.
        extra_notes = st.text_area("Extra Notes", placeholder="Any constraints or priorities?")

    # Generate plan when button is clicked.
    if st.button("Generate Study Plan"):
        if subject is None:
            st.error("Subject not found.")
        else:
            # Generate the study plan text.
            markdown = generate_study_plan(
                subject_name=str(subject["name"]),
                exam_date=subject["exam_date"],
                difficulty=str(subject["difficulty"]),
                weak_topics=weak_topics,
                weekly_hours=weekly_hours,
                extra_notes=extra_notes,
                weeks=int(plan_weeks),
            )

            # Turn the study plan into task data.
            plan_tasks = build_plan_tasks(
                subject_name=str(subject["name"]),
                weak_topics=weak_topics,
                weeks=int(plan_weeks),
                weekly_hours=weekly_hours,
            )

            # Save the generated results in session state.
            st.session_state["generated_plan_markdown"] = markdown
            st.session_state["generated_plan_tasks"] = plan_tasks
            st.session_state["generated_plan_subject_id"] = int(subject_id)

    # Show generated results only if a plan exists.
    if st.session_state["generated_plan_markdown"]:
        st.subheader("Generated Plan")

        # Show the markdown study plan.
        st.markdown(st.session_state["generated_plan_markdown"])

        # Get the generated tasks from session state.
        generated_tasks = st.session_state["generated_plan_tasks"]

        if generated_tasks:
            st.subheader("Tasks to be Added")

            # Convert the task list to a DataFrame so it can be shown in a table.
            preview_df = pd.DataFrame(generated_tasks)

            # Show the preview table.
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            # Save all generated tasks to the database.
            if st.button("Add Plan as Tasks"):
                bulk_add_tasks(
                    subject_id=int(st.session_state["generated_plan_subject_id"]),
                    tasks=generated_tasks,
                )

                # Show success message.
                st.success("Study plan tasks added successfully.")

                # Clear old AI results so the page resets.
                st.session_state["generated_plan_markdown"] = ""
                st.session_state["generated_plan_tasks"] = []
                st.session_state["generated_plan_subject_id"] = None

                # Refresh the app.
                st.rerun()


def main() -> None:
    """
    Main function of the app.

    This function:
    - applies styling
    - loads data
    - shows the sidebar
    - opens the selected page
    """
    # Apply custom CSS before showing the app.
    apply_custom_css()

    # Load subjects and tasks from the database.
    subjects = fetch_subjects()
    tasks = fetch_tasks()

    # Show the sidebar and get the selected page.
    page = render_sidebar(subjects, tasks)

    # Open the page chosen in the sidebar.
    if page == "Dashboard":
        dashboard_page(subjects, tasks)
    elif page == "Subjects":
        subjects_page(subjects, tasks)
    elif page == "Add Subject":
        add_subject_page()
    elif page == "Add Task":
        add_task_page(subjects)
    elif page == "Manage Tasks":
        manage_tasks_page(subjects, tasks)
    elif page == "AI Study Assistant":
        ai_study_assistant_page(subjects)


# This makes sure main() only runs when this file is executed directly.
if __name__ == "__main__":
    main()