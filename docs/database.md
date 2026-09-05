# Database

MySQL is the production persistence target. The schema is normalized around users, pregnancy profiles, appointments, conversations, messages, reminders, health workers, escalations, supported languages, communication channels, and user channels.

Initialize a database after creating it and configuring `.env`:

```bash
.venv/bin/python scripts/seed_database.py
```

The script applies `sql/schema.sql`, `sql/indexes.sql`, and safe development seed data. All application queries use connector parameters; user input is never concatenated into SQL. Connection failures become `DatabaseConnectionError`, and failed transactions roll back.

For local tests, `DATABASE_BACKEND=memory` uses an in-memory repository with the same workflow methods. It is not durable and must not be used as a production data store.
