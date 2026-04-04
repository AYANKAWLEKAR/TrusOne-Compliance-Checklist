# Supabase Workflow

This directory is the schema source of truth for the project database.

## Supabase CLI install

If `brew install supabase/tap/supabase` fails (e.g. Xcode/CLT version checks), install the binary to your user path (Apple Silicon):

```bash
mkdir -p ~/.local/bin
curl -fsSL https://github.com/supabase/cli/releases/latest/download/supabase_darwin_arm64.tar.gz | tar -xz -C ~/.local/bin
chmod +x ~/.local/bin/supabase
```

Ensure `~/.local/bin` is on your `PATH` (e.g. in `~/.zshrc`), then open a new terminal or run `source ~/.zshrc`.

## Team migration flow

```bash
supabase login
supabase link --project-ref <project-ref>
supabase migration new <name>
supabase db push
```

## Notes

- Keep schema changes in `supabase/migrations/`.
- Avoid dashboard-only schema edits unless they are immediately backfilled into a migration.
- Seed data should be run intentionally through backend ingestion scripts or a separate seed process.
