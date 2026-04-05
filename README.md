# Finance Intelligence System

A backend system for managing personal financial records and generating meaningful financial insights — built with FastAPI, SQLAlchemy, and Python 3.11.

The goal of this project was not just to build a CRUD API, but to design something that a real finance application could run on: one with a clean separation of concerns, predictable error handling, and analytics that actually tell you something useful about your spending.

---

## What it does

Users can log income and expense transactions, filter and export them, and get back analytics that go beyond simple totals — monthly breakdowns, category rankings, savings rate, and a spending trend engine that tells you whether you're doing better or worse than last month.

Access is role-gated: a **Viewer** can read and export, an **Analyst** can access the full analytics suite, and an **Admin** can create, update, and delete records and manage users.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Framework | FastAPI | Async-native, automatic OpenAPI docs, clean dependency injection |
| Database | SQLite / PostgreSQL | SQLite for zero-config evaluation; swap to PostgreSQL in one env variable |
| ORM | SQLAlchemy 2.0 (async) | Type-safe, supports both databases, integrates cleanly with FastAPI |
| Validation | Pydantic v2 | Fast, declarative, excellent error messages |
| Auth | JWT via python-jose | Stateless, no session store needed |
| Password hashing | passlib + bcrypt | Industry-standard, safe defaults |
| Logging | Loguru | Structured, rotating, coloured output with one line of setup |
| Testing | pytest + pytest-asyncio + httpx | In-memory SQLite test DB, no mocking of the HTTP layer |

---

## Architecture

The project follows a strict layered architecture. Each layer has one responsibility and only communicates with the layer directly below it.

```
Request
   │
   ▼
┌─────────────────────────────────┐
│          API Layer              │  Route handlers — thin, no business logic
│   app/api/v1/{resource}.py      │  Role guards applied via Depends()
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│        Service Layer            │  Business logic, orchestration
│   app/services/{resource}.py    │  Raises typed exceptions on rule violations
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│       Repository Layer          │  Database queries only — no logic
│   app/repositories/{repo}.py    │  Generic BaseRepository[T] shared across models
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│         Model Layer             │  SQLAlchemy ORM definitions
│   app/models/{model}.py         │  UUID primary keys, timestamps, indexed fields
└─────────────────────────────────┘

In parallel:
┌─────────────────────────────────┐
│       Analytics Module          │  Pure functions — no database access
│   app/analytics/{engine,        │  Takes a list of transactions, returns metrics
│                  insights}.py   │  Fully unit-testable in isolation
└─────────────────────────────────┘

┌─────────────────────────────────┐
│         Core Layer              │  Config, security, exceptions, logging
│   app/core/{config,security,    │  Used everywhere, depends on nothing
│             exceptions}.py      │
└─────────────────────────────────┘
```

The analytics engine deserves a specific mention: it's a collection of pure functions that operate only on a list of transaction objects. No database calls happen inside it. This means it can be tested completely independently, and the same logic can be reused in different contexts (batch processing, reporting) without touching the database layer.

---

## Project structure

```
Finance-Intelligence-System/
├── app/
│   ├── api/
│   │   ├── deps.py                  # JWT decoding + role-enforcement dependencies
│   │   └── v1/
│   │       ├── router.py            # Aggregates all routers under /api/v1
│   │       ├── auth.py              # POST /auth/signup, /auth/login
│   │       ├── transactions.py      # Full CRUD + filtering + export
│   │       ├── analytics.py         # Summary, monthly, category, insights
│   │       └── users.py             # User listing and role management
│   ├── analytics/
│   │   ├── engine.py                # Pure computation functions
│   │   └── insights.py              # Human-readable insight generator
│   ├── core/
│   │   ├── config.py                # pydantic-settings reads from .env
│   │   ├── security.py              # bcrypt hashing + JWT encode/decode
│   │   ├── exceptions.py            # AppException hierarchy (400–422)
│   │   └── logging.py               # Loguru setup with rotation
│   ├── db/
│   │   ├── base.py                  # DeclarativeBase + TimestampMixin
│   │   └── session.py               # Async engine + get_db dependency
│   ├── models/
│   │   ├── user.py                  # User with role enum (viewer/analyst/admin)
│   │   └── transaction.py           # Transaction with indexed fields
│   ├── repositories/
│   │   ├── base.py                  # Generic CRUD — get, create, update, delete
│   │   ├── user_repo.py             # User-specific queries
│   │   └── transaction_repo.py      # Filtering, sorting, pagination
│   ├── schemas/
│   │   ├── common.py                # SuccessResponse[T], PaginatedResponse[T]
│   │   ├── user.py                  # UserCreate, UserRead, RoleUpdate
│   │   ├── transaction.py           # TransactionCreate/Update/Read/Filter
│   │   └── analytics.py             # SummaryResponse, MonthlyEntry, etc.
│   ├── services/
│   │   ├── auth_service.py          # Registration + login with duplicate checks
│   │   ├── transaction_service.py   # CRUD with ownership enforcement
│   │   ├── analytics_service.py     # Loads transactions, delegates to engine
│   │   ├── user_service.py          # User management + role changes
│   │   └── export_service.py        # Streams CSV / JSON without pagination
│   └── tests/
│       ├── conftest.py              # In-memory SQLite fixtures + async client
│       ├── test_auth.py             # Registration, login, error cases
│       ├── test_transactions.py     # Full CRUD, validation, RBAC, pagination
│       └── test_analytics.py        # Engine unit tests — no DB needed
├── scripts/
│   └── seed.py                      # Creates 3 users + ~300 realistic transactions
├── logs/                            # Runtime log files (gitignored)
│   └── .gitkeep
├── main.py                          # App factory, middleware, exception handlers
├── pytest.ini                       # Test config — asyncio mode, test paths
├── requirements.txt                 # All dependencies pinned
├── .env                             # Local config (do not commit in production)
├── .env.example                     # Template — copy to .env and fill in values
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Getting started

### Option 1 — Docker (recommended)

This is the fastest path and the one that most closely mirrors a real deployment.

**Prerequisites:** Docker Desktop must be installed and running.

```bash
# 1. Clone / download the project and enter the directory
cd Finance-Intelligence-System

# 2. Build and start the container
docker compose build
docker compose up -d

# 3. Load sample data (3 users + ~300 transactions across 12 months)
docker compose exec api python scripts/seed.py

# 4. Open the interactive API docs
#    http://localhost:8000/docs
```

To stop:
```bash
docker compose down          # Keeps data intact
docker compose down -v       # Also deletes the database volume
```

---

### Option 2 — Local (Python virtual environment)

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. The .env file is already configured for SQLite out of the box
#    No changes needed for local evaluation

# 4. Load sample data
python scripts/seed.py

# 5. Start the server
uvicorn main:app --reload

# API:       http://localhost:8000
# Docs:      http://localhost:8000/docs
# ReDoc:     http://localhost:8000/redoc
```

---

## Seeded accounts

The seed script creates three accounts with 12 months of realistic transaction history:

| Role | Email | Password | Can do |
|------|-------|----------|--------|
| Admin | admin@finance.io | Admin@1234 | Everything |
| Analyst | analyst@finance.io | Analyst@1234 | Read + full analytics |
| Viewer | viewer@finance.io | Viewer@1234 | Read + export only |

---

## Running the tests

```bash
pytest -v
```

The test suite uses an in-memory SQLite database — no setup needed, no side effects on the real database.

```
app/tests/test_analytics.py::test_compute_totals               PASSED
app/tests/test_analytics.py::test_savings_rate_normal          PASSED
app/tests/test_analytics.py::test_savings_rate_zero_income     PASSED
app/tests/test_analytics.py::test_category_breakdown_expense   PASSED
app/tests/test_analytics.py::test_monthly_summary_count        PASSED
app/tests/test_analytics.py::test_spending_trend_increased     PASSED
app/tests/test_analytics.py::test_build_summary_empty          PASSED
app/tests/test_auth.py::test_signup_success                    PASSED
app/tests/test_auth.py::test_signup_duplicate_email            PASSED
app/tests/test_auth.py::test_login_success                     PASSED
app/tests/test_auth.py::test_login_wrong_password              PASSED
app/tests/test_auth.py::test_login_unknown_email               PASSED
app/tests/test_transactions.py::test_create_transaction_requires_auth  PASSED
app/tests/test_transactions.py::test_viewer_cannot_create      PASSED
app/tests/test_transactions.py::test_create_and_read_transaction PASSED
app/tests/test_transactions.py::test_invalid_amount_rejected   PASSED
app/tests/test_transactions.py::test_invalid_date_rejected     PASSED
app/tests/test_transactions.py::test_update_transaction        PASSED
app/tests/test_transactions.py::test_delete_transaction        PASSED
app/tests/test_transactions.py::test_list_transactions_pagination PASSED

22 passed in 4.75s
```

---

## API reference

Every response — success or error — uses the same envelope shape.

**Success:**
```json
{ "status": "success", "data": { ... } }
```

**Paginated list:**
```json
{
  "status": "success",
  "data": [ ... ],
  "meta": { "total": 84, "page": 1, "page_size": 20, "total_pages": 5 }
}
```

**Error:**
```json
{ "status": "error", "message": "Invalid or expired token.", "code": 401 }
```

---

### Authentication

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/v1/auth/signup` | Public | Create a new account |
| POST | `/api/v1/auth/login` | Public | Get a JWT access token |

**Login request:**
```json
{ "email": "admin@finance.io", "password": "Admin@1234" }
```

**Login response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": { "id": "...", "email": "...", "role": "admin" }
  }
}
```

Pass the access token in every subsequent request:
```
Authorization: Bearer eyJ...
```

---

### Transactions

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/v1/transactions` | Viewer+ | List with filters and pagination |
| POST | `/api/v1/transactions` | Admin | Create a record |
| GET | `/api/v1/transactions/{id}` | Viewer+ | Get a single record |
| PUT | `/api/v1/transactions/{id}` | Admin | Update a record |
| DELETE | `/api/v1/transactions/{id}` | Admin | Delete a record |
| GET | `/api/v1/transactions/export` | Viewer+ | Download as CSV or JSON |

**Create / update request body:**
```json
{
  "amount": 52000.00,
  "type": "income",
  "category": "Salary",
  "date": "2024-06-01",
  "description": "June salary"
}
```

**Query parameters for the list endpoint:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | `income` \| `expense` | — | Filter by type |
| `category` | string | — | Partial match, case-insensitive |
| `start_date` | YYYY-MM-DD | — | Range start |
| `end_date` | YYYY-MM-DD | — | Range end |
| `sort_by` | `date` \| `amount` | `date` | Sort field |
| `sort_order` | `asc` \| `desc` | `desc` | Sort direction |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Records per page (max 100) |

**Export:**
```
GET /api/v1/transactions/export?fmt=csv
GET /api/v1/transactions/export?fmt=json
```
All active filters apply; pagination is ignored and all matching records are exported.

---

### Analytics

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/v1/analytics/summary` | Viewer+ | Overall financial snapshot |
| GET | `/api/v1/analytics/monthly` | Analyst+ | Month-by-month breakdown |
| GET | `/api/v1/analytics/category` | Analyst+ | Category breakdown for income or expense |
| GET | `/api/v1/analytics/insights` | Analyst+ | Human-readable insights and spending trend |

**Summary response:**
```json
{
  "total_income": 728528.74,
  "total_expense": 385590.21,
  "current_balance": 342938.53,
  "savings_rate": 47.07,
  "transaction_count": 106,
  "top_expense_category": "Rent",
  "top_income_category": "Salary",
  "recent_transactions_count": 4
}
```

**Insights response:**
```json
{
  "spending_trend": "decreased",
  "spending_change_pct": -13.13,
  "top_spending_category": "Rent",
  "savings_rate": 47.07,
  "insights": [
    "✅  Spending decreased by 13.1% in December compared to November — great job!",
    "🌟  Excellent savings rate of 47.1%! You are on track for strong financial health.",
    "🏷️   Your top expense category is 'Rent'. Review if this aligns with your goals.",
    "📅  Your best financial month so far was June 2024 with a balance of ₹96,241.58."
  ],
  "alerts": []
}
```

---

### User management (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List all users |
| PUT | `/api/v1/users/{id}/role` | Change a user's role |
| DELETE | `/api/v1/users/{id}` | Delete a user and all their records |

---

## Role-based access control

| Action | Viewer | Analyst | Admin |
|--------|:------:|:-------:|:-----:|
| View own transactions | ✅ | ✅ | ✅ |
| Export transactions | ✅ | ✅ | ✅ |
| View financial summary | ✅ | ✅ | ✅ |
| Monthly / category analytics | ❌ | ✅ | ✅ |
| Spending insights | ❌ | ✅ | ✅ |
| Create / update / delete transactions | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

Role enforcement is implemented as injectable FastAPI dependencies (`require_viewer`, `require_analyst`, `require_admin`) applied at the route level — not scattered through business logic.

---

## Switching to PostgreSQL

Update `.env` (and, if running locally, install `asyncpg`):

```bash
# .env
DATABASE_URL="postgresql+asyncpg://finance:finance_pass@localhost:5432/finance_db"
```

```bash
pip install asyncpg
```

For Docker, uncomment the `db` service block in `docker-compose.yml` and add a `depends_on` to the `api` service. The application code does not change at all — SQLAlchemy handles the rest.

---

## Design decisions

**Why async throughout?** Using `AsyncSession` from SQLAlchemy 2.0 keeps the server from blocking on I/O. For a finance API that might fan out to multiple queries per request (transactions + analytics), this matters.

**Why a Generic Repository?** `BaseRepository[T]` provides standard CRUD once. Each concrete repository only adds the queries specific to that domain. Adding a new entity means writing maybe 20 lines of new code.

**Why are analytics pure functions?** The analytics engine has no idea a database exists. It takes a list and returns a result. This means tests for analytics logic don't need fixtures, sessions, or any async setup — they just call a function and assert on the output.

**Why SQLite as default?** For an evaluation context, asking someone to spin up a database server before they can run a project is friction that doesn't demonstrate anything useful. SQLite works with the exact same SQLAlchemy code; swapping to PostgreSQL is a one-line change.

**Why Loguru over standard logging?** The setup is two lines instead of twenty, rotation and formatting are built in, and the output is actually readable in a terminal.

---

## Assumptions

1. Transactions are **user-scoped** — each user sees only their own records. There is no shared transaction pool.
2. Dates are stored as ISO strings (`YYYY-MM-DD`). The API rejects any other format.
3. Amount must be strictly greater than 0. Zero and negative values are rejected at the schema level.
4. Deletions are **permanent** — there is no soft-delete or archive. User deletion cascades to transactions.
5. The `create_all` startup call handles schema creation. For a production deployment, Alembic migrations would replace this.
6. New registrations receive the `viewer` role by default. Only an Admin can promote a user.
