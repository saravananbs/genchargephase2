# GenCharge Backend

> A comprehensive mobile recharge and telecom wallet backend built with FastAPI, PostgreSQL, MongoDB, and Redis

## Table of Contents

- [System Overview](#system-overview)
- [Default Credentials](#default-credentials-for-development--testing)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [API Documentation](#api-documentation)
- [Seed Data](#seed-data)

---

## System Overview

The **GenCharge Backend** powers a mobile recharge and digital wallet platform focused on Indian telecom users. It provides APIs for prepaid/postpaid plan discovery, one-time and recurring recharges, wallet top-ups, referral rewards, notifications, content management, analytics, and administrative operations.

The system is designed as a multi-tenant backend for:

- End-users managing their own mobile numbers, plans, and wallet
- Admin teams operating offers, plans, campaigns, and support tooling

### Key Capabilities

- **For Administrators:**
	- Manage admins, roles, and fine-grained permissions
	- Configure plan groups, plans, and offer types (festive, cashback, loyalty, etc.)
	- Monitor recharges, wallet transactions, current active plans, and autopay schedules
	- Generate detailed reports and analytics (users, plans, offers, referrals, transactions, backups)
	- Send announcements and in-app notifications via a centralized notification center
	- Review contact-form submissions and audit logs (MongoDB)
	- Manage backup metadata and trigger database backup/restore flows

- **For Users:**
	- Sign up and log in using phone number + OTP
	- Manage profile and notification preferences
	- Switch between prepaid/postpaid user types (where supported)
	- Browse public plans and offers, including popular and special campaigns
	- Recharge a mobile number and top up wallet balance
	- View and manage current active plans and recharge history
	- Configure Autopay for recurring recharges
	- Use and share referral codes, earning rewards when friends join
	- Receive announcements, reminders, and transactional notifications

---

## Default Credentials (For Development & Testing)

> **Important:** This project primarily uses **OTP-based authentication**. There is **a hardcoded otp 111111** in the codebase.

When you run the seeding pipeline (see [Seed Data](#seed-data)):

- Multiple **admin accounts** are generated per role (e.g. `SuperAdmin`, `Manager`, `Support`, etc.).
- Admin emails follow the pattern: `"<role_name_lower>_admin<index>@example.com"` (for example: `superadmin_admin1@example.com`).
- Admin phone numbers are generated starting from `9000000001` upwards.

To log in during development:

- Use the normal **signup / login + OTP** flows.
- Or, query the database for a seeded admin/user phone number and request an OTP for that number.

There are intentionally **a default password for otp as 111111**; this helps for the fast paced development.

---

## Architecture

The backend follows a **layered architecture** with clear separation of concerns.

```text
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                        (app/main.py)                        │
└──────────────────────────────────────────────────────────────┘
														 │
					┌──────────────────┼──────────────────┐
					│                  │                  │
┌─────────▼───────┐  ┌───────▼─────────┐  ┌─────▼────────┐
│    API Layer    │  │  Service Layer  │  │  CRUD Layer  │
│ (app/api/routes)│──▶│  (app/services) │──▶│  (app/crud) │
└─────────────────┘  └─────────────────┘  └──────────────┘
					│                  │                  │
					│                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────┐
│                         Data Layer                         │
│  ┌────────────────┐   ┌──────────────────┐   ┌───────────┐ │
│  │ PostgreSQL     │   │   MongoDB        │   │  Redis    │ │
│  │ (Core entities │   │ (content, logs,  │   │ (cache,   │ │
│  │  & transactions)│ │  notifications)  │   │  sessions)│ │
│  └────────────────┘   └──────────────────┘   └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Components

1. **API Layer** (`app/api/routes/`): FastAPI routers grouped by domain (Auth, Users, Plans, Offers, Recharge, Autopay, Referrals, Notification, Content, Backup, Reports, Analytics, etc.).
2. **Service Layer** (`app/services/`): Business logic and orchestration; applies validation, coordinates multiple CRUD calls, and integrates external services (SMS, email, notifications).
3. **CRUD Layer** (`app/crud/`): Data-access layer for PostgreSQL and MongoDB collections.
4. **Models** (`app/models/`): SQLAlchemy ORM models for users, admins, plans, offers, transactions, autopay, backups, referrals, etc.
5. **Schemas** (`app/schemas/`): Pydantic models for request/response validation and documentation.
6. **Core** (`app/core/`): Central configuration (`config.py`), database sessions (`database.py`), MongoDB (`document_db.py`), Redis client (`redis_client.py`).
7. **Dependencies** (`app/dependencies/`): Shared dependency-injection helpers for auth, permissions, and DB sessions.
8. **Middleware** (`app/middleware/`): CORS, structured logging, and exception handling.

On startup, `app/main.py` uses a FastAPI **lifespan** context to automatically create database tables from SQLAlchemy models and dispose the engine on shutdown.

---

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
