---
doc_id: doc_014
title: "Monitoring & Alerting Runbook"
author: Markus Lang
source_type: notion
---

# Monitoring & Alerting Runbook

**Author:** Markus Lang (DevOps Lead)
**Last Updated:** October 2025
**On-Call Team:** DevOps + Senior Developers (rotation schedule in PagerDuty)

## Introduction

This runbook describes the monitoring and alerting infrastructure used across all TechVision projects, including Projekt Aurora, the FinSecure Portal, and MedTech Analytics. It covers the monitoring stack, dashboard organization, alert severity definitions, on-call procedures, and common alert resolution playbooks.

Reliable monitoring is a prerequisite for the continuous deployment model described in our CI/CD documentation (doc_013). Every production service must be observable before it is deployed.

---

## Monitoring Stack

### Components

| Component | Purpose | Deployment |
|---|---|---|
| **Prometheus** | Metrics collection and storage | AKS (Prometheus Operator via Helm) |
| **Grafana** | Dashboards and visualization | AKS, accessible via VPN at `grafana.internal.techvision.de` |
| **Alertmanager** | Alert routing, grouping, and silencing | AKS (co-deployed with Prometheus) |
| **Loki** | Log aggregation (structured logs) | AKS with Azure Blob Storage backend |
| **Promtail** | Log shipping agent (DaemonSet on all nodes) | AKS |
| **Tempo** | Distributed tracing (OpenTelemetry backend) | AKS |
| **PagerDuty** | On-call management and escalation | SaaS |
| **StatusPage** | Client-facing status communication | SaaS (`status.techvision.de`) |

### Data Retention

- **Prometheus metrics:** 30 days local, 1 year in Thanos long-term storage (Azure Blob).
- **Loki logs:** 14 days hot storage, 90 days in Azure Blob cold storage.
- **Tempo traces:** 7 days (sampled at 10% for production, 100% for staging).

---

## Key Dashboards

### Infrastructure Dashboard

**URL:** `grafana.internal.techvision.de/d/infrastructure`

Provides a cluster-level view of all AKS environments:
- Node CPU and memory utilization (target: below 70% sustained).
- Pod counts by namespace and status (Running, Pending, Failed).
- Persistent volume usage and I/O throughput.
- Network ingress/egress by namespace.
- Node pool autoscaler activity.

### Application Dashboard

**URL:** `grafana.internal.techvision.de/d/application`

Per-service metrics following the RED method (Rate, Errors, Duration):
- Request rate (requests per second) by endpoint.
- Error rate (4xx and 5xx) by endpoint and status code.
- Latency distribution (p50, p95, p99) by endpoint.
- Active database connections and query duration.
- Background job queue depth and processing rate (critical for Projekt Aurora's data pipeline, see doc_017).

### Business Metrics Dashboard

**URL:** `grafana.internal.techvision.de/d/business`

Project-specific KPIs:
- **Projekt Aurora:** Documents ingested per hour, pipeline processing time, data freshness (time since last successful sync from SAP).
- **FinSecure Portal:** Active user sessions, transaction processing rate, authentication success/failure rate.
- **MedTech Analytics:** Dashboard query response time, data export completions, concurrent users.

### CI/CD Dashboard

**URL:** `grafana.internal.techvision.de/d/cicd`

Pipeline health metrics from GitHub Actions (see doc_013):
- Deployment frequency by environment.
- Pipeline success rate and mean duration.
- Failure breakdown by stage.
- Time from commit to production.

---

## Alert Severity Levels

### P1 — Critical (Page Immediately)

**Response Time:** 5 minutes (acknowledgment), 15 minutes (first responder engaged).
**Notification:** PagerDuty page to primary on-call, auto-escalate to secondary after 5 minutes, then to Markus Lang after 15 minutes.
**Communication:** StatusPage incident created within 15 minutes for client-facing impact.

**Triggers:**
- Production service down (zero healthy pods).
- API error rate exceeds 10% for more than 2 minutes.
- API p99 latency exceeds 10 seconds for more than 5 minutes.
- Database unreachable or replication lag exceeds 60 seconds.
- Security breach indicators (unusual authentication patterns, data exfiltration alerts).
- SSL certificate expires in less than 24 hours.
- Data pipeline halted for more than 1 hour (Projekt Aurora).

### P2 — High (Slack + 15-Minute Response)

**Response Time:** 15 minutes (acknowledgment), 1 hour (investigation started).
**Notification:** Slack `#alerts-high` channel + PagerDuty notification (no page).

**Triggers:**
- API error rate exceeds 5% for more than 5 minutes.
- API p95 latency exceeds 5 seconds for more than 10 minutes.
- AKS node pool at 85% capacity (approaching autoscale limit).
- Disk usage exceeds 85% on any persistent volume.
- Database connection pool utilization exceeds 80%.
- Background job failure rate exceeds 10%.
- Deployment failed and auto-rolled back.

### P3 — Medium (Next Business Day)

**Response Time:** Next business day.
**Notification:** Slack `#alerts-medium` channel. Jira ticket auto-created.

**Triggers:**
- API p95 latency exceeds 2 seconds (performance degradation but within SLO).
- Non-critical dependency health check failing (e.g., email service, analytics).
- Certificate expires within 14 days.
- Cost anomaly detected (spend exceeds 120% of daily average).
- Dependency vulnerability detected (medium severity, see doc_013 security scan).
- Log volume spike (potential log-flooding from a bug).

---

## On-Call Rotation

### Schedule

- **Rotation:** Weekly, Monday 09:00 CET to Monday 09:00 CET.
- **Roles:** Primary on-call (first responder) and Secondary on-call (backup and escalation).
- **Team:** DevOps team (4 members) + Senior developers (rotating, 2 per month from the engineering team).
- **Schedule managed in PagerDuty.** All participants must have the PagerDuty app installed with push notifications enabled.

### On-Call Expectations

- Primary on-call must acknowledge P1 alerts within 5 minutes.
- On-call engineer must have laptop and VPN access available at all times during their rotation.
- On-call hours: 24/7 for P1, business hours (08:00-20:00 CET) for P2.
- Compensation: On-call bonus per rotation week, additional compensation per P1 incident outside business hours (per company policy).

### Escalation Path

```
P1 Alert → Primary On-Call (5 min) → Secondary On-Call (10 min) → Markus Lang (15 min) → Sandra Hoffmann (30 min)
```

For FinSecure Portal (banking): Tobias Fischer (Security Officer) is added to the escalation path for any security-related alerts.

---

## Common Alert Runbooks

### High CPU Usage (> 85% sustained for 10 minutes)

1. Identify the affected pod(s): Check the Infrastructure Dashboard, filter by namespace and pod.
2. Check if autoscaling is active: `kubectl get hpa -n {namespace}`. If HPA is at max replicas, consider temporarily increasing the max.
3. Review application logs in Loki for unusual patterns (retry storms, infinite loops).
4. Check for recent deployments that may have introduced a performance regression.
5. If a single pod is affected, restart it: `kubectl delete pod {pod-name} -n {namespace}` (the ReplicaSet will recreate it).
6. If cluster-wide, check for noisy neighbor effects. Consider isolating the workload to a dedicated node pool.
7. File a Jira ticket for root cause investigation if the issue is not immediately explained.

### Disk Space Low (> 85% on PersistentVolume)

1. Identify the volume: Check the Infrastructure Dashboard for PV utilization.
2. For database volumes: Check for long-running transactions, bloat (`pg_stat_user_tables`), or unvacuumed tables.
3. For log volumes: Check Loki ingestion rate. If a service is log-flooding, increase log level or fix the root cause.
4. Expand the PV if possible (AKS supports online PV expansion for managed disks).
5. For Projekt Aurora data lake: Check Bronze layer retention policy. Old raw files should be archived per the lifecycle policy (see doc_017 and doc_011).
6. Emergency: Identify and delete temporary files or old snapshots.

### Error Rate Spike (> 5% for 5 minutes)

1. Open the Application Dashboard. Identify which endpoint(s) are generating errors.
2. Check the error status code distribution: 4xx errors suggest client issues (bad deployment of a frontend, invalid API calls), 5xx errors suggest backend issues.
3. Correlate with recent deployments. If a deployment happened in the last 30 minutes, consider rollback (see doc_013).
4. Check dependency health: database connectivity, external API responses, message broker availability.
5. Review error logs in Loki, filtered by the affected service and time window.
6. For FinSecure Portal: Check if the error affects transaction processing. If yes, escalate to P1 immediately.

### Certificate Expiry (< 14 days)

1. Check which certificate is approaching expiry in the cert-manager dashboard.
2. Verify cert-manager is running and can reach Let's Encrypt: `kubectl logs -n cert-manager deploy/cert-manager`.
3. Check the Certificate resource status: `kubectl describe certificate {name} -n {namespace}`.
4. Common issues: DNS challenge failing (check DNS provider credentials), rate limiting from Let's Encrypt (check for duplicate issuance attempts).
5. If cert-manager cannot renew automatically, manually trigger renewal: `kubectl delete secret {tls-secret-name} -n {namespace}` (cert-manager will recreate it).
6. For Azure-managed certificates (Application Gateway), check the Key Vault integration.

---

## SLO Definitions

### Production APIs

| Metric | Target | Measurement Window |
|---|---|---|
| Availability | 99.9% | Rolling 30 days |
| p95 Latency | < 500ms | Rolling 30 days |
| p99 Latency | < 2000ms | Rolling 30 days |
| Error Rate (5xx) | < 0.1% | Rolling 30 days |

**Error Budget:** 99.9% availability allows 43.2 minutes of downtime per 30-day window. When the error budget is below 25%, non-critical deployments are paused until the budget recovers.

### Data Pipelines (Projekt Aurora)

| Metric | Target | Measurement Window |
|---|---|---|
| Pipeline Success Rate | 99.5% | Rolling 7 days |
| Data Freshness | < 1 hour | Continuous |
| End-to-End Processing Time | < 30 minutes | Per batch |

---

## Incident Communication

### Internal Communication

- All incidents communicated in `#incidents` Slack channel.
- Incident commander (usually the primary on-call) posts regular updates every 30 minutes during P1 incidents.
- Post-incident review (blameless retrospective) within 48 hours for all P1 and P2 incidents.

### Client-Facing Communication (StatusPage)

- StatusPage updated within 15 minutes of a P1 incident being confirmed.
- Status levels: Operational, Degraded Performance, Partial Outage, Major Outage.
- Updates posted every 30 minutes until resolution.
- Resolution note includes brief root cause summary and preventive measures.
- StatusPage URL: `status.techvision.de` — all clients are subscribed to their relevant service components.

---

## Adding Monitoring to New Services

Before any new service is deployed to production, it must meet these observability requirements (see also our Microservices Architecture Patterns, doc_018):

1. **Metrics endpoint:** Expose Prometheus metrics at `/metrics` (use `prometheus-fastapi-instrumentator` for Python, `micrometer` for Java).
2. **Structured logging:** JSON-formatted logs to stdout. Include `request_id`, `service_name`, `environment`.
3. **Health endpoints:** `/health` (liveness) and `/ready` (readiness) as defined in the API Design Guidelines (doc_012).
4. **Distributed tracing:** OpenTelemetry SDK integrated, exporting traces to Tempo.
5. **Dashboard:** A Grafana dashboard created from the service dashboard template.
6. **Alerts:** At minimum, alerts for error rate, latency, and pod health configured in Alertmanager.

Contact Markus Lang or the DevOps team in `#devops` for assistance setting up monitoring for new services.
