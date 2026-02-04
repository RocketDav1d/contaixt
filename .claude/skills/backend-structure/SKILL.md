---
name: backend-structure
description: This skill provides a visual and conceptual overview of the end-to-end backend architecture for a production-grade GraphRAG data platform integrating Nango (OAuth/Sync), Gmail, Notion, Postgres (with pgvector), Neo4j, and OpenAI. Use this as a reference for understanding system boundaries, API and worker service roles, ingestion pipelines, document processing, chunking, embedding, job orchestration, entity extraction, GraphRAG querying, and response assembly with citations. Intended for developers and architects planning or building robust backend data systems focused on multi-source knowledge ingestion, retrieval, and context-augmented answering.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---


flowchart LR
  %% ========== Actors / External Systems ==========
  Nango["Nango (OAuth + Sync)"]:::ext
  Gmail["Gmail"]:::ext
  Notion["Notion"]:::ext
  OpenAI["LLM + Embeddings (OpenAI)"]:::ext

  %% ========== Backend ==========
  subgraph Backend["Backend"]
    API["API Service (REST)"]:::svc
    Worker["Worker Service (Job runner)"]:::svc

    PG[("Postgres: Raw Docs + Jobs + Chunks + Embeddings")]:::db
    Neo4j[("Neo4j: Knowledge Graph")]:::db
  end

  %% ========== Ingestion ==========
  Gmail -->|"OAuth/Sync"| Nango
  Notion -->|"OAuth/Sync"| Nango

  Nango -->|"Webhook: synced items"| API

  API -->|"Upsert Document (workspace_id, source_type, external_id)"| PG
  API -->|"Enqueue PROCESS_DOCUMENT job"| PG

  %% ========== Processing Pipeline ==========
  Worker -->|"Poll/claim queued jobs"| PG

  Worker -->|"Load Document content"| PG
  Worker -->|"Chunk Document"| PG
  Worker -->|"Create Embeddings"| OpenAI
  OpenAI -->|"Embedding vectors"| Worker
  Worker -->|"Store chunk embeddings"| PG

  Worker -->|"Entity/Topic Extraction (strict JSON)"| OpenAI
  OpenAI -->|"Entities + Relations"| Worker

  Worker -->|"Upsert entities + evidence edges"| Neo4j
  Worker -->|"Optional: store mentions (chunk->entity)"| PG

  %% ========== Query (GraphRAG) ==========
  Client["Client / CLI"]:::ext -->|"POST /v1/query"| API

  API -->|"Embed query"| OpenAI
  OpenAI -->|"Query vector"| API

  API -->|"Vector search top-k chunks"| PG
  PG -->|"chunk_ids + texts"| API

  API -->|"Seed entities from top chunks (and/or mentions table)"| PG
  API -->|"Graph traversal depth=N, collect evidence edges"| Neo4j
  Neo4j -->|"Facts + entity neighborhood"| API

  API -->|"Compose context (facts + chunk texts), generate answer + citations"| OpenAI
  OpenAI -->|"Answer + citation mapping"| API

  API -->|"Return answer + citations (doc_url, chunk quote)"| Client

  %% ========== Styles ==========
  classDef svc fill:#eef,stroke:#333,stroke-width:1px;
  classDef db fill:#efe,stroke:#333,stroke-width:1px;
  classDef ext fill:#fee,stroke:#333,stroke-width:1px;
