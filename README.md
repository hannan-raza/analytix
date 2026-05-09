# Analtix

A natural language analytics API for e-commerce data. Ask questions in plain English — Analtix figures out what you're asking, queries the database, and returns a human-readable answer.

> "How many orders were placed this month?" → **"Found 6 orders created this month."**

---

## What It Is

Analtix is a backend API that acts as an intelligent query layer over a PostgreSQL database. Instead of writing SQL, users send natural language questions via a REST endpoint. An LLM (GPT-4o-mini) parses the intent, a query planner translates it into a structured query, SQLAlchemy executes it, and a formatter turns the raw results into a readable response.

**Think of it as:** a lightweight, self-hosted version of the "Ask your data" feature found in BI tools like Tableau or Google Looker — built from scratch with full control.

---

## Architecture

```
POST /query  {"question": "Show me user names created this month"}
      │
      ▼
┌──────────────────┐
│  Intent Parser   │  Sends question to GPT-4o-mini
│  intent_parser   │  Returns structured JSON: { intent, entity, metrics, time_range }
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Planner      │  Validates entity against Schema Registry
│    planner.py    │  Resolves metrics & time filters
│   registry.py    │  Outputs a Query DSL (plain dict — no SQL yet)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Executor     │  Reads Query DSL
│   executor.py    │  Builds & runs SQLAlchemy query against PostgreSQL
│                  │  Applies name search + time filters dynamically
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Formatter     │  Receives raw rows + metadata
│  formatter.py    │  Generates human-readable answer string
└────────┬─────────┘
         │
         ▼
{ "intent": {...}, "data": {...}, "answer": "User names created this month: ..." }
```

---

## Pipeline Explained

| Stage | File | Responsibility |
|---|---|---|
| Intent Parser | `app/query/intent_parser.py` | Calls GPT-4o-mini, returns structured intent JSON |
| Schema Registry | `app/query/registry.py` | Single source of truth for tables, fields, and filter columns |
| Planner | `app/query/planner.py` | Validates intent, resolves entity, builds Query DSL |
| Executor | `app/query/executor.py` | Executes SQLAlchemy query, handles name search & time filters |
| Formatter | `app/query/formatter.py` | Converts raw data into a human-readable answer |

**Key design principle:** each stage is a pure transformation. The planner never touches the database; the executor never builds response strings; the formatter has no SQLAlchemy imports.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| AI | OpenAI GPT-4o-mini |
| Auth | JWT (python-jose) |
| Password hashing | bcrypt (passlib) |
| Runtime | Python 3.9+ / Uvicorn |

---

## Example Queries & Responses

### Count query
```
Question: "How many products do we have?"

Response:
{
  "answer": "Found 10 products.",
  "intent": { "intent": "count", "entity": "products" }
}
```

### Field selection (metrics)
```
Question: "Show me user names"

Response:
{
  "answer": "User names: Ali Hassan, Sara Khan, Ahmed Raza, ..."
}
```

### Time-filtered count
```
Question: "How many orders today?"

Response:
{
  "answer": "Found 1 orders created today."
}
```

### Time-filtered list
```
Question: "Show me orders from this month"

Response:
{
  "answer": "Orders created this month:\n- Order #5 — total $399.99\n- Order #6 — total $149.97\n..."
}
```

### Product search (entity fallback)
```
Question: "Find me a laptop"

Response:
{
  "answer": "Found 1 product: Laptop Pro 15 — $1299.99 (42 in stock)"
}
```

### Multi-field selection
```
Question: "Show me user names and emails"

Response:
{
  "answer": "Users:\n- Ali Hassan (ali@example.com)\n- Sara Khan (sara@example.com)\n..."
}
```

---

## Local Setup

### Prerequisites
- Python 3.9+
- PostgreSQL running locally
- An OpenAI API key

### 1. Clone and create environment
```bash
git clone <your-repo-url>
cd Analtix
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic \
            python-dotenv python-jose passlib bcrypt openai
```

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres@localhost:5432/fastapi_db
OPENAI_API_KEY=sk-...          # your OpenAI key
SECRET_KEY=any-long-random-string
```

### 4. Create the database
```bash
psql -U postgres -c "CREATE DATABASE fastapi_db;"
```

### 5. Seed the database
```bash
python seed.py
```

This drops and recreates all tables, then inserts:
- 10 users (password: `password123` for all)
- 10 products
- 15 orders, spread across the last 60 days

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

API is live at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## API Usage

### Step 1 — Get a token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ali@example.com", "password": "password123"}'
```

Response:
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### Step 2 — Query the API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"question": "How many orders were placed this month?"}'
```

Response:
```json
{
  "intent": { "intent": "count", "entity": "orders", "time_range": "this month" },
  "data": { "type": "single", "name": "orders_count", "value": 6, "meta": {...} },
  "answer": "Found 6 orders created this month."
}
```

### Error response format

When a query cannot be processed, the API returns:
```json
{
  "error": true,
  "message": "Could not understand the question — please try rephrasing it.",
  "stage": "intent"
}
```

`stage` is one of: `intent` | `planner` | `executor` | `formatter` | `unknown`

---

## Supported Query Types

| Type | Example |
|---|---|
| Count | "How many users do we have?" |
| Count with time | "How many orders today?" / "this week" / "this month" |
| List all | "Show me all products" |
| Field selection | "Show me user names and emails" |
| Name search | "Find me a laptop" |
| Time-filtered list | "Show me users created this month" |

---

## Project Structure

```
Analtix/
├── app/
│   ├── main.py               # FastAPI app, table creation, router registration
│   ├── logger.py             # Shared logging config
│   ├── auth/
│   │   ├── hash.py           # bcrypt password hashing
│   │   ├── jwt.py            # JWT token creation
│   │   └── deps.py           # JWT validation dependency
│   ├── db/
│   │   ├── database.py       # SQLAlchemy engine + Base
│   │   └── session.py        # DB session dependency
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   ├── query/                # Core pipeline
│   │   ├── exceptions.py     # PipelineError
│   │   ├── registry.py       # Schema registry (tables + fields)
│   │   ├── intent_parser.py  # GPT-4o-mini → intent JSON
│   │   ├── planner.py        # Intent → Query DSL
│   │   ├── executor.py       # Query DSL → SQLAlchemy → data
│   │   └── formatter.py      # Data → human-readable answer
│   ├── routes/
│   │   ├── auth.py           # /auth/register, /auth/login
│   │   ├── query.py          # /query (protected)
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   └── schemas/              # Pydantic request/response models
├── seed.py                   # Database seed script
├── .env.example              # Environment variable template
└── README.md
```
