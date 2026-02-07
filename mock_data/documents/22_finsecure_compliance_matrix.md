---
doc_id: doc_022
title: "FinSecure Portal – BaFin Compliance Matrix"
author: Tobias Fischer
source_type: notion
---

# FinSecure Portal -- BaFin Compliance Matrix

**Version:** 1.1
**Date:** September 5, 2025
**Author:** Tobias Fischer, Security Lead
**Reviewed by:** Sandra Hoffmann (CTO), Dr. Claudia Berger (FinSecure Bank AG)
**Status:** Under Review
**Classification:** Confidential -- TechVision / FinSecure Bank AG

---

## 1. Purpose

This document provides a comprehensive mapping of applicable regulatory requirements to the technical and organizational measures implemented in the FinSecure Portal project. It serves as an auditable reference for FinSecure Bank AG's internal compliance team and external auditors.

The matrix covers BaFin MaRisk (Minimum Requirements for Risk Management), PSD2 (Payment Services Directive 2), GDPR (General Data Protection Regulation), and supplementary guidance from BSI (Federal Office for Information Security). This document accompanies the Commercial Proposal (doc_021) and should be read in conjunction with it.

## 2. BaFin MaRisk -- AT 7.2: IT Operations

### 2.1 Monitoring and Capacity Management (AT 7.2 Tz. 1-3)

**Requirement:** IT systems must be monitored continuously. Capacity planning must ensure systems can handle expected and peak loads.

**Implementation:**

- **Infrastructure Monitoring:** Azure Monitor collects metrics from all platform components (AKS, PostgreSQL, Redis, Elasticsearch) at 1-minute intervals. Retention period: 90 days for metrics, 2 years for logs.
- **Application Performance Monitoring:** Application Insights provides distributed tracing, dependency mapping, and performance counters for both frontend and backend services. Custom availability tests run every 5 minutes from three Azure regions.
- **Capacity Alerts:** Automated alerts trigger when CPU utilization exceeds 70% (warning) or 85% (critical), when memory usage exceeds 80%, when database connection pools exceed 75% utilization, or when disk usage exceeds 70%.
- **Capacity Planning:** Monthly capacity review meetings analyze growth trends and adjust resource allocations. Azure Advisor recommendations are reviewed weekly.
- **Dashboards:** Dedicated Grafana dashboards for operations team showing real-time system health, SLA compliance, and capacity metrics. Access restricted to authorized operations personnel.

### 2.2 Change Management (AT 7.2 Tz. 4-6)

**Requirement:** Changes to IT systems must follow a structured process with appropriate testing and approval.

**Implementation:**

- **Change Process:** All changes follow a four-stage process: Request, Review, Test, Deploy. Changes are classified as Standard (pre-approved, low risk), Normal (requires CAB approval), or Emergency (expedited approval with post-implementation review).
- **Code Review:** All code changes require at least one peer review via pull request before merging. Critical components (authentication, encryption, payment processing) require two reviews including a senior developer.
- **Testing Pipeline:** Automated CI/CD pipeline executes unit tests (minimum 80% code coverage), integration tests, OWASP ZAP security scan, and performance regression tests before any deployment.
- **Deployment:** Blue-green deployments on AKS ensure zero-downtime releases. Automatic rollback triggers if error rates exceed 1% or response times exceed 2x baseline within 15 minutes of deployment.
- **Change Log:** All changes are recorded in an immutable audit trail including the change description, requester, approver, timestamp, and deployment artifacts.

### 2.3 Incident Response (AT 7.2 Tz. 7-9)

**Requirement:** Institutions must have documented procedures for handling IT incidents, including escalation paths and communication protocols.

**Implementation:**

- **Incident Classification:** Four severity levels: Critical (complete service outage or data breach), High (partial service degradation affecting >10% of users), Medium (isolated issues affecting individual features), Low (cosmetic issues or minor bugs).
- **Response Times:** Critical: 30-minute response, 4-hour resolution target. High: 2-hour response, 8-hour resolution target. Medium: 8-hour response (business hours), 3-business-day resolution. Low: next business day response.
- **On-Call Rotation:** 24/7 on-call rotation with PagerDuty integration. Primary and secondary on-call engineers. Escalation to TechVision management after 2 hours for Critical incidents.
- **Post-Incident Review:** Blameless post-mortem within 5 business days for all Critical and High severity incidents. Findings documented and shared with FinSecure Bank AG. Corrective actions tracked to completion.
- **Communication:** Dedicated status page for FinSecure Bank AG operations team. Automated incident notifications via email and SMS for Critical events. Monthly incident summary report.

## 3. BaFin MaRisk -- AT 4.3.1: Information Security

### 3.1 Encryption (AT 4.3.1 Tz. 2)

**Requirement:** Sensitive data must be protected through appropriate cryptographic measures.

**Implementation:**

- **Data at Rest:** AES-256 encryption for all data stores. PostgreSQL uses Transparent Data Encryption (TDE) via Azure. Redis uses Azure-managed encryption. Elasticsearch encryption via Azure Managed Disk encryption. Azure Key Vault (Premium tier, HSM-backed) manages all encryption keys.
- **Data in Transit:** TLS 1.3 enforced for all external communications (customer browser to portal). TLS 1.2 minimum for internal service-to-service communication within the AKS cluster. HSTS (HTTP Strict Transport Security) headers with 1-year max-age and includeSubDomains.
- **Key Rotation:** Encryption keys rotated every 12 months. Key rotation is automated and does not require downtime. Previous keys retained for decryption of archived data.
- **Certificate Management:** Azure Key Vault manages all TLS certificates. Automated renewal via Let's Encrypt for public-facing endpoints. Internal certificates issued by Azure-managed CA.

### 3.2 Access Control (AT 4.3.1 Tz. 3-4)

**Requirement:** Access to IT systems must follow the principle of least privilege with appropriate authentication and authorization.

**Implementation:**

- **Customer Authentication:** Azure AD B2C with PSD2-compliant Strong Customer Authentication (see Section 4). Session timeout: 15 minutes of inactivity (configurable per customer segment).
- **Administrative Access:** Azure AD with Conditional Access policies. Multi-factor authentication required for all administrative access. Privileged Identity Management (PIM) for just-in-time elevated access with 4-hour maximum duration.
- **Role-Based Access Control:** Seven defined roles for bank staff (Branch Advisor, Relationship Manager, Operations, Compliance, IT Admin, Security, Auditor). Each role has granular permissions mapped to API endpoints and data scopes.
- **Service Account Management:** All service accounts use managed identities where possible. Where service principals are required, credentials are stored in Key Vault with automated rotation every 90 days.
- **Access Reviews:** Quarterly access reviews for all administrative accounts. Annual review of all role definitions and permission mappings. Automated deprovisioning for inactive accounts after 90 days.

### 3.3 Audit Logging (AT 4.3.1 Tz. 5)

**Requirement:** Security-relevant events must be logged and retained for audit purposes.

**Implementation:**

- **Events Logged:** Authentication events (login, logout, failed attempts, MFA challenges), authorization decisions (access granted, access denied), data access (read, create, update, delete for sensitive resources), administrative actions (configuration changes, user management), system events (deployments, restarts, scaling events).
- **Log Format:** Structured JSON format with ISO 8601 timestamps, correlation IDs for request tracing, actor identification (user ID, IP address, device fingerprint), and event classification.
- **Immutability:** Logs are written to Azure Immutable Blob Storage (WORM -- Write Once Read Many) with a legal hold policy. Logs cannot be modified or deleted, even by administrators.
- **Retention:** 10-year retention period for all audit logs as per BaFin requirements. Hot storage (searchable) for 2 years, cold storage for remaining 8 years. Automated lifecycle management policies handle tier transitions.
- **Access to Logs:** Read access restricted to Security and Compliance roles. Audit log access itself is logged (meta-auditing). FinSecure Bank AG's internal audit team receives direct read access to the Log Analytics workspace.

## 4. PSD2 Strong Customer Authentication

### 4.1 Two-Factor Authentication Implementation

**Requirement:** PSD2 Article 97 requires Strong Customer Authentication (SCA) for accessing payment accounts online, initiating electronic payment transactions, and any action through a remote channel that may imply a risk of payment fraud.

**Implementation:**

- **Knowledge Factor:** Customer password (minimum 12 characters, complexity requirements, bcrypt hashing with cost factor 12, breach detection via HaveIBeenPwned API).
- **Possession Factor -- Option A (TOTP):** Time-based One-Time Password using RFC 6238. Supported authenticator apps: Google Authenticator, Microsoft Authenticator, Authy. QR code enrollment with backup recovery codes (10 single-use codes, stored as bcrypt hashes).
- **Possession Factor -- Option B (FIDO2):** WebAuthn-based hardware security key or platform authenticator (Touch ID, Windows Hello). Supports USB, NFC, and Bluetooth transports. Stored as public key credentials in Azure AD B2C.
- **Risk-Based Step-Up:** Low-risk actions (balance check, transaction history viewing) require standard SCA at login only. High-risk actions (transfers exceeding EUR 500, new payee registration, personal data changes) trigger additional SCA challenge using dynamic linking per PSD2 Article 97(2).
- **Session Binding:** SCA sessions are bound to the client device via a device fingerprint and IP address. Session tokens are signed JWTs with 15-minute expiry, refreshable up to 4 hours from initial authentication.

### 4.2 Transaction Monitoring

- **Real-time fraud detection:** Rule-based engine evaluating transaction amount, frequency, geographic patterns, and device anomalies.
- **Dynamic linking:** High-value transactions display the amount and payee in the SCA challenge, ensuring the customer explicitly authorizes the specific transaction.
- **Fallback procedures:** If primary SCA method is unavailable (lost phone, broken security key), the customer can authenticate via a fallback channel (SMS OTP to registered mobile number) with additional identity verification.

## 5. Data Residency and GDPR

### 5.1 Data Residency

**Requirement:** All customer data must remain within the European Union.

**Implementation:**

- **Primary Region:** Azure West Europe (Netherlands). All compute, storage, and database resources deployed exclusively in this region.
- **Disaster Recovery Region:** Azure North Europe (Ireland). Geo-replicated data for business continuity purposes only. Both regions are within the EU.
- **Data Flow Controls:** Azure Policy enforcements prevent resource deployment outside approved EU regions. Network egress rules block data transfers to non-EU endpoints.
- **Sub-Processors:** Azure (Microsoft Ireland Operations Limited) serves as the primary sub-processor. Nango (EU-based) is used for OAuth token management in the internal TechVision platform, but is not involved in processing FinSecure Bank AG customer data. All sub-processors are documented in the Data Processing Agreement.

### 5.2 GDPR Implementation

- **Data Minimization:** Only data necessary for portal functionality is collected. No tracking cookies beyond essential session cookies. Analytics use privacy-preserving, aggregated metrics only.
- **Right to Erasure:** Automated data deletion pipeline triggered by customer request. Audit logs referencing the customer are pseudonymized (customer ID replaced with hash) but not deleted, as required by retention regulations.
- **Data Portability:** Customer data exportable in machine-readable JSON format via a self-service portal function.
- **Privacy Impact Assessment:** Completed and documented prior to development start. Filed with FinSecure Bank AG's Data Protection Officer.

## 6. Audit Trail and Retention

- **Immutable Audit Log:** All security-relevant events written to tamper-proof storage (Azure Immutable Blob Storage). Integrity verification via SHA-256 hash chains.
- **Retention Period:** 10 years for financial transaction records and audit logs, per German commercial law (HGB Section 257) and BaFin requirements. 6 years for general business correspondence. Automated lifecycle policies enforce retention and deletion.
- **Audit Access:** FinSecure Bank AG's internal audit team and external auditors (appointed by BaFin) receive read-only access to the complete audit trail. Access is provisioned through a dedicated audit portal with its own authentication and audit logging.

## 7. Security Testing

### 7.1 Penetration Testing

- **Annual External Penetration Test:** Conducted by an independent, BSI-certified security firm (to be mutually agreed upon by TechVision and FinSecure Bank AG). Scope includes web application, APIs, infrastructure, and social engineering vectors.
- **Findings Management:** All findings classified using CVSS 3.1 scoring. Critical findings (CVSS >= 9.0) must be remediated within 48 hours. High findings (CVSS 7.0-8.9) within 2 weeks. Medium findings (CVSS 4.0-6.9) within 30 days. Low findings tracked and addressed in next regular release.
- **Re-Testing:** Failed remediations are re-tested by the penetration testing firm at no additional cost within the engagement.

### 7.2 Continuous Security Scanning

- **SAST (Static Application Security Testing):** SonarQube integrated into CI/CD pipeline. Zero critical or high findings required for deployment approval.
- **DAST (Dynamic Application Security Testing):** OWASP ZAP automated scans run against staging environment after every deployment. Weekly scheduled comprehensive scans.
- **Dependency Scanning:** Snyk monitors all third-party dependencies for known vulnerabilities. Automated pull requests for security patches. Critical CVEs block deployment pipeline.
- **Container Scanning:** Azure Defender for Containers scans all container images in the registry. Images with critical vulnerabilities are quarantined and cannot be deployed.
- **Infrastructure Scanning:** Azure Security Center (Defender for Cloud) continuously assesses infrastructure configuration against CIS benchmarks and BaFin-specific policies.

## 8. Third-Party Risk Management

### 8.1 Azure as Sub-Processor

- **Contractual Framework:** Microsoft Standard Contractual Clauses (SCCs) and Data Processing Agreement in place. Azure is ISO 27001, SOC 2 Type II, and C5 (BSI Cloud Computing Compliance Criteria Catalogue) certified.
- **Shared Responsibility:** Infrastructure security managed by Microsoft. Application security, data classification, and access management managed by TechVision.
- **Exit Strategy:** Data export procedures documented and tested. All data can be migrated to an alternative cloud provider within 90 days if required.

### 8.2 Open Source Components

- **License Compliance:** All open source dependencies verified for license compatibility (MIT, Apache 2.0, BSD approved; GPL reviewed case-by-case). SBOM (Software Bill of Materials) maintained and updated with each release.
- **Vulnerability Management:** Automated monitoring via Snyk with daily scans. Quarterly manual review of all dependencies with transitive dependency analysis.

## 9. Compliance Validation Schedule

| Activity | Frequency | Responsible | Next Scheduled |
|---|---|---|---|
| Internal security review | Monthly | Tobias Fischer | Oct 2025 |
| External penetration test | Annually | Independent firm | Mar 2026 (pre go-live) |
| Access rights review | Quarterly | TechVision + FinSecure Bank AG | Jan 2026 |
| Disaster recovery test | Bi-annually | Operations team | Mar 2026 |
| Compliance audit (BaFin) | Annually | FinSecure Bank AG audit team | Per BaFin schedule |
| GDPR assessment review | Annually | Data Protection Officers | Sep 2026 |

---

*This compliance matrix is a living document and will be updated throughout the project lifecycle. For questions or audit requests, contact Tobias Fischer (t.fischer@techvision.de). This document has been prepared in alignment with the security framework also applied in the Projekt Aurora engagement (doc_020, Section 5).*
