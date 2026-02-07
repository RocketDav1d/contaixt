---
doc_id: doc_020
title: "Projekt Aurora – Technical Design Document"
author: Felix Braun
source_type: notion
---

# Projekt Aurora -- Technical Design Document

**Version:** 1.2
**Date:** September 20, 2025
**Author:** Felix Braun, Senior Developer / Technical Lead
**Reviewed by:** Sandra Hoffmann (CTO), Anna Richter (Data Engineer)
**Status:** Approved
**Classification:** Confidential -- TechVision / Muller Maschinenbau AG

---

## 1. Introduction

This Technical Design Document (TDD) defines the architecture, data flows, integration patterns, security model, and deployment strategy for Projekt Aurora. It serves as the authoritative technical reference for all implementation decisions and should be read in conjunction with the Project Charter (doc_019), which outlines the project scope, budget, and timeline.

The design has been developed based on findings from the Discovery and Planning phase (Phase 1), including interviews with Muller Maschinenbau AG's IT Director Stefan Braun, ERP Administrator Jorg Becker, and production floor managers across the three manufacturing facilities in Augsburg, Ingolstadt, and Regensburg.

## 2. System Architecture Overview

The Projekt Aurora platform follows a three-tier architecture designed for scalability, maintainability, and clear separation of concerns:

### Tier 1: Ingestion Layer

The ingestion layer is responsible for extracting data from all source systems and landing it in the data lake in its raw form. This tier operates on a near-real-time basis for IoT data and on scheduled intervals (every 15 minutes to hourly) for ERP and MES data.

**Components:**
- Azure Data Factory (ADF) with self-hosted integration runtime for on-premise connectivity
- Azure IoT Hub for MQTT-based sensor data ingestion
- Azure Event Hubs for high-throughput streaming scenarios
- Custom SAP RFC connector deployed as an Azure Function

### Tier 2: Processing Layer

The processing layer transforms raw data through a series of increasingly refined stages (Bronze, Silver, Gold) using Azure Synapse Analytics. Data quality checks, business logic transformations, and aggregations are applied at each stage.

**Components:**
- Azure Synapse Analytics (Spark pools for heavy transformations, SQL pools for serving)
- Azure Databricks (reserved for advanced analytics workloads if required in future phases)
- Azure Functions for lightweight event-driven transformations
- Great Expectations for data quality validation

### Tier 3: Serving Layer

The serving layer provides data to end users through dashboards, APIs, and direct database access for power users. This tier is optimized for read performance and low-latency queries.

**Components:**
- Power BI Premium for interactive dashboards and scheduled reports
- FastAPI application for custom REST endpoints (deployed on AKS)
- Azure API Management for external API exposure and rate limiting
- Azure Synapse SQL Serverless for ad-hoc queries by data analysts

## 3. Data Flow Architecture

The end-to-end data flow follows the Medallion Architecture pattern:

### 3.1 Source Systems to Bronze (Raw)

**ERP Data (Oracle):**
Oracle ERP 12.1 contains approximately 2.3 TB of data across 847 tables. After analysis in Phase 1, we identified 124 tables as relevant for the analytics platform. Data extraction uses Azure Data Factory with an Oracle connector via the self-hosted integration runtime installed on a dedicated Windows Server VM in Muller Maschinenbau AG's Augsburg data center.

- Full load: Initial migration of all historical data (5-year window as per scope)
- Incremental load: Change Data Capture (CDC) using Oracle LogMiner, polling every 15 minutes
- Format: Parquet files partitioned by extraction date

**SAP Data (Procurement and Warehouse):**
SAP data is extracted using SAP RFC function modules (BAPI calls) wrapped in a custom Azure Function. The function is written in Python using the PyRFC library and handles authentication via SAP's SNC (Secure Network Communications).

- Key BAPIs: BAPI_MATERIAL_GETLIST, BAPI_PO_GETDETAIL, BAPI_WAREHOUSE_GETLIST
- Extraction frequency: Hourly for transactional data, daily for master data
- Format: Parquet files with schema evolution support

**MES Data (REST APIs):**
The three production facilities use different MES systems (Siemens SIMATIC IT at Augsburg, MPDV Hydra at Ingolstadt, a custom solution at Regensburg). Each exposes REST APIs for production orders, machine states, and quality measurements.

- Azure Data Factory REST connector with paginated extraction
- Extraction frequency: Every 15 minutes
- Data normalization occurs in the Silver layer to unify the three different schemas

**IoT Sensor Data (MQTT):**
Approximately 340 sensors across the three facilities publish telemetry data (temperature, pressure, vibration, energy consumption) via MQTT to local brokers. Azure IoT Hub serves as the cloud-side MQTT broker.

- Protocol: MQTT v3.1.1, TLS 1.2 encrypted
- Message throughput: approximately 5,000 messages per minute across all facilities
- Azure IoT Hub routes messages to Event Hubs for stream processing
- Azure Stream Analytics performs windowed aggregations (1-minute, 5-minute, 1-hour)
- Raw telemetry stored in Bronze zone; aggregated data flows to Silver

### 3.2 Bronze to Silver (Cleansed)

The Silver layer applies data cleansing, schema standardization, and basic business logic:

- **Deduplication:** Remove duplicate records from incremental loads using composite keys
- **Type casting:** Standardize data types across all source systems (e.g., dates to ISO 8601, currencies to EUR with 2 decimal places)
- **Null handling:** Apply default values or flag records for manual review based on field criticality
- **Schema unification:** Map MES data from three different schemas into a unified production data model
- **Referential integrity:** Validate foreign key relationships across source systems
- **Data quality scoring:** Each record receives a quality score (0-100) based on completeness, consistency, and timeliness checks

Processing engine: Azure Synapse Spark pools (auto-scaling, 4-16 nodes, Standard_E8s_v3). Transformations are implemented as PySpark notebooks orchestrated by Synapse Pipelines.

### 3.3 Silver to Gold (Business-Ready)

The Gold layer contains aggregated, business-ready datasets optimized for dashboard consumption:

- **Production KPIs:** OEE (Overall Equipment Effectiveness), cycle times, yield rates, downtime analysis
- **Supply Chain Metrics:** Inventory turnover, supplier lead times, purchase order fulfillment rates
- **Financial Summaries:** Revenue by product line, cost center analysis, margin calculations
- **Quality Indicators:** Defect rates, SPC (Statistical Process Control) charts, complaint trends

Gold layer tables are implemented as materialized views in Azure Synapse SQL Dedicated Pool, refreshed every 15 minutes. Power BI connects to Gold layer via DirectQuery for real-time dashboards and Import mode for historical trend reports.

## 4. Integration Points

### 4.1 SAP RFC Connectors

The SAP integration uses a custom-built Azure Function (Python 3.12, PyRFC 3.3) that manages connection pooling and handles SAP's proprietary data types. The function runs on a dedicated App Service Plan (Premium V3 P1v3) to ensure consistent performance.

Authentication: SAP SNC with X.509 certificates. Certificates are stored in Azure Key Vault and rotated every 12 months.

Error handling: Failed RFC calls are retried 3 times with exponential backoff (30s, 60s, 120s). After exhausting retries, the failed extraction is logged to a dead-letter table and an alert is sent to the operations channel.

### 4.2 REST APIs for MES

Each MES system requires a dedicated connector configuration:

- **Siemens SIMATIC IT (Augsburg):** OAuth 2.0 client credentials flow, JSON responses, pagination via offset/limit
- **MPDV Hydra (Ingolstadt):** API key authentication, XML responses (transformed to JSON in ADF), cursor-based pagination
- **Custom MES (Regensburg):** Basic authentication over TLS, JSON responses, no pagination (full dataset per request)

### 4.3 MQTT for IoT Sensors

Sensor data flows through a multi-hop architecture:

1. Sensors publish to local Mosquitto brokers in each facility
2. Azure IoT Edge gateway devices bridge local MQTT to Azure IoT Hub
3. IoT Hub routes messages to Event Hubs (partitioned by facility)
4. Stream Analytics jobs perform real-time aggregation and anomaly detection
5. Processed data lands in both Bronze (raw) and Silver (aggregated) zones

## 5. Security Architecture

### 5.1 Identity and Access Management

- **Azure Active Directory:** Central identity provider for all platform services. Muller Maschinenbau AG's on-premise AD is synchronized via Azure AD Connect (password hash sync mode).
- **Role-Based Access Control (RBAC):** Four roles defined: Platform Admin, Data Engineer, Analyst, Viewer. Mapped to Azure AD security groups.
- **Power BI Row-Level Security (RLS):** Dashboard access restricted by facility and department. Production managers see only their facility's data.
- **Service Principals:** All automated processes (ADF pipelines, Functions, AKS workloads) authenticate using managed identities or service principals with least-privilege permissions.

### 5.2 Network Security

- **Azure ExpressRoute:** Private 100 Mbps connection between Augsburg data center and Azure West Europe region. No data traverses the public internet for on-premise connectivity.
- **Virtual Network:** Hub-and-spoke topology with Network Security Groups (NSGs) enforcing micro-segmentation.
- **Private Endpoints:** All Azure PaaS services (Storage, SQL, Synapse, Key Vault) accessible only via private endpoints within the VNet.
- **Azure Firewall:** Centralized outbound traffic inspection and DNS filtering.
- **Web Application Firewall (WAF):** Azure Front Door with WAF v2 for the FastAPI custom endpoints.

### 5.3 Data Protection

- **Encryption at Rest:** Azure Storage Service Encryption (SSE) with Microsoft-managed keys for Bronze/Silver zones. Customer-managed keys (CMK) via Azure Key Vault for Gold zone and SQL databases.
- **Encryption in Transit:** TLS 1.2 enforced for all communications. MQTT connections use TLS with X.509 device certificates.
- **Data Classification:** All datasets tagged with sensitivity labels (Public, Internal, Confidential, Restricted) using Azure Purview.
- **Key Management:** Azure Key Vault (Premium tier, HSM-backed) for all secrets, certificates, and encryption keys. Access policies follow least-privilege principle.

The security architecture has been reviewed by Tobias Fischer (TechVision Security Lead) and aligns with the security framework applied in the FinSecure Bank AG engagement (see Compliance Matrix, doc_022), adapted for manufacturing industry requirements.

## 6. Database Design

### 6.1 Bronze Zone (Raw)

Storage: Azure Data Lake Storage Gen2, hierarchical namespace enabled.

```
/bronze/
  /oracle-erp/
    /{table_name}/
      /year=YYYY/month=MM/day=DD/
        {table_name}_{timestamp}.parquet
  /sap/
    /{bapi_name}/
      /year=YYYY/month=MM/day=DD/
        {bapi_name}_{timestamp}.parquet
  /mes/
    /{facility}/
      /{entity}/
        /year=YYYY/month=MM/day=DD/
          {entity}_{timestamp}.parquet
  /iot/
    /{facility}/
      /year=YYYY/month=MM/day=DD/hour=HH/
        telemetry_{timestamp}.parquet
```

Retention: 90 days in Hot tier, then moved to Cool tier for 2 years, then Archive tier.

### 6.2 Silver Zone (Cleansed)

Storage: Azure Data Lake Storage Gen2 with Delta Lake format for ACID transactions and time travel.

Key tables:
- `production_orders` -- Unified production order data from all three MES systems
- `materials` -- Master material data merged from Oracle ERP and SAP
- `machine_telemetry` -- Aggregated sensor data (1-minute granularity)
- `purchase_orders` -- Procurement data from SAP
- `inventory_movements` -- Warehouse transactions from SAP
- `quality_measurements` -- Quality inspection results from MES

### 6.3 Gold Zone (Business-Ready)

Storage: Azure Synapse SQL Dedicated Pool (DW1000c).

Key datasets:
- `fact_production` -- Production order facts with dimensional keys
- `fact_inventory` -- Daily inventory snapshots
- `fact_quality` -- Quality metrics per production order
- `dim_material`, `dim_machine`, `dim_facility`, `dim_time` -- Dimension tables
- `agg_oee_hourly`, `agg_oee_daily` -- Pre-aggregated OEE calculations
- `agg_supply_chain_daily` -- Supply chain KPIs

## 7. API Layer

### 7.1 Custom API (FastAPI)

A FastAPI application provides custom endpoints for use cases not covered by Power BI:

- `GET /api/v1/production/oee/{facility_id}` -- Real-time OEE for a specific facility
- `GET /api/v1/inventory/alerts` -- Active inventory alerts (below minimum stock levels)
- `POST /api/v1/quality/reports` -- Generate quality reports for a date range
- `GET /api/v1/machines/{machine_id}/health` -- Machine health score based on sensor data

The API is implemented in Python 3.12 with FastAPI, SQLAlchemy 2.0 for database access, and Pydantic v2 for request/response validation. It runs on AKS (see Section 9) with 2-4 replicas behind an internal load balancer.

### 7.2 Azure API Management

External-facing APIs (for Muller Maschinenbau AG's partners and suppliers) are exposed through Azure API Management (APIM):

- Rate limiting: 1,000 requests per hour per subscription key
- Authentication: OAuth 2.0 with Azure AD B2C for external users
- Caching: 5-minute cache for read-heavy endpoints
- API versioning: URL path-based (e.g., /v1/, /v2/)

## 8. Monitoring and Observability

### 8.1 Azure Monitor

- **Infrastructure metrics:** CPU, memory, disk, network for all Azure resources
- **Application Insights:** Distributed tracing for FastAPI application and Azure Functions
- **Log Analytics Workspace:** Centralized log aggregation with 90-day retention
- **Alert rules:** 47 alert rules covering resource health, pipeline failures, data freshness SLA breaches, and security events

### 8.2 Grafana Dashboards

A Grafana instance (deployed on AKS) provides custom operational dashboards beyond what Azure Monitor offers natively:

- **Pipeline Health:** Real-time view of all ADF pipeline runs, success rates, and durations
- **Data Freshness:** Time since last successful load per source system (with SLA indicators)
- **Platform Costs:** Daily Azure consumption breakdown by resource group and service
- **Capacity Planning:** Storage growth trends, compute utilization, and scaling predictions

Grafana connects to Azure Monitor via the Azure Monitor data source plugin and to the Synapse SQL pool for custom queries.

## 9. Deployment Strategy

### 9.1 Azure Kubernetes Service (AKS)

The FastAPI application and Grafana are deployed on AKS:

- **Cluster:** Single cluster, 3 node pools (system, application, monitoring)
- **Node size:** Standard_D4s_v5 (4 vCPU, 16 GB RAM)
- **Autoscaling:** Cluster autoscaler (min 3, max 8 nodes) and Horizontal Pod Autoscaler
- **Namespaces:** `aurora-api`, `aurora-monitoring`, `aurora-system`

### 9.2 Helm Charts

All Kubernetes workloads are packaged as Helm charts stored in Azure Container Registry (ACR):

- `aurora-api` -- FastAPI application (values per environment)
- `aurora-grafana` -- Grafana with pre-configured dashboards and data sources
- `aurora-common` -- Shared resources (ConfigMaps, Secrets, NetworkPolicies)

### 9.3 GitOps with Flux

Flux v2 manages the deployment lifecycle:

- **Source:** Git repository (`techvision/aurora-infra`) with environment-specific overlays
- **Kustomizations:** `base/`, `overlays/dev/`, `overlays/staging/`, `overlays/prod/`
- **Reconciliation interval:** 5 minutes
- **Image automation:** Flux Image Reflector and Image Automation controllers update image tags in Git when new container images are pushed to ACR

CI pipeline (Azure DevOps):
1. Developer pushes code to feature branch
2. Pull request triggers build, lint, unit tests, and container image build
3. Merged to `main` triggers image push to ACR with semantic version tag
4. Flux detects new image and updates the Git repository
5. Flux reconciles the Kubernetes cluster with the updated manifests

### 9.4 Infrastructure as Code

All Azure infrastructure is defined in Terraform (v1.6+):

- **State backend:** Azure Storage Account with state locking via blob lease
- **Modules:** Networking, AKS, Synapse, Data Factory, Key Vault, Monitoring
- **Environments:** `dev`, `staging`, `prod` using Terraform workspaces
- **CI/CD:** Terraform plan on PR, apply on merge to `main` (with manual approval for `prod`)

## 10. Disaster Recovery Strategy

### 10.1 Recovery Objectives

- **Recovery Point Objective (RPO):** Less than 1 hour. No more than 1 hour of data loss in a disaster scenario.
- **Recovery Time Objective (RTO):** Less than 4 hours. Full platform operational within 4 hours of a declared disaster.

### 10.2 Strategy

- **Data Lake:** Geo-redundant storage (GRS) with continuous replication to Azure North Europe. Recovery via storage account failover.
- **Synapse SQL Pool:** Geo-backup enabled with automatic restore points every 8 hours. User-defined restore points before major deployments.
- **AKS:** Cluster configuration stored in Git (GitOps). New cluster can be provisioned from Terraform in approximately 30 minutes. Application state is stateless; all persistent data resides in managed services.
- **Azure SQL Managed Instance:** Auto-failover group with asynchronous replication to North Europe. Automatic failover with 1-hour grace period.
- **Secrets and Configuration:** Azure Key Vault with soft delete and purge protection enabled. Regular backup of Key Vault contents to a secondary vault.

### 10.3 DR Testing

- **Tabletop exercise:** Quarterly, involving TechVision and Muller Maschinenbau AG teams
- **Automated failover test:** Bi-annually for Azure SQL auto-failover group
- **Full DR drill:** Annually, simulating complete primary region failure

## 11. Non-Functional Requirements

| Requirement | Target | Measurement Method |
|---|---|---|
| Dashboard load time | < 2 seconds | Power BI Performance Analyzer |
| API response time (P95) | < 500 ms | Application Insights |
| Data freshness (ERP) | < 30 minutes | Custom Grafana dashboard |
| Data freshness (IoT) | < 5 minutes | Stream Analytics diagnostics |
| System availability | 99.9% | Azure Monitor composite SLA |
| Concurrent dashboard users | 50+ | Power BI Premium capacity metrics |
| Data lake storage growth | ~50 GB/month | Azure Cost Management |

## 12. Open Items and Decisions Pending

| ID | Item | Owner | Target Date | Status |
|---|---|---|---|---|
| OI-001 | SAP license transfer approval from SAP AG | Stefan Braun | Oct 10, 2025 | In Progress |
| OI-002 | ExpressRoute circuit provisioning confirmation | Markus Lehmann | Oct 3, 2025 | Ordered |
| OI-003 | IoT Edge device specifications for Regensburg facility | Felix Braun | Sep 30, 2025 | Open |
| OI-004 | Power BI Premium capacity sizing (P1 vs P2) | Anna Richter | Oct 15, 2025 | Analysis |

---

*This document is maintained in TechVision's Notion workspace and versioned alongside the Project Charter (doc_019). For technical questions, contact Felix Braun (f.braun@techvision.de).*
