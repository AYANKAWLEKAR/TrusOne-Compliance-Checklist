# TrusOne Compliance Checklist

Monorepo for the Chemical Compliance MVP. The project contains:

- `frontend/`: Next.js App Router UI for collecting company profile inputs and rendering the compliance report
- `backend/`: FastAPI service for retrieval, orchestration, ingestion, and external API wrappers
- `supabase/`: Supabase CLI config and checked-in SQL migrations for the shared PostgreSQL + pgvector schema

## Architecture

- Frontend runs natively with Next.js
- Backend runs natively with FastAPI
- Database runs in a shared Supabase PostgreSQL project with the `vector` extension enabled
- Schema changes are managed through Supabase CLI migrations checked into the repo

## Prerequisites

- Node.js 22+
- Python 3.13+
- [Supabase CLI](https://supabase.com/docs/guides/cli)

## Quick Start

1. Copy environment templates:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

2. Authenticate and link the repo to the shared Supabase project:

```bash
supabase login
supabase link --project-ref <your-project-ref>
```

3. Apply the checked-in schema migrations to the linked Supabase project:

```bash
supabase db push
```

4. Set up and run the backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

5. Install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

6. Open `http://localhost:3000`

## Development Workflow

- `POST /api/compliance/report` builds the four-section compliance response with citations
- `POST /api/geoip/resolve` proxies geo-IP lookups through the backend
- `POST /api/ingest/documents` ingests regulatory text into Supabase Postgres/pgvector
- `GET /api/health` checks API and database connectivity

## Collaboration Rules

- Treat Supabase CLI migrations in `supabase/migrations/` as the schema source of truth.
- Do not make schema-only changes in the Supabase dashboard without creating a matching repo migration.
- Before starting schema work:
  1. pull the latest branch
  2. create a new migration with `supabase migration new <name>`
  3. review the generated SQL in a PR
  4. apply changes to the shared project with `supabase db push`
- Keep data seeding separate from schema migration unless a migration explicitly requires reference data.

## Notes

- The seed dataset is intentionally small and meant for local development only.
- Third-party APIs are wrapped in backend tools with timeout, retry, and caching hooks.
- The backend still connects with `DATABASE_URL`; the only change is that it should point to the hosted Supabase Postgres instance.
