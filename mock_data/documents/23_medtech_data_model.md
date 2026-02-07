---
doc_id: doc_023
title: "MedTech Analytics – Data Model & FHIR Integration"
author: Anna Richter
source_type: notion
---

# MedTech Analytics -- Data Model & FHIR Integration

**Version:** 1.0
**Date:** September 28, 2025
**Author:** Anna Richter, Data Engineer
**Reviewed by:** Felix Braun (Senior Developer), Robert Engel (MedTech Solutions GmbH)
**Status:** Draft
**Classification:** Confidential -- TechVision / MedTech Solutions GmbH

---

## 1. Introduction

This document describes the data model and HL7 FHIR R4 integration strategy for the MedTech Analytics platform. The platform is being developed for MedTech Solutions GmbH to provide hospital operational analytics dashboards and a companion mobile application, as outlined in the Statement of Work (doc_024).

MedTech Solutions GmbH serves as a technology partner to 14 hospitals across Bavaria and Baden-Wurttemberg. Their existing product suite includes a hospital information system (HIS) that stores clinical and operational data in HL7 FHIR R4 format. The analytics platform will ingest data from these FHIR servers, transform it into an analytics-optimized schema, and serve aggregated insights to hospital administrators, department heads, and clinical staff.

Robert Engel, CEO of MedTech Solutions GmbH, has emphasized that the solution must integrate seamlessly with existing FHIR infrastructure and comply with German healthcare data protection requirements (BDSG, Landesdatenschutzgesetze, and the Patientendatenschutzgesetz).

## 2. HL7 FHIR R4 Resource Mapping

The analytics platform consumes the following FHIR R4 resources from MedTech Solutions' FHIR servers. Each resource is mapped to internal analytics tables optimized for query performance.

### 2.1 Patient Resource

The FHIR Patient resource contains demographic information required for cohort analysis and population health metrics.

**FHIR Fields Consumed:**
- `Patient.id` -- Unique identifier (mapped to pseudonymized patient ID)
- `Patient.birthDate` -- Used to derive age groups for demographic analysis
- `Patient.gender` -- Administrative gender for statistical breakdowns
- `Patient.address.postalCode` -- First 3 digits only, for regional analysis (k-anonymity requirement)
- `Patient.maritalStatus` -- Optional, used in specific epidemiological reports
- `Patient.generalPractitioner` -- Reference to referring physician for referral pattern analysis

**Analytics Table:** `dim_patient`

| Column | Type | Source | Notes |
|---|---|---|---|
| patient_key | BIGINT (PK) | Generated | Surrogate key |
| pseudo_id | VARCHAR(64) | Derived | HMAC-SHA256 of Patient.id |
| age_group | VARCHAR(10) | Patient.birthDate | 5-year bands (0-4, 5-9, ..., 85+) |
| gender | VARCHAR(20) | Patient.gender | male, female, other, unknown |
| region_code | VARCHAR(3) | Patient.address.postalCode | First 3 digits only |
| first_seen_date | DATE | Earliest Encounter | Date of first encounter |
| last_seen_date | DATE | Latest Encounter | Date of most recent encounter |

### 2.2 Encounter Resource

The FHIR Encounter resource tracks patient visits and admissions, forming the core of operational analytics.

**FHIR Fields Consumed:**
- `Encounter.id` -- Unique identifier
- `Encounter.status` -- Current status (planned, arrived, in-progress, finished, cancelled)
- `Encounter.class` -- Type of encounter (ambulatory, emergency, inpatient, virtual)
- `Encounter.type` -- Specific encounter type (coded with ICD-10 procedure codes)
- `Encounter.subject` -- Reference to Patient
- `Encounter.period.start` / `Encounter.period.end` -- Admission and discharge timestamps
- `Encounter.serviceProvider` -- Reference to managing Organization (department)
- `Encounter.diagnosis` -- List of diagnosis references with roles (admission, discharge, billing)
- `Encounter.length` -- Duration of encounter

**Analytics Table:** `fact_encounter`

| Column | Type | Source | Notes |
|---|---|---|---|
| encounter_key | BIGINT (PK) | Generated | Surrogate key |
| encounter_id | VARCHAR(64) | Encounter.id | Original FHIR ID (non-identifying) |
| patient_key | BIGINT (FK) | Encounter.subject | Reference to dim_patient |
| department_key | BIGINT (FK) | Encounter.serviceProvider | Reference to dim_department |
| encounter_class | VARCHAR(20) | Encounter.class | ambulatory, emergency, inpatient, virtual |
| status | VARCHAR(20) | Encounter.status | Current encounter status |
| admission_ts | TIMESTAMP | Encounter.period.start | Admission timestamp |
| discharge_ts | TIMESTAMP | Encounter.period.end | Discharge timestamp (nullable) |
| length_minutes | INTEGER | Calculated | Duration in minutes |
| primary_diagnosis_icd | VARCHAR(10) | Encounter.diagnosis | ICD-10-GM code (primary) |
| drg_code | VARCHAR(10) | Derived | DRG classification for inpatient |

### 2.3 Observation Resource

The FHIR Observation resource contains clinical measurements and laboratory results used for quality indicators and clinical dashboards.

**FHIR Fields Consumed:**
- `Observation.id` -- Unique identifier
- `Observation.status` -- Observation status (registered, preliminary, final, amended)
- `Observation.category` -- Classification (vital-signs, laboratory, procedure, exam)
- `Observation.code` -- LOINC code identifying the observation type
- `Observation.subject` -- Reference to Patient
- `Observation.encounter` -- Reference to Encounter
- `Observation.effectiveDateTime` -- When the observation was made
- `Observation.valueQuantity` -- Numerical result with unit
- `Observation.interpretation` -- High, low, normal, critical flags
- `Observation.referenceRange` -- Normal range for the observation

**Analytics Table:** `fact_observation`

| Column | Type | Source | Notes |
|---|---|---|---|
| observation_key | BIGINT (PK) | Generated | Surrogate key |
| patient_key | BIGINT (FK) | Observation.subject | Reference to dim_patient |
| encounter_key | BIGINT (FK) | Observation.encounter | Reference to fact_encounter |
| loinc_code | VARCHAR(10) | Observation.code | LOINC code |
| observation_category | VARCHAR(30) | Observation.category | vital-signs, laboratory, etc. |
| effective_ts | TIMESTAMP | Observation.effectiveDateTime | Observation timestamp |
| value_numeric | NUMERIC(18,6) | Observation.valueQuantity.value | Numerical value |
| value_unit | VARCHAR(20) | Observation.valueQuantity.unit | Unit of measure |
| interpretation | VARCHAR(20) | Observation.interpretation | H, L, N, HH, LL, etc. |
| status | VARCHAR(20) | Observation.status | final, preliminary, etc. |

### 2.4 DiagnosticReport Resource

The FHIR DiagnosticReport resource aggregates observations into clinical reports, used for reporting turnaround time metrics and departmental workload analysis.

**FHIR Fields Consumed:**
- `DiagnosticReport.id` -- Unique identifier
- `DiagnosticReport.status` -- Report status (partial, preliminary, final)
- `DiagnosticReport.category` -- Report category (e.g., LAB, RAD, PAT)
- `DiagnosticReport.code` -- Report type (LOINC coded)
- `DiagnosticReport.subject` -- Reference to Patient
- `DiagnosticReport.encounter` -- Reference to Encounter
- `DiagnosticReport.issued` -- Timestamp when report was issued
- `DiagnosticReport.result` -- References to Observation resources included in report

**Analytics Table:** `fact_diagnostic_report`

| Column | Type | Source | Notes |
|---|---|---|---|
| report_key | BIGINT (PK) | Generated | Surrogate key |
| patient_key | BIGINT (FK) | DiagnosticReport.subject | Reference to dim_patient |
| encounter_key | BIGINT (FK) | DiagnosticReport.encounter | Reference to fact_encounter |
| report_category | VARCHAR(10) | DiagnosticReport.category | LAB, RAD, PAT |
| loinc_code | VARCHAR(10) | DiagnosticReport.code | Report type |
| issued_ts | TIMESTAMP | DiagnosticReport.issued | When report was finalized |
| turnaround_minutes | INTEGER | Calculated | Time from order to report |
| observation_count | INTEGER | DiagnosticReport.result | Number of observations in report |
| status | VARCHAR(20) | DiagnosticReport.status | Report status |

## 3. Data Anonymization Strategy

Healthcare data requires the highest level of protection. The anonymization strategy implements multiple layers of protection to ensure patient privacy while maintaining analytical utility.

### 3.1 Pseudonymization

All patient identifiers are pseudonymized before entering the analytics database:

- **Patient ID:** FHIR Patient.id is replaced with a pseudonym generated using HMAC-SHA256 with a secret key stored in Azure Key Vault. The key is accessible only to the ETL service account and is rotated annually. The original Patient.id is never stored in the analytics database.
- **Names and Contact Information:** Not ingested. The FHIR query profiles explicitly exclude `Patient.name`, `Patient.telecom`, and detailed `Patient.address` fields.
- **Dates:** Birth dates are generalized to age groups (5-year bands). Encounter and observation dates retain full precision, as they are essential for time-series analysis and are not directly identifying without additional context.

### 3.2 K-Anonymity

The platform enforces k-anonymity (k=5) for all queryable dimensions. This means any combination of quasi-identifiers (age group, gender, region code, department) must apply to at least 5 distinct patients in any query result.

**Implementation:**
- Queries returning fewer than 5 patients for any group are automatically suppressed, displaying "< 5" instead of exact counts.
- The suppression logic is implemented at the API layer (FastAPI middleware) and cannot be bypassed by direct database access, as the analytics database itself only contains pseudonymized and generalized data.
- Regional analysis uses only the first 3 digits of postal codes, ensuring a minimum population of approximately 10,000 per region in Bavaria.

### 3.3 Access Logging

All data access is logged with the requesting user, timestamp, query parameters, and result set size. Anomalous access patterns (e.g., queries targeting very small populations, unusually frequent queries from a single user) trigger alerts to the MedTech Solutions compliance team.

## 4. Database Schema

The analytics database uses PostgreSQL 16 with the following design principles:

### 4.1 Schema Organization

```
analytics_db/
  public/          -- Dimension tables and fact tables (star schema)
  staging/         -- Temporary tables for ETL processing
  fhir_raw/        -- JSONB storage for raw FHIR resources (for audit and reprocessing)
  reporting/       -- Materialized views for dashboard queries
  system/          -- ETL metadata, job logs, data quality results
```

### 4.2 JSONB Storage for FHIR Resources

Raw FHIR resources are stored in their original JSON format using PostgreSQL's JSONB type. This provides flexibility for future analytics requirements without requiring ETL pipeline changes.

```sql
CREATE TABLE fhir_raw.resources (
    id              BIGSERIAL PRIMARY KEY,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     VARCHAR(64) NOT NULL,
    hospital_id     VARCHAR(20) NOT NULL,
    version_id      INTEGER NOT NULL DEFAULT 1,
    resource_data   JSONB NOT NULL,
    ingested_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (resource_type, resource_id, hospital_id, version_id)
);

CREATE INDEX idx_resources_type_hospital
    ON fhir_raw.resources (resource_type, hospital_id);
CREATE INDEX idx_resources_data_gin
    ON fhir_raw.resources USING GIN (resource_data jsonb_path_ops);
```

The JSONB storage serves as the system of record and enables reprocessing of the analytical schema if business rules change. Raw resources are retained for 5 years.

### 4.3 Dimension Tables

Key dimension tables supporting the star schema:

- **dim_patient** -- Pseudonymized patient demographics (see Section 2.1)
- **dim_department** -- Hospital departments with hierarchy (clinic > department > ward)
- **dim_hospital** -- Hospital master data (14 hospitals, anonymized identifiers)
- **dim_date** -- Calendar dimension with German holiday calendar and fiscal periods
- **dim_time** -- Time-of-day dimension (hour, shift, day/night classification)
- **dim_icd10** -- ICD-10-GM code catalog with chapter, block, and category hierarchy
- **dim_loinc** -- LOINC code catalog with class, system, and component attributes

### 4.4 ICD-10 and LOINC Code Integration

**ICD-10-GM (German Modification):**
The ICD-10-GM catalog is imported from the official BfArM (Federal Institute for Drugs and Medical Devices) publication. It is updated annually when BfArM publishes the new catalog (typically in October for the following year).

- Hierarchical structure: Chapter (I-XXII) > Block (e.g., A00-A09) > Category (e.g., A00) > Subcategory (e.g., A00.0)
- Cross-references to DRG grouping rules for reimbursement analysis
- Historical versions retained for trend analysis across catalog years

**LOINC (Logical Observation Identifiers Names and Codes):**
LOINC codes from the Regenstrief Institute provide standardized identifiers for laboratory tests and clinical observations.

- Version: LOINC 2.77 (latest stable release)
- Mapped to local hospital laboratory catalogs via a mapping table maintained by MedTech Solutions' clinical informatics team
- Supports hierarchical grouping by LOINC class (e.g., CHEM for chemistry, HEM for hematology)

## 5. ETL Pipeline

### 5.1 Architecture

The ETL pipeline follows an extract-load-transform (ELT) pattern, leveraging PostgreSQL's processing capabilities:

```
FHIR Server (per hospital)
    |
    v
FHIR Extractor (Azure Function, Python)
    |-- Queries FHIR REST API with _lastUpdated filter
    |-- Handles pagination (_count=100, next links)
    |-- Writes raw FHIR JSON to fhir_raw.resources
    |
    v
Transformer (dbt, scheduled via Airflow)
    |-- Parses JSONB into structured staging tables
    |-- Applies pseudonymization (HMAC-SHA256)
    |-- Validates data quality rules
    |-- Loads dimension and fact tables (SCD Type 2 for dimensions)
    |
    v
Materializer (PostgreSQL scheduled jobs)
    |-- Refreshes materialized views in reporting schema
    |-- Updates aggregate tables for dashboards
    |-- Generates data quality reports
```

### 5.2 Extraction

The FHIR Extractor is implemented as an Azure Function (Python 3.12, consumption plan) triggered on a 15-minute schedule for each hospital:

- Uses FHIR REST API search with `_lastUpdated` parameter for incremental extraction
- Handles pagination using FHIR Bundle `next` links
- Authenticates via OAuth 2.0 client credentials flow (tokens managed by Azure Key Vault)
- Implements retry logic (3 attempts, exponential backoff) for transient network failures
- Writes extraction metadata (record counts, duration, errors) to `system.etl_log`

### 5.3 Transformation

Transformations are implemented using dbt (data build tool) with the following model layers:

- **staging:** One-to-one mapping of FHIR resources to relational tables. JSONB parsing, type casting, null handling.
- **intermediate:** Business logic transformations, joins across resources, calculated fields (e.g., length of stay, turnaround times).
- **marts:** Final analytical tables organized by business domain (clinical, operational, financial).

dbt tests validate referential integrity, accepted values, uniqueness, and custom business rules after each transformation run.

## 6. Data Quality Rules

Data quality is assessed across five dimensions for every ETL run:

### 6.1 Completeness

- Required fields (patient pseudo_id, encounter dates, observation codes) must be present
- Completeness score: percentage of non-null values for expected fields per resource type
- Threshold: Resources with completeness below 80% are flagged for review and excluded from aggregate calculations

### 6.2 Consistency

- Cross-resource consistency: Encounter references in Observations must exist in the Encounter table
- Temporal consistency: Observation timestamps must fall within the encounter period
- Code consistency: ICD-10 and LOINC codes must exist in the reference catalogs
- Numerical consistency: Observation values must fall within physiologically plausible ranges (e.g., body temperature between 30 and 45 degrees Celsius)

### 6.3 Timeliness

- Data freshness: Time between the FHIR resource's `lastUpdated` timestamp and the analytics database ingestion timestamp
- SLA: Data must be available in analytics within 30 minutes of being written to the FHIR server
- Stale data detection: Hospitals that have not sent updates in over 2 hours trigger an alert

### 6.4 Uniqueness

- No duplicate records in fact tables (enforced by composite unique constraints)
- FHIR resource versioning: Only the latest version of each resource is included in analytical tables; all versions are retained in `fhir_raw.resources`

### 6.5 Validity

- Code validation: All ICD-10 codes validated against BfArM catalog, all LOINC codes validated against Regenstrief catalog
- Date validation: No future dates for historical events, no dates before 2015 (system inception)
- Value range validation: Configurable per observation type (e.g., heart rate 20-300 bpm, systolic blood pressure 50-300 mmHg)

## 7. Access Control Model

### 7.1 Role-Based Access Control

The analytics platform implements role-based access control with department-level scoping:

| Role | Description | Data Access | Dashboard Access |
|---|---|---|---|
| Hospital Admin | Hospital-level administrator | All departments within their hospital | All dashboards for their hospital |
| Department Head | Department-level manager | Own department only | Department dashboards + hospital summary |
| Clinical Staff | Doctors and nurses | Own department, aggregated data only | Clinical quality dashboards |
| Analyst | Data analyst at MedTech Solutions | All hospitals, anonymized | All dashboards, data export capability |
| System Admin | TechVision / MedTech technical team | System tables, ETL logs | System monitoring dashboards |

### 7.2 Implementation

- Authentication: Azure AD with SAML 2.0 federation to hospital identity providers
- Authorization: PostgreSQL Row-Level Security (RLS) policies enforce department and hospital scoping at the database level
- API layer: FastAPI dependency injection validates user roles and scopes before executing queries
- Dashboard layer: Power BI Row-Level Security maps Azure AD groups to data filters

## 8. Performance Considerations

### 8.1 Table Partitioning

Fact tables are partitioned by date using PostgreSQL declarative partitioning:

- `fact_encounter`: Monthly partitions by `admission_ts`
- `fact_observation`: Monthly partitions by `effective_ts`
- `fact_diagnostic_report`: Monthly partitions by `issued_ts`

Partition pruning significantly reduces query times for time-bounded analyses, which represent over 90% of dashboard queries.

### 8.2 Materialized Views

Frequently accessed KPIs are pre-computed as materialized views in the `reporting` schema:

- `mv_daily_admissions` -- Daily admission counts by hospital, department, encounter class
- `mv_bed_occupancy` -- Hourly bed occupancy rates by department
- `mv_avg_length_of_stay` -- Monthly average length of stay by department and diagnosis group
- `mv_lab_turnaround` -- Daily laboratory report turnaround times by hospital and test category
- `mv_emergency_wait_times` -- Hourly emergency department wait time statistics

Materialized views are refreshed concurrently (non-blocking) every 15 minutes by a PostgreSQL cron job (pg_cron extension).

### 8.3 Indexing Strategy

- B-tree indexes on all foreign keys and commonly filtered columns
- GIN indexes on JSONB columns in `fhir_raw.resources` for ad-hoc FHIR queries
- Partial indexes on `status = 'active'` for dimension tables (most queries filter for active records)
- BRIN indexes on timestamp columns in partitioned fact tables for efficient range scans

### 8.4 Query Performance Targets

| Query Type | Target Response Time | Notes |
|---|---|---|
| Dashboard widget (single KPI) | < 500 ms | Served from materialized views |
| Dashboard page (all widgets) | < 2 seconds | Parallel widget loading |
| Ad-hoc query (single hospital, 1 month) | < 5 seconds | Partition pruning + indexes |
| Ad-hoc query (all hospitals, 1 year) | < 30 seconds | Full table scan on partitions |
| Data export (CSV, up to 100k rows) | < 60 seconds | Streaming response |

---

*This document is maintained in TechVision's Notion workspace. For technical questions, contact Anna Richter (a.richter@techvision.de). For clinical data model questions, contact Robert Engel (r.engel@medtech-solutions.de). See also the Statement of Work (doc_024) for project scope and timeline.*
