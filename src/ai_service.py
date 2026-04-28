
# =========================
# File: src/ai_service.py
# =========================
from __future__ import annotations

import os
from datetime import date, datetime
from math import ceil

import streamlit as st


def _fallback_plan(
    subject_name: str,
    exam_date: str | None,
    difficulty: str,
    weak_topics: str,
    weekly_hours: float,
    extra_notes: str,
) -> str:
    weeks_left = 4
    if exam_date:
        try:
            days_left = max((datetime.fromisoformat(exam_date).date() - date.today()).days, 1)
            weeks_left = max(1, ceil(days_left / 7))
        except ValueError:
            weeks_left = 4

    topics = [topic.strip() for topic in weak_topics.split(",") if topic.strip()]
    if not topics:
        topics = ["core review", "practice questions", "revision"]

    difficulty_multiplier = {"Easy": 0.8, "Medium": 1.0, "Hard": 1.2}.get(difficulty, 1.0)
    adjusted_hours = round(weekly_hours * difficulty_multiplier, 1)

    lines = [
        f"## Study Plan for {subject_name}",
        f"- **Exam date:** {exam_date or 'Not set'}",
        f"- **Difficulty:** {difficulty}",
        f"- **Recommended weekly hours:** {adjusted_hours}",
        f"- **Weeks until exam:** {weeks_left}",
        "",
        "### Priorities",
    ]

    for index, topic in enumerate(topics, start=1):
        lines.append(f"{index}. Focus on **{topic}**")

    lines.append("")
    lines.append("### Weekly Plan")

    for week in range(1, weeks_left + 1):
        lines.append(
            f"- **Week {week}:** "
            f"Spend {adjusted_hours:.1f} hours on concept review, examples, and timed practice."
        )

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

    if extra_notes.strip():
        lines.extend(["", f"### Notes Considered", f"- {extra_notes.strip()}"])

    return "\n".join(lines)


def generate_study_plan(
    subject_name: str,
    exam_date: str | None,
    difficulty: str,
    weak_topics: str,
    weekly_hours: float,
    extra_notes: str,
) -> str:
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

    if not api_key:
        return _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        prompt = f"""
Create a concise study plan.

Subject: {subject_name}
Exam date: {exam_date or "Not set"}
Difficulty: {difficulty}
Weak topics: {weak_topics or "Not provided"}
Available study hours per week: {weekly_hours}
Extra notes: {extra_notes or "None"}

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

        return response.choices[0].message.content or _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
        )
    except Exception:
        return _fallback_plan(
            subject_name=subject_name,
            exam_date=exam_date,
            difficulty=difficulty,
            weak_topics=weak_topics,
            weekly_hours=weekly_hours,
            extra_notes=extra_notes,
        )