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

# “Day-by-day” Reihenfolge (schnellster Pfad)

1. B0 + B1 + B2 (compose + schema)
2. B3 + B4.2 (job system + ingest endpoint)
3. B5 (nango webhook + normalizer) + ingest real data
4. B6 (chunk/embed/extract/upsert) end-to-end
5. B4.3 + B7 (query endpoint + traversal + citations)
6. B8 (hardening)

---

## Mini-Definition of Done (damit ihr wisst, ihr seid “fertig”)

* Backfill Gmail+Notion via Nango → 200+ docs in Postgres
* Worker baut chunks+embeddings+graph
* `POST /v1/query` beantwortet 3 feste Queries und liefert 5–10 citations mit echten Notion/Gmail Links

Wenn du sagst, ob du Node oder Python fürs Backend nimmst, kann ich die Tickets noch in eine konkrete Ordnerstruktur + konkrete Libraries übersetzen (FastAPI + SQLAlchemy + neo4j driver vs NestJS + Prisma + neo4j-js).
