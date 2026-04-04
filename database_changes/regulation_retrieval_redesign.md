# Database Changes Summary

## Overview

The database layer was redesigned from a document-first model into a scalable regulation/document retrieval model that supports:

- many regulations
- many source documents per regulation
- vector search over regulation summaries
- future vector search over document chunks
- many-to-many links between regulations and source documents

## Schema Changes

The following canonical tables are now part of the active design:

- `regulations`
  - one row per canonical regulation/checklist requirement
  - stores industry, function, geography, jurisdiction level, regulation name/reference, description, and action required
- `regulation_vectors`
  - one vector row per regulation for now
  - stores synthesized search text and `vector(1536)` embeddings
- `source_documents`
  - stores document metadata only
  - supports nullable `raw_text` and nullable storage/source references so the schema works before PDFs are uploaded
- `source_document_chunks`
  - stores chunk text and embeddings for each source document
- `regulation_document_links`
  - supports many-to-many links between regulations and source documents

## Migration Work

Checked-in Supabase SQL migrations now support the redesign:

- `supabase/migrations/20250404120000_init_pgvector.sql`
- `supabase/migrations/20260404150000_regulation_retrieval_model.sql`

The redesign migration:

- drops the retired `documents` / `document_chunks` path
- removes the dummy test table
- creates the new scalable regulation/document tables
- creates the required foreign keys, uniqueness constraints, and vector indexes

## Backend Changes

Implemented code changes include:

- new SQLAlchemy models for:
  - `Regulation`
  - `RegulationVector`
  - `SourceDocument`
  - `SourceDocumentChunk`
  - `RegulationDocumentLink`
- workbook parser for the Excel checklist
- workbook import command:
  - `python -m app.ingestion.import_checklist /path/to/checklist.xlsx`
- regulation-first vector search path
- updated ingestion API route:
  - `POST /api/ingest/regulations/workbook`
- updated compliance fallback logic so regulation-only retrieval works before raw documents are attached

## Workbook Import

Workbook used:

- `/Users/ayankawlekar/Downloads/chemical_storage_compliance.xlsx`

Import result:

- `parsed_regulations`: 37
- `inserted_regulations`: 37
- `updated_regulations`: 0
- `inserted_vectors`: 37

This means every regulation row from the checklist is now represented in the database and is vector-searchable even without raw PDFs attached.

## Verification Completed

### Local tests

- Backend non-integration tests: `11 passed, 3 deselected`
- Frontend tests: `2 passed`

### Live database verification

- Supabase connectivity check passed
- checked-in schema SQL was applied to the configured database
- integration tests passed: `3 passed, 11 deselected`

Integration coverage confirmed:

- database connection works
- `vector` extension exists
- required regulation/document tables exist
- HNSW vector indexes exist

## Notes

- Raw compliance PDFs and source documents have **not** been inserted yet.
- The schema is now ready for many documents per regulation and many regulations per document.
- Future document ingestion should populate `source_documents`, `source_document_chunks`, and `regulation_document_links` without needing another schema redesign.
