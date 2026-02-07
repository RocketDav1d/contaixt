---
doc_id: doc_018
title: "Microservices Architecture Patterns"
author: Sandra Hoffmann
source_type: notion
---

# Microservices Architecture Patterns

**Author:** Sandra Hoffmann (CTO)
**Contributors:** Felix Braun (Senior Developer), Markus Lang (DevOps Lead)
**Last Updated:** October 2025
**Applies to:** All TechVision distributed system designs

## Introduction

This document describes the microservices architecture patterns adopted at TechVision. It provides guidance on service decomposition, communication patterns, resilience strategies, and observability. These patterns have been developed through our experience building and operating distributed systems across Projekt Aurora, the FinSecure Portal, and MedTech Analytics.

Not every project requires a microservices architecture. For smaller projects or early-stage products, a modular monolith is often the better starting point. This document helps teams make informed decisions about when and how to decompose into services, and provides proven patterns for the challenges that distributed architectures introduce.

---

## Service Decomposition Guidelines

### Domain-Driven Design (DDD)

We use Domain-Driven Design principles to identify service boundaries. The key concepts:

**Bounded Contexts:** Each microservice owns a single bounded context — a cohesive area of the business domain with its own ubiquitous language, data model, and business rules. Services communicate across bounded context boundaries via well-defined APIs or events, never by sharing databases.

**Context Mapping:** Before decomposing a system, we create a context map that identifies:
- Which bounded contexts exist in the domain.
- How they relate to each other (upstream/downstream, partnership, customer-supplier).
- Where anti-corruption layers are needed to translate between contexts.

**Example (Projekt Aurora):**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Data Ingestion  │────►│  Data Processing  │────►│  Data Serving   │
│  Context         │     │  Context          │     │  Context        │
│                  │     │                   │     │                 │
│  - Source config │     │  - Transformations│     │  - Query API    │
│  - Connectors    │     │  - Quality rules  │     │  - Dashboards   │
│  - CDC           │     │  - Scheduling     │     │  - Exports      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                        ┌──────────────────┐
                        │  Platform         │
                        │  Context          │
                        │                   │
                        │  - Auth/AuthZ     │
                        │  - Monitoring     │
                        │  - Config mgmt    │
                        └──────────────────┘
```

**Example (FinSecure Portal):**
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Authentication  │     │  Transaction     │     │  Reporting      │
│  Context         │     │  Processing      │     │  Context        │
│                  │     │  Context         │     │                 │
│  - User mgmt    │     │  - Payments      │     │  - Audit logs   │
│  - OAuth/OIDC   │     │  - Compliance    │     │  - Reports      │
│  - MFA          │     │  - Validation    │     │  - Exports      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Decomposition Criteria

A service should be extracted when:
1. **Independent deployment** is needed — the component has a different release cadence or team ownership.
2. **Different scaling requirements** — the component has significantly different load patterns (e.g., Projekt Aurora's IoT ingestion service handles 50,000 msg/sec while the query API handles 100 req/sec).
3. **Technology heterogeneity** — a component benefits from a different technology stack (e.g., Rust for performance-critical ingestion, Python for data processing, as noted in the Technology Radar, doc_009).
4. **Organizational alignment** — follows Conway's Law. Service boundaries should mirror team boundaries.

A service should NOT be extracted when:
- The two components always change together and are always deployed together.
- The interaction between them requires shared transactions or strong consistency.
- The team is too small to support the operational overhead of a separate service.

---

## Communication Patterns

### Synchronous: REST

REST is our default for synchronous, request-response communication between services.

- Follow the API Design Guidelines (doc_012) for all REST endpoints.
- Use for queries and commands that require an immediate response.
- Timeout configuration: 5 seconds for inter-service calls (configurable per endpoint).
- Retry with exponential backoff for transient failures (see Circuit Breaker section below).

**When to use REST:**
- Client-facing APIs (user-initiated requests).
- Service-to-service queries where the caller needs the response to continue processing.
- Simple CRUD operations on well-defined resources.

### Synchronous: gRPC

gRPC is used for performance-sensitive, high-throughput inter-service communication.

- Protobuf schemas are maintained in a shared repository (`techvision/proto-schemas`) and versioned with semantic versioning.
- gRPC is currently used for the internal communication between Projekt Aurora's ingestion gateway and the processing workers (where REST overhead is noticeable at 50k msg/sec).
- Both Python (grpcio) and Java (grpc-java) clients are generated from the shared Protobuf definitions.

**When to use gRPC:**
- High-throughput internal service communication (> 1,000 req/sec).
- Streaming data (bidirectional streaming for real-time pipelines).
- Strict schema enforcement is critical.

### Asynchronous: Azure Service Bus

Asynchronous messaging via Azure Service Bus is used for event-driven communication where the sender does not need an immediate response.

**Topics and Subscriptions:**
- Each bounded context publishes domain events to a dedicated topic (e.g., `aurora.ingestion.document-ingested`, `finsecure.transaction.payment-completed`).
- Consuming services subscribe to topics they are interested in, with subscription filters for routing.
- Dead-letter queues (DLQ) are enabled on all subscriptions. DLQ messages are monitored and alerted (see doc_014).

**Message Design:**
```json
{
  "event_type": "document.ingested",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-15T14:30:00Z",
  "source": "ingestion-service",
  "data": {
    "document_id": "doc_123",
    "workspace_id": "ws_aurora_prod",
    "source_type": "sap",
    "size_bytes": 15420
  },
  "metadata": {
    "correlation_id": "req_abc123",
    "schema_version": "1.0"
  }
}
```

**Message Guarantees:**
- At-least-once delivery (consumers must be idempotent).
- Message ordering guaranteed within a session (session-enabled queues for ordered processing).
- Message TTL: 7 days (configurable per topic).

**When to use async messaging:**
- Fire-and-forget commands (email notifications, audit logging).
- Event-driven workflows (document processed triggers entity extraction, triggers graph update).
- Cross-service data synchronization where eventual consistency is acceptable.
- Decoupling services with different availability requirements.

---

## Service Mesh

### Current State: Basic Kubernetes Networking

We currently use standard Kubernetes networking with NGINX Ingress Controller for external traffic and Kubernetes Services for internal service discovery. Network policies (see doc_016) provide basic traffic control.

### Istio Evaluation

We are evaluating Istio as a service mesh for the FinSecure Portal, where the banking regulatory environment demands:
- Mutual TLS (mTLS) between all services.
- Fine-grained traffic policies and access control.
- Detailed traffic observability without application code changes.

The evaluation is being conducted in the `finsecure-staging` namespace. Early findings:
- **Pros:** Automatic mTLS, traffic shifting for canary deployments, built-in retry and timeout policies.
- **Cons:** Significant resource overhead (sidecar proxy per pod adds ~50MB memory, ~10ms p99 latency), operational complexity, steep learning curve.

Decision expected by end of Q4 2025. For now, Istio is in the "Assess" category — not approved for production use. If adopted, it would move to "Trial" for FinSecure only, given the regulatory requirements.

---

## Circuit Breaker Pattern

### Purpose

Circuit breakers prevent cascade failures when a downstream service is degraded or unavailable. Instead of continuously sending requests to a failing service (which wastes resources and increases latency), the circuit breaker "opens" after a threshold of failures, returning an immediate error or fallback response.

### Implementation

**Java services (FinSecure Portal) — resilience4j:**
```java
@CircuitBreaker(name = "transactionService", fallbackMethod = "fallbackTransaction")
@Retry(name = "transactionService")
@TimeLimiter(name = "transactionService")
public CompletableFuture<TransactionResult> processTransaction(TransactionRequest request) {
    return transactionClient.process(request);
}

// Circuit breaker configuration (application.yml)
resilience4j:
  circuitbreaker:
    instances:
      transactionService:
        slidingWindowSize: 10
        failureRateThreshold: 50
        waitDurationInOpenState: 30s
        permittedNumberOfCallsInHalfOpenState: 3
```

**Python services (Aurora, MedTech) — tenacity:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=ServiceUnavailableError
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TransientError)
)
@circuit_breaker
async def call_processing_service(document_id: str) -> ProcessingResult:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{PROCESSING_SERVICE_URL}/v1/process",
            json={"document_id": document_id}
        )
        response.raise_for_status()
        return ProcessingResult(**response.json())
```

### Circuit Breaker States

```
CLOSED (normal operation)
  │
  │ failure rate > threshold
  ▼
OPEN (all requests fail fast)
  │
  │ wait duration elapsed
  ▼
HALF-OPEN (limited test requests)
  │
  ├─ test requests succeed → CLOSED
  └─ test requests fail → OPEN
```

Circuit breaker state transitions are logged and exposed as Prometheus metrics. An open circuit breaker triggers a P2 alert (see doc_014).

---

## Event Sourcing and CQRS

### When to Use Event Sourcing

Event sourcing stores the state of an entity as a sequence of events rather than the current state. Each event represents a fact that happened in the domain.

**Appropriate use cases:**
- Audit-critical domains where a complete history is required (FinSecure Portal transaction processing).
- Domains where temporal queries are needed ("What was the account balance at 3pm yesterday?").
- Systems that need to reconstruct state from events (data reprocessing in Projekt Aurora).

**Not appropriate for:**
- Simple CRUD operations (most internal tools).
- High-throughput write scenarios where event storage overhead is prohibitive.
- Teams without experience in event-sourced systems (the learning curve is significant).

### CQRS (Command Query Responsibility Segregation)

CQRS separates the write model (commands) from the read model (queries), allowing each to be optimized independently.

**Implementation at TechVision:**
- The FinSecure Portal uses CQRS for the transaction processing bounded context: commands go through a validation and processing pipeline, events are persisted to Azure Service Bus, and a separate read model (optimized PostgreSQL views) serves the reporting API.
- Projekt Aurora uses a lightweight CQRS variant: Data Factory writes to the Bronze/Silver/Gold layers (command side), while Synapse Serverless SQL serves queries (read side) from the Gold layer (see doc_017).

---

## Saga Pattern for Distributed Transactions

### Problem

In a microservices architecture, a single business operation may span multiple services. Traditional ACID transactions are not possible across service boundaries. The saga pattern provides a way to maintain data consistency through a sequence of local transactions, each with a compensating action for rollback.

### Orchestration-Based Saga (Preferred)

We prefer orchestration-based sagas where a central coordinator (saga orchestrator) manages the sequence of steps.

**Example: FinSecure Portal — New Account Opening:**
```
Saga: OpenAccountSaga
  1. AuthService: Create user account
     Compensation: Delete user account
  2. ComplianceService: Run KYC verification
     Compensation: Cancel KYC check
  3. AccountService: Create bank account
     Compensation: Close bank account
  4. NotificationService: Send welcome email
     Compensation: (none — notification is best-effort)
```

The saga orchestrator is implemented as a state machine, with each step publishing a command to Azure Service Bus and listening for the result event. If any step fails, the orchestrator executes compensation actions in reverse order.

### Choreography-Based Saga

In simpler scenarios, services can coordinate through events without a central orchestrator:

**Example: Projekt Aurora — Document Processing Pipeline:**
```
1. IngestionService publishes "DocumentIngested" event
2. ChunkingService processes document, publishes "DocumentChunked" event
3. EmbeddingService creates embeddings, publishes "ChunksEmbedded" event
4. ExtractionService extracts entities, publishes "EntitiesExtracted" event
5. GraphService updates knowledge graph, publishes "GraphUpdated" event
```

Each service listens for its trigger event and publishes a completion event. This is simpler but harder to monitor and debug than orchestration. We use it when the flow is linear and compensation logic is minimal (failed processing jobs are simply retried, see the job queue implementation).

---

## Service Discovery and Load Balancing

### Internal Service Discovery

Within Kubernetes, services discover each other via Kubernetes DNS:

```
http://{service-name}.{namespace}.svc.cluster.local:{port}
```

Example: The Aurora API calling the processing worker:
```
http://aurora-worker.aurora-prod.svc.cluster.local:8080
```

We use environment variables (injected via Helm values) to configure service URLs, keeping the actual discovery mechanism abstracted from the application code.

### Load Balancing

- **Internal traffic:** Kubernetes Service (ClusterIP) with kube-proxy (iptables mode) provides round-robin load balancing.
- **External traffic:** Azure Application Gateway (L7) for HTTP/S traffic with path-based routing (see doc_011).
- **gRPC traffic:** Client-side load balancing using gRPC's built-in round-robin policy, since Kubernetes Service L4 load balancing does not work well with HTTP/2 multiplexing.

---

## Observability

### Distributed Tracing with OpenTelemetry

All services must implement distributed tracing using OpenTelemetry:

- **SDK:** `opentelemetry-sdk` for Python, `opentelemetry-java` for Spring Boot services.
- **Propagation:** W3C Trace Context headers (`traceparent`, `tracestate`) propagated across all HTTP and gRPC calls.
- **Exporter:** OTLP exporter sending traces to Tempo (see doc_014 for the monitoring stack).
- **Sampling:** 100% in dev/staging, 10% in production (configurable via environment variable).

**Instrumentation requirements:**
1. **Automatic instrumentation** for HTTP frameworks (FastAPI, Spring Boot) and database clients (SQLAlchemy, JDBC) — these capture spans for inbound requests, outbound HTTP calls, and database queries automatically.
2. **Manual spans** for significant business operations (document processing, entity extraction, transaction validation) to provide domain-level visibility.

**Example (FastAPI + OpenTelemetry):**
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Automatic instrumentation (app startup)
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
HTTPXClientInstrumentor().instrument()

# Manual span for business logic
tracer = trace.get_tracer("aurora.processing")

async def process_document(document_id: str):
    with tracer.start_as_current_span("process_document") as span:
        span.set_attribute("document.id", document_id)
        chunks = await chunk_document(document_id)
        span.set_attribute("document.chunk_count", len(chunks))
        embeddings = await embed_chunks(chunks)
        return embeddings
```

### Structured Logging

All services emit structured JSON logs to stdout, collected by Promtail and stored in Loki:

```json
{
  "timestamp": "2025-10-15T14:30:00.123Z",
  "level": "INFO",
  "service": "aurora-api",
  "message": "Document processing completed",
  "document_id": "doc_123",
  "processing_time_ms": 1523,
  "trace_id": "abc123def456",
  "span_id": "789ghi012"
}
```

The `trace_id` field links logs to distributed traces in Tempo, enabling seamless correlation between logs and traces during incident investigation.

### Metrics

Each service exposes Prometheus metrics at `/metrics`:

- **RED metrics** (Rate, Errors, Duration) for all API endpoints — provided automatically by instrumentation middleware.
- **Custom business metrics** (e.g., `aurora_documents_processed_total`, `finsecure_transactions_completed_total`) defined per service.
- **Runtime metrics** (garbage collection, thread pool usage, connection pool stats) for performance debugging.

Grafana dashboards for each service are created from a standard template and customized with service-specific panels (see doc_014).

---

## Anti-Patterns to Avoid

1. **Distributed monolith:** Services that must be deployed together or share a database. If two services cannot function independently, they should be merged.
2. **Chatty communication:** A single user request requiring 10+ inter-service calls. Redesign the API or merge services to reduce round trips.
3. **Shared database:** Two services reading/writing the same database tables. Each service owns its data store. Use events to synchronize.
4. **Synchronous chains:** A calls B, which calls C, which calls D synchronously. Failure in D cascades to A. Use async messaging or break the chain.
5. **God service:** A single service that accumulates too much responsibility. Apply the decomposition criteria to identify extraction opportunities.

---

## Decision Framework

When designing a new system or evaluating decomposition, use this decision tree:

1. **Start with a modular monolith.** Separate bounded contexts as modules within a single deployable unit.
2. **Extract a service when** there is a concrete need (different scaling, different team, different release cadence).
3. **Choose sync (REST/gRPC) when** the caller needs the response to continue.
4. **Choose async (Service Bus) when** the caller does not need an immediate response, or the operation is long-running.
5. **Apply circuit breakers** to all synchronous inter-service calls.
6. **Use sagas** when a business operation spans multiple services and requires consistency guarantees.
7. **Instrument everything** with OpenTelemetry from day one. Observability is not optional.

For architecture reviews and guidance on applying these patterns, contact Sandra Hoffmann or request a session with the Architecture Guild via `#architecture` on Slack.
