# Italian Coach Pro

Professional A2→B1 Italian learning dashboard for a Persian-speaking learner.

## Daily system
- 50 single-word vocabulary flashcards (5×10)
- 10 high-frequency everyday expressions
- Ordered complete A2 grammar roadmap with visual structured lessons and exactly 10 exercises/unit
- Voice conversation + shadowing
- Writing correction
- Adapted Italian news reading
- Daily quiz
- SQLite activity log, streak, calendar and grammar progress

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m streamlit run app.py
```
