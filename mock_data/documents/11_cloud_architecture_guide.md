---
doc_id: doc_011
title: "Azure Cloud Architecture Reference Guide"
author: Sandra Hoffmann
source_type: notion
---

# Azure Cloud Architecture Reference Guide

**Author:** Sandra Hoffmann (CTO)
**Contributors:** Markus Lang (DevOps Lead), Anna Richter (Data Engineer)
**Last Updated:** October 2025
**Status:** Active — Living Document

## Introduction

This document defines the reference architecture and conventions for all TechVision Azure deployments. It serves as the authoritative guide for provisioning, organizing, and securing Azure resources across client engagements and internal projects. The patterns described here were developed and validated during Projekt Aurora (cloud migration for Muller Maschinenbau) and are now the baseline for all Azure-based projects, including the FinSecure Portal and MedTech Analytics.

All infrastructure must be provisioned via Terraform (see our Technology Radar, doc_009, for tooling decisions). Manual resource creation via the Azure Portal is prohibited for any environment beyond personal sandboxes.

---

## Azure Landing Zone Architecture

### Hub-Spoke Network Topology

We implement the Azure Hub-Spoke network topology as recommended by the Cloud Adoption Framework. This provides centralized network management, security controls, and shared services while giving each workload isolated networking.

**Hub Virtual Network:**
- Hosts shared services: Azure Firewall, VPN Gateway, Azure Bastion, DNS resolvers.
- One hub per Azure region. Currently, we operate a primary hub in `westeurope` (Netherlands) and a secondary in `germanywestcentral` (Frankfurt) for data residency requirements.
- Address space: `10.0.0.0/16` for the primary hub.

**Spoke Virtual Networks:**
- Each spoke represents a workload or project (e.g., one spoke for Projekt Aurora production, one for FinSecure Portal staging).
- Spokes are peered to the hub. Spoke-to-spoke communication routes through the hub firewall for inspection.
- Address space: Assigned from our IP Address Management (IPAM) sheet. Each spoke receives a `/20` block (4,096 addresses) subdivided into subnets for AKS, databases, application gateways, and private endpoints.

**Example (Projekt Aurora):**
```
Hub VNet (10.0.0.0/16)
  ├── AzureFirewallSubnet     (10.0.1.0/24)
  ├── GatewaySubnet            (10.0.2.0/24)
  └── BastionSubnet            (10.0.3.0/24)

Spoke VNet - Aurora Prod (10.1.0.0/20)
  ├── aks-subnet               (10.1.0.0/22)  - 1024 IPs for AKS pods
  ├── db-subnet                (10.1.4.0/24)  - Azure SQL private endpoints
  ├── appgw-subnet             (10.1.5.0/24)  - Application Gateway
  └── pe-subnet                (10.1.6.0/24)  - Private endpoints (Key Vault, Storage)
```

---

## Subscription Strategy

We use a **one subscription per environment** model for each client engagement:

| Subscription | Purpose | Example |
|---|---|---|
| `tv-{client}-dev` | Development and testing | `tv-mueller-dev` |
| `tv-{client}-staging` | Pre-production validation | `tv-mueller-staging` |
| `tv-{client}-prod` | Production workloads | `tv-mueller-prod` |
| `tv-internal-shared` | Shared services (DNS, monitoring, container registry) | — |

All subscriptions are organized under a Management Group hierarchy:

```
TechVision Root
  ├── Internal
  │     ├── tv-internal-shared
  │     └── tv-internal-dev
  ├── Client Projects
  │     ├── Mueller Maschinenbau
  │     │     ├── tv-mueller-dev
  │     │     ├── tv-mueller-staging
  │     │     └── tv-mueller-prod
  │     └── FinSecure
  │           ├── tv-finsecure-dev
  │           ├── tv-finsecure-staging
  │           └── tv-finsecure-prod
  └── Sandbox (personal experimentation)
```

Azure Policies are applied at the Management Group level to enforce tagging, allowed regions, and resource type restrictions.

---

## Resource Naming Convention

All Azure resources follow this naming pattern:

```
tv-{environment}-{region}-{service}-{instance}
```

**Components:**
- `tv` — TechVision prefix (constant)
- `{environment}` — `dev`, `stg`, `prd`
- `{region}` — `weu` (West Europe), `gwc` (Germany West Central)
- `{service}` — Service abbreviation (see table below)
- `{instance}` — Descriptive name or numeric identifier

**Service Abbreviations:**

| Service | Abbreviation | Example |
|---|---|---|
| Resource Group | `rg` | `tv-prd-weu-rg-aurora` |
| AKS Cluster | `aks` | `tv-prd-weu-aks-aurora` |
| Azure SQL | `sql` | `tv-prd-weu-sql-aurora` |
| Storage Account | `st` | `tvprdweustaurora` (no hyphens, Azure limitation) |
| Key Vault | `kv` | `tv-prd-weu-kv-aurora` |
| App Gateway | `agw` | `tv-prd-weu-agw-aurora` |
| Virtual Network | `vnet` | `tv-prd-weu-vnet-aurora` |
| Data Factory | `adf` | `tv-prd-weu-adf-aurora` |
| Container Registry | `cr` | `tvsharedweucr` |

All resources must be tagged with:
- `project` — Project codename (e.g., `aurora`, `finsecure`)
- `environment` — `dev`, `staging`, `production`
- `owner` — Responsible team or individual
- `cost-center` — For billing allocation
- `managed-by` — `terraform` (to identify IaC-managed resources)

---

## Core Services

### Azure Kubernetes Service (AKS)

AKS is our primary compute platform for containerized workloads. See doc_016 for the detailed Kubernetes operations runbook.

- **Version:** We track the latest stable Kubernetes version minus one (currently 1.28.x). Upgrades follow the procedure in doc_016.
- **Node Pools:** Three pools per cluster — `system` (3 nodes, Standard_D4s_v5), `workload` (autoscale 3-12, Standard_D8s_v5), `data` (4 nodes, Standard_E8s_v5 for memory-intensive workloads).
- **Networking:** Azure CNI with dynamic IP allocation. Pods receive IPs from the AKS subnet.
- **Identity:** Workload Identity (AAD Pod Identity successor) for keyless access to Azure services.

### Azure SQL Database

- **Tier:** General Purpose for dev/staging, Business Critical for production.
- **Configuration:** Zone-redundant, geo-replication for production databases. Auto-failover groups for Projekt Aurora and FinSecure Portal.
- **Security:** Transparent Data Encryption (TDE) enabled. Azure AD authentication mandatory. SQL authentication disabled.
- **Connectivity:** Private endpoints only. No public access.

Refer to doc_015 for database design standards and best practices.

### Azure Data Factory

Used extensively in Projekt Aurora for data pipeline orchestration (see doc_017 for the full data platform architecture).

- **Environment isolation:** Separate ADF instances per environment with linked CI/CD via GitHub Actions.
- **Integration Runtimes:** Self-hosted IR for on-premises SAP connectivity, Azure IR for cloud-to-cloud operations.
- **Monitoring:** Pipeline run metrics exported to Log Analytics and surfaced in Grafana dashboards (see doc_014).

### Azure Key Vault

Central secret management for all environments.

- One Key Vault per environment per project.
- Access policies use RBAC (not vault access policies). Only managed identities and service principals have access; no personal accounts in production.
- Secret rotation automated via Azure Automation runbooks on a 90-day cycle.
- CI/CD pipelines retrieve secrets at deployment time via GitHub Actions OIDC federation (see doc_013).

### Azure Application Gateway

- Serves as the L7 load balancer and WAF for internet-facing services.
- WAF v2 with OWASP 3.2 ruleset enabled in prevention mode for production.
- SSL termination with certificates from Key Vault (auto-renewed via cert-manager integration).
- Path-based routing to different backend pools (e.g., `/api/*` to AKS, `/static/*` to Storage Account).

---

## Network Security

### Defense in Depth

Our network security follows a layered approach:

1. **Azure Firewall (Hub):** Centralized egress filtering. All outbound traffic from spokes routes through the firewall. Explicit allow-list for external endpoints (package registries, API endpoints, monitoring services).
2. **Network Security Groups (NSGs):** Applied at the subnet level in each spoke. Default deny-all inbound, with explicit rules for required traffic flows.
3. **Private Endpoints:** All PaaS services (SQL, Storage, Key Vault, Container Registry) are accessed via private endpoints. No public endpoints in staging or production.
4. **Azure DDoS Protection:** Standard tier enabled on all public-facing VNets.
5. **Web Application Firewall:** On Application Gateway for HTTP/HTTPS traffic inspection.

### Network Flow Rules

| Source | Destination | Port | Purpose |
|---|---|---|---|
| App Gateway | AKS Subnet | 443 | Ingress traffic to services |
| AKS Subnet | DB Subnet | 5432 | PostgreSQL connections |
| AKS Subnet | PE Subnet | 443 | Key Vault, Storage access |
| Hub Firewall | Internet | 443 | Outbound HTTPS (allow-listed) |
| All Subnets | Azure Monitor | 443 | Metrics and logs |

Tobias Fischer (Security Officer) reviews all NSG rule changes as part of the PR process for Terraform modifications. Security-sensitive network changes require his explicit approval.

---

## Cost Management

### Budget Controls

- Each subscription has an Azure Budget with alerts at 75%, 90%, and 100% of the monthly allocation.
- Cost anomaly detection is enabled and alerts the DevOps team in `#azure-costs` Slack channel.
- Monthly cost review meetings with project leads to identify optimization opportunities.

### Cost Optimization Practices

1. **Reserved Instances:** 1-year reservations for production AKS nodes and SQL databases (35-40% savings).
2. **Spot Instances:** Used for dev/staging AKS node pools and non-critical batch workloads in Projekt Aurora's data pipelines.
3. **Auto-shutdown:** Dev environments automatically shut down at 20:00 CET and restart at 07:00 CET on weekdays.
4. **Right-sizing:** Monthly review of resource utilization via Azure Advisor recommendations. Markus Lang's team processes these in sprint planning.
5. **Storage Tiering:** Azure Blob lifecycle policies move data from Hot to Cool after 30 days and to Archive after 90 days for Projekt Aurora's raw data lake (Bronze layer, see doc_017).

### Projekt Aurora Cost Reference

As a reference implementation, Projekt Aurora's monthly Azure spend breaks down approximately:
- AKS Cluster (production): 38%
- Azure SQL (production + replicas): 22%
- Data Factory + Storage (data lake): 18%
- Networking (Firewall, App Gateway, VPN): 12%
- Other (Key Vault, Monitoring, Misc): 10%

---

## Disaster Recovery

- **RPO:** 1 hour for production databases (continuous replication).
- **RTO:** 4 hours for full environment recovery.
- **Strategy:** Active-passive with Azure Site Recovery for VMs. Active geo-replication for Azure SQL. AKS redeployment via Terraform + Helm (infrastructure is fully reproducible from code).
- **DR Testing:** Quarterly failover drills. Last drill (August 2025) achieved RTO of 2.5 hours.

---

## Compliance

All Azure deployments must comply with:
- **ISO 27001** — TechVision's information security management system.
- **GDPR** — Data residency in EU (Germany West Central preferred for German clients).
- **BSI C5** — For public sector and regulated industry clients (FinSecure Portal).
- **Azure Policy:** Enforced at Management Group level. Non-compliant resources are flagged and must be remediated within 48 hours.

For questions or exceptions to this guide, contact Sandra Hoffmann or Markus Lang. All exceptions require a documented Architecture Decision Record.
