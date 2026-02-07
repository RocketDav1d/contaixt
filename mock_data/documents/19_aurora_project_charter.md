---
doc_id: doc_019
title: "Projekt Aurora – Project Charter"
author: Lisa Weber
source_type: notion
---

# Projekt Aurora -- Project Charter

**Version:** 1.0
**Date:** August 15, 2025
**Author:** Lisa Weber, Project Manager
**Status:** Approved
**Classification:** Confidential -- TechVision / Muller Maschinenbau AG

---

## 1. Project Overview

Projekt Aurora is a strategic cloud migration and data platform initiative commissioned by Muller Maschinenbau AG, a mid-sized manufacturing company headquartered in Augsburg, Germany, with approximately 1,200 employees and annual revenue of EUR 180 million. The project aims to migrate their legacy on-premise ERP landscape to Microsoft Azure and establish a modern data platform that enables real-time operational insights through interactive dashboards.

Muller Maschinenbau AG currently operates a fragmented IT landscape consisting of an Oracle-based ERP system (version 12.1, deployed in 2014), SAP modules for procurement and warehouse management, and several standalone MES (Manufacturing Execution System) applications across three production facilities. This fragmentation has led to data silos, inconsistent reporting, and an inability to leverage operational data for strategic decision-making.

Hans Muller, CEO of Muller Maschinenbau AG, identified the digital transformation of their data infrastructure as a top priority during the board meeting in June 2025. Following a competitive evaluation of three consulting firms, TechVision GmbH was selected as the implementation partner based on our demonstrated expertise in Azure cloud migrations and industrial data platforms. Dr. Martin Schreiber, CEO of TechVision GmbH, and Hans Muller signed the engagement letter on August 1, 2025.

This project charter establishes the formal authorization for Projekt Aurora, defines its scope, objectives, constraints, and governance structure, and serves as the reference document for all project decisions throughout the engagement.

## 2. Project Objectives

The following objectives have been agreed upon with Muller Maschinenbau AG:

1. **Cloud Migration:** Migrate all ERP workloads from on-premise Oracle and SAP systems to Microsoft Azure, ensuring zero data loss and minimal operational disruption during the transition period.

2. **Data Platform:** Design and implement a centralized data lake architecture on Azure Data Lake Storage Gen2, consolidating data from ERP, MES, and IoT sensor systems into a unified analytical layer.

3. **Dashboards and Reporting:** Deliver a suite of Power BI dashboards providing real-time visibility into production KPIs, supply chain metrics, financial summaries, and quality control indicators.

4. **Operational Continuity:** Maintain uninterrupted business operations throughout the migration, with all cutover activities scheduled during planned maintenance windows.

5. **Knowledge Transfer:** Equip the Muller Maschinenbau AG IT team (6 staff members) with the skills and documentation necessary to operate and extend the platform independently after project completion.

## 3. Scope

### 3.1 In Scope

- Migration of Oracle ERP 12.1 database (approximately 2.3 TB) to Azure SQL Managed Instance
- Migration of SAP procurement and warehouse modules to SAP on Azure (Infrastructure-as-a-Service)
- Implementation of Azure Data Lake Storage Gen2 with Bronze/Silver/Gold zone architecture (see Technical Design Document, doc_020)
- Azure Data Factory pipelines for data ingestion from ERP, MES, and IoT sources
- Azure Synapse Analytics workspace for data transformation and modeling
- 12 Power BI dashboards across four business domains (production, supply chain, finance, quality)
- Azure Active Directory integration with existing on-premise AD via Azure AD Connect
- Network architecture: Azure ExpressRoute connection to Augsburg data center
- Monitoring and alerting setup using Azure Monitor
- Comprehensive documentation and three days of on-site training

### 3.2 Out of Scope

- Migration of email systems (handled separately by Muller Maschinenbau AG internal IT)
- Replacement of MES applications (data integration only; MES remains on-premise)
- Development of custom mobile applications
- Hardware procurement for on-premise systems
- Historical data beyond 5 years (archived data remains in legacy cold storage)
- IoT sensor hardware upgrades (existing MQTT-capable sensors will be integrated as-is)

## 4. Budget

The total project budget is EUR 450,000 (four hundred fifty thousand euros), allocated as follows:

| Category | Amount (EUR) | Percentage | Description |
|---|---|---|---|
| Infrastructure | 120,000 | 26.7% | Azure subscriptions (12 months), ExpressRoute, licensing |
| Development | 250,000 | 55.6% | Personnel costs for TechVision team (design, implementation, testing) |
| Consulting | 50,000 | 11.1% | Workshops, training, architecture reviews, knowledge transfer |
| Contingency | 30,000 | 6.7% | Reserve for unforeseen technical challenges or scope adjustments |

**Payment Schedule:**

- 20% upon contract signing (EUR 90,000) -- August 2025
- 30% upon completion of migration phase (EUR 135,000) -- November 2025
- 30% upon delivery of data platform and dashboards (EUR 135,000) -- January 2026
- 20% upon final acceptance (EUR 90,000) -- February 2026

Budget overruns exceeding the contingency reserve require written approval from both Hans Muller (Muller Maschinenbau AG) and Sandra Hoffmann (TechVision GmbH steering committee). Any use of the contingency budget must be documented with a change request form and approved by the steering committee before expenditure.

## 5. Timeline

The project spans six months from September 1, 2025 to February 28, 2026.

| Phase | Duration | Start | End | Key Milestones |
|---|---|---|---|---|
| Phase 1: Discovery and Planning | 4 weeks | Sep 1 | Sep 26 | Architecture sign-off, migration plan approved |
| Phase 2: Infrastructure Setup | 3 weeks | Sep 29 | Oct 17 | Azure environment provisioned, ExpressRoute active |
| Phase 3: Data Migration | 6 weeks | Oct 20 | Nov 28 | Oracle migration complete, SAP migration complete |
| Phase 4: Data Platform | 6 weeks | Nov 3 | Dec 12 | Data lake operational, ETL pipelines running |
| Phase 5: Dashboards | 4 weeks | Dec 15 | Jan 16, 2026 | All 12 dashboards delivered and reviewed |
| Phase 6: Testing and Go-Live | 4 weeks | Jan 19 | Feb 13, 2026 | UAT complete, production cutover |
| Phase 7: Hypercare | 2 weeks | Feb 16 | Feb 28, 2026 | Stabilization, knowledge transfer, project closure |

Note: Phases 3 and 4 overlap by approximately four weeks, as data platform development can begin with initial datasets while migration of remaining systems continues. Detailed sprint planning is documented in the project management tool (Jira).

## 6. Project Team

### TechVision GmbH

| Name | Role | Allocation | Responsibilities |
|---|---|---|---|
| Lisa Weber | Project Manager | 100% | Overall project delivery, stakeholder communication, risk management |
| Felix Braun | Technical Lead | 100% | Architecture decisions, code reviews, technical escalations |
| Anna Richter | Data Engineer | 100% | Data lake design, ETL pipelines, data quality |
| Markus Lehmann | DevOps Engineer | 80% | Azure infrastructure, CI/CD, monitoring |
| Daniel Hartmann | Developer | 80% | Dashboard development, API integration, testing |

### Muller Maschinenbau AG

| Name | Role | Responsibilities |
|---|---|---|
| Hans Muller | Executive Sponsor | Strategic direction, budget approval, escalation resolution |
| Stefan Braun | IT Director | Technical counterpart, system access, internal coordination |
| Maria Schneider | Data Analyst | Business requirements, dashboard validation, UAT coordination |
| Jorg Becker | ERP Administrator | Legacy system expertise, migration support, data validation |

## 7. Governance Structure

### Steering Committee

- **Members:** Hans Muller, Sandra Hoffmann (TechVision CTO), Stefan Braun, Lisa Weber
- **Cadence:** Monthly (first Thursday of each month)
- **Purpose:** Strategic oversight, budget approvals, escalation resolution, scope change decisions

### Project Status Meetings

- **Cadence:** Weekly (Tuesday 10:00 CET, video call)
- **Attendees:** Lisa Weber, Felix Braun, Stefan Braun, Maria Schneider
- **Deliverables:** Status report (RAG), updated risk register, upcoming milestone review

### Technical Syncs

- **Cadence:** Bi-weekly (Thursday 14:00 CET)
- **Attendees:** Felix Braun, Anna Richter, Markus Lehmann, Jorg Becker
- **Purpose:** Technical deep-dives, integration testing coordination, architecture decisions

## 8. Risk Register

| ID | Risk | Probability | Impact | Mitigation Strategy | Owner |
|---|---|---|---|---|---|
| R-001 | Data migration complexity exceeds estimates due to Oracle schema inconsistencies | High | High | Conduct thorough schema analysis in Phase 1; allocate extra time in migration phase; engage Oracle specialist if needed | Felix Braun |
| R-002 | Legacy system documentation gaps for SAP customizations | Medium | High | Interview key users and ERP administrator; reverse-engineer critical customizations; document findings before migration | Anna Richter |
| R-003 | Azure consumption costs exceed infrastructure budget | Medium | Medium | Implement Azure Cost Management alerts at 60%, 80%, and 95% thresholds; right-size resources monthly; use reserved instances for predictable workloads | Markus Lehmann |
| R-004 | Key personnel unavailability (illness, departure) | Low | High | Cross-train team members; document all architectural decisions; maintain updated onboarding materials | Lisa Weber |
| R-005 | Muller Maschinenbau AG stakeholder availability for UAT | Medium | Medium | Schedule UAT windows early; provide pre-configured test scenarios; offer flexible testing hours | Lisa Weber |
| R-006 | Network latency between on-premise MES and Azure impacts real-time data ingestion | Low | Medium | Test connectivity early in Phase 2; implement buffering and retry mechanisms; consider Azure IoT Hub as intermediary | Felix Braun |
| R-007 | Data quality issues in legacy systems discovered during migration | High | Medium | Define data cleansing rules in Phase 1; implement automated validation checks; establish data quality dashboard | Anna Richter |

Risk reviews are conducted weekly during status meetings and monthly during steering committee sessions. New risks can be raised by any team member via the shared risk register in Confluence.

## 9. Success Criteria

The following measurable criteria define project success and will be evaluated during the final acceptance phase:

1. **System Availability:** The Azure-hosted platform must achieve 99.9% uptime during the first 30 days of production operation, measured by Azure Monitor availability metrics.

2. **Dashboard Performance:** All Power BI dashboards must load within 2 seconds under standard usage conditions (up to 50 concurrent users).

3. **Data Integrity:** Zero data loss during migration, verified through automated row count reconciliation and checksum validation across all migrated tables.

4. **Data Freshness:** Production dashboards must reflect data no older than 15 minutes from source systems.

5. **User Adoption:** At least 80% of identified dashboard users (approximately 40 individuals) must have logged in and used the platform within 30 days of go-live.

6. **Budget Adherence:** Total project expenditure must remain within the approved budget of EUR 450,000 including contingency.

7. **Knowledge Transfer:** Muller Maschinenbau AG IT team must be able to independently perform routine operations (pipeline monitoring, dashboard modifications, user management) as verified through a hands-on assessment.

## 10. Assumptions and Dependencies

### Assumptions

- Muller Maschinenbau AG will provide timely access to all legacy systems and relevant documentation.
- An Azure Enterprise Agreement is already in place or will be established before Phase 2 begins.
- The existing on-premise Active Directory is compatible with Azure AD Connect.
- IoT sensors in production facilities are MQTT-capable and accessible via the factory network.

### Dependencies

- Azure ExpressRoute provisioning by Microsoft (estimated 4-6 weeks lead time).
- SAP license transfer to Azure IaaS must be approved by SAP (engagement with SAP account manager initiated).
- Muller Maschinenbau AG must complete a planned network infrastructure upgrade in Augsburg by mid-September 2025.

## 11. Approvals

| Name | Role | Signature | Date |
|---|---|---|---|
| Hans Muller | Executive Sponsor, Muller Maschinenbau AG | [Signed] | August 15, 2025 |
| Dr. Martin Schreiber | CEO, TechVision GmbH | [Signed] | August 15, 2025 |
| Sandra Hoffmann | CTO, TechVision GmbH (Steering Committee) | [Signed] | August 15, 2025 |
| Lisa Weber | Project Manager, TechVision GmbH | [Signed] | August 15, 2025 |

---

*This document is maintained in TechVision's Notion workspace. For questions or change requests, contact Lisa Weber (l.weber@techvision.de).*
