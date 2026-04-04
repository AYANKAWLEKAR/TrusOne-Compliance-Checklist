# Test Results

## Summary

This document records verification status for the current Supabase-oriented project setup.

Overall status: backend and frontend application tests pass locally, and the repository is now configured to use Supabase CLI migrations as the schema source of truth.

Deferred: live Supabase verification still requires a linked project plus valid credentials.

## Backend Unit Tests

- Status: Passed
- Command: `cd backend && .venv/bin/pytest -m 'not integration'`
- Result: `8 passed, 2 deselected in 2.79s`
- Coverage notes:
  - chunking utilities
  - compliance schema citation enforcement
  - HTTP retry behavior
  - vector size filter parsing
  - geo-IP response formatting

## Backend Connectivity Tests

- Status: Pending live Supabase verification
- Command: `cd backend && DATABASE_URL='<supabase-db-url>' .venv/bin/pytest`
- Verify:
  - Supabase Postgres accepts connections
  - `vector` extension exists
  - `documents` and `document_chunks` tables exist after `supabase db push`

## Frontend Unit Tests

- Status: Passed
- Command: `cd frontend && npm test`
- Result: `2 passed`
- Notes: Frontend remains database-agnostic because it only calls the backend.

## Frontend Build Verification

- Status: Last known passing result from the current app snapshot
- Command: `cd frontend && npm run build`
- Notes: Re-run once Supabase credentials are added and final README/env polish is complete.

## Supabase Migration Verification

- Status: Pending
- Command: `supabase login`
- Command: `supabase link --project-ref <project-ref>`
- Command: `supabase db push`
- Verify:
  - migration creates `documents`
  - migration creates `document_chunks`
  - `vector` extension exists
  - GIN and HNSW indexes exist

## Observations

- The repo no longer treats Docker or Alembic as the expected database workflow.
- The backend lockfile was regenerated after removing Alembic from the dependency set.
- Seed ingestion remains intentionally separate from schema migration.
- A final live verification pass requires Supabase CLI plus the project reference and database credentials.
