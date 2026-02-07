---
doc_id: doc_003
title: "Data Protection & GDPR Compliance Guidelines"
author: Tobias Fischer
source_type: notion
---

# Data Protection & GDPR Compliance Guidelines

**Effective Date:** January 1, 2025
**Version:** 2.1
**Classification:** Internal
**Approved by:** Dr. Martin Schreiber, CEO

## 1. Introduction

TechVision GmbH is committed to protecting the personal data of its employees, clients, and partners in full compliance with the EU General Data Protection Regulation (GDPR / Datenschutz-Grundverordnung, DSGVO) and the German Federal Data Protection Act (Bundesdatenschutzgesetz, BDSG).

This document provides practical guidelines for all TechVision employees on how to handle personal data responsibly. It supplements, but does not replace, the specific contractual obligations we have toward our clients. Every employee who processes personal data in the course of their work must be familiar with these guidelines.

For technical and organizational measures related to data protection, please also review the *Information Security Policy* (doc_002).

## 2. Data Protection Officer (DPO)

TechVision has appointed a Data Protection Officer in accordance with Art. 37 GDPR:

**Tobias Fischer**
Email: t.fischer@techvision-gmbh.de
Phone: +49 89 1234 5678
Office: Munich HQ, Room 4.12

The DPO is your first point of contact for all data protection questions, concerns, and incidents. The DPO operates independently and reports directly to the CEO, Dr. Martin Schreiber.

## 3. Core GDPR Principles

All personal data processing at TechVision must comply with the following principles (Art. 5 GDPR):

1. **Lawfulness, fairness, and transparency:** We process personal data only when we have a lawful basis (e.g., contract performance, legitimate interest, consent) and inform data subjects about how their data is used.
2. **Purpose limitation:** Data is collected for specified, explicit, and legitimate purposes and not further processed in a manner incompatible with those purposes.
3. **Data minimization:** We collect and process only the minimum amount of personal data necessary for the intended purpose.
4. **Accuracy:** We take reasonable steps to ensure personal data is accurate and kept up to date.
5. **Storage limitation:** Personal data is retained only as long as necessary for the processing purpose or as required by law. Our data retention schedule is maintained in Notion under the "Compliance" workspace.
6. **Integrity and confidentiality:** Personal data is protected against unauthorized or unlawful processing and against accidental loss, destruction, or damage through appropriate technical and organizational measures.

## 4. Lawful Bases for Processing

Before processing personal data, you must identify the applicable lawful basis. The most common bases at TechVision are:

- **Contract performance (Art. 6(1)(b)):** Processing employee data for payroll, benefits administration, and employment management; processing client contact data for project delivery.
- **Legal obligation (Art. 6(1)(c)):** Tax records retention, social security reporting, and compliance with German commercial law (HGB).
- **Legitimate interest (Art. 6(1)(f)):** IT security monitoring, fraud prevention, business analytics on aggregated data. A balancing test must be documented before relying on legitimate interest.
- **Consent (Art. 6(1)(a)):** Used sparingly and only when no other basis applies (e.g., marketing newsletters, employee photos on the website). Consent must be freely given, specific, informed, and revocable at any time.

When in doubt about the correct lawful basis, consult the DPO before initiating processing.

## 5. Records of Processing Activities (Verarbeitungsverzeichnis)

TechVision maintains a comprehensive Record of Processing Activities (RoPA) as required under Art. 30 GDPR. This register is maintained by the DPO in a dedicated Notion database and includes:

- Name and purpose of each processing activity
- Categories of data subjects and personal data
- Recipients of personal data (internal and external)
- Transfers to third countries
- Retention periods
- Technical and organizational security measures

**Your responsibility:** If you introduce a new processing activity (e.g., a new tool that collects personal data, a new client project involving PII, a new analytics process), you must notify the DPO so the register can be updated. Submit a processing activity notification via the #data-protection Slack channel or email the DPO directly.

## 6. Data Subject Rights

Under GDPR, individuals have the following rights regarding their personal data. TechVision must be able to respond to such requests within 30 days.

| Right | Description | GDPR Article |
|-------|-------------|-------------|
| Right of access | Data subjects may request confirmation of whether their data is processed and obtain a copy | Art. 15 |
| Right to rectification | Data subjects may request correction of inaccurate data | Art. 16 |
| Right to erasure | Data subjects may request deletion of their data under certain conditions | Art. 17 |
| Right to restriction | Data subjects may request limitation of processing | Art. 18 |
| Right to data portability | Data subjects may receive their data in a structured, machine-readable format | Art. 20 |
| Right to object | Data subjects may object to processing based on legitimate interest | Art. 21 |

**Handling process:**

1. Any data subject request received by a TechVision employee must be forwarded to the DPO (t.fischer@techvision-gmbh.de) immediately, and no later than 24 hours after receipt.
2. Do not attempt to fulfill or deny a request on your own.
3. The DPO will verify the identity of the requester, determine the scope of the request, coordinate with relevant departments, and issue a formal response.
4. All requests and responses are logged in the compliance tracker.

## 7. Data Protection Impact Assessments (DPIA)

A Data Protection Impact Assessment (Datenschutz-Folgenabschatzung) is required under Art. 35 GDPR when processing is likely to result in a high risk to the rights and freedoms of individuals. This includes:

- Systematic and extensive profiling with significant effects
- Large-scale processing of special categories of data (health, biometric, political opinions)
- Systematic monitoring of publicly accessible areas
- Use of new technologies that may pose elevated privacy risks (e.g., AI/ML models trained on personal data)

**Process:** If your project may require a DPIA, contact the DPO early in the planning phase. The DPO will assess the need for a formal DPIA and guide you through the process, which typically takes 2-4 weeks.

## 8. Sub-Processor Management

When TechVision engages sub-processors (Unterauftragsverarbeiter) to process personal data on our behalf or on behalf of our clients, the following steps are required:

1. **Prior approval:** The DPO must approve the engagement of any new sub-processor before personal data is shared.
2. **Data Processing Agreement (AVV):** A written Auftragsverarbeitungsvertrag compliant with Art. 28 GDPR must be executed with each sub-processor.
3. **Security assessment:** Sub-processors must demonstrate adequate security measures. SOC 2 Type II, ISO 27001, or equivalent certification is preferred. See also Section 12 of the *Information Security Policy* (doc_002).
4. **Register:** All active sub-processors are listed in the sub-processor register maintained by the DPO. The current list includes cloud infrastructure providers (AWS, Azure), SaaS tools (Google Workspace, Slack, Notion, Personio), and our embedded analytics provider.
5. **Client notification:** For client data, sub-processor changes must be communicated to affected clients in accordance with our Data Processing Agreements. Most client contracts require 30 days advance notice.

## 9. Data Breach Notification

In the event of a personal data breach (Datenschutzverletzung), TechVision is legally obligated to:

1. **Notify the supervisory authority** (Bayerisches Landesamt fur Datenschutzaufsicht, BayLDA) within **72 hours** of becoming aware of the breach, unless the breach is unlikely to result in a risk to the rights and freedoms of individuals (Art. 33 GDPR).
2. **Notify affected data subjects** without undue delay if the breach is likely to result in a high risk to their rights and freedoms (Art. 34 GDPR).

**Your responsibility:** If you become aware of or suspect a personal data breach, report it immediately to the DPO (t.fischer@techvision-gmbh.de) and follow the procedures outlined in the *Security Incident Response Plan* (doc_008). The 72-hour clock starts when TechVision becomes aware of the breach, so timely internal reporting is critical. As stated in the *Information Security Policy* (doc_002), all incidents must be reported within 1 hour of discovery.

**The DPO will:**
- Assess the severity and scope of the breach
- Determine notification obligations
- Prepare and submit the notification to BayLDA if required
- Coordinate communication to affected data subjects
- Document the breach and response in the breach register

## 10. Cross-Border Data Transfers

Transfer of personal data outside the European Economic Area (EEA) is only permitted when an adequate level of data protection is ensured. TechVision relies on the following mechanisms:

- **EU adequacy decisions:** Transfers to countries with an EU adequacy decision (e.g., Switzerland, UK, Japan, South Korea) are permitted without additional safeguards.
- **EU-US Data Privacy Framework:** For US-based processors certified under the EU-US Data Privacy Framework, transfers are permitted based on the adequacy decision of July 2023.
- **Standard Contractual Clauses (SCCs):** Where no adequacy decision exists, TechVision uses the European Commission's Standard Contractual Clauses (2021 version) supplemented by a Transfer Impact Assessment (TIA).
- **Binding Corporate Rules:** Not currently applicable at TechVision.

Before initiating a new data transfer to a country outside the EEA, contact the DPO to ensure appropriate safeguards are in place.

## 11. Employee Data Protection

TechVision processes employee personal data for employment administration, payroll, benefits, performance management, and IT security purposes. Detailed information is provided in the employee privacy notice issued with your employment contract.

Key points:

- Employee data is stored in Personio (HR system) and Google Workspace.
- Access to employee data is restricted to HR and authorized management on a need-to-know basis.
- Employee monitoring beyond standard IT security logging is not conducted. Any future monitoring measures would require Works Council consultation (Betriebsrat, if established) and DPO approval.
- Employee data is retained for the duration of employment plus statutory retention periods (typically 6-10 years depending on the data category).

## 12. Training and Awareness

All employees receive data protection training as part of their onboarding process (see *New Employee Onboarding Checklist*, doc_005). Annual refresher training is conducted alongside the security awareness training program described in the *Information Security Policy* (doc_002).

Employees in roles with elevated data processing responsibilities (HR, client-facing consultants, engineering teams handling production data) receive additional targeted training.

## 13. Compliance and Enforcement

Violations of these guidelines may result in disciplinary action. Serious breaches that constitute violations of GDPR or BDSG may also result in personal liability and regulatory fines.

TechVision encourages employees to report data protection concerns without fear of retaliation. Our whistleblower protection policy, described in the *Code of Conduct* (doc_004), applies equally to data protection matters.

## 14. Contact

For all data protection inquiries:

**Tobias Fischer, Data Protection Officer**
Email: t.fischer@techvision-gmbh.de
Phone: +49 89 1234 5678
Slack: #data-protection

---

*This document is maintained by Tobias Fischer, Data Protection Officer. Version 2.1, January 2025. Next scheduled review: January 2026.*
