# MamaBot

Flask-based maternal-health chatbot for English, Shona, and Ndebele. Supabase is
the system of record, SMSPoP sends outbound Zimbabwe SMS, and Twilio handles
WhatsApp replies and scheduled WhatsApp reminders.

## Project layout

```text
app/
  db/                 Supabase REST persistence
  nlp/                Intent classification and responses
  routes/             Flask web, admin, and provider webhooks
  services/           SMSPoP and Twilio messaging integrations
  reminders.py        Separate scheduled-reminder worker
data/intents/         Chatbot language and intent data
supabase/
  migrations/         Versioned database schema
init_db.py            Safe Supabase migration runner
run.py                Flask entry point
```

Generated databases, model caches, virtual environments, and `.env` files are
ignored by git. The old SQLite/SQLAlchemy model files are not used; Supabase is
the configured database.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
```

Set `SECRET_KEY` to a unique random value of at least 32 characters and
`ADMIN_PASSWORD` to a unique password of at least 12 characters.
`SUPABASE_URL` and `SUPABASE_KEY` are required for every production deployment;
the key must be a server-side Supabase service-role/secret key and must never
go in browser code. Production startup fails with a list of missing or
incomplete settings instead of silently running without persistence. Link this
directory to the intended Supabase project, inspect the migration, then apply
it explicitly:

```bash
supabase link --project-ref YOUR_PROJECT_REF
python init_db.py --apply
```

`python init_db.py` without `--apply` is a no-op. It never drops or recreates
tables. The migration enables RLS and limits table access to the server role.
For local development, the Supabase API uses `http://127.0.0.1:55421` to avoid
colliding with other Supabase projects on the same machine.

Run the web process with `python run.py`. Hosting-platform readiness checks
should use `GET /healthz`; it returns `200` only when Supabase is reachable and
`503` otherwise. Admin diagnostics are available at `/api/health/data` after
logging in. They report the reminder worker as a separate, unmonitored process;
the web process cannot claim that worker is running. Set `FLASK_ENV=production`
in the hosting environment; the checked-in `.env.example` intentionally uses
development mode for local work.

Messaging providers are optional, but each enabled integration must be fully
configured. SMSPoP requires both `SMSPOP_API_TOKEN` and `SMSPOP_SENDER_ID`.
When delivery reports are enabled with `SMSPOP_DELIVERY_REPORT_URL`, also set
`SMSPOP_WEBHOOK_SECRET`. Twilio WhatsApp reminders require
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, and an
approved `TWILIO_WHATSAPP_REMINDER_CONTENT_SID`. Leave all settings for an
unused provider empty. Production startup rejects partially configured
providers.

For scheduled messages, configure a separate worker process using
`python -m app.reminders --loop`. Do not run the reminder loop inside Gunicorn
workers; multiple workers could claim duplicate jobs. The Supabase claim
function uses row locking so separate worker instances only claim disjoint
jobs.

## Messaging setup

### SMSPoP outbound SMS

Set `SMSPOP_API_TOKEN` and an approved `SMSPOP_SENDER_ID`. The app sends one
recipient per campaign using `POST https://smspop.co.zw/api/campaigns`.
`SMSPOP_DELIVERY_REPORT_URL` is optional if the account-level report webhook
is configured in SMSPoP. Set `SMSPOP_WEBHOOK_SECRET` to the signing secret
SMSPoP provides for that webhook.

Delivery reports are received at:

```text
POST /webhook/smspop/delivery-reports
```

The endpoint verifies SMSPoP's HMAC-SHA256 signature over the raw body and
rejects timestamps older than five minutes. `webhook_id` is stored as a unique
key so provider retries do not duplicate reports.

SMSPoP's published API documents outbound messages and delivery reports, not
incoming SMS. SMS-based user conversations therefore remain unconfigured.

### WhatsApp reminders

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_WHATSAPP_NUMBER`, and an approved
`TWILIO_WHATSAPP_REMINDER_CONTENT_SID`. The approved Twilio Content Template
must accept one variable containing the reminder body. The worker does not
fall back to free-form WhatsApp messages outside the customer-service window.

For inbound Twilio messages, configure `TWILIO_AUTH_TOKEN` and point the
provider at `POST /webhook/twilio` (or its `/webhook/sms` and
`/webhook/whatsapp` aliases). Requests without a valid `X-Twilio-Signature`
are rejected. If the application is behind a proxy or its internal URL differs
from the public HTTPS URL, set `TWILIO_WEBHOOK_BASE_URL` to the public origin,
for example `https://bot.example.org` (no path or trailing slash). Leave it
empty when Twilio's public URL matches the URL received by Flask.

The public browser chat is `GET /chat` and `POST /chat/send`. The admin login
is at `/admin/login`; the admin dashboard and APIs require its session.
`GET /healthz` is a public readiness probe that checks Supabase, not the
separate reminder worker.

Admin API routes require a logged-in admin session:

- `POST /admin/retrain` reloads the configured intent examples and retrains the
  local classifier.
- `GET /admin/test-nlp` runs a small set of diagnostic examples.
- `POST /admin/patients` creates/updates a patient, language, due date, and
  recorded reminder consent. Consent is off unless explicitly enabled.
- `POST /admin/appointments` stores an appointment and schedules reminders
  seven days and one day beforehand when those times are still in the future.
- `POST /admin/pregnancy-reminders` schedules one distinct,
  staff-provided message for each upcoming Wednesday at 10:00
  `Africa/Harare`, through the recorded due date. Supply reviewed,
  language-appropriate content for every scheduled week.
- `POST /admin/reminders` schedules a single opt-in WhatsApp reminder.
- `POST /admin/sms` sends a one-off SMS with SMSPoP.

Example patient registration:

```json
{
  "phone_number": "+263771234567",
  "preferred_lang": "english",
  "due_date": "2027-06-01",
  "consent": true,
  "consent_source": "in_person"
}
```

Do not set `consent` to true unless the patient has explicitly agreed to receive
these messages. Setting it to false cancels pending reminders.

The worker marks a message sent only after the provider accepts it; that does
not mean the handset received it. SMSPoP delivery reports provide final SMS
delivery status.

Every automated chat response carries an English safety notice. It explains
that the chatbot is not a diagnosis and cannot contact a nurse. There is no
live nurse escalation or handoff. The safety notice and maternal-health
responses require qualified clinical and Shona/Ndebele language review before
deployment to patients.

Africa's Talking handler code is not registered as a Flask route and is not an
active inbound integration. There is no SMS inbound service in the configured
SMSPoP flow; current SMSPoP support is outbound messages and delivery reports.

## API and implementation status

The current implementation, known gaps, and discrepancies with the project
dissertation are recorded in [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).
The dissertation is retained as a historical academic document; its technical
descriptions and reported study results should not be treated as a description
of the current code or as verified evaluation results.

## Validation

```bash
python -m unittest discover -s tests
python test_phase1.py
python evaluate.py
```

`test_phase1.py` is a 12-example smoke test. `evaluate.py` performs a fixed-seed
stratified holdout evaluation of the current intent patterns and rewrites
`evaluation_report.json`. The evaluation is limited to curated-pattern intent
classification; it does not establish clinical accuracy, language
identification quality, user acceptance, or production performance.
