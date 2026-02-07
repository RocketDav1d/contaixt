---
doc_id: doc_012
title: "API Design Guidelines"
author: Felix Braun
source_type: notion
---

# API Design Guidelines

**Author:** Felix Braun (Senior Developer)
**Approved by:** Sandra Hoffmann (CTO)
**Last Updated:** September 2025
**Applies to:** All TechVision REST APIs

## Introduction

This document establishes the API design standards for all TechVision services, both internal and client-facing. Consistent API design reduces integration friction, improves developer experience, and simplifies maintenance. These guidelines apply to all REST APIs. gRPC service contracts follow a separate addendum (see the Microservices Architecture Patterns document, doc_018).

All APIs must have a corresponding OpenAPI 3.1 specification. This specification is the single source of truth for the API contract and must be kept in sync with the implementation. FastAPI generates this automatically; for Spring Boot services (such as the FinSecure Portal), use springdoc-openapi.

---

## RESTful Conventions

### Resource Naming

- Use **plural nouns** for collection endpoints: `/v1/documents`, `/v1/patients`, `/v1/sensors`.
- Use **kebab-case** for multi-word resources: `/v1/sensor-readings`, `/v1/access-tokens`.
- Nest resources to express ownership: `/v1/workspaces/{workspace_id}/documents`.
- Limit nesting to two levels. Deeper nesting should be flattened using query filters.
- Avoid verbs in URLs. Use HTTP methods to express actions:
  - `POST /v1/reports` (not `POST /v1/create-report`)
  - `POST /v1/reports/{id}/publish` is acceptable for non-CRUD actions (controller endpoints).

### HTTP Methods

| Method | Purpose | Idempotent | Response Code |
|---|---|---|---|
| `GET` | Retrieve resource(s) | Yes | 200 OK |
| `POST` | Create a new resource | No | 201 Created |
| `PUT` | Full replacement of a resource | Yes | 200 OK |
| `PATCH` | Partial update of a resource | No* | 200 OK |
| `DELETE` | Remove a resource | Yes | 204 No Content |

*PATCH is idempotent if using JSON Merge Patch (RFC 7396), which we recommend.

### Status Codes

Use standard HTTP status codes consistently:

- **200 OK** — Successful GET, PUT, PATCH.
- **201 Created** — Successful POST. Include a `Location` header with the URL of the new resource.
- **204 No Content** — Successful DELETE.
- **400 Bad Request** — Client sent invalid data (malformed JSON, validation errors).
- **401 Unauthorized** — Missing or invalid authentication credentials.
- **403 Forbidden** — Authenticated but insufficient permissions.
- **404 Not Found** — Resource does not exist.
- **409 Conflict** — Resource state conflict (e.g., duplicate key, concurrent modification).
- **422 Unprocessable Entity** — Request is well-formed but semantically invalid.
- **429 Too Many Requests** — Rate limit exceeded. Include `Retry-After` header.
- **500 Internal Server Error** — Unexpected server failure. Log the error, return a generic message.

Never return 200 for errors. Never return 500 for client mistakes.

---

## API Versioning

### URL Path Versioning

We use URL path versioning as it is the most explicit and discoverable approach:

```
https://api.example.com/v1/documents
https://api.example.com/v2/documents
```

**Rules:**
- Major version in the path (`/v1/`, `/v2/`). Minor and patch versions are not reflected in the URL.
- A new major version is required when making breaking changes (removing fields, changing field types, altering behavior).
- Non-breaking changes (adding optional fields, new endpoints) do not require a version bump.
- Support at most two major versions simultaneously. The previous version enters deprecation with a 6-month sunset period.
- Deprecation is communicated via the `Deprecation` header (RFC 8594) and the `Sunset` header with a date.

### Version Lifecycle (Example)

```
v1 released: January 2025 (current)
v2 released: July 2025 (current)
v1 deprecated: July 2025 (Sunset: January 2026)
v1 removed: January 2026
```

---

## Authentication & Authorization

### OAuth 2.0 + JWT

All client-facing APIs use OAuth 2.0 with JWT access tokens:

- **Authorization Code Flow with PKCE** for single-page applications (FinSecure Portal, MedTech Analytics dashboards).
- **Client Credentials Flow** for service-to-service communication.
- Tokens issued by Azure AD (Entra ID) or our internal auth service, depending on the project.
- Access tokens are short-lived (15 minutes). Refresh tokens are long-lived (7 days) with rotation on use.

**JWT Validation Requirements:**
1. Verify the signature using the JWKS endpoint.
2. Check the `iss` (issuer) claim matches the expected identity provider.
3. Check the `aud` (audience) claim matches the API identifier.
4. Check the `exp` (expiration) claim. Reject expired tokens.
5. Check scopes/roles for authorization.

### API Keys

API keys are used for:
- Service-to-service communication within a trusted network (internal microservices).
- Third-party webhook integrations (e.g., Nango sync callbacks).

API keys must be transmitted in the `X-API-Key` header, never in query parameters. Keys are stored hashed in the database and managed via Azure Key Vault. Keys must be rotatable without downtime.

---

## Error Response Format

All errors follow the **RFC 7807 Problem Details** format:

```json
{
  "type": "https://api.techvision.de/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The 'email' field must be a valid email address.",
  "instance": "/v1/users/registration",
  "errors": [
    {
      "field": "email",
      "message": "Must be a valid email address",
      "value": "not-an-email"
    }
  ]
}
```

**Fields:**
- `type` — A URI identifying the error type. Should link to documentation.
- `title` — A short human-readable summary.
- `status` — The HTTP status code (repeated for convenience).
- `detail` — A human-readable explanation specific to this occurrence.
- `instance` — The request path that generated the error.
- `errors` — (Optional) Array of field-level validation errors.

**Important:** Never expose internal details (stack traces, database errors, internal service names) in error responses. Log them server-side with a correlation ID and return the correlation ID in a `X-Request-ID` header for debugging.

---

## Pagination

### Cursor-Based Pagination (Preferred)

Cursor-based pagination is the default for all list endpoints. It provides consistent results even when data is being added or removed.

**Request:**
```
GET /v1/documents?limit=20&cursor=eyJpZCI6MTAwfQ==
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIwfQ==",
    "has_more": true
  }
}
```

The cursor is an opaque, base64-encoded token. Clients must not parse or construct cursors.

### Offset-Based Pagination (Simple Cases)

Offset pagination may be used for administrative interfaces or internal tools where total counts are needed and data volatility is low.

```
GET /v1/admin/audit-log?page=3&per_page=50
```

Response includes `total_count`, `page`, `per_page`, and `total_pages`.

**Do not** use offset pagination for high-traffic public APIs or datasets exceeding 100,000 rows, as performance degrades with large offsets.

---

## Rate Limiting

All APIs enforce rate limits to protect service stability:

| Client Type | Default Limit | Burst |
|---|---|---|
| Unauthenticated | 30 req/min | 10 req/sec |
| Authenticated (user) | 100 req/min | 20 req/sec |
| Authenticated (service) | 1000 req/min | 50 req/sec |

Rate limits are communicated via response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1698765432
```

When exceeded, return `429 Too Many Requests` with a `Retry-After` header (seconds).

Rate limiting is implemented at the API Gateway level (Azure Application Gateway + custom middleware). Per-endpoint overrides can be configured for resource-intensive operations.

---

## Request and Response Standards

### Common Patterns

- **Envelope pattern** for list responses: `{ "data": [...], "pagination": {...} }`.
- **Direct object** for single resource responses: `{ "id": "...", "name": "...", ... }`.
- **Timestamps** in ISO 8601 format with UTC timezone: `"2025-10-15T14:30:00Z"`.
- **IDs** as UUIDs (v4) represented as strings.
- **Monetary values** as integers in the smallest unit (cents) with a separate `currency` field.
- **Field naming** in `snake_case` for Python APIs, `camelCase` for JavaScript/TypeScript APIs. Each project selects one and uses it consistently.

### Filtering and Sorting

List endpoints should support filtering via query parameters:
```
GET /v1/documents?status=processed&source_type=gmail&created_after=2025-01-01
```

Sorting via `sort` parameter with prefix for direction:
```
GET /v1/documents?sort=-created_at,title
```
(`-` prefix for descending, no prefix for ascending)

### Health Check Endpoint

Every API must expose:
- `GET /health` — Returns `200 OK` with `{"status": "healthy"}`. Used by load balancers and Kubernetes liveness probes.
- `GET /ready` — Returns `200 OK` only when all dependencies (database, cache, external services) are reachable. Used by Kubernetes readiness probes.

---

## Documentation

- All APIs must publish an OpenAPI 3.1 specification at `/openapi.json`.
- Interactive documentation available at `/docs` (Swagger UI) for development environments. Disabled in production.
- Changelog maintained per API version in the repository's `CHANGELOG.md`.
- Breaking changes communicated to API consumers at least 30 days before release.

For questions or proposed changes to these guidelines, contact Felix Braun or raise a discussion in the `#api-design` Slack channel.
