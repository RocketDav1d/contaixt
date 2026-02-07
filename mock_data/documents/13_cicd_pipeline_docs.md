---
doc_id: doc_013
title: "CI/CD Pipeline Documentation"
author: Markus Lang
source_type: notion
---

# CI/CD Pipeline Documentation

**Author:** Markus Lang (DevOps Lead)
**Last Updated:** October 2025
**Applies to:** All TechVision repositories

## Introduction

This document describes the CI/CD pipeline architecture used across all TechVision projects. We use GitHub Actions as our sole CI/CD platform, having completed the migration from Jenkins in mid-2025 (Jenkins is now on Hold per the Technology Radar, doc_009). The pipeline standards described here apply to all repositories, with project-specific customizations documented in each repository's `.github/` directory.

Our pipeline philosophy is: every commit to `main` is potentially deployable. The pipeline gates quality, security, and correctness so that the team can merge with confidence and deploy continuously.

---

## GitHub Actions Workflow Structure

### Reusable Workflows

The DevOps team maintains a central repository (`techvision/gh-actions-workflows`) containing reusable workflow templates. Project repositories call these templates rather than duplicating pipeline logic.

**Available templates:**
- `python-ci.yml` — Lint (ruff), type check (mypy), test (pytest), coverage report.
- `typescript-ci.yml` — Lint (ESLint), type check (tsc), test (vitest), build.
- `docker-build.yml` — Multi-stage Docker build, push to Azure Container Registry, Trivy vulnerability scan.
- `terraform-plan.yml` — Terraform init, validate, plan with cost estimation.
- `terraform-apply.yml` — Terraform apply with manual approval gate.
- `deploy-aks.yml` — Helm upgrade to AKS cluster with health check verification.

### Typical Workflow File

```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    uses: techvision/gh-actions-workflows/.github/workflows/python-ci.yml@v2
    with:
      python-version: "3.12"
      coverage-threshold: 80

  build:
    needs: lint-and-test
    uses: techvision/gh-actions-workflows/.github/workflows/docker-build.yml@v2
    with:
      registry: tvsharedweucr.azurecr.io
      image-name: aurora-api
    secrets: inherit

  deploy-dev:
    if: github.ref == 'refs/heads/main'
    needs: build
    uses: techvision/gh-actions-workflows/.github/workflows/deploy-aks.yml@v2
    with:
      environment: dev
      cluster: tv-dev-weu-aks-aurora
      namespace: aurora
    secrets: inherit
```

---

## Pipeline Stages

Every code change passes through these sequential stages:

### 1. Lint

- **Python:** ruff check + ruff format (see coding standards, doc_010).
- **TypeScript:** ESLint + Prettier.
- **Terraform:** `terraform fmt -check` + `terraform validate`.
- **Docker:** Hadolint for Dockerfile best practices.

Lint failures block the pipeline immediately. There are no exceptions for "minor" lint issues.

### 2. Test

- **Unit tests** run on every PR and push to `main`.
- **Integration tests** run on push to `main` and on PRs labeled `integration-test`. These use Testcontainers for database and service dependencies.
- **Coverage gates:** Python services require 80% minimum, TypeScript 70% minimum. Coverage reports are posted as PR comments via Codecov.

### 3. Build

- Docker images built using multi-stage Dockerfiles.
- Images tagged with both the semantic version and the git SHA: `v1.3.2` and `abc123def`.
- Images pushed to Azure Container Registry (`tvsharedweucr.azurecr.io`).
- Build metadata (commit SHA, build time, branch) injected as image labels.

### 4. Security Scan

- **Trivy** scans Docker images for OS and application dependency vulnerabilities.
- **Snyk** scans dependency manifests (`requirements.txt`, `package-lock.json`) for known CVEs.
- **Checkov** scans Terraform and Kubernetes manifests for misconfigurations.
- **Gitleaks** scans for accidentally committed secrets.

Critical and high vulnerabilities block the pipeline. Medium vulnerabilities generate warnings and Jira tickets. Tobias Fischer (Security Officer) receives a weekly digest of all security findings.

### 5. Deploy

Deployment is stage-specific. Only code on `main` is deployed. PR branches are only built and tested, never deployed.

---

## Environment Promotion

### Environment Chain

```
dev → staging → production
```

**Development (dev):**
- Auto-deployed on every merge to `main`.
- Used for integration testing and developer verification.
- May have relaxed resource limits and shorter data retention.
- Accessible only via VPN.

**Staging:**
- Promoted from dev via manual trigger (workflow dispatch) or automated schedule (nightly).
- Mirrors production configuration as closely as possible (same AKS node sizes, same database tier).
- Used for QA, performance testing, and client UAT.
- Runs synthetic monitoring to catch issues before production.

**Production:**
- Promoted from staging via manual approval.
- Requires at least two approvals from designated approvers (team lead + DevOps engineer).
- Deployment window: Monday through Thursday, 09:00-16:00 CET (no Friday deployments, to avoid weekend firefighting).
- Emergency hotfix deployments may bypass the window with CTO approval and on-call coverage.

### Promotion Workflow

```yaml
# .github/workflows/promote-staging.yml
name: Promote to Staging
on:
  workflow_dispatch:
    inputs:
      image-tag:
        description: "Image tag to promote"
        required: true

jobs:
  promote:
    runs-on: ubuntu-latest
    environment: staging  # Requires approval in GitHub
    steps:
      - uses: techvision/gh-actions-workflows/.github/workflows/deploy-aks.yml@v2
        with:
          environment: staging
          image-tag: ${{ inputs.image-tag }}
```

---

## Deployment Strategies

### Blue-Green Deployment (APIs)

All API services use blue-green deployments:

1. New version deployed to the "green" slot (a parallel Kubernetes Deployment).
2. Health checks and smoke tests run against the green slot.
3. If healthy, the Kubernetes Service switches traffic to green.
4. Old "blue" deployment kept running for 15 minutes as a rollback target.
5. If smoke tests fail, traffic remains on blue and the green deployment is removed.

This is implemented using Kubernetes labels and the `deploy-aks.yml` reusable workflow, which manages the blue-green switchover.

### Rolling Deployment (Workers & Background Jobs)

Worker processes (job runners, queue consumers) use rolling deployments:

- Kubernetes RollingUpdate strategy with `maxUnavailable: 0` and `maxSurge: 1`.
- Workers finish their current job before shutting down (graceful termination period: 300 seconds).
- New pods must pass readiness probes before old pods are terminated.

---

## Secret Management

### GitHub Secrets

- **Repository secrets** for project-specific values (API keys, database passwords).
- **Organization secrets** for shared values (container registry credentials, Snyk tokens).
- Secrets are scoped to specific environments (dev, staging, production) in GitHub Environments.

### Azure Key Vault Integration

For runtime secrets (accessed by applications at runtime, not just CI/CD):

1. Secrets stored in Azure Key Vault (one per environment, see doc_011).
2. GitHub Actions authenticates to Azure via OIDC federation (no stored credentials).
3. During deployment, Helm values reference Key Vault via the Azure Key Vault CSI driver.
4. Applications access secrets as mounted files or environment variables in the pod.

**No secrets are baked into Docker images.** Ever. Gitleaks scanning in the pipeline enforces this.

---

## Rollback Procedures

### Automated Rollback

If post-deployment health checks fail for more than 3 minutes, the pipeline automatically triggers a rollback:

1. Kubernetes Deployment is rolled back to the previous ReplicaSet (`kubectl rollout undo`).
2. An alert is sent to the `#deployments` Slack channel with the failure reason.
3. A Jira ticket is automatically created for investigation.

### Manual Rollback

For issues discovered after the automated health check window:

```bash
# Option 1: Redeploy the previous version via workflow dispatch
# Go to Actions → Deploy → Run workflow → enter previous image tag

# Option 2: kubectl rollback (emergency, direct cluster access)
kubectl rollout undo deployment/aurora-api -n aurora-prod
```

All rollbacks are logged in the `#deployments` Slack channel and require a post-incident review within 48 hours.

---

## Artifact Versioning

### Semantic Versioning

All deployable artifacts follow semantic versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR** — Breaking API changes or significant architecture changes.
- **MINOR** — New features, backward-compatible changes.
- **PATCH** — Bug fixes, performance improvements.

### Tagging Strategy

- Git tags trigger release builds: `v1.3.2`.
- Docker images are tagged with: `v1.3.2`, `v1.3`, `v1`, and the git SHA `abc123d`.
- Helm charts are versioned independently from application versions.
- The `latest` tag is never used. All references must use explicit versions.

### Release Process

1. Create a release branch: `release/v1.3.2`.
2. Update `CHANGELOG.md` with the release notes.
3. Merge to `main` via PR (standard review process).
4. Tag the merge commit: `git tag v1.3.2`.
5. Push the tag: the pipeline automatically builds and pushes release artifacts.
6. Promote through environments: dev (automatic) → staging (manual trigger) → production (manual approval).

---

## Pipeline Monitoring

- Pipeline run metrics are exported to Grafana (see doc_014) via the GitHub Actions metrics exporter.
- Key metrics tracked: pipeline duration, success rate, failure by stage, deployment frequency.
- Weekly pipeline health report generated automatically and shared in `#devops` Slack channel.
- Target: 95% pipeline success rate, average pipeline duration under 10 minutes.

For pipeline issues or improvement requests, contact Markus Lang or the DevOps team in `#devops` on Slack.
