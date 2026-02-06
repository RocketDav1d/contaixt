# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contaixt is a GraphRAG platform that ingests documents from multiple sources (Gmail, Notion via Nango OAuth), processes them through a pipeline (chunking, embedding, entity extraction), stores them in PostgreSQL (pgvector) and Neo4j, and enables context-aware querying that combines vector similarity search with knowledge graph traversal.

## Commands

### Development (Docker Compose — primary method)

```bash
docker compose up                  # Start all services (postgres, api, worker)
docker compose logs -f api         # Tail API logs
docker compose logs -f worker      # Tail worker logs
docker compose down                # Stop all services
```

### Local Development (without Docker)

```bash
pip install -r backend/requirements.txt
alembic -c backend/alembic/alembic.ini upgrade head       # Run migrations
python -m app.scripts.neo4j_init                           # Init Neo4j constraints/indexes
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Run API (from backend/)
python -m app.worker                                       # Run worker (from backend/)
```

### Database Migrations

```bash
alembic -c backend/alembic/alembic.ini upgrade head        # Apply migrations
alembic -c backend/alembic/alembic.ini revision -m "desc"  # Create new migration
```

### Linting & Type-Checking (Backend)

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt   # einmalig
ruff check app && ruff format app                         # Linting + Format
mypy app                                                  # Type-Checking (benötigt installierte Dependencies)
```

Config: `backend/pyproject.toml` (Ruff + mypy). Dev-Tools: `backend/requirements-dev.txt`.

## Architecture

### Two-Process Model

The backend runs as two separate processes sharing the same codebase (`backend/app/`):

- **API** (`app.main:app`) — FastAPI server handling HTTP requests on port 8000. Routes live in `backend/app/api/`.
- **Worker** (`app.worker`) — Async job poller that claims and executes jobs from a Postgres-based queue. Job handlers live in `backend/app/jobs/handlers.py`.

### 5-Stage Job Pipeline

Document processing is fully async via a Postgres job queue (`SELECT ... FOR UPDATE SKIP LOCKED`). The API enqueues jobs; the worker processes them:

```
PROCESS_DOCUMENT (fan-out)
  ├─► CHUNK_DOCUMENT → sentence-boundary splitting (1000 chars, 200 overlap)
  │     └─► EMBED_CHUNKS → OpenAI text-embedding-3-small → pgvector
  └─► EXTRACT_ENTITIES_RELATIONS → gpt-4o-mini JSON extraction + entity resolution
        └─► UPSERT_GRAPH → Neo4j merge (nodes + edges)
```

Jobs retry up to 3 times with exponential backoff (30s × attempt). Handler registration happens in `handlers.py:register_all()`.

### GraphRAG Query Flow (`POST /v1/query`)

1. Embed the user query via OpenAI
2. Top-K vector similarity search in pgvector (filtered by workspace)
3. Extract seed entities from matched chunks via `entity_mentions` table
4. Traverse Neo4j graph (variable-length paths up to configurable depth)
5. Assemble context (chunks + graph facts) via `context_builder.py`
6. LLM answer generation (gpt-4o-mini, temperature 0, JSON mode with `cited_chunk_ids`)
7. Map cited chunks back to source documents for citation URLs

### Multi-Tenancy

Every table and Neo4j node carries a `workspace_id`. All queries filter by workspace.

### MCP Server (`/mcp`)

A FastMCP 2.0 server is mounted at `/mcp` on the API, exposing Contaixt over the Model Context Protocol (Streamable HTTP). MCP clients (Claude Desktop, Cursor, etc.) can connect to `http://localhost:8000/mcp`.

- `backend/app/mcp/` — MCP module: `__init__.py` (FastMCP instance), `tools.py` (6 tools), `resources.py` (2 resources)
- **Tools:** `search_context` (GraphRAG query), `list_workspaces`, `list_vaults`, `list_documents`, `get_document`, `get_job_stats`
- **Resources:** `contaixt://workspaces`, `contaixt://workspaces/{workspace_id}/vaults`

### Key Directories

- `backend/app/api/` — FastAPI route handlers (workspaces, ingest, query, sources, webhooks)
- `backend/app/jobs/` — Job queue: `runner.py` (poll loop + claim), `handlers.py` (5 job types), `enqueue.py`
- `backend/app/processing/` — Pipeline stages: `chunker.py`, `embeddings.py`, `extraction.py`, `entity_resolution.py`, `graph.py`, `context_builder.py`
- `backend/app/nango/` — Nango integration: `client.py`, `normalizers.py` (Gmail/Notion), `content.py` (Notion blocks), `sync.py`
- `backend/alembic/` — Database migrations (single migration file: `001_initial_schema.py`)

### Tech Stack

- **Python 3.12**, **FastAPI**, **SQLAlchemy 2.0 (async)**, **asyncpg**
- **PostgreSQL 16 + pgvector** — documents, chunks, embeddings (1536-dim), jobs queue
- **Neo4j** — knowledge graph (entities, relationships, document links)
- **OpenAI** — `text-embedding-3-small` for embeddings, `gpt-4o-mini` for extraction and querying
- **Nango** — OAuth and sync for Gmail and Notion
- **FastMCP 2.0** — MCP server for LLM client integration (Streamable HTTP)
- **Pydantic Settings** — configuration via environment variables (`backend/app/config.py`)

### Entity Resolution

Entities get deterministic stable keys: `person:email:user@domain.com`, `company:domain:example.com`, `topic:machine_learning`. This ensures deduplication across documents. Logic is in `entity_resolution.py`.

### Docker Compose Services

- `postgres` — pgvector/pgvector:pg16 (host port from `POSTGRES_PORT`, default 5432)
- `api` — FastAPI with hot-reload (host port from `API_PORT`, default 8000)
- `worker` — Job processor (no exposed port)

Both `api` and `worker` mount `./backend` as a volume for live code changes and depend on postgres health.
