# Deployment

## Build and run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python scripts/train_nlp.py
.venv/bin/python scripts/seed_database.py
.venv/bin/gunicorn --bind 0.0.0.0:8000 app:app
```

Set `DATABASE_BACKEND=mysql` and real MySQL values in `.env`. Set a non-default `SECRET_KEY` and configure `ADMIN_TOKEN`. Never commit `.env`, passwords, access tokens, or generated model artifacts.

## Reminders

Set `ENABLE_REMINDER_SCHEDULER=true`, `REMINDER_TIMEZONE`, `REMINDER_HOUR`, and `REMINDER_MINUTE`. The Flask process starts one APScheduler instance per process. For multi-worker deployments, run reminders in a dedicated single-worker process or use an external scheduler to avoid one scheduler per web worker.

Manual trigger:

```bash
.venv/bin/python scripts/run_reminders.py --date 2026-09-05
```

## Messaging providers

The browser and mock providers require no paid account. Real SMSPOP and WhatsApp transport hooks require current vendor documentation, credentials, webhook verification configuration, and deployment-specific wiring. The repository deliberately does not claim those external services are configured.

Use HTTPS for public webhooks, restrict inbound routes at the proxy, rotate secrets, avoid logging message contents or credentials, and protect maternal-health records with least-privilege database access.
