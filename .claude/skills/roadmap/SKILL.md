---
name: roadmap
description: End-to-end backend roadmap for building a production-ready GraphRAG data platform with Nango, Gmail, Notion, Postgres, pgvector, Neo4j, and OpenAI. This skill provides concrete implementation steps for local development, database/model design, document ingestion, entity extraction, job orchestration, pipeline composition, RAG querying with context/citations, Nango integration, security, observability, and a "definition of done". Use this as a template or reference for orchestrating all backend components, including API endpoints, worker pipelines, chunking, embedding, knowledge graph upserts, and RAG-based question answering with source-linked citations. Target audience: backend developers, tech leads, and architects building composable, multi-source, knowledge-driven APIs.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

## Backend Tickets (du allein, mit Nango, Gmail + Notion, kein Frontend)

### 0) Repo & Infra

**B0.1 – Docker Compose Dev Stack**

* Services: `api`, `worker`, `postgres`, `neo4j`
* Healthchecks + env wiring
  **Done:** `docker compose up` bringt alles hoch.

**B0.2 – Config & Secrets**

* `.env.example` mit: DB URLs, Neo4j creds, Nango secret, OpenAI key (oder anderes LLM), Notion/Gmail scopes nur als Doku
  **Done:** local setup in <5 min.

---

## 1) Datenmodell (Postgres) + Migrations

**B1.1 – Postgres Schema**
Tabellen:

* `workspaces(id, name, created_at)`
* `source_connections(id, workspace_id, source_type ENUM('gmail','notion'), nango_connection_id, external_account_id, status, config_json, created_at, updated_at)`
* `documents(id, workspace_id, source_type, external_id, url, title, author_name, author_email, created_at, updated_at, content_text, content_hash)`
* `document_chunks(id, workspace_id, document_id, idx, text, start_offset, end_offset, embedding VECTOR, created_at)`
* `jobs(id, workspace_id, type, payload_json, status, attempts, last_error, run_after, created_at, updated_at)`
* `entity_mentions(id, workspace_id, document_id, chunk_id, entity_key, entity_type, entity_name, confidence)` (optional aber hilft)
  Indexes/constraints:
* unique `(workspace_id, source_type, external_id)` on `documents`
* index `(workspace_id, document_id)` on chunks
* index `(status, run_after)` on jobs
  **Done:** migrations + pgvector enabled.

**B1.2 – pgvector Setup**

* `CREATE EXTENSION vector;`
* Index für embedding search (MVP: ivfflat oder hnsw; falls zu viel, erstmal ohne, aber extension muss da sein)
  **Done:** embeddings speicherbar + similarity query läuft.

---

## 2) Neo4j Schema (Knowledge Graph)

**B2.1 – Constraints/Indexes**

* Node labels: `Person`, `Company`, `Topic`, `Document`
* Required props: `workspace_id`, `key`
* Unique constraint: `(workspace_id, key)` pro label (oder global via single `Entity` label)
  **Done:** Cypher script `neo4j_init.cypher` läuft idempotent.

**B2.2 – Graph “Evidence” Standard**
Relationship properties (mindestens):

* `document_id` (uuid/string)
* `chunk_id` (uuid/string)
* `confidence` (float)
  **Done:** jedes Knowledge-Fact ist auf Evidence zurückführbar.

---

## 3) Job System (Worker) – ohne extra Queue

**B3.1 – Job Runner**

* Polling loop: claim jobs via `SELECT ... FOR UPDATE SKIP LOCKED`
* Status: `queued -> running -> done|failed`
* Retries: `attempts < N`, backoff (`run_after`)
  **Done:** crash-safe, parallelisierbar (später).

**B3.2 – Job Types**

* `PROCESS_DOCUMENT` (fan-out)
* `CHUNK_DOCUMENT`
* `EMBED_CHUNKS`
* `EXTRACT_ENTITIES_RELATIONS`
* `UPSERT_GRAPH`
  **Done:** ingest doc erzeugt Pipeline zuverlässig.

---

## 4) API: Workspace + Ingest + Query

**B4.1 – Workspace Minimal**

* `POST /v1/workspaces` → `{id}`
* `GET /v1/health`
  **Done:** Grundlage fürs scoping.

**B4.2 – Generic Ingest Endpoint (wichtig für Nango Webhook)**

* `POST /v1/ingest/document`
  Body:

```json
{
  "workspace_id":"...",
  "source_type":"gmail|notion",
  "external_id":"...",
  "url":"...",
  "title":"...",
  "author_name":"...",
  "author_email":"...",
  "created_at":"...",
  "updated_at":"...",
  "content_text":"..."
}
```

Behavior:

* upsert `documents` by unique key
* if content_hash changed/new: enqueue `PROCESS_DOCUMENT`
  **Done:** beliebige Quelle kann Dokumente pushen.

**B4.3 – Query Endpoint (GraphRAG)**

* `POST /v1/query`
  Body:

```json
{ "workspace_id":"...", "prompt":"...", "depth":2, "top_k_chunks":20 }
```

Response:

```json
{ "answer":"...", "citations":[{"url":"...","title":"...","quote":"...","document_id":"...","chunk_id":"..."}], "debug":{...}}
```

Flow:

1. embed(prompt)
2. pgvector top_k chunk search (workspace-scoped)
3. context builder (Neo4j traversal + evidence)
4. LLM answer constrained to provided context
   **Done:** echtes “knowledge layer query” mit Quellen.

---

## 5) Nango Integration (Gmail + Notion)

**B5.1 – Nango Webhook Receiver**

* `POST /v1/webhooks/nango`
* Verify signature/secret (sofern Nango das anbietet)
* Parse event → route by `provider` + `syncName`
  **Done:** ihr bekommt payloads rein, sicher.

**B5.2 – Nango Connection Registry**

* Endpoint oder CLI to register:

  * `POST /v1/sources/nango/register` `{workspace_id, source_type, nango_connection_id, external_account_id?}`
    **Done:** workspace ↔ nango connection mapping steht.

**B5.3 – Gmail Sync Normalizer**
Aus Nango Gmail payload:

* map message to `documents`:

  * `external_id = gmail_message_id`
  * `title = subject`
  * `author_email/name = from`
  * `created_at = internalDate`
  * `content_text = plain text` (strip HTML)
  * `url = gmail web link` (oder leave null)
* enqueue via `/ingest/document` intern
  **Done:** Gmail mails landen als docs + pipeline läuft.

**B5.4 – Notion Sync Normalizer**
Aus Nango Notion payload:

* `external_id = page_id`
* `title`
* `updated_at = last_edited_time`
* `content_text = blocks -> plaintext` (MVP: headings/paragraphs/bullets)
* `url = page url`
  **Done:** Notion pages landen als docs + pipeline läuft.

**B5.5 – Backfill Trigger**

* `POST /v1/sources/:source_type/backfill` (calls Nango to start sync, oder dokumentiert “start sync in Nango dashboard”)
  **Done:** 1 Befehl → Daten kommen rein.

> Falls Nango API-Aufruf zum Triggern nervt: MVP ok, Sync im Nango UI starten. Wichtig ist Webhook+Normalizer.

---

## 6) Processing: Chunking, Embeddings, Extraction, Upsert

**B6.1 – Chunker**

* deterministic chunking + overlap
* store offsets
  **Done:** chunks sind stabil reproduzierbar.

**B6.2 – Embeddings Writer**

* embed chunk text
* store in pgvector
  **Done:** similarity search liefert sinnvolle chunks.

**B6.3 – Extraction (LLM → strict JSON)**
Prompt: extract minimal entities (`Person`, `Company`, `Topic`) + optional relations.

* Conservative mode: primär `Document MENTIONS Entity`
* Add heuristic entities:

  * Person from email headers
  * Company from email domain (ignore public domains)
    **Done:** extraktion robust, wenig hallucination.

**B6.4 – Entity Resolution**

* Person: email exact → key `person:email:<email>`
* Company: domain exact → key `company:domain:<domain>`
* Topic: normalized label
* fallback: normalized name
  **Done:** dedupe ok.

**B6.5 – Neo4j Upsert**

* Upsert `(:Document {workspace_id, document_id})`
* Upsert entities by key
* Create `(:Document)-[:MENTIONS {document_id, chunk_id, confidence}]->(:Entity)`
  Option: store `entity_mentions` in Postgres for faster traversal seeds.
  **Done:** graph traversal möglich.

---

## 7) Context Builder (Traversal) + Answer Composer

**B7.1 – Seed Entities from Top Chunks**
Option A (recommended): when extracting, write `entity_mentions` rows (chunk→entity_key).
Then:

* get entities mentioned in top_k chunks quickly from Postgres.
  **Done:** seeds ohne extra LLM.

**B7.2 – Neo4j Traversal**
Cypher pattern:

* start entities (keys) → expand up to `depth`
* collect edges with evidence props
* return facts list
  **Done:** context enthält relevante, verlinkte Evidence.

**B7.3 – Answer with Citations**

* Provide the model only: prompt + selected chunk texts + fact list
* Force output format: answer + citation mapping to chunk_ids
* Build citations array with `{url,title,quote}`
  **Done:** Antwort ist nachprüfbar.

---

## 8) Hardening (MVP-sicher)

**B8.1 – Workspace Scoping Everywhere**

* every query filtered by `workspace_id`
  **Done:** keine cross-tenant leaks.

**B8.2 – Idempotency**

* Upsert docs by unique key
* Job fan-out checks content_hash change
  **Done:** webhook spam erzeugt keine Duplikate.

**B8.3 – Observability**

* structured logs + job metrics counters
* store `last_error` on jobs
  **Done:** ihr könnt debuggen.

---

## 9) Context Vaults (Datenpartitionierung)

> Workspace = Mandant (Firma/Team). Context Vault = Datenpartition innerhalb eines Workspace.
> Beispiel: Workspace "Acme Corp" hat Vaults "Sales", "Engineering", "Operations".
> Jede Datenquelle wird einem Vault zugeordnet. Queries können auf einzelne Vaults eingeschränkt werden.

**B9.1 – Context Vault Schema + Migration**

* Neue Tabelle `context_vaults(id, workspace_id, name, description, is_default, created_at, updated_at)`
* `vault_id` (NOT NULL) auf: `source_connections`, `documents`, `document_chunks`, `entity_mentions`
* NICHT auf `jobs` (vault transitiv via document_id)
* Unique Constraint documents: `(workspace_id, vault_id, source_type, external_id)`
* Migration: Default Vault pro Workspace + Backfill aller bestehenden Rows
  **Done:** Datenmodell unterstützt Vault-Partitionierung.

**B9.2 – Vault CRUD API**

* `POST /v1/vaults` – Vault erstellen
* `GET /v1/vaults?workspace_id=` – Vaults auflisten
* `PATCH /v1/vaults/{vault_id}` – Update Name/Description
* `DELETE /v1/vaults/{vault_id}` – Nur wenn leer, nie Default
* `POST /v1/workspaces` erstellt automatisch Default Vault
  **Done:** Vaults verwaltbar.

**B9.3 – Vault Flow im Ingest-Pfad**

* `POST /v1/ingest/document` bekommt optionales `vault_id` (Default falls leer)
* `POST /v1/sources/nango/register` bekommt optionales `vault_id`
* Backfill + Webhooks: vault_id von SourceConnection erben
* Processing Pipeline: vault_id propagiert von Document → Chunks, EntityMentions, Graph Upsert
  **Done:** Daten landen im richtigen Vault.

**B9.4 – Neo4j Vault Isolation**

* Entity-Nodes (Person/Company/Topic): KEIN vault_id (workspace-global, gleiche Person existiert einmal)
* Document-Nodes: vault_id als Property
* Alle Edges (MENTIONS, WORKS_AT, etc.): vault_id als Property
* Traversal filtert auf Edge-Ebene
  **Done:** Graph-Traversal respektiert Vault-Grenzen.

**B9.5 – Query mit Vault-Filter**

* `POST /v1/query` bekommt optionales `vault_ids: list[uuid]`
* Ohne Filter: alle Vaults im Workspace durchsuchen (backward compatible)
* pgvector-Suche, Seed-Entities, Neo4j-Traversal: alle vault-gefiltert
  **Done:** Queries auf Vault-Ebene einschränkbar.

---

# "Day-by-day" Reihenfolge (schnellster Pfad)

1. B0 + B1 + B2 (compose + schema)
2. B3 + B4.2 (job system + ingest endpoint)
3. B5 (nango webhook + normalizer) + ingest real data
4. B6 (chunk/embed/extract/upsert) end-to-end
5. B4.3 + B7 (query endpoint + traversal + citations)
6. B8 (hardening)
7. B9 (context vaults)

---

## Mini-Definition of Done (damit ihr wisst, ihr seid "fertig")

* Backfill Gmail+Notion via Nango → 200+ docs in Postgres
* Worker baut chunks+embeddings+graph
* `POST /v1/query` beantwortet 3 feste Queries und liefert 5–10 citations mit echten Notion/Gmail Links
* Context Vaults: Daten partitionierbar, Query auf Vault-Ebene einschränkbar

---

## 10) Frontend (Next.js + Supabase + shadcn)

> Next.js App Router mit Supabase Auth und shadcn/ui Komponenten.
> Drei Hauptseiten: Overview (Chat), Context Vaults, Integrations.
> Design: Sidebar-Navigation links, Hauptinhalt rechts.

**F10.1 – Next.js App Setup**

* `npx create-next-app -e with-supabase app`
* shadcn/ui initialisieren
* Tailwind + CSS Variables für Theming
  **Done:** App läuft lokal mit Supabase Auth.

**F10.2 – Layout: Sidebar + Navigation**

* Sidebar links: Logo, Workspace-Selector, Navigation (Overview, Context Vaults, Integrations)
* Bottom: Settings, Help, User Profile mit Avatar
* Responsive: Collapsible auf Mobile
  **Done:** Navigation zwischen Seiten funktioniert.

**F10.3 – Overview Page (Chat Interface)**

* Chat-Input unten
* Nachrichten-Liste mit User/Assistant Bubbles
* Citations als klickbare Links
* Vault-Selector für Query-Scope
  **Done:** User kann Fragen stellen und bekommt Antworten mit Quellen.

**F10.4 – Context Vaults Page**

* Grid mit Vault-Cards (Purple Folder Design wie Referenz-Image)
* Vault-Name + "Used by X tools" Subtitle
* "+ New" Button zum Erstellen neuer Vaults
* Edit/Delete Actions pro Vault
  **Done:** Vaults CRUD über UI.

**F10.5 – Integrations Page (Data Sources)**

* Tabelle: Data Source, Status (Active/Inactive), Last Sync, Actions
* Icons für verschiedene Provider (Gmail, Notion, Drive, etc.)
* "+ Add Integration" Button mit Nango Connect Flow
* Backfill Trigger Button pro Connection
  **Done:** User kann Datenquellen verbinden und Status sehen.

**F10.6 – API Client + Auth Flow**

* Supabase Auth Session an Backend API weiterleiten
* API Client für alle Backend-Endpoints
* Error Handling + Loading States
  **Done:** Frontend kommuniziert sicher mit Backend.

---

## 11) Vector Search Improvements

> Upgrade pgvector with HNSW indexing, cosine similarity, and Cohere reranking for better retrieval quality.

**F11.1 – HNSW Index**

* Add migration `003_hnsw_index.py`
* Create HNSW index on `document_chunks.embedding` with `vector_cosine_ops`
* Parameters: m=16, ef_construction=64
  **Done:** ~100x faster similarity search at scale.

**F11.2 – Cosine Similarity**

* Already using `<=>` operator (cosine distance in pgvector)
* HNSW index configured with `vector_cosine_ops`
* Lower distance = more similar (0-2 range)
  **Done:** Semantically appropriate distance metric for text.

**F11.3 – Cohere Reranking**

* Add `cohere` to requirements.txt
* Add `COHERE_API_KEY` to config
* Two-stage retrieval: fetch 3x candidates, rerank to top_k
* Model: `rerank-v3.5`
* Graceful fallback if API unavailable
  **Done:** Significantly improved retrieval precision.

---

## 12) Vault-Connection Restructure

> Decouple vaults from connections with a many-to-many relationship. Connections exist at workspace level, vaults select which connections to include. Enables flexible data organization.

**F12.1 – Schema Restructure**

* New join table `vault_source_connections(vault_id, source_connection_id)`
* Remove `vault_id` from: `source_connections`, `documents`, `document_chunks`, `entity_mentions`
* Add `source_connection_id` to `documents` (link to ingesting connection)
* Migration `004_vault_connection_restructure.py` with full backfill logic
  **Done:** Cleaner data model with flexible vault membership.

**F12.2 – Model Updates**

* New `VaultSourceConnection` model (join table)
* `SourceConnection`: Remove vault_id, now workspace-level
* `Document`: Replace vault_id with source_connection_id
* `DocumentChunk`, `EntityMention`: Inherit vault via document → connection
  **Done:** Models reflect new architecture.

**F12.3 – Vault Filtering via Connections**

* `context_builder.py`: New `get_connection_ids_for_vaults()` helper
* `top_k_chunks()`: Filter by connection_id via document join
* `seed_entities()`: Filter by connection_id via document join
* `neo4j_traverse_simple()`: Unified graph (no vault filtering on edges)
  **Done:** Vault filtering works through connection membership.

**F12.4 – API Updates**

* `vaults.py`: Manage vault-connection assignments
* `sources.py`: Connections are workspace-level, assign to vaults
* `ingest.py`: Use source_connection_id on documents
* `webhooks.py`: Resolve connection for incoming syncs
  **Done:** APIs support new data model.

**F12.5 – Frontend Updates**

* Vaults page: Show/manage assigned connections
* Integrations page: Assign connections to vaults
  **Done:** UI supports vault-connection management.

---

### Architecture: Before vs After

**Before (vault_id everywhere):**
```
Vault ──1:N──> Connection ──1:N──> Document ──1:N──> Chunk
                                              └──> EntityMention
```

**After (many-to-many via join table):**
```
Workspace ──1:N──> Connection ──1:N──> Document ──1:N──> Chunk
                       │                           └──> EntityMention
                       │
              vault_source_connections (M:N)
                       │
Workspace ──1:N──> Vault
```

**Benefits:**
- Same connection can be in multiple vaults
- Documents stored once, accessible from multiple vaults
- Cleaner separation: connections = data sources, vaults = retrieval scopes
- Unified knowledge graph across workspace (cross-vault discovery)

---

## 13) Nango Frontend Integration

> Enable users to connect their own OAuth data sources through the UI using Nango's frontend SDK and Connect UI. No more manual connection ID entry.

**F13.1 – Backend Connect Session Endpoint**

* `POST /v1/sources/nango/connect-session` – Create session token for frontend OAuth flow
* Request: `{workspace_id, user_id, user_email?, user_display_name?}`
* Response: `{token, expires_at}`
* Calls Nango API `POST /connect/sessions` with `allowed_integrations: ["google-mail", "notion", "google-drive"]`
  **Done:** Backend can create secure session tokens for frontend.

**F13.2 – Frontend SDK Integration**

* Install `@nangohq/frontend` package
* Initialize Nango with connect session token
* Use `openConnectUI()` method to launch OAuth flow
* Handle events: `close`, `connect`
  **Done:** Frontend can initiate OAuth flows.

**F13.3 – Integrations Page Rewrite**

* Remove manual connection ID input form
* Add "Add integration" button that triggers Nango Connect UI
* Session token fetched from backend before opening modal
* On successful connect: refresh connections list
* On modal close: refresh after delay (webhook may have created connection)
  **Done:** User-friendly OAuth integration flow.

**F13.4 – Connection Lifecycle**

* User clicks "Add integration" → backend creates session → Nango UI opens
* User authorizes in Nango UI → Nango sends webhook → backend creates `source_connection`
* Frontend refreshes and shows new connection
* User can trigger "Sync" to backfill data
  **Done:** Complete flow from UI to ingested data.

---

## 14) Google Drive Integration

> Add Google Drive as a data source. Unlike Gmail/Notion (which have inline content), Drive contains **binary files** that require content extraction based on MIME type.

### Architecture Overview

```
Nango OAuth ──> File Metadata Sync ──> Backfill Trigger
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  PROCESS_FILE   │  (new job type)
                                    │     Job         │
                                    └────────┬────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            Google Docs/Sheets         PDF Files              Office Files
            (Export via API)         (pdfplumber)         (python-docx, openpyxl)
                    │                         │                         │
                    └─────────────────────────┴─────────────────────────┘
                                              │
                                              ▼
                                    Standard Ingest Pipeline
                                    (chunk → embed → extract → graph)
```

### Nango Proxy for Content Fetching

Nango's Proxy enables authenticated Google Drive API calls:
```bash
curl "https://api.nango.dev/proxy/drive/v3/files/{fileId}?alt=media" \
  -H "Authorization: Bearer <NANGO-SECRET-KEY>" \
  -H "Provider-Config-Key: google-drive" \
  -H "Connection-Id: <CONNECTION-ID>"
```

For Google Docs/Sheets export:
```bash
curl "https://api.nango.dev/proxy/drive/v3/files/{fileId}/export?mimeType=text/plain" \
  -H "Authorization: Bearer <NANGO-SECRET-KEY>" \
  -H "Provider-Config-Key: google-drive" \
  -H "Connection-Id: <CONNECTION-ID>"
```

---

### Phase 14a: Foundation

**F14a.1 – Nango Integration Setup**

* Add `google-drive` to `SOURCE_TO_PROVIDER` mapping in `sources.py`
* Add `google-drive` to `allowed_integrations` in connect session endpoint
* Add `google-drive` to `SourceType` enum in models
* Add `DEFAULT_MODELS["google-drive"]` for metadata sync
  **Done:** Google Drive appears in Nango Connect UI.

**F14a.2 – Frontend Provider Config**

* Add `google-drive` to `PROVIDERS` in `integrations/page.tsx`
* Add Google Drive icon (folder with Drive colors)
* Provider name: "Google Drive"
* Nango key: `google-drive`
  **Done:** Google Drive shows in integrations table.

**F14a.3 – Nango Proxy Client**

* New module `app/nango/proxy.py`
* `async def proxy_get(connection_id, endpoint, params)` - GET requests
* `async def proxy_get_binary(connection_id, endpoint)` - Binary file downloads
* `async def export_google_doc(connection_id, file_id, mime_type)` - Export Docs/Sheets
* Uses `NANGO_SECRET_KEY` for auth
  **Done:** Backend can make authenticated Google Drive API calls.

**F14a.4 – File Metadata Normalizer**

* New normalizer `normalize_google_drive()` in `normalizers.py`
* Map Nango sync records to document metadata:
  * `external_id` = file ID
  * `title` = file name
  * `url` = web view link
  * `mime_type` = Google MIME type (new field)
  * `content_text` = empty (fetched later)
* Store MIME type for processing decision
  **Done:** File metadata can be synced.

---

### Phase 14b: Google Workspace Files

**F14b.1 – Google Docs Extraction**

* Detect MIME type `application/vnd.google-apps.document`
* Export as `text/plain` via Drive API
* Pass to standard ingest pipeline
  **Done:** Google Docs fully searchable.

**F14b.2 – Google Sheets Extraction**

* Detect MIME type `application/vnd.google-apps.spreadsheet`
* Export as CSV via Drive API (`text/csv`)
* Convert CSV to semantic text representation:
  ```
  Sheet: Sales Data
  Row 1: Company=Acme Corp, Revenue=$1.2M, Quarter=Q1 2024
  Row 2: Company=Globex, Revenue=$850K, Quarter=Q1 2024
  ```
* Alternative: Export as `text/plain` for simpler approach
  **Done:** Spreadsheet data searchable with context.

**F14b.3 – Google Slides Extraction**

* Detect MIME type `application/vnd.google-apps.presentation`
* Export as `text/plain` via Drive API
* Extracts text from all slides
  **Done:** Presentation content searchable.

---

### Phase 14c: PDF Support

**F14c.1 – PDF Extractor Module**

* New module `app/processing/extractors/pdf.py`
* Add `pdfplumber` to requirements.txt
* `async def extract_pdf_text(file_bytes: bytes) -> str`
* Handle multi-page documents
* Graceful fallback for encrypted/corrupted PDFs
  **Done:** PDF text extraction working.

**F14c.2 – PDF Processing Integration**

* Detect MIME type `application/pdf`
* Download file via Nango proxy
* Extract text with pdfplumber
* Pass to standard ingest pipeline
  **Done:** PDFs fully searchable.

---

### Phase 14d: Office Documents

**F14d.1 – Word Document Extractor**

* New module `app/processing/extractors/docx.py`
* Add `python-docx` to requirements.txt
* `async def extract_docx_text(file_bytes: bytes) -> str`
* Extract paragraphs, tables, headers
  **Done:** Word documents searchable.

**F14d.2 – Excel Extractor**

* New module `app/processing/extractors/xlsx.py`
* Add `openpyxl` to requirements.txt
* `async def extract_xlsx_text(file_bytes: bytes) -> str`
* Convert sheets to semantic text (like Google Sheets)
* Handle multiple worksheets
  **Done:** Excel files searchable.

**F14d.3 – PowerPoint Extractor**

* New module `app/processing/extractors/pptx.py`
* Add `python-pptx` to requirements.txt
* `async def extract_pptx_text(file_bytes: bytes) -> str`
* Extract text from all slides
  **Done:** PowerPoint files searchable.

---

### Phase 14e: Processing Pipeline

**F14e.1 – File Processor Registry**

* New module `app/processing/extractors/__init__.py`
* Registry mapping MIME types to extractors:
  ```python
  EXTRACTORS = {
      "application/vnd.google-apps.document": extract_google_doc,
      "application/vnd.google-apps.spreadsheet": extract_google_sheet,
      "application/pdf": extract_pdf,
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx,
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": extract_xlsx,
      "text/plain": extract_plain_text,
  }
  ```
* `async def extract_content(mime_type, file_bytes, connection_id, file_id)`
  **Done:** Unified extraction interface.

**F14e.2 – PROCESS_FILE Job Type**

* New job type in `JobType` enum
* Payload: `{document_id, file_id, mime_type, connection_id}`
* Handler in `handlers.py`:
  1. Fetch file content via Nango proxy
  2. Route to appropriate extractor
  3. Update document `content_text`
  4. Enqueue `PROCESS_DOCUMENT` for standard pipeline
  **Done:** Async file processing with retry support.

**F14e.3 – Google Drive Backfill Update**

* Update `backfill()` endpoint for google-drive source
* For each file:
  * Create document with metadata (no content yet)
  * Enqueue `PROCESS_FILE` job
* Processing happens asynchronously via worker
  **Done:** Scalable backfill for large drives.

---

### Phase 14f: Advanced Features (Future)

**F14f.1 – Incremental Sync**

* Track `modified_time` per file
* Only re-process changed files
* Webhook support for real-time updates
  **Done:** Efficient ongoing sync.

**F14f.2 – Folder Structure Context**

* Store folder path as document metadata
* Use folder context in entity extraction
* "This document is in /Projects/Q1 Planning/"
  **Done:** Folder context enhances understanding.

**F14f.3 – Image OCR (Optional)**

* Add Tesseract or cloud OCR service
* Extract text from images, scanned PDFs
* MIME types: `image/png`, `image/jpeg`
  **Done:** Image content searchable.

**F14f.4 – Large File Handling**

* Streaming download for large files
* Chunked processing for PDFs > 100 pages
* Memory-efficient extraction
  **Done:** No file size limits.

---

### Supported File Types Summary

| MIME Type | Source | Extractor | Phase |
|-----------|--------|-----------|-------|
| `application/vnd.google-apps.document` | Google Docs | Export API | 14b |
| `application/vnd.google-apps.spreadsheet` | Google Sheets | Export API | 14b |
| `application/vnd.google-apps.presentation` | Google Slides | Export API | 14b |
| `application/pdf` | PDF files | pdfplumber | 14c |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Word .docx | python-docx | 14d |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Excel .xlsx | openpyxl | 14d |
| `application/vnd.openxmlformats-officedocument.presentationml.presentation` | PowerPoint .pptx | python-pptx | 14d |
| `text/plain` | Text files | Direct read | 14a |
| `text/csv` | CSV files | Direct read | 14a |
| `text/markdown` | Markdown | Direct read | 14a |

### Dependencies to Add

```
# requirements.txt additions
pdfplumber>=0.10.0
python-docx>=1.1.0
openpyxl>=3.1.0
python-pptx>=0.6.23
```

---

## 15) Neo4j Unified Vector + Graph Search

> Migrate vector embeddings from pgvector to Neo4j. Combines semantic vector search with knowledge graph traversal in Neo4j. Follows Neo4j best practices for driver management and multi-tenant pre-filtering.

### Architecture: Before vs After

**Before (two databases):**
```
Query Flow:
1. Embed prompt via OpenAI
2. pgvector similarity search → top_k chunks
3. Seed entities from PostgreSQL entity_mentions
4. Neo4j graph traversal from seeds
5. Combine results in Python
→ 2 databases, multiple round-trips, application-level joining
```

**After (Neo4j for vectors + graph):**
```
Query Flow:
1. Embed prompt via OpenAI
2. Neo4j ENN pre-filter search (workspace/vault isolation guaranteed)
3. Neo4j seed entity lookup from matching documents
4. Neo4j graph traversal from seeds
5. Cohere reranking for precision
→ 1 vector store, proper multi-tenant isolation
```

**Benefits:**
- Single vector store (Neo4j) instead of two (pgvector + Neo4j)
- Pre-filtering guarantees workspace/vault isolation
- Connection pooling via singleton driver
- Modular functions with proper error handling

### Key Design Decisions

**1. ENN Pre-filtering (not ANN Post-filtering)**

Per [Neo4j Vector Search docs](https://neo4j.com/developer/genai-ecosystem/vector-search/), use `vector.similarity.cosine()` with `MATCH WHERE` for multi-tenant pre-filtering:

```cypher
// Pre-filter: workspace isolation BEFORE similarity computation
MATCH (chunk:Chunk)
WHERE chunk.workspace_id = $ws
  AND chunk.source_connection_id IN $conn_ids
  AND chunk.embedding IS NOT NULL
WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
WHERE score > 0.0
ORDER BY score DESC
LIMIT $top_k
RETURN chunk, score
```

This guarantees workspace isolation. The alternative `db.index.vector.queryNodes()` does post-filtering which can return fewer results than expected.

**2. Singleton Driver Pattern**

Per [Neo4j Driver Best Practices](https://neo4j.com/blog/developer/neo4j-driver-best-practices/):
> "Your application should only create one driver instance per Neo4j DBMS"

New module `app/neo4j_client.py` provides:
- Application-scoped singleton driver with connection pooling
- `get_session()` context manager for per-operation sessions
- `verify_connectivity()` for startup health checks
- `close_driver()` for graceful shutdown

**3. Vector Index with Filtering Properties**

Neo4j 2026.01+ supports filtering properties in vector indexes:

```cypher
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (n:Chunk) ON (n.embedding)
WITH [n.workspace_id, n.source_connection_id]
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}
```

---

### Phase 15a: Neo4j Schema

**F15a.1 – Chunk Node Schema**

* New node type `:Chunk` with properties:
  * `workspace_id`, `document_id`, `idx` (unique constraint)
  * `chunk_id`, `text`, `start_offset`, `end_offset`
  * `embedding` (1536-dim vector)
  * `source_connection_id` (for vault filtering)
* Relationship: `(Chunk)-[:PART_OF]->(Document)`
  **Done:** Chunk nodes store embeddings alongside document graph.

**F15a.2 – Vector Index with Filtering**

* HNSW vector index with filtering properties:
  ```cypher
  CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
  FOR (n:Chunk) ON (n.embedding)
  WITH [n.workspace_id, n.source_connection_id]
  OPTIONS {indexConfig: {
      `vector.dimensions`: 1536,
      `vector.similarity_function`: 'cosine'
  }}
  ```
* Requires Neo4j 2026.01+ for filtering properties
  **Done:** Vector index supports pre-filtering.

**F15a.3 – Supporting Indexes**

* `CREATE INDEX chunk_workspace_idx FOR (n:Chunk) ON (n.workspace_id)`
* `CREATE INDEX chunk_document_idx FOR (n:Chunk) ON (n.document_id)`
* `CREATE INDEX chunk_connection_idx FOR (n:Chunk) ON (n.source_connection_id)`
  **Done:** Efficient filtering by workspace/vault.

---

### Phase 15b: Singleton Driver Module

**F15b.1 – Neo4j Client Module**

* New module `app/neo4j_client.py`
* Singleton driver with connection pooling:
  ```python
  def get_driver() -> AsyncDriver:
      """Get singleton driver, create on first call."""
      global _driver
      if _driver is None:
          _driver = AsyncGraphDatabase.driver(
              settings.neo4j_uri,
              auth=(settings.neo4j_username, settings.neo4j_password),
              max_connection_pool_size=50,
          )
      return _driver

  @asynccontextmanager
  async def get_session() -> AsyncGenerator[AsyncSession, None]:
      """Get session from singleton driver."""
      driver = get_driver()
      session = driver.session(database=settings.neo4j_database)
      try:
          yield session
      finally:
          await session.close()
  ```
  **Done:** Connection pooling per Neo4j best practices.

**F15b.2 – Update All Neo4j Callers**

* `app/processing/embeddings.py`: Use `get_session()`
* `app/processing/graph.py`: Use `get_session()`
* `app/processing/context_builder.py`: Use `get_session()`
* `app/scripts/migrate_embeddings_to_neo4j.py`: Use `get_session()`
  **Done:** No more driver-per-request anti-pattern.

---

### Phase 15c: Dual-Write Pipeline

**F15c.1 – Embeddings Writer Update**

* `app/processing/embeddings.py` writes to both:
  * PostgreSQL pgvector column (legacy, backward compatibility)
  * Neo4j Chunk nodes with embeddings
* Fetches `source_connection_id` from Document for vault filtering
* Batch upsert using UNWIND for efficiency
* Uses singleton driver via `get_session()`
  **Done:** New embeddings go to both databases.

**F15c.2 – Document Node Enhancement**

* Store `source_connection_id` on Document nodes
* Updated in both `graph.py` and `embeddings.py`
* Enables vault filtering via document → connection path
  **Done:** Document nodes have connection metadata.

**F15c.3 – Job Handler Updates**

* `handle_extract_entities_relations`: Pass `source_connection_id` in UPSERT_GRAPH payload
* `handle_upsert_graph`: Forward to `graph.py`
* Both paths (embedding + graph) now store connection ID
  **Done:** Connection ID flows through all pipelines.

---

### Phase 15d: Context Builder Rewrite

**F15d.1 – Modular Function Design**

* Complete rewrite of `app/processing/context_builder.py`
* Separate functions instead of one giant query:
  ```python
  async def vector_search_chunks(workspace_id, query_embedding, top_k, connection_ids)
  async def get_seed_entities(workspace_id, document_ids)
  async def traverse_graph(workspace_id, entity_keys, depth)
  async def build_context(workspace_id, prompt, vault_ids, depth, top_k)
  ```
* Each function has try/except with logging
  **Done:** Modular, testable, debuggable.

**F15d.2 – ENN Pre-filtering for Multi-tenant**

* Uses `vector.similarity.cosine()` with `MATCH WHERE`:
  ```cypher
  MATCH (chunk:Chunk)
  WHERE chunk.workspace_id = $ws
    AND chunk.source_connection_id IN $conn_ids
    AND chunk.embedding IS NOT NULL
  WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
  WHERE score > 0.0
  ORDER BY score DESC
  LIMIT $top_k
  ```
* Pre-filter guarantees workspace isolation
  **Done:** Multi-tenant safe.

**F15d.3 – Error Handling**

* Each Neo4j operation wrapped in try/except
* Graceful degradation: return empty results on failure
* Structured logging for debugging
  **Done:** Production-ready error handling.

---

### Phase 15e: Migration

**F15e.1 – Migration Script**

* Script `app/scripts/migrate_embeddings_to_neo4j.py`
* Reads all chunks with embeddings from PostgreSQL
* Creates corresponding Chunk nodes in Neo4j
* Uses singleton driver with proper cleanup
* Batch processing with progress logging
* Idempotent (uses MERGE)
  **Done:** Existing data migrated to Neo4j.

**F15e.2 – Verification**

* Compare counts: PostgreSQL vs Neo4j
* Verify vector index is populated
* Test query returns results
  **Done:** Migration verified.

---

### Phase 15f: Cleanup (Future)

**F15f.1 – Remove pgvector Dependency**

* Stop dual-write in `embeddings.py`
* Remove embedding column from `DocumentChunk` model
* Migration to drop column
* Remove pgvector queries from codebase
  **Pending:** After production validation.

---

### Deployment Steps

```bash
# 1. Run Neo4j schema init (creates vector index with filtering)
docker compose exec backend python -m app.scripts.neo4j_init

# 2. Migrate existing embeddings to Neo4j
docker compose exec backend python -m app.scripts.migrate_embeddings_to_neo4j

# 3. Restart backend to use new context builder
docker compose restart backend

# 4. Test a query
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "...", "prompt": "What projects is John working on?"}'
```

---

### Files Modified

| File | Changes |
|------|---------|
| `app/neo4j_client.py` | **New** - Singleton driver with connection pooling |
| `app/scripts/neo4j_init.py` | Vector index with `WITH [n.workspace_id, n.source_connection_id]` |
| `app/processing/embeddings.py` | Uses `get_session()`, dual-write to Neo4j + pgvector |
| `app/processing/graph.py` | Uses `get_session()`, stores source_connection_id |
| `app/jobs/handlers.py` | Pass source_connection_id through UPSERT_GRAPH |
| `app/processing/context_builder.py` | **Rewritten** - ENN pre-filter, modular functions, error handling |
| `app/scripts/migrate_embeddings_to_neo4j.py` | Uses singleton driver, proper cleanup |

---

### References

* [Neo4j Driver Best Practices](https://neo4j.com/blog/developer/neo4j-driver-best-practices/) - Singleton driver pattern
* [Neo4j Vector Search](https://neo4j.com/developer/genai-ecosystem/vector-search/) - ENN pre-filtering vs ANN post-filtering
* [Neo4j Cypher Manual - Vector Indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) - Index creation with filtering properties

---

## 16) Project Graph Layer

> Isolated, mutable graph per project for reasoning and exploration. Enables a feedback loop where chat insights can be explicitly synced back to the Unified Knowledge Layer (UKL).

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Knowledge Flow                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   UKL (Read-only Context)                                               │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Person, Company, Topic, Document, Chunk                         │  │
│   │  (Never mutated during chat)                                     │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│              │                                           ▲              │
│              │ Context for Chat                          │ Explicit     │
│              ▼                                           │ Sync         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Project Graph (PRJ_Node, PRJ_REL)                               │  │
│   │  - Mutable during chat                                           │  │
│   │  - Isolated per project                                          │  │
│   │  - LLM extracts graph_delta inline                               │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Strict Isolation (Infection Control)**

| Rule | Implementation |
|------|----------------|
| UKL never mutated during chat | API layer + separate modules |
| PRJ Graph isolated | Own Neo4j labels: `:PRJ_Node`, `:PRJ_REL` |
| Sync only explicit | Dedicated `/sync` endpoint |
| Traceability | `SYNCED_AS` relationship + audit log |

**2. Label Strategy**

```
UKL Labels (existing):     PRJ Labels (new):
- Person                   - PRJ_Node (with node_type property)
- Company
- Topic
- Document
- Chunk

UKL Relationships:         PRJ Relationships:
- MENTIONS                 - PRJ_REL (generic with rel_type property)
- WORKS_AT                 - SYNCED_AS (PRJ_Node → UKL Entity)
- PART_OF                  - REFS_UKL (read-only reference to UKL)
```

**3. LLM Inline Graph Extraction**

Chat responses include structured `graph_delta`:
```json
{
  "answer": "Based on my analysis...",
  "graph_delta": {
    "nodes": [{"key": "auto", "node_type": "person", "name": "John", "properties": {}}],
    "edges": [{"from_key": "...", "to_key": "...", "rel_type": "WORKS_AT"}],
    "ukl_refs": [{"prj_key": "...", "ukl_key": "person:email:john@acme.com"}]
  }
}
```

---

### Phase 16a: PostgreSQL Schema

**F16a.1 – New Models**

* `projects(id, workspace_id, name, description, status, created_at, updated_at)`
* `project_vault_associations(project_id, vault_id)` – M:N join
* `chat_sessions(id, project_id, workspace_id, title, created_at, updated_at)`
* `chat_messages(id, session_id, workspace_id, role, content, context_vault_ids_used, graph_delta_json, created_at)`
* `project_sync_log(id, project_id, workspace_id, synced_node_keys, synced_edge_keys, ukl_entity_keys, synced_by, created_at)`
  **Done:** Models in `app/models.py`, migration `006_projects_and_chat.py`.

---

### Phase 16b: Neo4j Schema

**F16b.1 – PRJ_Node Constraints & Indexes**

```cypher
-- Uniqueness: (workspace_id, project_id, key)
CREATE CONSTRAINT prj_node_workspace_project_key IF NOT EXISTS
FOR (n:PRJ_Node) REQUIRE (n.workspace_id, n.project_id, n.key) IS UNIQUE

-- Performance indexes
CREATE INDEX prj_node_project_idx IF NOT EXISTS FOR (n:PRJ_Node) ON (n.project_id)
CREATE INDEX prj_node_workspace_idx IF NOT EXISTS FOR (n:PRJ_Node) ON (n.workspace_id)
CREATE INDEX prj_node_type_idx IF NOT EXISTS FOR (n:PRJ_Node) ON (n.node_type)
CREATE INDEX prj_node_status_idx IF NOT EXISTS FOR (n:PRJ_Node) ON (n.status)
```
**Done:** Added to `app/scripts/neo4j_init.py`.

**F16b.2 – PRJ_Node Properties**

```
PRJ_Node {
    workspace_id: STRING
    project_id: STRING
    key: STRING              // e.g., "prj:person:john-doe"
    node_type: STRING        // person, company, topic, claim, etc.
    name: STRING
    properties: STRING       // JSON-serialized flexible properties
    ukl_ref: STRING | NULL   // Optional read-only UKL entity key
    source_message_id: STRING
    status: STRING           // draft, synced
    created_at: DATETIME
    updated_at: DATETIME
}
```

---

### Phase 16c: Project CRUD API

**F16c.1 – Project Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/projects` | Create project with vault associations |
| GET | `/v1/projects?workspace_id=` | List projects |
| GET | `/v1/projects/{id}` | Get single project |
| PATCH | `/v1/projects/{id}` | Update project |
| DELETE | `/v1/projects/{id}` | Delete project + graph |

**Done:** `app/api/projects.py` with full CRUD.

---

### Phase 16d: Project Graph Operations

**F16d.1 – Graph Module**

* New module `app/processing/project_graph.py`
* GUARDRAIL: Only writes to `:PRJ_Node` and `:PRJ_REL` labels
* Functions:
  * `write_prj_node()` – Create/update PRJ_Node
  * `write_prj_edge()` – Create/update PRJ_REL
  * `create_ukl_reference()` – Create REFS_UKL edge
  * `get_project_graph()` – Get all nodes/edges for UI
  * `delete_prj_node()` – Delete node and edges
  * `delete_project_graph()` – Delete all nodes/edges for project
  **Done:** Full CRUD for project graph nodes and edges.

**F16d.2 – Graph Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/projects/{id}/graph` | Get graph for visualization |
| POST | `/v1/projects/{id}/graph/update` | Add nodes/edges to graph |
| DELETE | `/v1/projects/{id}/graph/nodes/{key}` | Delete a node |

**Done:** Graph endpoints in `app/api/projects.py`.

---

### Phase 16e: Chat API

**F16e.1 – Chat Session Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/projects/{id}/chat/sessions` | Create chat session |
| GET | `/v1/projects/{id}/chat/sessions` | List sessions |
| GET | `/v1/projects/{id}/chat/sessions/{sid}` | Get single session |
| DELETE | `/v1/projects/{id}/chat/sessions/{sid}` | Delete session + messages |

**F16e.2 – Chat Message Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/projects/{id}/chat/sessions/{sid}/messages` | Add message with graph_delta |
| GET | `/v1/projects/{id}/chat/sessions/{sid}/messages` | List messages |

* Messages with `graph_delta` automatically create PRJ nodes/edges
  **Done:** `app/api/chat.py` with full chat support.

---

### Phase 16f: Sync to UKL

**F16f.1 – Sync Module**

* New module `app/processing/project_sync.py`
* Uses existing `resolve_entity_key()` for entity resolution
* Functions:
  * `sync_prj_nodes_to_ukl()` – Sync selected nodes
  * `sync_prj_edges_to_ukl()` – Sync selected edges
  * `get_sync_preview()` – Preview what would sync
  * `get_sync_log()` – Get audit log
  **Done:** Sync logic with entity resolution and audit logging.

**F16f.2 – Sync Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/projects/{id}/sync` | Sync nodes/edges to UKL |
| POST | `/v1/projects/{id}/sync/preview` | Preview sync results |
| GET | `/v1/projects/{id}/sync/log` | Get sync audit log |

**F16f.3 – Sync Rules**

* **Never overwrite**: Existing UKL data is not modified (ON CREATE only)
* **Entity resolution**: Uses `resolve_entity_key()` for stable keys
* **Traceability**: Creates `SYNCED_AS` edge from PRJ_Node to UKL entity
* **Audit log**: Every sync recorded in PostgreSQL
* **Status update**: PRJ_Node status changes from 'draft' to 'synced'
  **Done:** Sync endpoints in `app/api/projects.py`.

---

### Files Created/Modified

| File | Changes |
|------|---------|
| `app/models.py` | Added Project, ProjectVaultAssociation, ChatSession, ChatMessage, ProjectSyncLog |
| `alembic/versions/006_projects_and_chat.py` | **New** - Migration for all new tables |
| `app/scripts/neo4j_init.py` | Added PRJ_Node constraints and indexes |
| `app/api/projects.py` | **New** - Project CRUD + Graph + Sync endpoints (668 lines) |
| `app/api/chat.py` | **New** - Chat sessions and messages API (377 lines) |
| `app/processing/project_graph.py` | **New** - PRJ_Node/PRJ_REL operations (458 lines) |
| `app/processing/project_sync.py` | **New** - Sync to UKL with entity resolution (555 lines) |
| `app/main.py` | Registered projects_router and chat_router |

---

### Deployment Steps

```bash
# 1. Run database migration
docker compose exec api alembic upgrade head

# 2. Run Neo4j schema init (creates PRJ_Node constraints)
docker compose exec api python -m app.scripts.neo4j_init

# 3. Restart API to pick up new routes
docker compose restart api

# 4. Test project creation
curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "...", "name": "My Project"}'

# 5. Test graph operations
curl -X POST http://localhost:8000/v1/projects/{id}/graph/update \
  -H "Content-Type: application/json" \
  -d '{"nodes": [{"key": "auto", "node_type": "person", "name": "John"}]}'

# 6. Test sync to UKL
curl -X POST http://localhost:8000/v1/projects/{id}/sync \
  -H "Content-Type: application/json" \
  -d '{"node_keys": ["prj:person:..."]}'
```

---

### Verification Checklist

- [ ] Project CRUD works
- [ ] Graph nodes/edges can be created
- [ ] Chat messages with graph_delta create nodes
- [ ] Sync preview shows correct actions
- [ ] Sync creates UKL entities (Person/Company/Topic)
- [ ] SYNCED_AS edges exist after sync
- [ ] Sync log entries recorded
- [ ] PRJ_Node status changes to 'synced' after sync
- [ ] UKL entities are not modified during chat (isolation)
