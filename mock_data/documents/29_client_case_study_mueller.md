---
doc_id: doc_029
title: "Case Study: Müller Maschinenbau – Cloud Migration & Data Platform"
author: "Thomas Krüger"
source_type: notion
---

# Case Study: Muller Maschinenbau AG – Cloud Migration & Data Platform

**Prepared by:** Thomas Kruger (Head of Sales)
**Date:** September 20, 2025
**Classification:** External – Published with Client Permission

---

## At a Glance

| | |
|---|---|
| **Client** | Muller Maschinenbau AG |
| **Industry** | Manufacturing (Industrial Machinery) |
| **Headquarters** | Augsburg, Germany |
| **Employees** | 500+ |
| **Project Name** | Projekt Aurora |
| **Engagement Value** | €450,000 |
| **Duration** | 8 months (April 2025 – January 2026) |
| **TechVision Team** | 5 consultants |
| **Technologies** | Azure (AKS, Data Factory, Synapse Analytics, ADLS Gen2), Terraform, Python, Power BI |

---

## Client Background

Muller Maschinenbau AG is a mid-sized German manufacturer of industrial machinery and precision components, headquartered in Augsburg, Bavaria. Founded in 1967, the company has grown to over 500 employees across three production facilities in Germany, serving clients in the automotive, aerospace, and energy sectors. Annual revenue exceeds €120 million.

Hans Muller, CEO and grandson of the founder, has been leading a modernization initiative since 2023, recognizing that digital transformation is essential for maintaining the company's competitive position in an increasingly data-driven manufacturing landscape.

---

## The Challenge

When Muller Maschinenbau approached TechVision GmbH in early 2025, they faced several interconnected technology challenges:

**Legacy Infrastructure:** The company's core IT systems were running on-premises, centered around an Oracle ERP system installed in 2011. The infrastructure was aging, expensive to maintain, and approaching end-of-support. Annual infrastructure costs (hardware, licensing, maintenance contracts) exceeded €450,000.

**Data Silos:** Critical business data was spread across multiple disconnected systems — the Oracle ERP for finance and procurement, a separate MES (Manufacturing Execution System) for production data, a CRM system for sales, and dozens of Excel spreadsheets used by operations managers. There was no single source of truth.

**No Real-Time Visibility:** Production managers relied on daily batch reports generated overnight. If a quality issue emerged on the production line at 9 AM, it might not be visible in reports until the following morning. This lag led to costly delays in identifying and resolving production problems.

**Reporting Bottleneck:** The IT team of 8 people spent an estimated 30% of their time generating manual reports for different departments. The finance team alone required 15 different monthly reports, each taking 2-4 hours to compile.

**Compliance Pressure:** Automotive clients were increasingly requiring real-time quality documentation and traceability — capabilities that the existing infrastructure could not support without significant investment.

Hans Muller summarized the situation: "We were running a 21st-century production line with 20th-century IT. Our people were excellent, but our systems were holding them back."

---

## The Solution

TechVision GmbH designed and implemented a comprehensive cloud migration and data platform under the project name "Projekt Aurora." The solution was built on Microsoft Azure, leveraging the full spectrum of Azure data services.

### Phase 1: Cloud Foundation (Months 1-2)

Markus Lang, TechVision's DevOps Lead, architected the Azure landing zone using infrastructure-as-code principles:

- **Azure Kubernetes Service (AKS):** Container orchestration for application workloads, providing scalability and reliability that on-premises infrastructure could not match.
- **Networking:** Hub-and-spoke virtual network topology with ExpressRoute connectivity to Muller Maschinenbau's Augsburg headquarters, ensuring low-latency access to cloud resources.
- **Security:** Azure Active Directory integration, role-based access control, and encryption at rest and in transit. Tobias Fischer, TechVision's Security Officer, conducted a threat modeling workshop and implemented Azure Security Center monitoring.
- **Infrastructure as Code:** All resources provisioned via Terraform, with CI/CD pipelines for infrastructure changes. This ensures reproducibility and auditability — critical for Muller Maschinenbau's quality management requirements.

### Phase 2: Data Platform (Months 2-5)

Anna Richter led the design and implementation of the data platform using a **medallion architecture** (bronze/silver/gold layers):

- **Bronze Layer (Raw Data):** Azure Data Lake Storage Gen2 receives raw data from all source systems. Felix Braun developed custom connectors using Azure Data Factory to extract data from the Oracle ERP, MES, and CRM systems on scheduled and event-driven triggers.
- **Silver Layer (Cleaned & Enriched):** Python-based data transformation pipelines clean, validate, and enrich raw data. Entity resolution logic matches records across systems (e.g., linking a customer in CRM to the same entity in ERP). Anna Richter's expertise in data engineering was instrumental in designing robust data quality checks at this layer.
- **Gold Layer (Business-Ready):** Azure Synapse Analytics provides the analytical layer, with pre-computed aggregations and business metrics ready for consumption by reporting tools and APIs.

Data flows are orchestrated by Azure Data Factory, with monitoring and alerting configured through Azure Monitor. The entire pipeline processes data in near-real-time, with end-to-end latency under 5 minutes for most data sources.

### Phase 3: Analytics & Visualization (Months 4-7)

Lisa Weber, the Project Manager, coordinated closely with Muller Maschinenbau's operations and finance teams to design dashboards and reports that matched actual business workflows:

- **Production Monitoring Dashboard:** Real-time visibility into production line performance, including throughput, defect rates, machine utilization, and energy consumption. Operations managers can now see issues as they happen, not the next morning.
- **Financial Reporting Suite:** Automated generation of all 15 monthly finance reports, pulling directly from the gold layer. What previously took 30-60 hours per month now runs automatically.
- **Quality Traceability:** End-to-end traceability from raw material to finished product, meeting automotive client requirements for quality documentation.
- **Executive Dashboard:** A C-level overview combining financial, operational, and sales KPIs in a single Power BI dashboard accessible on desktop and mobile.

### Phase 4: Migration & Cutover (Months 6-8)

The most critical phase — migrating production workloads from on-premises to Azure without disrupting ongoing operations. Markus Lang designed a phased cutover strategy:

- **Parallel Running:** Both on-premises and cloud systems ran in parallel for 4 weeks, with automated data reconciliation to ensure consistency.
- **Gradual Cutover:** Individual workloads were migrated one at a time, starting with non-critical reporting systems and ending with the production monitoring feeds.
- **Zero Downtime:** The migration was completed with zero unplanned downtime. Production operations were never interrupted.

---

## The TechVision Team

Five TechVision consultants worked on Projekt Aurora:

| Name | Role | Key Contributions |
|------|------|-------------------|
| Lisa Weber | Project Manager | Client coordination, requirements, delivery management |
| Anna Richter | Data Engineer (Lead) | Medallion architecture, data pipelines, data quality |
| Felix Braun | Senior Developer | Data Factory connectors, API development, real-time ingestion |
| Markus Lang | DevOps Lead | Azure landing zone, Terraform, AKS, migration strategy |
| Tobias Fischer | Security Advisor | Threat modeling, compliance, security architecture |

Sandra Hoffmann, TechVision's CTO, provided technical oversight and architecture review throughout the project, joining the monthly steering committee meetings with Hans Muller and his leadership team.

---

## Results

The impact of Projekt Aurora has been significant and measurable:

### Operational Efficiency

- **60% reduction in report generation time:** Automated reporting replaced manual compilation. The finance team reclaimed approximately 40 hours per month.
- **Real-time production monitoring:** Replaced daily batch reports. Issues are now identified and addressed within minutes, not hours.
- **IT team freed up:** The 8-person IT team reduced time spent on report generation from 30% to under 5%, redirecting capacity to strategic initiatives.

### Cost Savings

- **€180,000 annual infrastructure cost savings:** Cloud operating costs (including Azure consumption, reserved instances, and managed services) are approximately €270,000 annually, compared to €450,000 for the previous on-premises setup. This represents a 40% reduction in infrastructure costs.
- **Reduced Oracle licensing costs:** By migrating reporting workloads off Oracle, Muller Maschinenbau was able to downsize their Oracle license, saving an additional €45,000 annually.

### Business Agility

- **New reports in hours, not weeks:** Business users can create new Power BI reports from the gold layer data without IT involvement. Previously, new report requests took 2-4 weeks in the IT backlog.
- **Scalable foundation:** The Azure platform can scale to accommodate Muller Maschinenbau's growth plans, including their planned expansion into Eastern European production.

### Compliance & Quality

- **Automotive quality requirements met:** Real-time traceability satisfies requirements from key automotive clients, protecting approximately €25M in annual automotive revenue.
- **Audit-ready infrastructure:** Terraform-managed infrastructure provides complete audit trails for all environment changes.

---

## What the Client Says

> "TechVision GmbH has been an outstanding partner for our digital transformation journey. From the first workshop to the final migration, the team demonstrated deep technical expertise, clear communication, and a genuine commitment to our success. Projekt Aurora has fundamentally changed how we run our business — our managers now have the data they need at their fingertips, and our production teams can respond to issues in real time rather than finding out the next day. The €180,000 in annual savings is significant, but the real value is in the agility and confidence that the new platform gives us. I look forward to continuing our partnership in Phase 2."
>
> — **Hans Muller, CEO, Muller Maschinenbau AG**

---

## Looking Ahead

Based on the success of Projekt Aurora, Muller Maschinenbau and TechVision are in discussions about a Phase 2 engagement (doc_026) focused on:

- **Predictive maintenance:** Using machine learning models on production sensor data to predict equipment failures before they occur.
- **Advanced analytics:** Expanding the data platform with Databricks for complex analytical workloads.
- **Supply chain optimization:** Integrating supplier data into the platform for end-to-end supply chain visibility.

The estimated value of Phase 2 is €200,000-€300,000, with a potential start date in Q1 2026.

---

## About TechVision GmbH

TechVision GmbH is a Munich-based IT consulting firm specializing in cloud migration, data platform engineering, and data-driven transformation for mid-market companies. With approximately 80 employees and Microsoft Gold Partnership status, TechVision combines deep technical expertise with the agility and client intimacy that mid-market organizations value. Learn more at techvision-gmbh.de.

---

*For inquiries about this case study, contact:*
*Thomas Kruger, Head of Sales*
*t.krueger@techvision-gmbh.de*
*+49 89 XXXX XXXX*
