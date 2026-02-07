# Mock Data: TechVision GmbH

Realistic mock data for demoing and testing the Contaixt GraphRAG platform.

## Company Profile

**TechVision GmbH** is a fictional German IT/software consulting firm (~80 employees) based in Munich. They specialize in cloud migration, data engineering, and custom software development for clients in manufacturing, finance, and healthcare.

## Key People

| Name | Role | Email |
|------|------|-------|
| Dr. Martin Schreiber | CEO / Geschäftsführer | m.schreiber@techvision-gmbh.de |
| Sandra Hoffmann | CTO | s.hoffmann@techvision-gmbh.de |
| Thomas Krüger | Head of Sales | t.krueger@techvision-gmbh.de |
| Lisa Weber | Project Manager | l.weber@techvision-gmbh.de |
| Felix Braun | Senior Developer | f.braun@techvision-gmbh.de |
| Anna Richter | Data Engineer | a.richter@techvision-gmbh.de |
| Markus Lang | DevOps Lead | m.lang@techvision-gmbh.de |
| Julia Meier | HR Manager | j.meier@techvision-gmbh.de |
| Tobias Fischer | Security Officer | t.fischer@techvision-gmbh.de |
| Katharina Schmidt | UX Designer | k.schmidt@techvision-gmbh.de |
| Daniel Wolff | Junior Developer | d.wolff@techvision-gmbh.de |
| Petra Neumann | Finance / Controlling | p.neumann@techvision-gmbh.de |

## Key Clients

| Company | Contact | Industry |
|---------|---------|----------|
| Müller Maschinenbau AG | Hans Müller, CEO | Manufacturing |
| FinSecure Bank AG | Dr. Claudia Berger | Finance |
| MedTech Solutions GmbH | Robert Engel | Healthcare |
| AutoParts24 GmbH | Stefan Vogel | Automotive |

## Key Projects

- **Projekt Aurora** — Cloud migration + data platform for Müller Maschinenbau (€450k budget)
- **FinSecure Portal** — Customer-facing banking portal for FinSecure Bank (€280k budget)
- **MedTech Analytics** — Analytics dashboard for MedTech Solutions
- **Internal: Platform Modernization** — Migrating internal tools to Kubernetes

## Data Structure

- `emails/` — 25 email threads as .md files (German with Denglisch)
- `documents/` — 30 documents as .md files (English)
- `seed.py` — Script to POST all data to the Contaixt API

## Usage

```bash
# Start the platform
docker compose up

# Seed mock data (requires a workspace_id)
python mock_data/seed.py --api-url http://localhost:8000 --workspace-id <uuid>
```

## Verification Queries

After seeding, test with `POST /v1/query`:

- "Wer arbeitet an Projekt Aurora?" → Felix, Lisa, Anna, Markus, etc.
- "What is TechVision's security policy?" → Security policy document
- "What was the budget for Projekt Aurora?" → €450k from project charter
- "Who is Hans Müller?" → CEO of Müller Maschinenbau, Aurora client
