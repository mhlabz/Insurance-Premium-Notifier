# Insurance Premium Notifier

A college project built with Python, Flask and SQLite to register insurance policies, calculate monthly/yearly premium due dates, monitor grace periods, and create reminders/lapse notifications.

## Features
- Add, view, edit and delete policies; duplicate policy numbers are rejected.
- Monthly and yearly due-date calculations, including month-end and leap-year handling.
- Per-policy grace periods and seven-day Due Soon window.
- Active, Due Soon, Grace Period, Lapsed and Paid-Up statuses.
- Record premium payments and mark policies Paid-Up.
- Monitor action refreshes statuses and creates idempotent notifications.
- SQLite persistence and automated unit tests.

## Run on Windows
1. Install Python 3.10+.
2. Extract this folder and open it in VS Code.
3. Open Terminal in the project folder.
4. Run `py -m venv .venv`
5. Activate: `.venv\Scripts\activate`
6. Install: `pip install -r requirements.txt`
7. Start: `python app.py`
8. Visit `http://127.0.0.1:5000`.

## Run on macOS/Linux
`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python app.py`

## Tests
Run `python -m unittest discover -s tests -v`.

## Project structure
- `app.py`: Flask routes and form handling
- `services.py`: date calculations, status rules and monitoring
- `database.py`: SQLite connection and schema
- `templates/`: Jinja2 pages
- `static/style.css`: responsive styling
- `tests/`: automated tests
- `database/`: database file is created automatically

## Status rules
- Active: due date is more than 7 days away.
- Due Soon: due date is today through the next 7 days.
- Grace Period: due date has passed, but the grace deadline has not.
- Lapsed: today is after the grace deadline.
- Paid-Up: excluded from monitoring, reminders and lapse checks.

This is an academic demonstration. It does not send real SMS/email messages or connect to an insurer.
