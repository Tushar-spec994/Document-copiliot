# Backend — Document Copilot API

FastAPI service powering chat orchestration, hybrid retrieval, and grounded citation verification.

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager

## Quick Start

### 1. Environment Setup

Ensure `.env` exists in the `backend/` directory (copied from `.env.example`):

```bash
cp .env.example .env
```

Fill in your Supabase credentials, Postgres connection string, and Gemini API key.

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Development Server

You can run the server in either of two ways from the `backend/` folder:

**Option A (Recommended — with live reload):**
```bash
uv run uvicorn app.main:app --reload
```

**Option B (Direct execution):**
```bash
uv run python app/main.py
```

The API will be available at:
- **Base URL:** http://127.0.0.1:8000
- **Interactive Swagger Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health

---

## Common Commands

| Task | Command |
| --- | --- |
| **Run Dev Server** | `uv run uvicorn app.main:app --reload` |
| **Apply Migrations** | `uv run alembic upgrade head` |
| **Generate Migration** | `uv run alembic revision --autogenerate -m "<description>"` |
| **Run Tests** | `uv run pytest` |
| **Lint Code** | `uv run ruff check .` |
