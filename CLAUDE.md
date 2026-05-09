# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Analtix is a FastAPI backend for an e-commerce analytics platform. The core feature is an AI-powered natural language query interface that converts user questions into SQLAlchemy queries via OpenAI GPT-4o-mini, then returns human-readable insights.

## Running the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
uvicorn app.main:app --reload

# API docs available at http://localhost:8000/docs
```

## Environment Setup

Requires a `.env` file with:
```
DATABASE_URL=postgresql://user:password@localhost:5432/fastapi_db
OPENAI_API_KEY=sk-...
```

Tables are created automatically on startup via `Base.metadata.create_all()` — no migration step needed in development.

## Architecture

The app is organized around a **query pipeline** in `app/query/`:

1. `intent_parser.py` — Calls OpenAI GPT-4o-mini to convert a natural language question into a structured intent JSON: `{intent, entity, metrics, time_range, operation, filters}`
2. `planner.py` — Maps the intent to a SQLAlchemy query function. Normalizes intent variants (e.g. `"get"` → `"check"`) and implements entity fallback: unrecognized entities are treated as product name searches.
3. `executor.py` — Executes the query plan and serializes ORM results to JSON. **Currently only handles `Product` fields** (`id, name, price, stock`); other entities won't serialize correctly.
4. `insights.py` — Converts raw results into a natural language answer string.

The main app (`app/main.py`) registers route modules from `app/routes/`. Authentication uses JWT tokens via `HTTPBearer` (see `app/auth/`). Only the `POST /products/` endpoint is protected.

## Key Patterns

- **No Alembic migrations** — schema changes require dropping/recreating tables or manual DDL.
- **Entity fallback** in `planner.py`: unrecognized `entity` values fall through to a product name search rather than raising an error.
- **ORM serialization** in `executor.py` is manual and product-specific; adding support for `User` or `Order` results requires extending the `serialize()` function there.
- **JWT secret** is currently hardcoded as `"mysecretkey"` in `app/auth/jwt.py` — must be moved to `.env` before any deployment.
