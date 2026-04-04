# Legacy Alembic Reference

The project originally used Alembic with revision `20250404_0001` to create the initial pgvector schema.

That migration has been replaced by the Supabase SQL migration in:

- `supabase/migrations/20250404120000_init_pgvector.sql`

For historical reference, use git history from the migration PR rather than reviving Alembic as an active schema workflow.
