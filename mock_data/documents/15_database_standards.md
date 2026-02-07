---
doc_id: doc_015
title: "Database Standards & Best Practices"
author: Anna Richter
source_type: notion
---

# Database Standards & Best Practices

**Author:** Anna Richter (Data Engineer)
**Reviewed by:** Felix Braun (Senior Developer), Sandra Hoffmann (CTO)
**Last Updated:** September 2025
**Applies to:** All TechVision projects using relational databases

## Introduction

This document establishes the database standards for all TechVision projects. PostgreSQL is our primary relational database management system, chosen for its reliability, extensibility, and strong ecosystem (see Technology Radar, doc_009). These standards cover naming conventions, migration workflows, indexing strategies, connection management, backups, and performance guidelines.

Consistent database practices across projects (Projekt Aurora, FinSecure Portal, MedTech Analytics) reduce onboarding time, prevent common mistakes, and make it easier for engineers to move between projects. Deviations from these standards require an Architecture Decision Record (ADR) approved by a senior engineer.

---

## PostgreSQL as Primary RDBMS

### Version Policy

- **PostgreSQL 16+** for all new projects. Older versions are acceptable only for existing systems that cannot be upgraded immediately.
- Extensions we commonly use: `pgvector` (vector similarity search), `pg_trgm` (fuzzy text search), `uuid-ossp` (UUID generation), `pg_stat_statements` (query performance monitoring).
- Version upgrades follow a quarterly evaluation cycle. Major version upgrades are tested in staging for at least 2 weeks before production rollout.

### When Not to Use PostgreSQL

In rare cases, a different database may be appropriate. These cases require an ADR:
- **Time-series data at extreme scale:** Consider TimescaleDB (a PostgreSQL extension, preferred) or InfluxDB.
- **Graph-heavy workloads:** Neo4j is used alongside PostgreSQL in projects that require knowledge graph traversal (e.g., entity relationship exploration).
- **Document storage:** PostgreSQL's JSONB type handles most document storage needs. MongoDB is on Hold (see doc_009) and must not be used for new projects.

---

## Naming Conventions

### General Rules

- Use **snake_case** for all identifiers (tables, columns, indexes, constraints).
- Use **singular nouns** for table names: `document`, `user_account`, `sensor_reading` (not `documents`, `users`).
- Use **lowercase** exclusively. PostgreSQL folds unquoted identifiers to lowercase anyway; being explicit avoids confusion.

### Tables

```sql
-- Good
CREATE TABLE document (...);
CREATE TABLE user_account (...);
CREATE TABLE sensor_reading (...);

-- Bad
CREATE TABLE Documents (...);     -- PascalCase, plural
CREATE TABLE tbl_user (...);      -- Hungarian notation
CREATE TABLE UserAccount (...);   -- camelCase
```

### Columns

- Primary keys: `id` (UUID, always).
- Foreign keys: `{referenced_table}_id` (e.g., `workspace_id`, `document_id`).
- Timestamps: `created_at`, `updated_at`, `deleted_at` (for soft deletes).
- Booleans: `is_` or `has_` prefix (e.g., `is_active`, `has_attachment`).
- Status fields: Use PostgreSQL enums or a `status` column with a CHECK constraint.

### Indexes

```
ix_{table}_{column(s)}           -- Regular index
ux_{table}_{column(s)}           -- Unique index
ix_{table}_{column(s)}_partial   -- Partial index (with WHERE clause)
```

Examples:
```sql
CREATE INDEX ix_document_workspace_id ON document(workspace_id);
CREATE UNIQUE INDEX ux_user_account_email ON user_account(email);
CREATE INDEX ix_document_status_partial ON document(status) WHERE status != 'archived';
```

### Constraints

```
pk_{table}                       -- Primary key
fk_{table}_{referenced_table}    -- Foreign key
ck_{table}_{description}         -- Check constraint
```

---

## Migration Workflow

### Python Services (Alembic)

All Python-based services use Alembic for database migrations:

- Migration files live in the repository under `alembic/versions/`.
- Each migration has an `upgrade()` and `downgrade()` function.
- Migrations must be **idempotent** where possible (use `IF NOT EXISTS`, `IF EXISTS`).
- Naming convention for migration files: `{revision_id}_{description}.py` (Alembic generates the revision ID automatically).

**Commands:**
```bash
# Apply all pending migrations
alembic -c backend/alembic/alembic.ini upgrade head

# Create a new migration
alembic -c backend/alembic/alembic.ini revision --autogenerate -m "add_sensor_reading_table"

# Rollback one migration
alembic -c backend/alembic/alembic.ini downgrade -1
```

**Rules:**
1. Never modify a migration that has been applied to staging or production. Create a new migration instead.
2. Test both `upgrade` and `downgrade` paths locally before pushing.
3. Migrations run automatically during deployment (in the CI/CD pipeline init container, see doc_013).
4. Data migrations (backfills) must be separate from schema migrations and must be tested with production-scale data volumes.

### Java Services (Flyway)

The FinSecure Portal (Spring Boot) uses Flyway:

- Migrations live in `src/main/resources/db/migration/`.
- File naming: `V{version}__{description}.sql` (e.g., `V1.3__add_transaction_audit_table.sql`).
- Flyway runs on application startup. Failed migrations require manual intervention.

---

## Indexing Strategy

### Guidelines

1. **Measure before indexing.** Run `EXPLAIN ANALYZE` on slow queries before adding indexes. Do not speculatively add indexes.
2. **Composite indexes:** Order columns by selectivity (most selective first). Remember that a composite index on `(a, b, c)` can serve queries filtering on `(a)`, `(a, b)`, and `(a, b, c)`, but not `(b, c)` alone.
3. **Partial indexes:** Use them when queries consistently filter on a subset (e.g., only active records). They are smaller and faster than full indexes.
4. **Covering indexes:** Use `INCLUDE` to add columns to an index for index-only scans, avoiding heap lookups.
5. **GIN indexes:** Use for JSONB columns, full-text search (`tsvector`), and array columns.
6. **pgvector indexes:** Use HNSW (`CREATE INDEX ... USING hnsw`) for vector similarity search. IVFFlat is acceptable for datasets under 1M vectors.

### Anti-Patterns

- Do not index every column. Each index adds write overhead and storage.
- Do not use single-column indexes when a composite index would serve multiple queries.
- Do not create indexes on low-cardinality columns (e.g., boolean flags with 50/50 distribution) unless combined in a composite index.
- Regularly review unused indexes: query `pg_stat_user_indexes` for indexes with `idx_scan = 0`.

---

## Connection Pooling

### PgBouncer

All production services connect to PostgreSQL through PgBouncer:

- **Mode:** Transaction pooling (connections returned to the pool after each transaction, not session).
- **Pool size guidelines:**
  - Small service (< 10 pods): `pool_size = 20`
  - Medium service (10-30 pods): `pool_size = 50`
  - Large service (30+ pods): `pool_size = 100`
- **Maximum connections on PostgreSQL:** Calculated as `sum(all pool sizes) + 20` (overhead for monitoring and admin connections).

### Application-Level Connection Settings

- **SQLAlchemy (Python):** `pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`.
- **HikariCP (Java/Spring Boot):** `maximumPoolSize=10`, `minimumIdle=5`, `connectionTimeout=30000`.
- Always use async connection pools for async frameworks (e.g., asyncpg with SQLAlchemy async for FastAPI services).

### Connection Monitoring

- Track active connections via `pg_stat_activity` (exposed as a Prometheus metric via `postgres_exporter`).
- Alert if connection count exceeds 80% of `max_connections` (see doc_014 for alert configuration).
- Investigate connection leaks promptly — they are often caused by missing `finally` blocks or unclosed sessions.

---

## Backup Strategy

### Automated Backups

| Backup Type | Frequency | Retention | Storage |
|---|---|---|---|
| Full base backup | Daily at 02:00 CET | 30 days | Azure Blob (Cool tier) |
| WAL archiving | Continuous | 30 days | Azure Blob (Cool tier) |
| Logical dump (`pg_dump`) | Weekly (Sunday 03:00 CET) | 90 days | Azure Blob (Archive tier) |

### Point-in-Time Recovery (PITR)

- Continuous WAL archiving enables PITR to any point within the 30-day retention window.
- WAL files are shipped to Azure Blob Storage via `pgBackRest`.
- Recovery procedure documented in the disaster recovery section of the Azure Architecture Guide (doc_011).

### Backup Verification

- **Weekly:** Automated restore test to a temporary database instance. Verify row counts and basic query results.
- **Monthly:** Full disaster recovery drill. Restore to a fresh environment and run integration tests (see doc_011 for DR procedures).
- Backup alerts: P1 alert if the daily backup fails or WAL archiving falls behind by more than 15 minutes (see doc_014).

### Backup Responsibility

- **Managed databases (Azure SQL):** Azure handles backups automatically. We configure retention policies via Terraform.
- **Self-managed PostgreSQL (AKS):** DevOps team (Markus Lang) manages pgBackRest configuration and monitoring.

---

## Performance Guidelines

### Query Standards

1. **No `SELECT *`** — Always specify the columns you need. This reduces I/O, improves cache efficiency, and prevents breakage when columns are added.
2. **Query timeout:** 30 seconds maximum for application queries. Analytical queries may use longer timeouts with explicit configuration.
3. **Use `EXPLAIN ANALYZE`** before optimizing. Do not guess at query performance; measure it.
4. **Avoid N+1 queries.** Use JOINs, subqueries, or batch fetching. SQLAlchemy's `selectinload` or `joinedload` for eager loading.
5. **Use parameterized queries** exclusively. No string interpolation or concatenation for SQL. This prevents SQL injection and enables query plan caching.
6. **Batch inserts:** Use `executemany` or `COPY` for bulk data loading. The Projekt Aurora data pipeline uses `COPY` for Bronze-to-Silver layer transfers (see doc_017).

### Table Design

- Always include `id` (UUID primary key), `created_at`, and `updated_at` columns.
- Use `BIGINT` for auto-incrementing identifiers if UUID is not suitable (e.g., dense sequential access patterns).
- Use `TIMESTAMPTZ` (timestamp with time zone) for all timestamp columns. Store everything in UTC.
- Use `TEXT` instead of `VARCHAR(n)` unless there is a genuine business constraint on length.
- Use PostgreSQL enums sparingly — they are difficult to modify. Prefer a `status TEXT CHECK (status IN ('active', 'inactive', 'archived'))` pattern for values that may evolve.
- Soft deletes (`deleted_at TIMESTAMPTZ NULL`) preferred over hard deletes for audit-sensitive data (FinSecure Portal, MedTech Analytics).

### Monitoring Queries

Enable `pg_stat_statements` on all environments and review regularly:

```sql
-- Top 10 queries by total execution time
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

Incorporate this review into the weekly DevOps standup. Queries with mean execution time exceeding 100ms should be investigated.

---

## Schema Change Review Process

All schema changes (migrations) require:

1. A PR with the migration file and a description of the change.
2. Review by at least one data engineer or senior developer.
3. `EXPLAIN ANALYZE` output for any new queries that will use the changed schema.
4. Impact assessment: Will the migration lock tables? How long will it run on production-scale data? Use `pg_stat_progress_create_index` for CREATE INDEX CONCURRENTLY monitoring.
5. For large tables (> 10M rows): Migration must use non-locking techniques (e.g., `CREATE INDEX CONCURRENTLY`, `ALTER TABLE ... ADD COLUMN` with default is non-locking in PG11+).

Contact Anna Richter for database design reviews or questions about these standards.
