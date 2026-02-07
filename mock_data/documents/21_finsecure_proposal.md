---
doc_id: doc_021
title: "FinSecure Portal – Commercial Proposal"
author: Thomas Kruger
source_type: notion
---

# FinSecure Portal -- Commercial Proposal

**Version:** 2.1
**Date:** September 5, 2025
**Author:** Thomas Kruger, Head of Sales
**Status:** Submitted to Client
**Classification:** Confidential -- TechVision / FinSecure Bank AG

---

## 1. Executive Summary

TechVision GmbH is pleased to present this commercial proposal for the design, development, and deployment of a modern customer-facing banking portal for FinSecure Bank AG. The portal will replace the existing legacy online banking interface (deployed in 2017) with a responsive, accessible, and secure platform that meets current BaFin regulatory requirements and positions FinSecure Bank AG for future digital banking services.

Dr. Claudia Berger, Head of Digital Transformation at FinSecure Bank AG, outlined the strategic vision during our initial meeting on July 18, 2025: to deliver a banking experience that matches the expectations of digitally native customers while maintaining the trust and security standards that FinSecure Bank AG's 120,000 retail customers rely upon.

TechVision GmbH brings deep expertise in financial services technology, demonstrated through our ongoing compliance and security consulting engagements. Our proposed solution leverages a modern technology stack, adheres to BaFin MaRisk requirements (detailed in the accompanying Compliance Matrix, doc_022), and is designed for extensibility to accommodate future features such as personal finance management, robo-advisory integration, and open banking APIs.

## 2. Scope of Work

### 2.1 Core Features

The FinSecure Portal will deliver the following core capabilities at launch:

**Account Overview:**
- Multi-account dashboard with real-time balance display (current accounts, savings, fixed deposits, securities)
- Account summary with spending categorization (automated and manual)
- Quick actions: internal transfers, standing order management, account statements

**Transaction History:**
- Full transaction history with search, filtering, and sorting capabilities
- Transaction categorization using ML-based classification (pre-trained model)
- Export functionality (CSV, PDF, MT940 format for corporate customers)
- Real-time transaction notifications via push and email

**Document Center:**
- Secure document storage for bank-generated documents (statements, tax certificates, contract documents)
- Document upload capability for customer-initiated correspondence
- Digital signature integration for contract amendments
- Retention policy enforcement (automatic archival after 10 years)

**Secure Messaging:**
- End-to-end encrypted messaging between customers and bank advisors
- Structured inquiry forms for common requests (address change, card replacement, limit adjustment)
- File attachment support with malware scanning
- Response time tracking and SLA indicators

### 2.2 Non-Functional Requirements

- **Accessibility:** WCAG 2.1 Level AA compliance for all customer-facing pages
- **Localization:** German (primary), English (secondary), Turkish (planned for Phase 2)
- **Responsive design:** Desktop, tablet, and mobile breakpoints
- **Browser support:** Chrome, Firefox, Safari, Edge (latest two major versions)
- **Performance:** Page load under 2 seconds, API response under 500ms (P95)

## 3. Technology Stack

The proposed technology stack has been selected for its maturity in financial services, strong community support, and compliance with FinSecure Bank AG's existing technology standards:

**Frontend:**
- React 18 with TypeScript 5.x
- Next.js 14 for server-side rendering and optimized page loads
- Tailwind CSS for styling with a custom design system
- React Query for server state management
- Playwright for end-to-end testing

**Backend:**
- Java 21 (LTS) with Spring Boot 3.2
- Spring Security for authentication and authorization
- Spring Data JPA for database access
- Apache Kafka for event streaming and audit logging
- JUnit 5 and Mockito for unit and integration testing

**Database:**
- PostgreSQL 16 for transactional data
- Redis for session management and caching
- Elasticsearch for full-text search across transactions and documents

**Infrastructure:**
- Microsoft Azure (West Europe region, as per data residency requirements)
- Azure Kubernetes Service for container orchestration
- Azure DevOps for CI/CD pipelines
- Azure Key Vault for secrets management

## 4. Regulatory Compliance

The FinSecure Portal has been designed with regulatory compliance as a foundational requirement, not an afterthought. The accompanying BaFin Compliance Matrix (doc_022) provides a detailed mapping of MaRisk requirements to specific technical implementations.

Key compliance areas addressed:

- **BaFin MaRisk AT 7.2 (IT Operations):** Comprehensive monitoring, structured change management process, documented incident response procedures
- **BaFin MaRisk AT 4.3.1 (Information Security):** AES-256 encryption at rest, TLS 1.3 in transit, role-based access control with principle of least privilege
- **PSD2 Strong Customer Authentication (SCA):** Two-factor authentication using TOTP or FIDO2 hardware tokens, with risk-based step-up authentication for high-value transactions
- **GDPR:** Data minimization, purpose limitation, right to erasure implementation, privacy-by-design architecture
- **BSI IT-Grundschutz:** Network segmentation, endpoint protection, regular vulnerability scanning

Tobias Fischer, our Security Lead, will serve as the dedicated compliance liaison throughout the project and will coordinate with FinSecure Bank AG's internal audit team for all compliance validations.

## 5. Budget

The total project investment is EUR 280,000, broken down as follows:

| Category | Amount (EUR) | Description |
|---|---|---|
| UX Design | 40,000 | User research, wireframes, UI design, design system, accessibility audit |
| Development | 180,000 | Frontend, backend, integration, database, infrastructure setup |
| Quality Assurance | 40,000 | Test strategy, automated testing, security testing, UAT support |
| Project Management | 20,000 | Planning, coordination, status reporting, risk management |
| **Total** | **280,000** | |

**Payment Terms:**
- 15% upon contract signing (EUR 42,000)
- 25% upon design approval (EUR 70,000)
- 35% upon completion of development (EUR 98,000)
- 25% upon final acceptance (EUR 70,000)

All amounts exclude applicable VAT (currently 19%). Travel expenses for on-site workshops at FinSecure Bank AG's Frankfurt headquarters are included in the budget.

## 6. Timeline

The project spans six months from October 2025 to March 2026.

| Phase | Duration | Period | Key Deliverables |
|---|---|---|---|
| Phase 1: Discovery and Design | 6 weeks | Oct 1 -- Nov 11, 2025 | User research report, wireframes, design system, technical architecture |
| Phase 2: Core Development | 10 weeks | Nov 12, 2025 -- Jan 23, 2026 | Account overview, transactions, document center, secure messaging |
| Phase 3: Integration and Testing | 6 weeks | Jan 26 -- Mar 6, 2026 | System integration, security testing, performance testing, UAT |
| Phase 4: Go-Live | 2 weeks | Mar 9 -- Mar 20, 2026 | Production deployment, monitoring setup, hypercare |

Note: The timeline accounts for a reduced-activity period during the Christmas holidays (December 22, 2025 -- January 2, 2026).

## 7. Team Composition

TechVision GmbH will allocate the following team for the duration of the engagement:

| Role | Name | Allocation | Key Responsibilities |
|---|---|---|---|
| Project Manager | TBD (to be assigned from TechVision PM pool) | 50% | Delivery management, client communication, risk management |
| Senior Developer / Tech Lead | TBD | 100% | Architecture, backend development, code reviews |
| Frontend Developer | TBD | 100% | React/TypeScript development, responsive design, accessibility |
| UX Designer | Katharina Schmidt | 60% (Phase 1: 100%) | User research, interaction design, usability testing |
| QA Engineer | TBD | 60% (Phase 3: 100%) | Test automation, security testing, performance testing |

Total team effort: 5 FTE (full-time equivalents) averaged across the project duration.

## 8. Service Level Agreement

Upon go-live, TechVision GmbH will provide operational support under the following SLA terms for a period of 12 months:

| Metric | Target | Measurement |
|---|---|---|
| System Availability | 99.95% uptime | Azure Monitor, measured monthly |
| Response Time (P95) | < 500 ms | Application Insights |
| Incident Response (Critical) | < 30 minutes | Ticketing system (PagerDuty) |
| Incident Response (High) | < 2 hours | Ticketing system |
| Incident Response (Medium) | < 8 hours (business hours) | Ticketing system |
| Monitoring Coverage | 24/7 | Automated alerting with on-call rotation |

SLA credits apply if availability falls below 99.95% in any calendar month: 5% credit for each 0.1% below target, up to a maximum of 30% of the monthly support fee.

## 9. Assumptions and Prerequisites

- FinSecure Bank AG will provide API access to the core banking system (Avaloq) within 4 weeks of project start
- A dedicated staging environment mirroring the production Avaloq instance will be available for integration testing
- FinSecure Bank AG's internal security team will be available for bi-weekly security review sessions
- The existing customer identity system (Azure AD B2C) will be extended rather than replaced
- FinSecure Bank AG will provide test data sets anonymized from production data

## 10. Next Steps

1. Review of this proposal and the accompanying Compliance Matrix (doc_022) by FinSecure Bank AG's technical and compliance teams
2. Clarification workshop (proposed: September 18, 2025, at FinSecure Bank AG Frankfurt)
3. Contract negotiation and signing (target: September 30, 2025)
4. Project kickoff (target: October 1, 2025)

We look forward to partnering with FinSecure Bank AG on this strategically important initiative. For questions regarding this proposal, please contact Thomas Kruger (t.krueger@techvision.de) or Dr. Martin Schreiber (m.schreiber@techvision.de).

---

*Prepared by TechVision GmbH, Leopoldstrasse 42, 80802 Munich, Germany. This proposal is valid for 30 days from the date of issue.*
