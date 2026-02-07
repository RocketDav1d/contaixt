---
doc_id: doc_017
title: "Data Platform Architecture – Projekt Aurora"
author: Anna Richter
source_type: notion
---

# Data Platform Architecture -- Projekt Aurora

**Author:** Anna Richter (Data Engineer)
**Contributors:** Sandra Hoffmann (CTO), Markus Lang (DevOps Lead)
**Last Updated:** October 2025
**Client:** Muller Maschinenbau GmbH
**Status:** In Production (Phase 2)

## Executive Overview

This document describes the data platform architecture for Projekt Aurora, TechVision's cloud migration and data modernization project for Muller Maschinenbau GmbH. Muller Maschinenbau is a mid-size manufacturing company based in Stuttgart with approximately 1,200 employees, operating three production facilities across Germany.

The data platform consolidates manufacturing data from multiple source systems into a unified Azure-based data lake, enabling advanced analytics, predictive maintenance, and real-time operational dashboards. The platform processes approximately 2 TB of raw data daily from ERP, MES, and IoT sources, serving 150+ internal users across production management, quality assurance, and executive leadership.

The platform follows the Medallion Architecture pattern (Bronze/Silver/Gold) and is deployed on Azure using the infrastructure patterns defined in our Azure Cloud Architecture Reference Guide (doc_011).

---

## Architecture Overview

### Medallion Architecture

The data platform uses a three-layer medallion architecture, providing progressive data refinement from raw ingestion to business-ready datasets:

```
                      +-----------------------+
  Source Systems      |     Bronze Layer       |     Raw, unprocessed
  ───────────────►    |  (Landing Zone)        |     Append-only
  SAP ERP             +-----------+-----------+     JSON/CSV/Parquet
  MES (Siemens)                   |
  IoT Sensors                     ▼
  Oracle DB           +-----------------------+
                      |     Silver Layer       |     Cleaned, validated
                      |  (Conformed Zone)      |     Deduplicated
                      +-----------+-----------+     Delta Lake format
                                  |
                                  ▼
                      +-----------------------+
                      |      Gold Layer        |     Business aggregates
                      |  (Curated Zone)        |     KPIs, dimensional
                      +-----------------------+     models, report-ready
                                  |
                                  ▼
                      +-----------------------+
                      |   Consumption Layer    |
                      |  Dashboards, APIs,     |
                      |  ML Models             |
                      +-----------------------+
```

### Azure Services Map

| Component | Azure Service | Purpose |
|---|---|---|
| Data Lake Storage | Azure Data Lake Storage Gen2 | Bronze, Silver, Gold layers |
| Orchestration | Azure Data Factory | Pipeline scheduling and monitoring |
| Stream Processing | Azure Event Hubs + Stream Analytics | Real-time IoT sensor data |
| Batch Processing | Azure Databricks | Silver and Gold transformations |
| Data Warehouse | Azure Synapse Analytics (Serverless SQL) | SQL access to Gold layer |
| Data Catalog | Azure Purview | Data discovery and governance |
| Monitoring | Prometheus + Grafana (via AKS) | Pipeline health metrics |
| Secret Management | Azure Key Vault | Connection strings, API keys |
| CDC | Self-hosted Debezium on AKS | Oracle DB change capture |

---

## Bronze Layer (Landing Zone)

### Purpose

The Bronze layer stores raw, unprocessed data exactly as received from source systems. Data is append-only and immutable, serving as the system of record for all downstream processing. If any Silver or Gold transformation is incorrect, we can always reprocess from Bronze.

### Source Systems and Ingestion

#### SAP ERP (S/4HANA)

- **Data:** Production orders, material master, bill of materials, inventory movements, quality inspection results.
- **Ingestion method:** Azure Data Factory with SAP CDC connector (ODP-based extraction).
- **Frequency:** Incremental extraction every 15 minutes during business hours (06:00-22:00 CET), full extraction nightly.
- **Format:** Parquet files partitioned by `extraction_date` and `source_table`.
- **Volume:** ~200 GB/day.

**Pipeline configuration:**
```
ADF Pipeline: pl_bronze_sap_incremental
  Trigger: Schedule (every 15 min, 06:00-22:00)
  Source: SAP ODP (linked service: ls_sap_prod)
  Sink: ADLS Gen2 (bronze/sap/{table_name}/year={yyyy}/month={mm}/day={dd}/)
  Watermark: Last extraction timestamp stored in Azure SQL metadata table
```

#### MES (Siemens SIMATIC IT)

- **Data:** Machine cycle times, production counts, downtime events, alarm logs.
- **Ingestion method:** REST API polling via Azure Data Factory.
- **Frequency:** Every 5 minutes for production data, hourly for alarm logs.
- **Format:** JSON files, one per API response.
- **Volume:** ~50 GB/day.

#### IoT Sensors

- **Data:** Temperature, pressure, vibration, power consumption from 2,400 sensors across three facilities.
- **Ingestion method:** Azure Event Hubs (sensors push via MQTT gateway to Event Hub).
- **Frequency:** Real-time (sensor readings every 5 seconds per sensor).
- **Processing:** Azure Stream Analytics job performs initial deduplication and time-window aggregation (1-minute averages) before writing to Bronze.
- **Format:** Parquet (aggregated), raw JSON retained for 7 days in Event Hub capture.
- **Volume:** ~1.5 TB/day raw, ~100 GB/day after aggregation.

#### Oracle Database (Legacy ERP)

- **Data:** Historical production records (2010-2022), customer master data, legacy quality records.
- **Ingestion method:** Change Data Capture via Debezium, running on AKS (see doc_016 for Kubernetes operations).
- **Frequency:** Continuous CDC for ongoing changes, initial full load completed in Phase 1.
- **Format:** Avro (Debezium native format), converted to Parquet during Silver processing.
- **Volume:** ~10 GB/day (mostly historical, diminishing as migration progresses).

**Debezium deployment:**
```yaml
# Helm chart: helm/debezium-oracle/values-prod.yaml
replicaCount: 1
connector:
  name: oracle-cdc-muller
  config:
    connector.class: io.debezium.connector.oracle.OracleConnector
    database.hostname: oracle-prod.muller-internal.de
    database.port: 1521
    database.dbname: MMPROD
    schema.include.list: PRODUCTION,QUALITY,MASTER_DATA
    topic.prefix: aurora.oracle
    snapshot.mode: schema_only  # Initial full load already completed
```

### Bronze Layer Storage Structure

```
bronze/
  sap/
    production_order/
      year=2025/month=10/day=15/
        extraction_20251015_080000.parquet
        extraction_20251015_081500.parquet
    material_master/
      ...
  mes/
    cycle_times/
      year=2025/month=10/day=15/
        poll_20251015_080000.json
        poll_20251015_080500.json
    downtime_events/
      ...
  iot/
    sensor_readings/
      year=2025/month=10/day=15/hour=08/
        aggregated_20251015_0800.parquet
  oracle/
    production/
      year=2025/month=10/day=15/
        cdc_batch_20251015_080000.avro
```

### Retention Policy

- Bronze data retained for **2 years** in Hot storage.
- After 2 years, moved to Cool storage for an additional 3 years.
- After 5 years total, moved to Archive storage (10-year regulatory retention for manufacturing quality data).
- Lifecycle policies managed via Terraform (see doc_011 for cost management practices).

---

## Silver Layer (Conformed Zone)

### Purpose

The Silver layer contains cleaned, validated, and conformed data. This is where data quality rules are enforced, schemas are standardized, deduplication occurs, and data from different sources is aligned on common keys and dimensions.

### Processing Framework

Silver layer transformations run on Azure Databricks using PySpark:

- **Cluster:** Shared autoscaling cluster (2-16 workers, Standard_D8s_v5).
- **Runtime:** Databricks Runtime 14.x with Delta Lake.
- **Scheduling:** Azure Data Factory triggers Databricks notebooks via linked service.
- **Processing cadence:** Every 30 minutes for production data, hourly for non-critical datasets.

### Transformation Patterns

**1. Schema Enforcement and Evolution:**
```python
# Silver transformation: SAP production orders
from pyspark.sql import functions as F
from delta.tables import DeltaTable

# Read from Bronze (raw Parquet)
bronze_df = spark.read.parquet("abfss://bronze@tvprdweustaurora.dfs.core.windows.net/sap/production_order/year=2025/month=10/day=15/")

# Apply schema (enforce column types, rename German column names)
silver_df = bronze_df.select(
    F.col("AUFNR").alias("production_order_id"),
    F.col("MATNR").alias("material_number"),
    F.col("WERKS").alias("plant_code"),
    F.col("GAMNG").cast("decimal(15,3)").alias("planned_quantity"),
    F.col("IGMNG").cast("decimal(15,3)").alias("confirmed_quantity"),
    F.to_timestamp("ERDAT", "yyyyMMdd").alias("created_date"),
    F.to_timestamp("AEDAT", "yyyyMMdd").alias("last_modified_date"),
    F.lit("sap").alias("source_system"),
    F.current_timestamp().alias("processed_at")
)

# Merge into Silver Delta table (upsert on production_order_id)
silver_table = DeltaTable.forPath(spark, "abfss://silver@tvprdweustaurora.dfs.core.windows.net/production/production_order")
silver_table.alias("target").merge(
    silver_df.alias("source"),
    "target.production_order_id = source.production_order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

**2. Deduplication:**
- SAP extractions may contain duplicate records across incremental pulls. Deduplication uses `production_order_id` + `last_modified_date` as the composite key, keeping the latest version.
- IoT sensor readings are deduplicated by `sensor_id` + `timestamp` (5-second window).

**3. Cross-Source Joining:**
- Silver layer creates unified views by joining SAP production orders with MES cycle time data on `production_order_id` and `plant_code`.
- Oracle historical data is joined by `material_number` after a mapping table reconciliation (maintained in Azure SQL metadata database).

### Data Quality Framework (Great Expectations)

Every Silver layer dataset is validated using Great Expectations suites:

```python
# Example expectation suite for production_order Silver table
expectation_suite = {
    "expectations": [
        {"expectation_type": "expect_column_values_to_not_be_null", "kwargs": {"column": "production_order_id"}},
        {"expectation_type": "expect_column_values_to_not_be_null", "kwargs": {"column": "material_number"}},
        {"expectation_type": "expect_column_values_to_be_between", "kwargs": {"column": "planned_quantity", "min_value": 0, "max_value": 1000000}},
        {"expectation_type": "expect_column_values_to_be_in_set", "kwargs": {"column": "plant_code", "value_set": ["1000", "2000", "3000"]}},
        {"expectation_type": "expect_column_pair_values_a_to_be_greater_than_b", "kwargs": {"column_A": "planned_quantity", "column_B": "confirmed_quantity", "or_equal": true}},
    ]
}
```

Quality check results are logged to Azure SQL and surfaced in a Grafana dashboard (see doc_014). Failed quality checks trigger P2 alerts for data freshness issues.

### Silver Layer Storage

- **Format:** Delta Lake (Parquet + transaction log).
- **Partitioning:** By `plant_code` and `year_month` for production data. By `sensor_group` and `date` for IoT data.
- **Optimization:** `OPTIMIZE` (compaction) runs nightly. `VACUUM` retains 7 days of history for time travel.

---

## Gold Layer (Curated Zone)

### Purpose

The Gold layer provides business-ready, aggregated datasets optimized for specific consumption patterns: dashboards, reports, API queries, and machine learning features. Gold tables follow dimensional modeling principles (star schema) for analytical workloads.

### Key Gold Datasets

**1. Production KPI Table (`gold.production_kpi_daily`):**
- Aggregated daily production metrics per plant and production line.
- Metrics: units produced, scrap rate, OEE (Overall Equipment Effectiveness), cycle time averages.
- Source: Silver production orders + Silver MES cycle times.
- Refresh: Every 30 minutes.

**2. Equipment Health Table (`gold.equipment_health`):**
- Machine-level health scores derived from IoT sensor readings.
- Includes vibration anomaly scores, temperature deviation trends, and predicted maintenance windows.
- Source: Silver IoT sensor readings + Silver MES downtime events.
- Refresh: Hourly.

**3. Quality Analytics Table (`gold.quality_inspection_summary`):**
- Quality inspection pass/fail rates by material, supplier, and production line.
- Includes trend analysis (7-day and 30-day rolling averages).
- Source: Silver SAP quality inspection results + Silver MES alarm logs.
- Refresh: Every 2 hours.

**4. Executive Dashboard Table (`gold.executive_summary`):**
- High-level KPIs for the executive team: total production output, cost per unit, delivery performance, top quality issues.
- Source: Aggregated from other Gold tables.
- Refresh: Daily at 06:00 CET.

### Consumption Interfaces

- **Dashboards:** Power BI connects to Gold layer via Azure Synapse Serverless SQL. MedTech Analytics team has built custom React dashboards accessing Gold data via a FastAPI service (see doc_012 for API design patterns).
- **APIs:** Projekt Aurora exposes production KPIs via a REST API for Muller Maschinenbau's internal portal. Rate-limited to 100 req/min per the API Design Guidelines.
- **ML Models:** Equipment health prediction model (scikit-learn) reads features from `gold.equipment_health`. Model retraining pipeline runs weekly on Databricks.

---

## Data Catalog (Azure Purview)

Azure Purview provides automated data discovery and governance:

- **Automated scanning:** Scans ADLS Gen2 (all three layers), Azure SQL, and Azure Synapse on a daily schedule.
- **Classification:** Automatic PII detection (names, emails, addresses). Manufacturing-specific classifications (material numbers, production order IDs) configured as custom classifiers.
- **Lineage:** End-to-end data lineage from source system to Gold layer, tracked via Data Factory activity metadata.
- **Glossary:** Business terms defined collaboratively with Muller Maschinenbau's domain experts. Links to technical metadata in Purview.

---

## Access Control

### Row-Level Security

Gold layer datasets implement row-level security based on the user's organizational unit:

- Plant managers see data only for their plant (`plant_code` filter).
- Quality managers see cross-plant quality data but not financial metrics.
- Executive users see all data.

Security is enforced at the Azure Synapse layer via security predicates and at the API layer via workspace-based filtering.

### Workspace Isolation

Each Muller Maschinenbau department accesses data through a dedicated workspace:

| Workspace | Access | Gold Tables |
|---|---|---|
| `production-ops` | Plant managers, shift leads | `production_kpi_daily`, `equipment_health` |
| `quality-assurance` | QA managers, inspectors | `quality_inspection_summary`, `production_kpi_daily` |
| `executive` | C-suite, controlling | All Gold tables |
| `data-science` | Data team | All Silver and Gold tables |

Workspace configuration is managed via Terraform and follows the multi-tenancy patterns used across TechVision projects (see doc_011).

---

## Data Quality Monitoring

### Metrics Tracked

| Metric | Target | Alert Threshold |
|---|---|---|
| Data freshness (Bronze) | < 30 min | > 1 hour (P1) |
| Data freshness (Silver) | < 1 hour | > 2 hours (P2) |
| Quality check pass rate | > 99% | < 95% (P2) |
| Pipeline success rate | > 99.5% | < 98% (P2) |
| Duplicate record rate | < 0.01% | > 0.1% (P3) |

Monitoring integrates with the Prometheus + Grafana stack described in doc_014. Custom metrics are exported from Data Factory pipeline runs and Databricks job status via a lightweight Python service running on AKS.

### Data Quality Incidents

When a data quality issue is detected:
1. Automated alert sent to `#data-quality` Slack channel.
2. Anna Richter (or the on-call data engineer) investigates the root cause.
3. If the issue is in the source system, a ticket is created for Muller Maschinenbau's IT team via the shared Jira project.
4. If the issue is in the transformation logic, a bugfix follows the standard PR process (doc_010).
5. Affected Gold tables are marked as "stale" in the data catalog until the issue is resolved.

---

## Disaster Recovery

- **RPO:** 1 hour (Bronze data can be re-extracted from source systems; Silver and Gold can be reprocessed from Bronze).
- **RTO:** 4 hours for full platform recovery.
- **Backup:** ADLS Gen2 with geo-redundant storage (GRS). Delta Lake time travel provides point-in-time recovery within the 7-day retention window.
- **DR procedure:** Documented in the Azure Architecture Guide (doc_011). Tested quarterly as part of the overall DR drill.

---

## Phase 2 Roadmap (Current)

Phase 2 focuses on:
1. **Predictive maintenance:** ML models for equipment failure prediction using IoT sensor features from the Gold layer.
2. **Real-time dashboards:** Streaming Silver layer processing for sub-minute data freshness on critical production KPIs.
3. **Apache Iceberg evaluation:** Trialing Iceberg as an alternative table format for the Silver layer (see Technology Radar, doc_009).
4. **Self-service analytics:** Enabling Muller Maschinenbau's analysts to query Silver and Gold data directly via Azure Synapse notebooks.

For questions about the data platform architecture, contact Anna Richter or the data engineering team in `#data-aurora` on Slack.
