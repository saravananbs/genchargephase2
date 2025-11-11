This repository contains the backend for GenCharge, a mobile recharge platform implemented with a modern Python async web stack. It provides APIs for user management, plans, recharge, autopay, referrals, notifications, backups, reporting, analytics, and more.

## Table of contents

- Project overview
- Features
- Tech stack
- Repository layout
- Quick start (development)
- Environment variables
- Database setup & seeding
- Running tests
- API docs
- Contributing
- Troubleshooting & notes

## Project overview

This backend implements core mobile recharge functionality and exposes a REST API used by mobile apps, web clients, and administrative tools. It aims to be modular, testable, and production-ready with features such as:

- OTP-based user authentication & authorization
- Plan and offer management
- Recharge and wallet operations
- Autopay for recurring recharges
- Referral rewards system
- Notifications and announcements
- Backup & restore utilities
- Reporting and analytics endpoints

## Features

- Async API using FastAPI (async endpoints)
- PostgreSQL for relational data storage (users, plans, transactions)
- MongoDB for document-oriented needs (content, audit logs, backups)
- Redis for caching, sessions, and ephemeral state
- Structured routers, services, CRUD layers, and pydantic schemas
- Middleware for logging, CORS, exception handling, and request tracing
- Seed scripts and utilities for core data (admin user, initial plans)

## Tech stack

- Python 3.x (project virtualenv present)
- FastAPI for API layer
- Uvicorn as ASGI server
- SQLAlchemy async for PostgreSQL
- Motor for MongoDB integration
- Redis client for caching
- Pydantic for schemas
- Pytest for tests

## Repository layout

Top-level and important folders/files:

- `app/` — main application package. Contains `main.py`, `api/` (routes), `core/` (config, database), `crud/`, `models/`, `schemas/`, `services/`, `utils/` and `middleware/`.
- `backup_test.sql`, `seed_core_data.sql` — SQL scripts to create admin accounts and seed core data.
- `requirements.txt` — Python dependencies (use `pip install -r requirements.txt`).
- `docs/` — API documentation.
- `backups/` — backup files.
- `static/uploads/` — static file uploads.
- `genchargephase2_env/` — virtual environment.

Inside `app/`:

- `api/routes/` — individual route modules (auth, users, plans, recharge, autopay, referrals, notifications, content, backup, reports, analytics).
- `core/database.py`, `core/document_db.py`, `core/redis_client.py` — DB and cache connection logic.
- `crud/` — data-access layer functions per resource.
- `services/` — higher-level business logic.
- `utils/` — helper utilities (analytics, etc.).

## Quick start (development)

Prerequisites:

- Python 3.x installed
- PostgreSQL server (local or remote)
- MongoDB (local or remote)
- Redis (local or remote)

1. Create and activate a virtual environment (example for fish shell):

```fish
python -m venv genchargephase2_env
source genchargephase2_env/bin/activate.fish
```

2. Install dependencies:

```fish
pip install -r requirements.txt
```

3. Create a `.env` file in the project root (see Environment variables below for needed keys).

4. Initialize the database(s):

- Run Postgres SQL scripts if you want to seed the DB with admin user / core data:

```fish
# Replace connection details or run with psql configured for your PG server
psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -f backup_test.sql
psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -f seed_core_data.sql
```

Alternatively, use the project's seeding utility if provided under `utils/`.

5. Start the server (development mode):

```fish
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You can also run the top-level `main.py` if the project exposes a different entry point.

## Environment variables

The project expects certain environment variables for configuration. Create a `.env` file or export them in your environment. Typical variables used by this project include:

- `DATABASE_URL` — PostgreSQL connection string (e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`).
- `MONGO_URL` — MongoDB connection URI.
- `REDIS_URL` — Redis connection string.
- `SECRET_KEY` — Application secret for JWT or other encryption.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — Access token expiry in minutes.
- `REFRESH_TOKEN_EXPIRE_DAYS` — Refresh token expiry in days.
- `OTP_EXPIRE_MINUTES` — OTP validity duration.
- `OTP_SECRET` — Secret for OTP generation.
- `ALGORITHM` — JWT algorithm.

Example `.env` snippet:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/gencharge_db
MONGO_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
SECRET_KEY=change_me_to_a_real_secret
ACCESS_TOKEN_EXPIRE_MINUTES=1
REFRESH_TOKEN_EXPIRE_DAYS=2
OTP_EXPIRE_MINUTES=5
OTP_SECRET=otp_secret_key
ALGORITHM=HS256
```

## Database setup & seeding

1. Create the PostgreSQL database and user as appropriate.
2. Ensure MongoDB and Redis are running.
3. Run provided SQL seed files to add an admin user and core data (see Quick start above).

4. Optional: run any Python seed helper if present.

## Running tests

Run unit/integration tests with pytest:

```fish
pytest -q
```

Add or update tests under `app/tests/` when modifying behavior. Aim to include a happy path plus a couple edge cases for each major module (auth, plans, recharge).

## API docs

When the server is running, FastAPI autodoc endpoints are available by default:

- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These endpoints list available routes, request/response models, and allow test calls.

## Development notes

- Follow the project's structure: routers are thin and delegate to `services/` and `crud/` layers for business logic and DB access.
- Keep pydantic schemas in `schemas/` to centralize request/response contracts.
- Use `core/config.py` for central configuration and `core/database.py` for DB lifecycle (startup/shutdown hooks).
- Add logging via `middleware/logging.py` and centralized error handling in `middleware/exception.py`.

## Contributing

1. Fork and create a feature branch.
2. Add tests for new behavior.
3. Run tests locally and ensure linting passes.
4. Submit a pull request with a clear description.

## Troubleshooting

- Database connection errors: verify `DATABASE_URL`, `MONGO_URL`, `REDIS_URL` and that services are reachable from your host.
- Missing dependencies: ensure you installed `requirements.txt` in the correct environment.
- If you hit CORS or auth issues, check the middleware and config in `middleware/cors.py` and `core/config.py`.

## Contact / Maintainers

If you need help or want to report a bug, open an issue in the repository or contact the project maintainer.

---

This README is a living document — update it when project setup, env vars, or run instructions change.





gencharge-phase-2/
├── backup_test.sql
├── readme.md
├── requirements.txt
├── app/
│ ├── __init__.py
│ ├── main.py
│ ├
│ ├── api/
│ │ ├── routes/
│ │ │ ├── admin/
│ │ │ ├── analyticas/
│ │ │ ├── audit_logs/
│ │ │ ├── auth/
│ │ │ ├── autopay/
│ │ │ ├── backup/
│ │ │ ├── contact_form/
│ │ │ ├── content/
│ │ │ ├── notification/
│ │ │ ├── offers/
│ │ │ ├── plans/
│ │ │ ├── recharge/
│ │ │ ├── referrals/
│ │ │ ├── reports/
│ │ │ ├── roles/
│ │ │ ├── testing/
│ │ │ └── users/
│ ├── core/
│ │ ├── __init__.py
│ │ ├── config.py
│ │ ├── database.py
│ │ ├── document_db.py
│ │ ├── redis_client.py
│ │ 
│ ├── crud/
│ │ ├── __init__.py
│ │ ├── admin.py
│ │ ├── audit_logs.py
│ │ ├── autopay.py
│ │ ├── backup_analytics.py
│ │ ├── backup.py
│ │ ├── contact_form.py
│ │ ├── content.py
│ │ ├── current_active_plan_analytics.py
│ │ ├── notification.py
│ │ ├── offer_analytics.py
│ │ ├── offer_type.py
│ │ ├── offer.py
│ │ ├── permissions.py
│ │ ├── plan_analytics.py
│ │ ├── plans.py
│ │ ├── recharge.py
│ │ ├── referral_analytics.py
│ │ ├── referrals.py
│ │ ├── reports.py
│ │ ├── role_permission.py
│ │ ├── role.py
│ │ ├── sessions.py
│ │ ├── token_revocation.py
│ │ ├── transaction_analytics.py
│ │ ├── user_insights.py
│ │ ├── users_admin_analytics.py
│ │ ├── users_archieve_analytics.py
│ │ ├── users.py
│ │ 
│ ├── dependencies/
│ │ ├── __init__.py
│ │ ├── auth.py
│ │ ├── permissions.py
│ │ 
│ ├── middleware/
│ │ ├── __init__.py
│ │ ├── cors.py
│ │ ├── exception.py
│ │ ├── logging.py
│ │ 
│ ├── models/
│ │ ├── __init__.py
│ │ ├── admins.py
│ │ ├── autopay.py
│ │ ├── backup.py
│ │ ├── current_active_plans.py
│ │ ├── offer_types.py
│ │ ├── offers.py
│ │ ├── permissions.py
│ │ ├── plan_groups.py
│ │ ├── plans.py
│ │ ├── referral.py
│ │ ├── roles_permissions.py
│ │ ├── roles.py
│ │ ├── sessions.py
│ │ ├── token_revocation.py
│ │ ├── transactions.py
│ │ ├── user_preference.py
│ │ ├── users_archieve.py
│ │ ├── users.py
│ │ 
│ ├── schemas/
│ │ ├── __init__.py
│ │ ├── admin.py
│ │ ├── auth.py
│ │ ├── autopay.py
│ │ ├── backup_analytics.py
│ │ ├── backup.py
│ │ ├── contact_form.py
│ │ ├── content.py
│ │ │ ├── current_active_plans_analytics.py
│ │ ├── notification.py
│ │ ├── offer_analytics.py
│ │ ├── offer_group.py
│ │ ├── offer.py
│ │ ├── permissions.py
│ │ ├── plan_analytics.py
│ │ ├── plan_group.py
│ │ ├── plans.py
│ │ ├── recharge.py
│ │ ├── referral_analytics.py
│ │ ├── referrals.py
│ │ ├── reports.py
│ │ ├── role_permission.py
│ │ ├── role.py
│ │ ├── transaction_analytics.py
│ │ ├── user_insights.py
│ │ ├── users_admins_analytics.py
│ │ ├── users_archive_analytics.py
│ │ ├── users.py
│ │ 
│ ├── services/
│ │ ├── __init__.py
│ │ ├── auth.py
│ │ ├── autopay.py
│ │ ├── backup_analytics.py
│ │ ├── backup.py
│ │ ├── contact_form.py
│ │ ├── content.py
│ │ ├── current_active_plans_analytics.py
│ │ ├── notification.py
│ │ ├── offer_analytics.py
│ │ ├── plan_analytics.py
│ │ ├── recharge.py
│ │ ├── referral_analytics.py
│ │ ├── referral.py
│ │ ├── reports.py
│ │ ├── transactions_analytics.py
│ │ ├── user_insights.py
│ │ ├── user.py
│ │ ├── users_admin_analytics.py
│ │ ├── users_archieve_analytics.py
│ │ 
│ ├── utils/
│ │ ├── __init__.py
│ │ ├── analytics.py
│ │ └── ...
├── backups/
│ ├── backup_20251107_160311.sql
│ ├── backup_20251107_162014.sql
│ ├── backup_20251107_163236.sql
│ ├── backup_20251108_223219.sql
├── docs/
│ ├── API_Documentation.md
├── genchargephase2_env/
│ ├── lib64
│ ├── pyvenv.cfg
│ ├── bin/
│ ├── include/
│ └── lib/
├── static/
│ └── uploads/
