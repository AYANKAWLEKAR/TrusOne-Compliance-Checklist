# Source documents: upload, storage, and database workflow

This guide is for **anyone preparing raw compliance documents** (PDFs, etc.) and for **engineers** wiring uploads into Supabase and the retrieval stack. Share it with collaborators who have access to the source files.

For background on **why** the schema looks like this, see `regulation_retrieval_redesign.md`.

---

## What we are trying to achieve

1. **Keep original files** in **object storage** (cheap, correct format for audits and “open original”).
2. **Store searchable data** in **Postgres (Supabase)**: metadata, links to regulations, text chunks, and **embeddings** so the app (and LLM) can retrieve relevant passages.
3. **Never rely on the LLM reading PDF bytes directly** at question-answering time. The model should receive **retrieved text chunks** (and optional citations), not raw files from a bucket.

---

## Where each kind of data lives

| Location | What goes here |
|----------|----------------|
| **Object storage** (Supabase Storage, S3, GCS, etc.) | Original files: PDFs, Word docs, etc. One object per file; stable path/key. |
| **Postgres table `source_documents`** | **Metadata** about each file: title, type, agency, dates, MIME type, checksum, processing status. **`storage_reference`**: pointer to the object (bucket + key or agreed URI format). Optional **`raw_text`**: full extracted text if you choose to store it (can be large). |
| **Postgres table `source_document_chunks`** | **Chunks** of extracted text plus **`vector(1536)`** embeddings for semantic search. This is what backs **document-level RAG**. |
| **Postgres table `regulation_document_links`** | **Many-to-many** links: which **regulations** (checklist rows) are supported by which **source documents**. |
| **Postgres table `regulations` + `regulation_vectors`** | Already populated from the Excel checklist import: one row per regulation and one embedding for **regulation-level** search. |

**Rule of thumb:** blobs in storage; **everything the LLM searches over** for document content should live in **`source_document_chunks`** (after extraction and embedding).

---

## End-to-end process (conceptual)

```text
Raw file (PDF)
    → upload to object storage
    → insert row in source_documents (metadata + storage_reference)
    → link to regulation(s) via regulation_document_links
    → backend job: download from storage → extract text → chunk → embed
    → insert rows in source_document_chunks
    → set source_documents.ingestion_status to success (or record failure)
```

1. **Upload** the file to cloud storage (or hand files to engineering if uploads are batch-only at first).
2. **Register** the document in the database with a **`storage_reference`** your backend can resolve (see conventions below).
3. **Associate** each document with the correct **regulation(s)** using `regulation_document_links` (by `regulation_id`, or by matching stable identifiers such as regulation code / reference from the checklist).
4. **Run ingestion** (automated): extract text → chunk → embed → write chunks. Until this runs, the file exists but is not searchable at the chunk level.

---

## Collaborator checklist (raw docs owner)

Use this so files can be ingested without ambiguity.

1. **Prefer one primary file per logical source** (e.g. one PDF per statute or CFR section if that matches how you cite it). If one PDF covers many regulations, we still store **one** `source_document` row; we attach **multiple** `regulation_document_links` to that row.
2. **Use consistent naming** so humans and scripts can match regulations:
   - Include **regulation code or reference** in the filename or in a sidecar spreadsheet (e.g. `40_CFR_262.34.pdf` or a CSV column `regulation_code_reference` matching the checklist).
3. **Provide a mapping file** (CSV/Excel) if there are many files, with columns such as:
   - `file_name` or `storage_path`
   - `regulation_code_reference` (must match the checklist / `regulations` table)
   - optional: `title`, `agency`, `effective_date`
4. **Avoid password-protected or corrupted PDFs**; extraction will fail until the file is fixed.
5. **Note language**: non-English or scanned-only PDFs may need OCR; call that out so engineering can enable the right pipeline.

---

## Storage reference conventions

The exact string in `storage_reference` must match what the **backend** uses to download the file. Examples:

| Setup | Example `storage_reference` |
|-------|-------------------------------|
| Supabase Storage | `regulations/2024/cfr-262-34.pdf` (bucket name configured in app env) or `my-bucket/regulations/...` if you encode bucket + key in one field—**pick one convention and document it in the backend**. |
| AWS S3 | `s3://my-bucket/prefix/file.pdf` or bucket + key in two config fields. |

**Do not** store secrets in the database. Store only **locators**; credentials stay in environment / IAM.

---

## Linking documents to regulations

- Regulations are keyed in the app by the **canonical identity** used in the checklist import (industry, function, geography, level, **`regulation_code_reference`**, etc.).
- Each **link** is one row in **`regulation_document_links`**: `regulation_id`, `source_document_id`, optional `relationship_type` (e.g. `supports`), optional `citation_note`.
- One **source document** can link to **many** regulations; one **regulation** can link to **many** source documents.

If the collaborator supplies **`regulation_code_reference`** plus filename, engineering can script: resolve `regulations.id` by that reference, then insert links.

---

## How the LLM uses this (runtime)

1. **Regulation-first**: optional search on **`regulation_vectors`** to find relevant checklist rows.
2. **Document evidence**: vector search on **`source_document_chunks`**, optionally filtered by `source_document_id` or by regulations connected through **`regulation_document_links`**.
3. **Prompt**: pass the **top chunk texts** (and titles/regulation names) into the model. Optionally include a **signed URL** or app link to open the original PDF in the UI—**not** by streaming the whole PDF into the model context.

---

## Supabase-specific notes

- **Migrations** for these tables live under `supabase/migrations/`; apply with the Supabase CLI (`supabase db push`) against the target project.
- **Supabase Storage**: uploads typically use the **service role** on the server for private buckets; the browser uses **signed URLs** for download. Store the **object path** (and bucket if not fixed) in `storage_reference`.
- **pgvector**: chunk embeddings use the same embedding model dimension as **`regulation_vectors`** (1536 in the current design); keep models aligned across tables.

---

## Operational status field

Use **`source_documents.ingestion_status`** (e.g. `pending`, `processing`, `ready`, `failed`) so the UI and support know whether chunk search is available for that file. Failed runs should log the error in **`external_metadata`** or your logging system, not only in the UI.

---

## What still requires engineering work

The **schema** supports documents and chunks; the **product** still needs implemented pieces such as:

- HTTP endpoint(s) for upload or batch import from a mapping file.
- Background worker or job queue for extract → chunk → embed.
- Text extraction library (e.g. PDF text layers) and optional OCR for scans.
- Vector search queries that join regulations ↔ documents ↔ chunks.

This document describes **process and data placement** so collaborators and developers stay aligned until those features are shipped.

---

## Related docs

- `database_changes/regulation_retrieval_redesign.md` — schema summary and migration filenames.
- `backend/README.md` — local API and environment setup.
