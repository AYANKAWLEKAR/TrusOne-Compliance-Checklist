# Backend

FastAPI service for compliance report generation, vector search, ingestion, and external API access.

## Commands

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Apply schema migrations through Supabase CLI from the repo root:

```bash
supabase db push
```

Seed ingestion remains separate and should only be run intentionally against the shared database:

```bash
uv run python -m app.ingestion.seed
```

## Database (Supabase)

Copy **`backend/.env`** from `backend/.env.example` and set `DATABASE_URL`.

- **Do not** wrap the database password in square brackets. Dashboard examples look like `postgres:[YOUR-PASSWORD]`; only the password goes in the URI, without `[` `]`.
- **Direct** connection (`db.<project>.supabase.co:5432`) is **IPv6-only**. If you see `connection refused`, use **Transaction pooler** (`db.<project>.supabase.co:6543`, user `postgres`) or **Session pooler** (`aws-0-<region>.pooler.supabase.com:5432`, user `postgres.<project-ref>`) from Dashboard → **Connect** — both work on IPv4. This app disables prepared statements automatically when the URL uses port **6543** (required for Supabase transaction pooling). It also normalizes `postgresql://` to **psycopg v3** and appends `sslmode=require` for `*.supabase.co` hosts.

## Tests

```bash
uv run pytest
```
