---
doc_id: doc_005
title: "New Employee Onboarding Checklist"
author: Julia Meier
source_type: notion
---

# New Employee Onboarding Checklist

**Effective Date:** January 1, 2025
**Version:** 4.0
**Maintained by:** Julia Meier, HR Manager

This checklist outlines the onboarding process for all new TechVision employees. It covers pre-boarding activities, the first day, first week, and first month. Managers and buddies should use this document alongside the new hire to ensure a smooth start.

---

## Phase 1: Pre-Boarding (Before Start Date)

The following tasks are completed by HR and IT before the new employee's first day:

### HR Tasks (Julia Meier / HR Team)
- [ ] Send signed employment contract and welcome email with start date, office address (Leopoldstra&szlig;e 120, 4th floor), and first-day instructions
- [ ] Register employee in Personio (HR system) with all personal and payroll details
- [ ] Prepare welcome folder: employee handbook (doc_001), code of conduct (doc_004), security policy (doc_002), data protection guidelines (doc_003), remote work policy (doc_007), travel & expense policy (doc_006)
- [ ] Assign an onboarding buddy from the same or adjacent team
- [ ] Notify the buddy and direct manager of the new hire's start date
- [ ] Prepare desk / workspace (for office days)

### IT Tasks (Markus Lang / DevOps Team)
- [ ] Order laptop (MacBook Pro 14" M3 Pro for engineering roles, MacBook Air M3 for non-engineering roles; ThinkPad X1 Carbon on request)
- [ ] Configure laptop via Jamf MDM with standard security profile: FileVault encryption, CrowdStrike Falcon, Tailscale VPN, automatic screen lock (5 min)
- [ ] Create Google Workspace account (firstname.lastname@techvision-gmbh.de)
- [ ] Provision 1Password account and generate initial vault with shared team passwords
- [ ] Create accounts in core tools:
  - Slack (add to #general, #announcements, team-specific channels)
  - Notion (add to company workspace and team spaces)
  - GitHub (add to techvision-gmbh organization, appropriate team)
  - Jira (add to relevant project boards)
  - Personio (employee self-service access)
- [ ] For engineering roles: Provision cloud access (AWS IAM or Azure AD) with least-privilege permissions, reviewed by Markus Lang
- [ ] Prepare YubiKey 5 NFC (for engineering and DevOps staff with production access)
- [ ] Set up Tailscale VPN profile on the new laptop

---

## Phase 2: Day 1

### Morning (09:00 - 12:00)

| Time | Activity | Responsible |
|------|----------|-------------|
| 09:00 | Welcome and office tour: reception, kitchen, meeting rooms, quiet zone, phone booths | Buddy |
| 09:30 | HR onboarding session: employment documents, Personio walkthrough, benefits enrollment (MVV pass, EGYM Wellpass, bAV pension), emergency contacts | Julia Meier |
| 10:30 | IT setup: laptop handover, account activation, 1Password setup, 2FA enrollment for all systems, YubiKey registration (if applicable) | Markus Lang's team |
| 11:30 | Buddy introduction: team overview, Slack culture, lunch spots near the office, FAQ | Buddy |

### Afternoon (13:00 - 17:00)

| Time | Activity | Responsible |
|------|----------|-------------|
| 13:00 | Lunch with buddy and team | Buddy |
| 14:00 | Manager welcome meeting: role expectations, 90-day goals, team structure, communication norms | Direct Manager |
| 15:00 | Self-guided: review employee handbook (doc_001), code of conduct (doc_004), set up Slack profile, explore Notion workspace | New Employee |
| 16:00 | End-of-day check-in with buddy: questions, comfort level, what to expect tomorrow | Buddy |

---

## Phase 3: Week 1 (Days 2-5)

### Day 2: Security and Compliance

- **Security training session with Tobias Fischer** (90 minutes, in-person or video)
  - Overview of the *Information Security Policy* (doc_002)
  - Password hygiene and 1Password best practices
  - Phishing awareness and reporting procedures
  - Device security and acceptable use
  - Data classification levels: Public, Internal, Confidential, Restricted
  - Hands-on: verify 2FA is active on all accounts, test VPN connection

- **Data protection briefing with Tobias Fischer** (60 minutes)
  - Overview of the *Data Protection & GDPR Compliance Guidelines* (doc_003)
  - Handling personal data in day-to-day work
  - Data subject rights and incident reporting
  - Sign data protection acknowledgment form

### Day 3: Tools and Workflow

- Deep dive into project management workflow: Jira boards, sprint ceremonies, definition of done
- Notion workspace orientation: where to find documentation, how to create and share pages
- GitHub workflow: branching strategy, PR review process, CI/CD pipeline overview (with Markus Lang or a senior engineer)
- For engineering roles: development environment setup, local Docker Compose configuration, access to staging environments

### Days 4-5: Team Integration

- Attend regular team meetings (stand-up, planning, or retrospective as scheduled)
- Pair programming / shadowing session with a senior team member (for engineering roles: Felix Braun is a frequent onboarding mentor)
- Review current project documentation and architecture decision records
- Begin first small task or ticket (assigned by manager, designed to be completable within 1-2 days)

---

## Phase 4: Month 1 (Weeks 2-4)

### Week 2
- [ ] Meet all direct team members in 1:1 sessions (30 min each)
- [ ] Complete first project contribution (code review, document, analysis, or deliverable)
- [ ] Manager check-in: progress on 90-day goals, blockers, feedback

### Week 3
- [ ] Meet team leads from other departments:
  - Sandra Hoffmann (CTO) -- technology strategy and engineering culture
  - Markus Lang (DevOps Lead) -- infrastructure, deployment, and monitoring
  - Tobias Fischer (Security Officer) -- security questions and compliance
  - Petra Neumann (Finance) -- expense process and travel booking
- [ ] Attend a cross-team meeting or company all-hands (held bi-weekly on Wednesdays)
- [ ] Review and understand client project context for assigned project(s)

### Week 4
- [ ] First project assignment: fully integrated into a project team with defined responsibilities
- [ ] End-of-month feedback session with manager: what's going well, what could improve, updated 90-day goals
- [ ] Buddy check-in: formal 30-minute session to close out the structured onboarding phase
- [ ] Submit feedback on the onboarding experience via the anonymous survey (link in Personio)

---

## Tool Access Summary

| Tool | Purpose | Provisioned By | Access Level |
|------|---------|---------------|-------------|
| Google Workspace | Email, Calendar, Drive | IT (Markus Lang) | Full |
| Slack | Team communication | IT | Full |
| Notion | Documentation, wiki | IT | Team workspace + company workspace |
| GitHub | Source code, CI/CD | IT | Organization member, team-specific repos |
| Jira | Project management | IT | Project-specific boards |
| 1Password | Password management | IT | Personal vault + shared team vaults |
| Personio | HR self-service | HR (Julia Meier) | Employee role |
| Tailscale | VPN | IT | Device-specific |
| AWS / Azure | Cloud infrastructure | IT (requires manager approval) | Engineering roles only, least-privilege |
| TravelPerk | Travel booking | HR / Finance | After probation (see doc_006) |

---

## Buddy Program

Every new employee is assigned an onboarding buddy for their first 4 weeks. The buddy is typically a colleague from the same or a related team who has been at TechVision for at least 6 months.

**Buddy responsibilities:**
- Be a friendly point of contact for informal questions
- Help the new hire navigate tools, processes, and team culture
- Have a brief daily check-in during Week 1 and weekly check-ins during Weeks 2-4
- Introduce the new hire to colleagues across the company
- Escalate any concerns to the manager or HR if needed

**To volunteer as a buddy:** Message Julia Meier on Slack or email j.meier@techvision-gmbh.de. Buddies receive a small thank-you gift at the end of each onboarding cycle.

---

## Onboarding Completion

The onboarding process is formally complete after 4 weeks. At this point:

1. The manager confirms that the new employee has completed all checklist items in Personio.
2. The new employee signs the security policy acknowledgment, data protection acknowledgment, and code of conduct acknowledgment.
3. The HR team closes the onboarding case.

Note: The 6-month probation period continues after onboarding completion. Performance check-ins are scheduled at months 2 and 5 (see *Employee Handbook*, doc_001, Section 7).

---

*This document is maintained by Julia Meier, HR Manager. Version 4.0, January 2025. Next scheduled review: July 2025.*
