# Alembic Migrations

This project includes a minimal Alembic setup under `backend/alembic`. It reads the application `settings.DATABASE_URL` and uses SQLModel metadata for autogenerate support.

- Config: `backend/alembic.ini`
- Env: `backend/alembic/env.py` (loads `app.models` and uses `SQLModel.metadata`)
- Versions: `backend/alembic/versions/`

Commands (run from `backend/`):

- Create a revision (requires Alembic installed in venv):
  `make db-revision message="add new field"`

- Upgrade to latest:
  `make db-upgrade`

Notes:

- Local SQLite dev DB is `sqlite:///./bakemate_dev.db` by default; ensure it matches `settings.DATABASE_URL`.
- For SQLite, migrations use `batch_alter_table` pattern for compatibility.
- If your DB file predates new columns, run `db-upgrade` or recreate the DB in dev.
