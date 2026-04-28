"""
AI helper functions for the Study Planner app.

This file generates a study plan and turns that plan into tasks.
If there is no OpenAI API key, it uses a simple backup planner instead.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from math import ceil

import streamlit as st


def _fallback_plan(
    subject_name: str,
    exam_date: str | None,
    difficulty: str,
    weak_topics: str,
    weekly_hours: float,
    extra_notes: str,
    weeks: int,
) -> str:
    """
    Create a simple study plan without using the OpenAI API.
    """
    # Start with the number of weeks chosen by the user.
    weeks_left = weeks

    # If there is an exam date, try to work out how many weeks are left.
    if exam_date:
        try:
            days_left = max((datetime.fromisoformat(exam_date).date() - date.today()).days, 1)
            weeks_left = max(1, min(weeks, ceil(days_left / 7)))
        except ValueError:
            # If the exam date is not valid, keep the original number of weeks.
            weeks_left = weeks

    # Split the weak topics into a list.
    topics = [topic.strip() for topic in weak_topics.split(",") if topic.strip()]

    # Use default topics if the user leaves the field empty.
    if not topics:
        topics = ["core review", "practice questions", "revision"]

    # Harder subjects get a little more study time.
    difficulty_multiplier = {"Easy": 0.8, "Medium": 1.0, "Hard": 1.2}.get(difficulty, 1.0)
    adjusted_hours = round(weekly_hours * difficulty_multiplier, 1)

    # Build the study plan as markdown text.
    lines = [
        f"## Study Plan for {subject_name}",
        f"- **Exam date:** {exam_date or 'Not set'}",
        f"- **Difficulty:** {difficulty}",
        f"- **Recommended weekly hours:** {adjusted_hours}",
        f"- **Weeks until exam:** {weeks_left}",
        "",
        "### Priorities",
    ]

    # Add the weak topics as priorities.
    for index, topic in enumerate(topics, start=1):
        lines.append(f"{index}. Focus on **{topic}**")

    lines.append("")
    lines.append("### Weekly Plan")

    # Create one study step for each week.
    for week in range(1, weeks_left + 1):
        topic = topics[(week - 1) % len(topics)]
        lines.append(
            f"- **Week {week}:** Spend {adjusted_hours:.1f} hours on **{topic}**, concept review, examples, and timed practice."
        )

    # Add some general advice at the end.
    lines.extend(
        [
            "",
            "### Final Advice",
            "- Study weakest topics first.",
            "- Leave one session each week for revision.",
            "- Use short quizzes after each study block.",
            "- In the final week, focus on practice and summary notes.",
        ]
    )

    # Add extra notes only if the user entered something.
    if extra_notes.strip():
        lines.extend(["", "### Notes Considered", f"- {extra_notes.strip()}"])

    return "\n".join(lines)


def generate_study_plan(
    subject_name: str,
    exam_date: str | None,
    difficulty: str,
    weak_topics: str,
    weekly_hours: float,
    extra_notes: str,
    weeks: int,
) -> str:
    """
    Generate a study plan using OpenAI if possible.
    If not, use the fallback planner.
    """
    # Check for the API key in Streamlit secrets or environment variables.
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

    # If there is no API key, use the backup planner.
    if not api_key:
        return _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
            weeks=weeks,
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # This prompt tells the model exactly what kind of plan to return.
        prompt = f"""
Create a concise study plan.

Subject: {subject_name}
Exam date: {exam_date or "Not set"}
Difficulty: {difficulty}
Weak topics: {weak_topics or "Not provided"}
Available study hours per week: {weekly_hours}
Extra notes: {extra_notes or "None"}
Weeks to plan: {weeks}

Return:
1. A short priority summary
2. A week-by-week plan
3. A final revision strategy
Use markdown.
""".strip()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a practical academic study planner."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        content = response.choices[0].message.content

        # If the API gives a response, return it.
        if content:
            return content

        # If the response is empty, use the backup planner.
        return _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
            weeks=weeks,
        )

    except Exception:
        # If anything goes wrong with the API call, use the backup planner.
        return _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
            weeks=weeks,
        )


def build_plan_tasks(
    subject_name: str,
    weak_topics: str,
    weeks: int,
    weekly_hours: float,
) -> list[dict[str, object]]:
    """
    Turn the generated study plan into task data that can be saved in the app.
    """
    # Split weak topics into a list.
    topics = [topic.strip() for topic in weak_topics.split(",") if topic.strip()]

    # Use default topics if no weak topics are given.
    if not topics:
        topics = ["core review", "practice questions", "revision"]

    base_date = date.today()

    # Share the weekly hours across the generated tasks.
    hours_per_task = max(round(weekly_hours / max(len(topics), 1), 1), 1.0)

    tasks: list[dict[str, object]] = []

    # Create one task for each week.
    for week in range(1, weeks + 1):
        topic = topics[(week - 1) % len(topics)]

        tasks.append(
            {
                "title": f"Week {week}: Study {topic}",
                "description": f"AI-generated study task for {subject_name}. Focus on {topic}.",
                "topic": topic,
                "status": "Planned",
                "priority": "High" if week == 1 else "Medium",
                "deadline": (base_date + timedelta(days=week * 7)).isoformat(),
                "estimated_hours": hours_per_task,
                "actual_hours": 0.0,
            }
        )

    return tasks