---
doc_id: doc_024
title: "MedTech Analytics – Statement of Work"
author: Thomas Kruger
source_type: notion
---

# MedTech Analytics -- Statement of Work

**Version:** 1.0
**Date:** September 15, 2025
**Author:** Thomas Kruger, Head of Sales
**Status:** Signed
**Classification:** Confidential -- TechVision / MedTech Solutions GmbH

---

## 1. Project Overview

This Statement of Work (SOW) defines the scope, deliverables, timeline, and commercial terms for the MedTech Analytics project between TechVision GmbH ("Provider") and MedTech Solutions GmbH ("Client").

MedTech Solutions GmbH provides hospital information systems to 14 hospitals across Bavaria and Baden-Wurttemberg. Robert Engel, CEO of MedTech Solutions GmbH, has engaged TechVision GmbH to design and develop an analytics platform that transforms operational data from these hospitals into actionable insights for hospital administrators and clinical staff.

The platform will consist of four core deliverables: a data integration layer connecting to MedTech Solutions' existing HL7 FHIR R4 infrastructure, an analytics engine for data transformation and KPI computation, a web-based dashboard application, and a companion mobile application for key metrics on the go.

This engagement builds on TechVision's expertise in data engineering (demonstrated in the Projekt Aurora engagement for Muller Maschinenbau AG, doc_019) and healthcare data standards. The detailed data model and FHIR integration design are documented separately in the Data Model & FHIR Integration document (doc_023).

## 2. Deliverables

### 2.1 Deliverable 1: Data Integration Layer

**Description:** An automated ETL pipeline that extracts data from MedTech Solutions' FHIR R4 servers, transforms it into an analytics-optimized schema, and loads it into a PostgreSQL analytical database.

**Components:**
- FHIR R4 REST API extractor supporting Patient, Encounter, Observation, and DiagnosticReport resources
- Incremental extraction using FHIR `_lastUpdated` parameter
- Data pseudonymization module (HMAC-SHA256 based)
- Data quality validation engine with configurable rules
- Raw FHIR resource archive in PostgreSQL JSONB format
- dbt transformation models (staging, intermediate, marts)
- Extraction scheduling and monitoring via Apache Airflow

**Acceptance Criteria:**
- Successful extraction from at least 3 pilot hospitals within the 15-minute SLA
- Data quality score of 95% or higher across all five quality dimensions (completeness, consistency, timeliness, uniqueness, validity)
- Zero patient-identifiable information in the analytics database (verified by independent review)
- ETL pipeline recovers automatically from transient failures within 3 retry attempts
- Full documentation of data lineage from FHIR source to analytics table

### 2.2 Deliverable 2: Analytics Engine

**Description:** A set of pre-computed KPIs and analytical models that power the dashboard and mobile application, implemented as PostgreSQL materialized views and a FastAPI service layer.

**Components:**
- 25 pre-defined KPIs across four domains: clinical quality, operational efficiency, financial performance, and patient flow
- Materialized views with 15-minute refresh cycle
- FastAPI REST API for KPI retrieval, filtering, and time-series queries
- Role-based data access enforcement via PostgreSQL Row-Level Security
- Configurable alerting engine for KPI threshold breaches

**Key KPIs Include:**
- Bed occupancy rate (by department, hospital)
- Average length of stay (by diagnosis group, department)
- Emergency department wait times (median, P90)
- Laboratory turnaround time (by test category)
- Readmission rate (30-day, by department)
- Operating room utilization
- Staff-to-patient ratio indicators

**Acceptance Criteria:**
- All 25 KPIs return correct results verified against manual calculations on sample data
- API response time under 500ms for single-KPI queries (P95)
- Materialized view refresh completes within 5 minutes across all hospitals
- Role-based access correctly restricts data by hospital and department
- Alert notifications delivered within 5 minutes of threshold breach

### 2.3 Deliverable 3: Web Dashboard

**Description:** A responsive web application providing interactive dashboards for hospital administrators, department heads, and clinical staff.

**Components:**
- Hospital overview dashboard with key metrics summary
- Department-level detail dashboards with drill-down capability
- Patient flow visualization (admissions, discharges, transfers over time)
- Clinical quality scorecards with trend analysis
- Financial performance views with DRG analysis
- Ad-hoc query builder for custom analyses
- Report generation and export (PDF, CSV, Excel)
- User management and role assignment interface

**Acceptance Criteria:**
- Dashboard page loads within 2 seconds under standard conditions (up to 20 concurrent users per hospital)
- All visualizations render correctly on desktop (minimum 1280x720) and tablet (minimum 768x1024)
- WCAG 2.1 Level AA accessibility compliance
- Export functionality produces accurate reports matching dashboard data
- User management supports Azure AD SSO with SAML 2.0

### 2.4 Deliverable 4: Mobile Application

**Description:** A companion mobile application for iOS and Android providing key metrics and alerts for hospital administrators and department heads.

**Components:**
- Native-feel application built with React Native
- Key metrics dashboard (subset of 10 most critical KPIs)
- Push notification support for KPI alert thresholds
- Offline capability for last-viewed data
- Biometric authentication (Face ID, Touch ID, Android Biometric)

**Acceptance Criteria:**
- Application installs and runs on iOS 16+ and Android 13+
- Push notifications delivered within 30 seconds of alert trigger
- Offline mode displays last-synced data with clear freshness indicator
- Biometric authentication integrates with device-native capabilities
- App store submission-ready (Apple App Store and Google Play Store)

## 3. Project Phases and Timeline

The project spans 22 weeks from October 6, 2025 to March 6, 2026.

### Phase 1: Discovery (4 weeks)
**Period:** October 6 -- October 31, 2025

**Activities:**
- Stakeholder interviews with hospital administrators from 3 pilot hospitals
- FHIR server connectivity assessment and API documentation review
- KPI definition workshops with MedTech Solutions product team
- UX research: user interviews, persona development, journey mapping
- Technical architecture design and security review
- Data model design (documented in doc_023)

**Deliverables:**
- Requirements specification document
- Technical architecture document
- UX research report with personas and user journeys
- Data model and FHIR integration document (doc_023)
- Sprint backlog for Phase 2

**Exit Criteria:** Requirements specification signed off by Robert Engel and MedTech Solutions product team.

### Phase 2: Development (12 weeks)
**Period:** November 3, 2025 -- January 23, 2026

**Activities:**
- Sprint-based development in 2-week iterations (6 sprints)
- Sprint 1-2: Data integration layer and core analytics engine
- Sprint 3-4: Web dashboard (core dashboards and visualizations)
- Sprint 5: Mobile application development
- Sprint 6: Integration, polish, and internal testing
- Bi-weekly sprint demos with MedTech Solutions stakeholders
- Continuous integration and automated testing throughout

**Deliverables:**
- Working data integration pipeline (end of Sprint 2)
- Web dashboard beta (end of Sprint 4)
- Mobile application beta (end of Sprint 5)
- Internal test report (end of Sprint 6)

**Note:** The Christmas holiday period (December 22, 2025 -- January 2, 2026) falls within Sprint 4. Development continues at reduced capacity. Sprint 4 is extended to 3 weeks to compensate.

### Phase 3: User Acceptance Testing (4 weeks)
**Period:** January 26 -- February 20, 2026

**Activities:**
- Deployment to UAT environment connected to 3 pilot hospitals
- Structured UAT sessions with hospital administrators and department heads
- Defect triage and resolution (daily stand-ups during UAT)
- Performance testing under simulated production load
- Security assessment and penetration testing
- Accessibility audit by independent evaluator
- Data accuracy validation against manual KPI calculations

**Deliverables:**
- UAT sign-off document from 3 pilot hospitals
- Performance test report
- Security assessment report
- Accessibility audit report
- Final defect resolution report

**Exit Criteria:** All Critical and High severity defects resolved. UAT sign-off received from at least 2 of 3 pilot hospitals.

### Phase 4: Go-Live (2 weeks)
**Period:** February 23 -- March 6, 2026

**Activities:**
- Production environment provisioning and hardening
- Data migration from UAT to production
- Phased rollout: 3 pilot hospitals first, then remaining 11 hospitals
- User training sessions (2 hours per hospital, remote)
- Monitoring setup and alert configuration
- Hypercare support with daily check-ins

**Deliverables:**
- Production deployment documentation
- User training materials (video recordings and written guides)
- Operations runbook
- Project closure report

## 4. Team Composition

TechVision GmbH will assign the following team members to the engagement:

| Role | Name | Allocation | Phase Involvement |
|---|---|---|---|
| Project Manager | Lisa Weber | 50% | All phases |
| Data Engineer | Anna Richter | 100% | All phases (lead for Deliverables 1 and 2) |
| Senior Developer | Felix Braun | 80% | Phases 1-3 (lead for Deliverables 3 and 4) |
| UX Designer | Katharina Schmidt | 60% | Phases 1-2 (100% in Phase 1, 40% in Phase 2) |

Lisa Weber serves as the primary point of contact for MedTech Solutions GmbH and is responsible for overall project delivery, schedule management, and stakeholder communication. Her experience managing the Projekt Aurora engagement (doc_019) for Muller Maschinenbau AG demonstrates her ability to handle data-intensive projects with multiple stakeholders.

Anna Richter leads the data engineering workstream, including FHIR integration, ETL pipeline development, and analytics engine implementation. Her detailed technical design is captured in the Data Model & FHIR Integration document (doc_023).

Felix Braun oversees the web dashboard and mobile application development, ensuring code quality, architectural consistency, and performance targets are met. His concurrent role as Technical Lead on Projekt Aurora (doc_019, doc_020) is managed through careful schedule coordination, with Aurora in its later phases requiring reduced involvement.

Katharina Schmidt leads UX research and design, ensuring the platform meets the needs of diverse user groups across hospital settings. She is also allocated to the FinSecure Portal project (doc_021) but with non-overlapping peak periods.

MedTech Solutions GmbH will provide:
- A product owner for requirements prioritization and sprint reviews
- Clinical domain experts for KPI validation and data interpretation
- IT operations staff for FHIR server access and infrastructure coordination
- UAT participants from 3 pilot hospitals

## 5. Budget

The total project budget is EUR 195,000, structured as follows:

| Category | Amount (EUR) | Description |
|---|---|---|
| Discovery and Design | 30,000 | Phase 1: research, architecture, UX design |
| Data Integration Layer | 45,000 | Deliverable 1: FHIR extraction, ETL, data quality |
| Analytics Engine | 30,000 | Deliverable 2: KPIs, API, alerting |
| Web Dashboard | 45,000 | Deliverable 3: dashboard application |
| Mobile Application | 25,000 | Deliverable 4: iOS and Android app |
| Testing and Go-Live | 20,000 | Phases 3-4: UAT, security testing, deployment, training |
| **Total** | **195,000** | |

**Payment Schedule:**
- 20% upon contract signing (EUR 39,000) -- October 2025
- 30% upon completion of Phase 2 / Sprint 3 (EUR 58,500) -- December 2025
- 30% upon UAT sign-off (EUR 58,500) -- February 2026
- 20% upon go-live acceptance (EUR 39,000) -- March 2026

All amounts exclude applicable VAT (19%). The budget assumes the team composition and allocation described in Section 4. Any increase in scope or team allocation requires a formal change request.

## 6. Change Management Process

Changes to scope, timeline, or budget follow a structured process:

1. **Change Request:** Either party may submit a change request in writing, describing the proposed change, rationale, and estimated impact on scope, timeline, and budget.

2. **Impact Assessment:** TechVision GmbH evaluates the change request within 5 business days, providing a detailed impact assessment including effort estimate, timeline impact, and cost.

3. **Approval:** Changes with budget impact of up to EUR 10,000 can be approved by Lisa Weber (TechVision) and the MedTech Solutions product owner jointly. Changes exceeding EUR 10,000 require approval from Thomas Kruger (TechVision, Head of Sales) and Robert Engel (MedTech Solutions, CEO).

4. **Implementation:** Approved changes are incorporated into the sprint backlog with adjusted priority. The project plan, budget tracker, and risk register are updated accordingly.

5. **Documentation:** All change requests, impact assessments, and approvals are logged in the project's Confluence space and referenced in the monthly status report.

Emergency changes (e.g., critical security vulnerabilities, regulatory compliance requirements) may bypass the standard timeline but still require documented approval within 2 business days.

## 7. Warranty Period

TechVision GmbH provides a warranty period of 3 months following the go-live acceptance date (estimated: March 6, 2026, through June 5, 2026).

**Warranty Coverage:**
- Defect resolution for bugs present at the time of go-live acceptance but not discovered during UAT
- Defect severity classification follows the same schema used during UAT (Critical, High, Medium, Low)
- Critical defects: 4-hour response, 24-hour resolution target
- High defects: 8-hour response, 3-business-day resolution target
- Medium and Low defects: next business day response, addressed in scheduled maintenance releases

**Warranty Exclusions:**
- Defects caused by changes to the FHIR server APIs or data formats by MedTech Solutions or hospitals after go-live
- Issues arising from infrastructure changes not coordinated with TechVision
- Feature requests or enhancements (handled through a separate maintenance agreement)
- Performance issues caused by data volumes exceeding the agreed capacity plan (14 hospitals, approximately 500,000 patient records total)

**Post-Warranty Support:**
TechVision GmbH will offer a separate maintenance and support agreement starting after the warranty period, to be negotiated during Phase 4. Petra Neumann (TechVision Finance) will prepare the commercial terms for the ongoing support agreement by February 2026.

## 8. Governance

**Status Reporting:**
- Weekly written status report (RAG format) delivered by Lisa Weber every Friday
- Bi-weekly sprint demo and retrospective (video call, 90 minutes)
- Monthly steering committee meeting with Robert Engel and TechVision management

**Escalation Path:**
1. Project level: Lisa Weber (TechVision) and MedTech Solutions product owner
2. Management level: Thomas Kruger (TechVision) and Robert Engel (MedTech Solutions)
3. Executive level: Dr. Martin Schreiber (TechVision CEO) and Robert Engel

**Communication Channels:**
- Day-to-day: Shared Slack workspace (#medtech-analytics channel)
- Documentation: Confluence space with guest access for MedTech Solutions team
- Issue tracking: Jira project (MEDTECH) with MedTech Solutions read access
- Video conferencing: Microsoft Teams (MedTech Solutions' preferred platform)

## 9. Legal and Compliance

- **Data Processing Agreement:** Separate DPA executed between TechVision GmbH and MedTech Solutions GmbH, covering GDPR Article 28 requirements.
- **Healthcare Data:** All development and testing uses pseudonymized data only. No real patient data is accessible to TechVision team members.
- **IP Ownership:** All custom code developed for this engagement is owned by MedTech Solutions GmbH upon final payment. TechVision retains the right to use general-purpose libraries and frameworks developed during the engagement in other projects, provided they contain no MedTech-specific business logic.
- **Confidentiality:** Both parties have signed a mutual NDA (dated August 2025) covering all project-related information.
- **Insurance:** TechVision GmbH maintains professional liability insurance of EUR 2 million per occurrence.

---

**Signatures:**

| Name | Role | Organization | Date |
|---|---|---|---|
| Thomas Kruger | Head of Sales | TechVision GmbH | September 15, 2025 |
| Robert Engel | CEO | MedTech Solutions GmbH | September 15, 2025 |

---

*This Statement of Work is maintained in TechVision's Notion workspace. For contractual questions, contact Thomas Kruger (t.krueger@techvision.de). For project execution questions, contact Lisa Weber (l.weber@techvision.de).*
