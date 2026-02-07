---
doc_id: doc_009
title: "TechVision Technology Radar Q4 2025"
author: Sandra Hoffmann
source_type: notion
---

# TechVision Technology Radar Q4 2025

**Author:** Sandra Hoffmann (CTO)
**Last Updated:** October 2025
**Review Cycle:** Quarterly
**Next Review:** January 2026

## Introduction

The TechVision Technology Radar is our quarterly assessment of technologies, tools, frameworks, and platforms relevant to our consulting practice. It serves as a guide for project technology decisions and professional development priorities. Every technology is classified into one of four rings based on our collective experience and strategic direction.

This edition reflects lessons learned from Projekt Aurora (Azure cloud migration for Muller Maschinenbau), ongoing work on the FinSecure Portal, and the MedTech Analytics platform. All technology selections for client projects must reference this radar during the architecture decision process (see our Architecture Decision Record template in Confluence).

### Ring Definitions

- **Adopt** — Proven in production at TechVision. Default choice for new projects. Team training is available.
- **Trial** — Promising technologies we are actively piloting in internal or low-risk client projects. Requires senior oversight.
- **Assess** — Technologies worth exploring through spikes, prototypes, or conference talks. Not approved for client projects yet.
- **Hold** — Technologies we are actively moving away from. Use only for maintaining existing systems, not for new development.

---

## Adopt

### Python

Python remains our primary language for backend services, data engineering, and automation. With the release of Python 3.12 and the performance improvements it brings, we have standardized on this version across all new projects. Our coding standards (see doc_010) mandate type hints and ruff-based linting. Python is the foundation of Projekt Aurora's data pipelines and the MedTech Analytics backend.

### TypeScript

TypeScript is our standard for all frontend development and Node.js-based services. Strict mode is mandatory per our coding standards. The type safety it provides has measurably reduced production bugs in the FinSecure Portal, where the frontend team reports a 40% decrease in runtime type errors since migrating from plain JavaScript.

### React

React continues to be our default frontend framework. We use React 18+ with functional components and hooks exclusively. The FinSecure Portal and MedTech Analytics dashboards are both built on React. Our internal component library (`@techvision/ui-kit`) is React-based and shared across projects.

### PostgreSQL

PostgreSQL 16 is our primary relational database. Its extensibility (pgvector for embeddings, PostGIS for geospatial, pg_cron for scheduling) makes it suitable for the vast majority of our use cases. Anna Richter has authored comprehensive database standards (see doc_015) covering naming conventions, indexing strategies, and performance guidelines. All three major projects currently run on PostgreSQL.

### Terraform

Terraform is our infrastructure-as-code tool of choice. All Azure resources for Projekt Aurora are provisioned via Terraform modules maintained by the DevOps team under Markus Lang. We maintain a private module registry with reusable modules for common patterns like AKS clusters, Azure SQL databases, and networking components. See doc_011 for our Azure architecture reference.

### GitHub Actions

GitHub Actions replaced Jenkins as our CI/CD platform in early 2025. Markus Lang's team has built a set of reusable workflow templates covering our standard pipeline stages: lint, test, build, security scan, and deploy (see doc_013). All new projects must use GitHub Actions. Migration of legacy Jenkins pipelines is ongoing and expected to complete by Q1 2026.

### Docker

Docker is the standard containerization platform for all services. Every deployable service must have a Dockerfile that produces a minimal, non-root image. We use multi-stage builds to keep image sizes small. Our container security scanning runs via Trivy in the CI pipeline. Docker is used for local development environments as well, ensuring parity with production.

### FastAPI

FastAPI has become our default Python web framework, replacing Flask for new projects. Its native async support, automatic OpenAPI documentation generation, and Pydantic-based validation align perfectly with our API design guidelines (see doc_012). The MedTech Analytics API and several Projekt Aurora microservices use FastAPI.

---

## Trial

### Rust (Performance-Critical Services)

We are evaluating Rust for performance-critical components where Python's throughput is insufficient. Felix Braun is leading a trial implementation of a high-throughput data ingestion service for Projekt Aurora's IoT sensor pipeline, where we need to process 50,000+ messages per second. Early benchmarks show a 12x improvement over the equivalent Python implementation. Adoption requires dedicated training; we currently have three team members with production-level Rust experience.

### Apache Iceberg

Apache Iceberg is being evaluated as our open table format for the data lake in Projekt Aurora. Anna Richter's team is piloting it as an alternative to Delta Lake for the Silver layer, attracted by its superior schema evolution capabilities and broader engine compatibility. The trial runs in parallel with the existing Delta Lake implementation. Initial results show comparable performance with better metadata management for partition-heavy tables.

### htmx

We are trialing htmx for internal tools and admin interfaces where a full React SPA would be overengineered. Daniel Wolff built an internal time-tracking tool using FastAPI + htmx that was delivered in one-third the time of an equivalent React implementation. The simplicity is appealing for CRUD-heavy internal applications, but we need more experience before recommending it for client-facing projects.

### Astro

Astro is being evaluated for content-heavy and documentation sites. Its island architecture allows us to use React components where interactivity is needed while generating static HTML for everything else. We are rebuilding the TechVision company website with Astro as a pilot. Performance benchmarks show significantly better Core Web Vitals compared to our current Next.js implementation.

---

## Assess

### Deno

Deno 2.0's improved Node.js compatibility makes it worth reassessing. The built-in TypeScript support, security-by-default model, and standard library are attractive. However, ecosystem maturity and team familiarity remain concerns. We plan to conduct a spike in Q1 2026 to evaluate Deno for a small internal API service.

### Bun

Bun's speed improvements for JavaScript tooling are impressive, particularly for package installation and test execution. We are monitoring its maturity and considering it as a drop-in replacement for Node.js in development toolchains. Production use is premature given the relatively young ecosystem, but the performance gains in CI pipelines (2-3x faster npm install) warrant continued assessment.

### WASM Edge Computing

WebAssembly at the edge (Cloudflare Workers, Fastly Compute) presents interesting possibilities for latency-sensitive services. We see potential applications in the FinSecure Portal for geographically distributed API gateways. Tobias Fischer is evaluating the security implications, and we plan a proof-of-concept in Q1 2026.

### LangChain

LangChain is being assessed for LLM-powered features in our products. While the framework provides useful abstractions for retrieval-augmented generation (RAG) and agent workflows, we have concerns about its rapid API changes and abstraction overhead. Anna Richter is evaluating it alongside direct OpenAI API usage for the MedTech Analytics natural language query feature.

---

## Hold

### Angular

Angular is in hold status. Our only remaining Angular application is an older module of the FinSecure Portal's back-office interface. We will maintain it but all new frontend development must use React. The planned migration of the remaining Angular components to React is scheduled for Q2 2026.

### Docker Compose for Production

Docker Compose is acceptable for local development but must not be used for production deployments. All production workloads must run on Kubernetes (AKS). We have observed reliability and scaling issues when teams attempted to use Docker Compose in staging environments. See doc_016 for our Kubernetes operations runbook.

### Jenkins

Jenkins is being phased out in favor of GitHub Actions. Existing Jenkins pipelines may continue to run during the migration period, but no new Jenkins pipelines may be created. The last Jenkins instance is scheduled for decommissioning by end of Q1 2026. See doc_013 for the GitHub Actions-based pipeline documentation.

### MongoDB

MongoDB is on hold for new projects. While it served us well in early prototyping phases, PostgreSQL with its JSONB capabilities covers our document storage needs without the operational overhead of maintaining a separate database system. The one remaining MongoDB instance (legacy customer portal) will be migrated to PostgreSQL as part of the Q1 2026 technical debt reduction initiative.

---

## Process Notes

Technology radar changes are proposed via Architecture Decision Records (ADRs) and discussed in the monthly Architecture Guild meeting. Any team member may propose a change. Promotions from Assess to Trial require a completed spike or proof-of-concept. Promotions from Trial to Adopt require at least one successful production deployment and a retrospective.

Questions or proposals should be directed to Sandra Hoffmann or discussed in the `#tech-radar` Slack channel.
