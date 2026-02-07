---
thread_id: email_thread_024
subject: "Jahresplanung 2026 – Strategische Ziele & OKRs"
---

## Message 1

**From:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krüger <t.krueger@techvision-gmbh.de>, Petra Neumann <p.neumann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-12-15 08:00

Liebes Leadership Team,

es ist Zeit, die Jahresplanung 2026 anzugehen. Ich möchte euch vorab meine strategische Vision mitteilen, bevor wir am 20. Dezember im Offsite die Details gemeinsam erarbeiten.

**Ausgangslage 2025:**
- Umsatz: €7,5M (Plan war €7,2M — wir haben übererfüllt, hauptsächlich durch den Müller Maschinenbau Großauftrag und das MedTech-Projekt)
- Team: 38 Mitarbeiter
- NPS: 67 (Aufwärtstrend)
- Wichtigste Produktentwicklung: Contaixt GraphRAG Platform, Aurora-Projekt

**Strategische Ziele 2026:**

1. **Revenue Target: €9M** (+20% YoY)
   - Bestandskunden-Wachstum: €6M (Upselling, Expansion)
   - Neukundengeschäft: €3M (mindestens 5 neue Enterprise Clients)

2. **Team-Wachstum: 15 Neueinstellungen** (Ziel: 53 Mitarbeiter bis Jahresende)
   - 8 Engineering (inkl. 2 Data Engineers, 1 ML Engineer, 1 DevOps)
   - 3 Sales/Account Management
   - 2 Professional Services/Consulting
   - 2 Support/Customer Success

3. **Healthcare Vertical erschließen**
   - Aufbauend auf den Erfahrungen mit MedTech Solutions wollen wir den Healthcare-Bereich als eigenständiges Vertical etablieren
   - Ziel: 3 Healthcare-Kunden bis Q3 2026
   - Notwendig: ISO 27001 Zertifizierung (Tobias Fischer leitet das Projekt), DSGVO-Compliance für Gesundheitsdaten

4. **Product-Led Growth für Contaixt**
   - Die GraphRAG-Plattform ist unser Differentiator. Ich möchte, dass wir Contaixt als eigenständiges SaaS-Produkt positionieren
   - MVP einer Self-Service Version bis Q3 2026

Ich bitte euch, basierend auf diesen Zielen eure bereichsspezifischen OKRs zu formulieren. Bringt diese zum Offsite am 20.12. mit.

Beste Grüße
Martin

---

## Message 2

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Thomas Krüger <t.krueger@techvision-gmbh.de>, Petra Neumann <p.neumann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-12-16 10:30

Hallo Martin, hallo alle,

danke für die klare Zielformulierung. Hier meine OKR-Vorschläge für den Tech/Engineering-Bereich:

**OKR 1: Launch Internal AI/ML Practice by Q2 2026**
- Key Result 1: ML Engineer und 2. Data Engineer eingestellt bis Ende Q1
- Key Result 2: Internes ML-Toolkit (Model Training Pipeline, Experiment Tracking mit MLflow) produktionsreif bis Q2
- Key Result 3: Mindestens 2 Kundenprojekte nutzen die interne ML Practice bis Q2

Hintergrund: Aktuell nutzen wir hauptsächlich OpenAI APIs (Embeddings, GPT-4o-mini). Um im Healthcare-Bereich wettbewerbsfähig zu sein, brauchen wir die Fähigkeit, Custom Models zu trainieren und On-Premise zu deployen. Viele Healthcare-Kunden werden ihre Daten nicht an OpenAI senden wollen.

**OKR 2: Contaixt Platform maturity erreichen**
- Key Result 1: Multi-Tenant SaaS Architecture implementiert bis Q2
- Key Result 2: Self-Service Onboarding Flow (Signup → first query in < 10 Minuten) bis Q3
- Key Result 3: 99.9% Uptime SLA für die Plattform (aktuell messen wir das gar nicht formell)

**OKR 3: Engineering Excellence**
- Key Result 1: Test Coverage von 45% auf 80% erhöhen (aktuell ist das unser größtes Tech Debt)
- Key Result 2: CI/CD Pipeline Deployment Time unter 5 Minuten
- Key Result 3: Alle Projekte auf Kubernetes migriert (Docker Compose in Production → Hold, wie im Tech Radar beschlossen)

Zum Thema Healthcare und On-Premise: Felix hat im Tech Radar Rust für performance-kritische Services vorgeschlagen. Das könnte für On-Premise Deployments sehr relevant sein — kleine Binaries, schnelle Startup-Zeiten.

Viele Grüße
Sandra

---

## Message 3

**From:** Thomas Krüger <t.krueger@techvision-gmbh.de>
**To:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Petra Neumann <p.neumann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-12-17 09:15

Hallo zusammen,

hier meine Sales OKRs für 2026:

**OKR 1: 5 neue Enterprise Clients gewinnen**
- Key Result 1: Sales Pipeline auf €5M Gesamtwert aufbauen bis Q1 (3x Coverage für €3M Target)
- Key Result 2: Mindestens 3 Healthcare-Leads qualifiziert bis Q2
- Key Result 3: Close Rate von 25% auf 30% verbessern

Meine konkrete Pipeline-Strategie:
- **Healthcare:** Kontakte über MedTech Solutions als Referenzkunde, Teilnahme an DMEA (Digital Medical Expertise & Applications) Konferenz im April
- **Fertigung/Industrie:** Erweiterung über Müller Maschinenbau Netzwerk, Referenz-Cases nutzen (Martin, die NPS-Bewertung von 9/10 ist Gold wert!)
- **Finanzdienstleistungen:** Neues Vertical, aber GraphRAG für Compliance-Dokumentation ist ein starker Use Case

**OKR 2: Account Management professionalisieren**
- Key Result 1: Dedicated Account Manager für Top-10 Kunden ab Januar (wie im NPS Action Plan beschlossen)
- Key Result 2: Quarterly Business Reviews mit allen Enterprise-Kunden etablieren
- Key Result 3: Net Revenue Retention Rate von 110% auf 120% steigern

Für die 3 neuen Sales-Stellen: Julia, ich brauche einen Senior Account Executive (Healthcare Fokus), einen Account Manager für Bestandskunden, und einen SDR (Sales Development Representative) für Outbound. Können wir die Stellenausschreibungen im Januar live haben?

Beste Grüße
Thomas

---

## Message 4

**From:** Petra Neumann <p.neumann@techvision-gmbh.de>
**To:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krüger <t.krueger@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-12-18 14:00

Hallo zusammen,

hier die Financial Projections und der Investitionsbedarf für 2026. Ich habe basierend auf Martins Zielen und euren OKRs ein Szenario-Modell erstellt.

**Revenue Projection 2026:**
| Quartal | Bestandskunden | Neukunden | Gesamt |
|---------|---------------|-----------|--------|
| Q1      | €1.4M         | €0.2M     | €1.6M  |
| Q2      | €1.5M         | €0.5M     | €2.0M  |
| Q3      | €1.5M         | €0.8M     | €2.3M  |
| Q4      | €1.6M         | €1.5M     | €3.1M  |
| **Total** | **€6.0M**   | **€3.0M** | **€9.0M** |

**Personalkosten (15 Neueinstellungen):**
- Durchschnittliche Kosten pro Mitarbeiter (inkl. Lohnnebenkosten): €85.000/Jahr
- Gesamte zusätzliche Personalkosten 2026: ca. €850.000 (nicht alle starten am 1.1.)
- Recruiting-Kosten (Headhunter, Job Ads): ca. €120.000

**Weitere Investitionen:**
- ISO 27001 Zertifizierung: €40.000-60.000 (Berater + Audit)
- Cloud Infrastructure Scaling (K8s, Confluent Cloud): €80.000 zusätzlich YoY
- Tooling (Linear, MLflow, etc.): ca. €30.000/Jahr
- Konferenzen & Weiterbildung: €60.000 (Budget pro Quartal €15.000, wie genehmigt)

**Gesamtinvestitionsbedarf: ca. €1.2M**

**EBIT-Prognose:**
- Revenue: €9.0M
- Personalkosten (gesamt): €4.8M
- Sonstige Kosten: €2.5M
- **EBIT: ca. €1.7M** (19% Marge, 2025 waren es 17%)

Das ist ein ambitionierter aber realistischer Plan. Die größten Risiken sehe ich bei der Neukundenakquise im Healthcare-Bereich (langer Sales Cycle, regulatorische Anforderungen) und beim Hiring (Markt für ML Engineers und Data Engineers ist extrem kompetitiv).

Ich habe das vollständige Financial Model als Excel im Confluence unter "Finance > Jahresplanung 2026" hochgeladen.

Beste Grüße
Petra

---

## Message 5

**From:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krüger <t.krueger@techvision-gmbh.de>, Petra Neumann <p.neumann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-12-20 16:00

Liebes Leadership Team,

nach unserem sehr produktiven Offsite heute möchte ich die beschlossenen Ergebnisse zusammenfassen:

**Genehmigte strategische Ziele 2026:**
1. Revenue Target €9M — bestätigt, mit Petras Szenario-Modell als Baseline
2. 15 Neueinstellungen — bestätigt, Julia startet Recruiting-Kampagne im Januar
3. Healthcare Vertical — bestätigt, ISO 27001 Projekt startet im Januar (Tobias leitet, Budget €50K)
4. Contaixt SaaS — bestätigt mit Einschränkung: MVP bis Q3, aber Full Launch erst wenn Product-Market Fit validiert

**Zusätzliche Beschlüsse vom Offsite:**
- Quartalsweise OKR Reviews (jeweils erste Woche des Quartals)
- Sandras OKR "AI/ML Practice" wird zum Company-Level OKR hochgestuft — das ist ein strategischer Differentiator
- Thomas baut Healthcare-Pipeline ab sofort auf, DMEA-Konferenz-Teilnahme ist genehmigt
- Petras Investitionsrahmen von €1.2M ist genehmigt, mit quartalsweiser Freigabe
- Lisa koordiniert ein Cross-Team Projekt "Contaixt SaaS", formaler Kickoff im Januar

Ich bin sehr zuversichtlich, dass 2026 unser bisher bestes Jahr wird. Wir haben ein starkes Team, einen klaren technologischen Vorsprung mit GraphRAG, und die richtigen Kunden, die uns vertrauen.

Das detaillierte Strategy Document mit allen OKRs wird von Lisa bis zum 5. Januar in Confluence veröffentlicht. Bitte reviewt es und gebt Feedback bis zum 10. Januar.

Frohe Weihnachten und einen guten Rutsch!

Herzliche Grüße
Martin
