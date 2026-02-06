# Backend Deployment & Database Updates

> This skill documents the complete process for deploying the Contaixt backend, running migrations, and testing changes.

---

## TL;DR - One Command Deploy

```bash
./deploy.sh
```

This script handles everything:
1. Rebuilds containers (picks up new dependencies)
2. Starts/restarts services
3. Waits for API health check
4. Runs all pending database migrations
5. Restarts worker

**Options:**
```bash
./deploy.sh          # Full deploy (rebuild + migrate)
./deploy.sh --quick  # Skip rebuild (code-only changes, hot reload handles it)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│    postgres     │      api        │        worker           │
│  (pgvector:16)  │   (FastAPI)     │   (Job processor)       │
│    Port 5432    │   Port 8000     │     No port             │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  Neo4j Aura   │
                   │   (Cloud)     │
                   └───────────────┘
```

**Services:**
- `postgres` - PostgreSQL 16 with pgvector extension
- `api` - FastAPI backend (uvicorn with hot reload)
- `worker` - Background job processor

**Note:** Neo4j runs on Aura (cloud), not in Docker.

---

## File Locations

| File | Purpose |
|------|---------|
| `/docker-compose.yml` | Service definitions |
| `/.env` | Environment variables (API keys, DB credentials) |
| `/backend/requirements.txt` | Python dependencies |
| `/backend/Dockerfile` | Container image definition |
| `/backend/alembic/versions/` | Database migrations |
| `/backend/app/` | Application code |

---

## Common Commands

### Start All Services

```bash
# From project root
cd /Users/davidkorn/contaixt

# Start all services (detached)
docker compose up -d

# Start with rebuild (after requirements.txt changes)
docker compose up -d --build

# View logs
docker compose logs -f           # All services
docker compose logs -f api       # API only
docker compose logs -f worker    # Worker only
```

### Stop Services

```bash
docker compose down              # Stop all
docker compose stop api          # Stop API only
docker compose restart api       # Restart API only
```

### Check Status

```bash
docker compose ps                # List running services
docker compose exec api bash     # Shell into API container
```

---

## Database Migrations

### Run Migrations

```bash
# Run all pending migrations
docker compose exec api alembic upgrade head

# Check current migration version
docker compose exec api alembic current

# View migration history
docker compose exec api alembic history
```

### Create New Migration

```bash
# Auto-generate from model changes
docker compose exec api alembic revision --autogenerate -m "Description"

# Create empty migration (for manual SQL)
docker compose exec api alembic revision -m "Description"
```

### Rollback Migration

```bash
# Rollback one version
docker compose exec api alembic downgrade -1

# Rollback to specific version
docker compose exec api alembic downgrade 002
```

---

## Deployment Workflow

### After Code Changes (No New Dependencies)

```bash
# Hot reload is enabled - changes apply automatically
# Just save files and the API restarts

# If hot reload doesn't pick up changes:
docker compose restart api worker
```

### After requirements.txt Changes

```bash
# Rebuild containers to install new packages
docker compose up -d --build api worker

# Verify new package is installed
docker compose exec api pip list | grep <package-name>
```

### After Migration Changes

```bash
# 1. Rebuild if new dependencies added
docker compose up -d --build api

# 2. Run migrations
docker compose exec api alembic upgrade head

# 3. Restart worker (picks up schema changes)
docker compose restart worker
```

### Full Redeployment

```bash
# Nuclear option - rebuild everything
docker compose down
docker compose up -d --build

# Run migrations
docker compose exec api alembic upgrade head
```

---

## Environment Variables

Edit `/.env` to change configuration:

```bash
# Required API Keys
OPENAI_API_KEY=sk-...          # For embeddings and LLM
COHERE_API_KEY=...             # For reranking (optional, graceful fallback)
NANGO_SECRET_KEY=...           # For OAuth integrations

# Database (usually don't change)
DATABASE_URL=postgresql+asyncpg://contaixt:contaixt@postgres:5432/contaixt

# Neo4j (Aura cloud instance)
NEO4J_URI=neo4j+s://...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
```

After changing `.env`:

```bash
docker compose up -d  # Recreates containers with new env
```

---

## Testing

### Health Check

```bash
curl http://localhost:8000/v1/health
```

### Test Query Endpoint

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "YOUR-WORKSPACE-ID",
    "prompt": "What do you know about me?"
  }'
```

### Check Logs for Errors

```bash
# Recent API logs
docker compose logs api --tail=100

# Follow logs in real-time
docker compose logs -f api worker
```

### Verify Database Connection

```bash
# Connect to postgres
docker compose exec postgres psql -U contaixt -d contaixt

# Run SQL
\dt                              # List tables
\d document_chunks               # Describe table
SELECT count(*) FROM documents;  # Query
\q                               # Exit
```

### Verify Indexes

```bash
docker compose exec postgres psql -U contaixt -d contaixt -c \
  "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'document_chunks';"
```

---

## Troubleshooting

### "Service is not running"

```bash
# Check what's running
docker compose ps

# Start services
docker compose up -d

# Check for startup errors
docker compose logs api --tail=50
```

### "Connection refused" to Postgres

```bash
# Check postgres is healthy
docker compose ps postgres

# Check postgres logs
docker compose logs postgres --tail=50

# Verify connection from API container
docker compose exec api python -c "from app.db import get_async_session; print('OK')"
```

### Migration Fails

```bash
# Check current state
docker compose exec api alembic current

# See what's pending
docker compose exec api alembic history

# Check for syntax errors in migration file
docker compose logs api --tail=50
```

### Package Not Found After Install

```bash
# Must rebuild container after requirements.txt change
docker compose up -d --build api worker

# Verify package installed
docker compose exec api pip list | grep <package>
```

---

## Quick Reference Card

```bash
# === MOST COMMON COMMANDS ===

# Start everything
docker compose up -d

# Rebuild after dependency changes
docker compose up -d --build

# Run migrations
docker compose exec api alembic upgrade head

# View logs
docker compose logs -f api

# Restart services
docker compose restart api worker

# Shell into container
docker compose exec api bash

# Database shell
docker compose exec postgres psql -U contaixt -d contaixt
```

---

## Current Migration Versions

| Version | Description |
|---------|-------------|
| 001 | Initial schema (documents, chunks, entities, jobs) |
| 002 | Context vaults (multi-tenant data partitioning) |
| 003 | HNSW index for vector search |

Run `docker compose exec api alembic history` for full list.
