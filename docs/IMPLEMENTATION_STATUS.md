# MamaBot implementation status

Status checked against the repository on 10 November 2026. The code and this
status document describe the implemented prototype; they do not establish
clinical suitability or validate external provider accounts.

## Current implementation

- Flask application with a browser chat, an admin session, admin APIs, and
  Twilio messaging webhooks.
- Intent classification uses scikit-learn TF-IDF features and Multinomial
  Naive Bayes, trained from `data/intents/intents.json`. The current data has
  446 example phrases across 13 intent tags, with English, Shona, and Ndebele
  response templates.
- Language selection in the messaging webhook uses small Shona and Ndebele
  word lists. The classifier does not implement the dissertation's custom
  character n-gram language detector or named-entity recognizer.
- Supabase REST is the configured persistence layer. The schema is maintained
  in `supabase/migrations/`; SQLite/SQLAlchemy model files are legacy and are
  not used by the configured application.
- SMSPoP handles outbound Zimbabwe SMS and delivery reports. Incoming SMS is
  not configured.
- Twilio handles inbound WhatsApp/SMS webhooks and scheduled WhatsApp
  reminders. Inbound webhook requests are checked using Twilio's request
  signature; reminders use a separate worker and an approved Content Template.
- Admin-managed appointment reminders are scheduled seven and one days before
  an appointment when those times remain in the future. Weekly pregnancy
  reminders require distinct, staff-supplied content and recorded patient
  consent.
- Automated chat answers now include an English safety notice. There is no
  staffed nurse-escalation mechanism; the bot explicitly says it cannot alert
  a nurse.

## Claims in the dissertation that do not describe this code

The accompanying dissertation remains unchanged as an academic record. Its
implementation sections need revision before they are used as current system
documentation. In particular:

| Dissertation description | Repository implementation |
|---|---|
| MySQL, SQLAlchemy, and an `INTENTS` table | Supabase REST and versioned SQL migrations |
| spaCy/NLTK classifier and NER | scikit-learn TF-IDF and Multinomial Naive Bayes; no NER |
| Custom Shona/Ndebele character n-gram language detector | Word-list language detection in the webhook |
| Six classes and 900–911 corpus examples | 13 intent tags and 446 configured example phrases |
| APScheduler running in the web application | Separate reminder worker process |
| Automatic reminder text and WhatsApp/SMS preference | Staff-supplied reminder text; WhatsApp reminders and one-off outbound SMS |
| Registered Africa's Talking inbound webhook | Handler code exists but has no registered Flask route |
| Nurse escalation and a clinician-reviewed mandatory disclaimer | No nurse handoff; current safety notice is informational and needs clinical and language review |

The dissertation's reported held-out F1, synthetic performance KPIs, and
participant user-acceptance results are not reproduced by the current
repository's tests. They must not be presented as verified outcomes of this
implementation without the original datasets, evaluation procedure, and
supporting study records.

## Evaluation boundaries

`python test_phase1.py` runs a small smoke test against selected examples.
`python evaluate.py` performs a reproducible, fixed-seed, stratified 80/20 split
of the configured intent phrases and writes `evaluation_report.json`. The
phrases are curated examples, not an independently collected evaluation set.
Neither command evaluates correctness of medical advice, Shona/Ndebele
naturalness, safety outcomes, user acceptance, provider delivery, or deployed
latency.

## Before any patient-facing deployment

- Have qualified maternal-health clinicians review every response and the
  safety wording.
- Have fluent Shona and Ndebele reviewers translate and approve safety notices
  and all clinical response templates.
- Decide and implement a staffed escalation process before claiming nurse
  escalation. No contact or on-call workflow is configured in this repository.
- Verify Supabase RLS, production credentials, HTTPS provider callbacks,
  Twilio signature URL configuration, SMSPoP authentication, and actual
  delivery in provider-controlled test accounts.
- Conduct and document an independently reviewable user-acceptance and
  clinical-safety evaluation.
