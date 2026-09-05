# MamaBot

MamaBot is a local-first Flask conversational system for maternal-health information for pregnant women in Zimbabwe. It supports English, Shona, and Ndebele, and implements the six documented intent categories: appointment reminders, danger-sign queries, nutrition information, language switching, greetings, and escalation to a nurse.

## Run locally

Create a virtual environment, install `requirements.txt`, optionally copy `.env.example` to `.env`, and run `python app.py`. Open `http://127.0.0.1:5000/`. The browser chat uses the deterministic local NLP pipeline and does not require SMSPOP, WhatsApp, MySQL, or a paid AI API.

MySQL is the production persistence target and `sql/schema.sql` contains the schema. The current local mode uses an in-memory repository so the test interface remains usable when MySQL is not running. SMSPOP is enabled only when `SMSPOP_API_KEY` is configured. WhatsApp is exposed through a provider-neutral interface, with a console adapter for local development.

To initialize MySQL, create the database named by `MYSQL_DATABASE`, set `DATABASE_BACKEND=mysql` and the `MYSQL_*` values in `.env`, then run `python scripts/seed_database.py`. The initializer applies `sql/schema.sql`, `sql/indexes.sql`, and safe development seed records. Credentials are read only from environment variables.

ANC reminders run at `REMINDER_HOUR` and `REMINDER_MINUTE` in `REMINDER_TIMEZONE` when `ENABLE_REMINDER_SCHEDULER=true`. For a manual development trigger, run `python scripts/run_reminders.py --date YYYY-MM-DD`.

MamaBot provides general information and does not diagnose. Messages containing potential danger signs receive urgent escalation guidance rather than a diagnosis.

## Checks

Run `pytest -q` for the automated tests and `ruff check .` for static checks.
