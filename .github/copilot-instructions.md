# Copilot instructions for meal-plan

Purpose: concise guidance for Copilot sessions in this project (FastAPI + SQLAlchemy + Jinja2).

---

## Build / run / dev commands

- Unix / macOS (from project root):
  - python3 -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
  - uvicorn main:app --reload
  - Open: http://127.0.0.1:8000

- Windows PowerShell (from project root):
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1
  - pip install -r requirements.txt
  - uvicorn main:app --reload

- Docker:
  - docker build -t meal-plan .
  - docker run -p 8000:8000 meal-plan
  - or: docker-compose up (docker-compose.yml present)

- Notes on environment:
  - DATABASE_URL env var overrides the default SQLite URL (default: sqlite:///./mealplan.db).
  - The app creates the DB schema on startup (Base.metadata.create_all).

- Tests / linting:
  - No tests or linters are present in the repository currently.
  - If pytest is added, run a single test directly: `pytest path/to/test_file.py::test_name -q`.

---

## High-level architecture (big picture)

- Single-process FastAPI application defined in `main.py`.
  - HTTP routes render Jinja2 templates from `templates/` and use HTML forms.
  - Data layer uses SQLAlchemy (declarative models + SessionLocal) and a file-backed SQLite DB by default.
- Core models (in `main.py`): Dish, Ingredient, MealPlan.
  - Dish ↔ Ingredient: one-to-many, cascade delete on ingredients when a dish is removed.
  - MealPlan has a day (unique) and optional dish_id; the FK uses `ondelete=SET NULL` so removing a Dish does not delete the plan entry.
- Startup behavior:
  - `Base.metadata.create_all(bind=engine)` ensures tables exist.
  - `init_db()` seeds the seven weekdays if missing.
- Templates drive the UI; routes frequently use RedirectResponse(status_code=303) after POSTs.

---

## Key conventions and repo-specific patterns

- Database location & override:
  - Default DB file: `mealplan.db` in project root. Use `DATABASE_URL` to point to another DB.
- Direct Session usage:
  - Routes create `SessionLocal()` directly (not using FastAPI dependency injection). `get_db()` generator exists but is not used across the route handlers.
- Forms and redirect pattern:
  - POST handlers accept Form(...) parameters and return RedirectResponse to the index with status 303.
  - The index page supports `expand_id` query parameter to open details for a specific Dish.
- Model behaviors to be aware of when changing schema:
  - Ingredient uses cascade delete (`cascade="all, delete-orphan"`) attached to Dish.
  - MealPlan.day is unique; seed logic assumes German weekday names ("Montag", ...).
- Concurrency and SQLite:
  - Engine is created with `connect_args={"check_same_thread": False}` to allow use from multiple threads in development, but SQLite has known limitations in concurrent write scenarios.

---

## Files of interest

- main.py — app, models, routes, DB init
- requirements.txt — Python deps
- Dockerfile, docker-compose.yml — container images / composition
- run.ps1 — convenience script for Windows
- templates/ — Jinja2 HTML templates

---

## Existing assistant / CI configs checked

- No .github/ directory existed prior to this file.
- No CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, AIDER_CONVENTIONS.md, or related AI assistant config files were found.

---

If you want me to also add short examples for common edits (e.g., adding a REST-only API endpoint, switching to DI for DB sessions, migrating to Postgres), say which area and I'll add example snippets.
