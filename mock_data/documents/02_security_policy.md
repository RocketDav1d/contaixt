---
doc_id: doc_002
title: "TechVision Information Security Policy"
author: Tobias Fischer
source_type: notion
---

# TechVision Information Security Policy

**Effective Date:** January 1, 2025
**Version:** 3.2
**Classification:** Internal
**Approved by:** Dr. Martin Schreiber, CEO & Sandra Hoffmann, CTO

## 1. Purpose and Scope

This policy establishes the information security requirements for all employees, contractors, and temporary staff of TechVision GmbH. It applies to all company-owned and personally-owned devices used to access TechVision systems, all data processed on behalf of the company and its clients, and all physical and digital workspaces.

Non-compliance with this policy may result in disciplinary action up to and including termination. Willful violations that result in data breaches may also have legal consequences under German and EU law.

All employees are required to review this policy during onboarding (see *New Employee Onboarding Checklist*, doc_005) and again annually as part of the security awareness training program.

## 2. Information Security Principles

TechVision's information security program is guided by the following principles:

- **Confidentiality:** Information is accessible only to those authorized to access it.
- **Integrity:** Information and processing methods are accurate and complete.
- **Availability:** Authorized users have access to information and associated assets when required.
- **Least privilege:** Users are granted the minimum level of access necessary to perform their duties.
- **Defense in depth:** Multiple layers of security controls protect against the failure of any single measure.

## 3. Data Classification

All information handled by TechVision must be classified according to the following scheme:

| Classification | Description | Examples | Handling Requirements |
|---------------|-------------|----------|----------------------|
| **Public** | Information intended for public disclosure | Marketing materials, blog posts, open-source code | No restrictions on sharing |
| **Internal** | General business information not intended for external parties | Internal meeting notes, org charts, process docs | Share only within TechVision; do not post publicly |
| **Confidential** | Sensitive business or client information | Client project data, financial reports, employee records, contracts | Encrypted in transit and at rest; access restricted to relevant project team |
| **Restricted** | Highly sensitive information whose disclosure would cause severe harm | Production credentials, cryptographic keys, security audit results, PII datasets | Encrypted at all times; access logged and audited; shared only on need-to-know basis |

When in doubt about classification, treat information as Confidential and consult with your manager or the Security Officer.

## 4. Password and Authentication Requirements

### 4.1 Password Policy

- **Minimum length:** 16 characters
- **Complexity:** Passwords must contain a mix of uppercase letters, lowercase letters, numbers, and special characters. Passphrases (4+ random words) of sufficient length are also acceptable.
- **Uniqueness:** Each account must have a unique password. Password reuse across services is strictly prohibited.
- **Password manager:** Use of 1Password (our corporate password manager) is mandatory for all employees. Your 1Password account will be provisioned during onboarding by Markus Lang's DevOps team.
- **Sharing:** Never share passwords via email, Slack, or any unencrypted channel. Use 1Password's secure sharing feature for legitimate credential sharing within teams.
- **Rotation:** Passwords must be changed immediately if a compromise is suspected. Routine rotation is not required when using strong, unique passwords managed via 1Password.

### 4.2 Two-Factor Authentication (2FA)

Two-factor authentication is required for all TechVision systems without exception:

- **Corporate accounts:** Google Workspace, Slack, Notion, GitHub, Jira, AWS, Azure, Personio
- **Preferred method:** TOTP via 1Password or a dedicated authenticator app (e.g., Google Authenticator)
- **Hardware security keys:** Required for all employees with production system access. TechVision issues YubiKey 5 NFC keys to engineering and DevOps staff. If you lose your hardware key, report it immediately to Tobias Fischer and Markus Lang.
- **SMS-based 2FA:** Not permitted as a primary factor due to SIM-swapping vulnerabilities. Only acceptable as a backup recovery method where no alternative exists.

### 4.3 Single Sign-On (SSO)

Where available, all SaaS applications must be accessed via our Google Workspace SSO integration. Contact Markus Lang (m.lang@techvision-gmbh.de) to request SSO configuration for new tools.

## 5. Device Security

### 5.1 Company-Issued Devices

All company-issued laptops (MacBook Pro or ThinkPad X1 Carbon) are managed through our MDM solution (Jamf for macOS, Microsoft Intune for Windows). The following settings are enforced:

- **Full disk encryption:** FileVault (macOS) or BitLocker (Windows) must be enabled at all times. This is configured automatically via MDM.
- **Automatic lock:** Screen lock activates after 5 minutes of inactivity. This setting cannot be overridden.
- **Firewall:** Host-based firewall must be enabled.
- **Automatic updates:** OS and security updates are applied automatically. Critical patches are pushed within 48 hours of release.
- **Antivirus/EDR:** CrowdStrike Falcon is installed on all endpoints and must remain active.

### 5.2 Personal Devices (BYOD)

Personal devices may be used to access TechVision email and Slack only. Access to client data, source code repositories, or production systems from personal devices is prohibited. Personal devices must meet the following minimum requirements:

- Current, supported operating system with automatic updates enabled
- Screen lock with biometric or PIN authentication
- Full disk encryption enabled
- No jailbroken or rooted devices

### 5.3 Mobile Devices

Company email on mobile devices is permitted via the Gmail app with Google Workspace managed account settings. The device must have a screen lock (biometric or 6-digit PIN minimum) and device encryption enabled.

## 6. Network Security

### 6.1 VPN

A VPN connection is mandatory when accessing TechVision systems from outside the office network. We use Tailscale for our mesh VPN. Your Tailscale account is provisioned during onboarding.

- All remote work must be conducted over VPN (see *Remote Work & Home Office Policy*, doc_007).
- Public Wi-Fi usage is strongly discouraged. If you must use public Wi-Fi, ensure the VPN is connected before accessing any TechVision resources.

### 6.2 Office Network

The Munich office network is segmented into the following VLANs:

- **Corporate:** General employee access (email, web, SaaS tools)
- **Engineering:** Development and staging environments
- **Guest:** Isolated network for visitors (no access to internal resources)

Network access control (802.1X) is enforced on all wired and wireless connections.

## 7. Acceptable Use

### 7.1 Permitted Use

TechVision systems and equipment are provided primarily for business purposes. Limited personal use is acceptable provided it:

- Does not interfere with your work or the work of others
- Does not violate any laws or this policy
- Does not consume excessive bandwidth or storage
- Does not expose TechVision to security risks

### 7.2 Prohibited Activities

The following activities are strictly prohibited on TechVision systems:

- Installing unauthorized software or browser extensions without IT approval
- Disabling security controls (encryption, firewall, antivirus, MDM)
- Accessing, downloading, or distributing illegal content
- Using TechVision resources for cryptocurrency mining
- Connecting unauthorized hardware to the corporate network
- Storing Confidential or Restricted data on personal cloud storage (e.g., personal Dropbox, Google Drive)
- Forwarding company email to personal email accounts
- Using unauthorized AI tools to process client data (approved AI tools are listed in the #engineering-tools Slack channel)

## 8. Email and Communication Security

- Be vigilant against phishing emails. Report suspicious emails by forwarding them to security@techvision-gmbh.de or using the "Report Phishing" button in Gmail.
- Do not click links or download attachments from unknown senders.
- Client-sensitive information should be shared via secure channels (encrypted email, secure file transfer) rather than standard email.
- TechVision conducts simulated phishing exercises quarterly. Employees who repeatedly fail phishing tests will be required to complete additional training.

## 9. Physical Security

- Office access is controlled via electronic key cards. Do not share your key card or hold the door for unidentified individuals.
- Visitors must be registered at reception and accompanied by a TechVision employee at all times.
- Laptops must be secured with a cable lock when left unattended in the office, or stored in a locked cabinet.
- Clean desk policy: At the end of each workday, ensure that Confidential and Restricted documents are secured. Screens must be locked when leaving your workstation, even briefly.

## 10. Incident Reporting

**All security incidents, suspected incidents, and near-misses must be reported within 1 hour of discovery.**

Report incidents via any of the following channels:

1. **Email:** t.fischer@techvision-gmbh.de (Security Officer)
2. **Slack:** #security-incidents channel (for non-confidential incidents)
3. **Phone:** +49 89 1234 5678 (Tobias Fischer, available 24/7 for P1/P2 incidents)

Examples of reportable events:

- Lost or stolen device
- Suspected phishing email that was clicked
- Unauthorized access to systems or data
- Accidental disclosure of Confidential or Restricted information
- Suspected malware infection
- Unusual system behavior that may indicate compromise

For the full incident response process, including severity classification and escalation procedures, refer to the *Security Incident Response Plan* (doc_008).

## 11. Security Awareness Training

All employees must complete the annual security awareness training program. This includes:

- **Initial training:** Completed during the first week of employment as part of onboarding (see doc_005). Delivered by Tobias Fischer or a designated security team member.
- **Annual refresher:** A 90-minute session conducted each January covering the latest threats, policy updates, and lessons learned from incidents.
- **Role-specific training:** Engineering staff receive additional training on secure coding practices, dependency management, and secrets handling. This is coordinated by Sandra Hoffmann (CTO).
- **Completion tracking:** Training completion is tracked in Personio. Employees who do not complete mandatory training by the deadline will have their system access restricted until training is completed.

## 12. Third-Party and Vendor Security

Before engaging a new SaaS vendor or third-party service that will process TechVision or client data:

1. Submit a vendor security assessment request to Tobias Fischer.
2. The vendor must complete our security questionnaire.
3. Vendors processing Confidential or Restricted data must demonstrate SOC 2 Type II compliance or equivalent certification.
4. Data Processing Agreements (Auftragsverarbeitungsvertrag, AVV) must be executed before data is shared. See the *Data Protection & GDPR Compliance Guidelines* (doc_003) for details.

## 13. Software Development Security

Engineering teams must adhere to the following secure development practices:

- All code must be reviewed by at least one other engineer before merging (enforced via GitHub branch protection rules).
- Secrets and credentials must never be committed to source code repositories. Use environment variables or a secrets management solution (AWS Secrets Manager or Azure Key Vault).
- Dependency scanning via Dependabot is enabled on all repositories. Critical vulnerabilities must be remediated within 7 days.
- Container images must be scanned before deployment. Only approved base images from our internal registry may be used.
- Production deployments follow the four-eyes principle and require approval from Markus Lang or Sandra Hoffmann.

## 14. Policy Review

This policy is reviewed and updated annually by the Security Officer in consultation with the CTO and CEO. Material changes are communicated to all employees via email and the #announcements Slack channel.

## 15. Contact

For questions about this policy or to report a security concern:

- **Security Officer:** Tobias Fischer, t.fischer@techvision-gmbh.de, +49 89 1234 5678
- **CTO:** Sandra Hoffmann, s.hoffmann@techvision-gmbh.de
- **DevOps Lead:** Markus Lang, m.lang@techvision-gmbh.de

---

*This document is maintained by Tobias Fischer, Information Security Officer. Version 3.2, March 2025. Next scheduled review: January 2026.*
