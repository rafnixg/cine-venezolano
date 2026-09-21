# Repository Guidelines

## Project Structure & Module Organization

The application lives in `app/`. HTTP routes are grouped under `app/routes/`, YouTube ingestion and classification under `app/services/`, templates under `app/templates/`, and vanilla CSS/JavaScript under `app/static/`. Database models and shared queries are in `app/models.py` and `app/repository.py`. Alembic migrations live in `alembic/versions/`; automated tests live in `tests/`. Runtime SQLite files belong in `data/` and are ignored by Git.

## Build, Test, and Development Commands

- `python -m pip install -r requirements.txt` installs runtime and development dependencies.
- `alembic upgrade head` applies database migrations.
- `python -m app.cli sync-youtube` imports the configured playlist.
- `uvicorn app.main:app --reload` runs the local development server.
- `python -m pytest` executes the test suite.
- `python -m pytest --cov=app --cov-fail-under=70` matches the CI coverage gate.
- `python -m ruff check .` validates imports, style, and common errors.
- `docker compose up --build` starts the production-shaped container locally.

Copy `.env.example` to `.env` before running the importer or admin panel. Never commit `.env` or API keys.

## Coding Style & Naming Conventions

Use Python 3.11+ type hints and four-space indentation. Ruff is the source of truth for formatting and linting. Use `snake_case` for modules, functions, and variables; `PascalCase` for ORM models; and lowercase kebab-case for URL slugs. Keep routes thin and place external-service or classification logic in `app/services/`. Frontend code must remain framework-free and progressively enhance server-rendered HTML.

## Testing Guidelines

Tests use pytest and should be named `test_*.py`. Add unit coverage for classification and parsing, integration coverage for database synchronization, and HTTP coverage for public/admin routes. Mock YouTube responses; tests must not consume API quota or depend on network access. Run both pytest and Ruff before submitting changes.

## Commit & Pull Request Guidelines

Use short imperative subjects, preferably Conventional Commits, such as `feat: add genre filters`. Keep migrations with the model changes they support. Pull requests should describe user-visible behavior, list verification commands, mention configuration or migration changes, and include screenshots for UI work. Do not include database files, secrets, downloaded videos, or generated caches.

## Licensing

All contributions are distributed under `AGPL-3.0-or-later`. New source files and bundled third-party assets must be compatible with that license; document any third-party attribution when adding assets.
