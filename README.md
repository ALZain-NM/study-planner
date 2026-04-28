# Study Planner

A Streamlit web application for planning study tasks, tracking academic progress, and generating AI-assisted study plans.

## Overview

This project is a practical **Study Planner** built with **Python** and **Streamlit**. It helps students organize subjects, manage study tasks, monitor deadlines, and view progress through an interactive dashboard.

The app was designed to solve a real problem: keeping track of study workload, upcoming assessments, and revision plans in one place.

## Live App

deployed Streamlit link here:

`https://your-streamlit-app-url-here`

## GitHub Repository

GitHub repository link here:

`https://github.com/ALZain-NM/study-planner`

---

## Features

### Core Features
- Add and manage subjects
- Add, edit, update, and delete study tasks
- Track task status: Planned, In Progress, Done
- Search tasks by title, topic, description, or subject
- Filter tasks by subject and status
- Sort tasks by deadline, priority, title, or status
- Input validation and error handling
- SQLite database storage
- Responsive Streamlit interface
- Dashboard with key academic insights

### AI Bonus Feature
- AI Study Assistant
- Generates a study plan based on:
  - selected subject
  - exam date
  - weak topics
  - weekly study hours
  - extra notes
- Converts the generated study plan into tasks with one click using **Add Plan as Tasks**

### Data Science Bonus Feature
- Dashboard analytics and visualizations
- Task completion metrics
- Progress by subject
- Important due dates
- Upcoming deadlines
- Status distribution charts

These features were implemented to satisfy the challenge requirement for one meaningful AI feature and one visible data science feature. :contentReference[oaicite:1]{index=1}

---

## App Pages

### Dashboard
Shows:
- total tasks
- completed tasks
- overdue tasks
- hours left
- subjects overview
- important due dates
- task status chart
- progress by subject
- upcoming deadlines
- recent tasks

### Subjects
Displays all subjects clearly, along with:
- difficulty
- exam date
- target study hours
- progress percentage

### Add Subject
Lets users add a new subject with:
- subject name
- exam date
- target study hours
- difficulty

### Add Task
Lets users create study tasks linked to a subject with:
- title
- topic
- description
- status
- priority
- deadline
- estimated hours

### Manage Tasks
Lets users:
- search tasks
- filter tasks
- sort tasks
- edit tasks
- update status quickly
- delete tasks

### AI Study Assistant
Lets users:
- generate a study plan
- preview the generated plan
- convert the plan into actual tasks automatically

---

## Tech Stack

- **Python**
- **Streamlit**
- **SQLite**
- **pandas**
- **plotly**
- **streamlit-option-menu**

---

## Project Structure

```text
study-planner/
├── app.py
├── requirements.txt
├── README.md
└── src/
    ├── ai_service.py
    ├── database.py
    ├── repository.py
    ├── services.py
    └── validators.py

## Setup Instructions

Follow these steps to set up and run the Study Planner app on your computer.

### 1. Clone the Repository

Open your terminal or command prompt and run:

```bash
git clone https://github.com/ALZain-NM/study-planner.git
```

Then move into the project folder:

```bash
cd study-planner
```

---

### 2. Create a Virtual Environment

Create a virtual environment so the project packages stay separate from your main Python installation.

```bash
python -m venv venv
```

Activate the virtual environment.

For Windows:

```bash
venv\Scripts\activate
```

For macOS or Linux:

```bash
source venv/bin/activate
```

---

### 3. Install the Required Packages

Install all required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

---

### 5. Run the App

Start the Streamlit app using:

```bash
streamlit run app.py
```

After running this command, Streamlit should open the app in your browser.

If the app does not open automatically, copy the local URL shown in the terminal and paste it into your browser.

---

### 6. Database Setup

No manual database setup is required.

The app uses SQLite, and the database is created automatically when the app runs.

The database stores:

- subjects
- tasks
- deadlines
- task status
- progress information