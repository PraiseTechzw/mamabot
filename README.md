# MamaBot

MamaBot is a local-first Flask conversational system for maternal-health information for pregnant women in Zimbabwe. It supports English, Shona, and Ndebele, and implements the six documented intent categories: appointment reminders, danger-sign queries, nutrition information, language switching, greetings, and escalation to a nurse.

## Run locally

MamaBot is a local-first Flask maternal-health information assistant for pregnant women in Zimbabwe. It supports English, Shona, and Ndebele, six documented intents, registration, appointments, ANC reminders, escalation to health workers, and provider-independent browser/SMS/WhatsApp adapters. It does not diagnose medical conditions.

### Requirements and setup

Python 3.11+ and, for production, MySQL 8+. Create an environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

### Environment variables

Configure `SECRET_KEY`, `ADMIN_TOKEN`, `DATABASE_BACKEND`, `MYSQL_*`, `INTENT_CONFIDENCE_THRESHOLD`, reminder timing, and optional provider settings in `.env`. `.env.example` contains placeholders only. Leave `DATABASE_BACKEND=memory` and provider modes at their local defaults for credential-free development.

### MySQL setup

Create the configured database and initialize it:

```bash
.venv/bin/python scripts/seed_database.py
```

Set `DATABASE_BACKEND=mysql` before starting the production application. SQL queries are parameterized and connection failures are handled without exposing credentials.

### Train NLP and start Flask

Generate the local intent artifact before running the app:

```bash
.venv/bin/python scripts/train_nlp.py
.venv/bin/python app.py
```

Open `http://127.0.0.1:5000/` for the browser chat. The browser uses the same Flask, NLP, dialogue, repository, and response path as the messaging adapters. Register users, select a language, ask health-information questions, create an appointment, and test nurse escalation through the local UI or test webhook.

MySQL is the production persistence target and `sql/schema.sql` contains the schema. The current local mode uses an in-memory repository so the test interface remains usable when MySQL is not running. SMSPOP is enabled only when `SMSPOP_API_KEY` is configured. WhatsApp is exposed through a provider-neutral interface, with a mock adapter for local development.

The SMSPOP adapter intentionally does not guess a vendor endpoint or payload because the current SMSPOP API documentation is not included in this repository. Supply a documentation-specific `send_transport` to `SmsPopProvider`; local development and tests use `MockSmsPopProvider`.

WhatsApp uses the same provider-independent pattern. Leave `WHATSAPP_PROVIDER=console` for credential-free local development. A real provider requires `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, a documented `send_transport`, and a documented signature verifier; no WhatsApp endpoint or vendor payload is guessed by this project.

To initialize MySQL, create the database named by `MYSQL_DATABASE`, set `DATABASE_BACKEND=mysql` and the `MYSQL_*` values in `.env`, then run `python scripts/seed_database.py`. The initializer applies `sql/schema.sql`, `sql/indexes.sql`, and safe development seed records. Credentials are read only from environment variables.

ANC reminders run at `REMINDER_HOUR` and `REMINDER_MINUTE` in `REMINDER_TIMEZONE` when `ENABLE_REMINDER_SCHEDULER=true`. For a manual development trigger, run `python scripts/run_reminders.py --date YYYY-MM-DD`.

### Messaging providers

SMSPOP and WhatsApp adapters are intentionally provider-independent. Local tests use mock providers and do not require paid accounts. Real SMSPOP/WhatsApp endpoint payloads, signature rules, credentials, and transport hooks must be supplied from current vendor documentation; none are claimed to be configured here.

MamaBot provides general information and does not diagnose. Messages containing potential danger signs receive urgent escalation guidance rather than a diagnosis.

## Checks

Run the application test suite and static checks:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check . --exclude OpenWA
```

The repository pytest configuration scopes tests to MamaBot's `tests/` directory. `OpenWA/` is an unrelated SDK tree and is excluded from the application checks.

See [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md), [docs/nlp.md](docs/nlp.md), [docs/database.md](docs/database.md), and [docs/deployment.md](docs/deployment.md) for operational details.
