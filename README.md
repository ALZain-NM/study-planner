# Study Planner

A Streamlit web app for planning study tasks, tracking progress, and generating study plans.

## Features

- Add and manage subjects
- Add and manage study tasks
- Search, filter, and sort tasks
- Track progress with charts and metrics
- SQLite database for persistent storage
- AI study plan generator
- Input validation and error handling

## Tech Stack

- Python
- Streamlit
- SQLite
- pandas
- plotly
- OpenAI API (optional)

## Project Structure

study-planner/
- app.py
- requirements.txt
- README.md
- src/
  - ai_service.py
  - database.py
  - repository.py
  - services.py
  - validators.py

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py