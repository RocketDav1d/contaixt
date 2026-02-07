---
thread_id: email_thread_003
subject: "Aurora – Technische Architektur & Cloud-Entscheidung"
---

## Message 1

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-09-25 08:30

Guten Morgen zusammen,

bevor wir in Sprint 1 tiefer in die Implementierung gehen, möchte ich die **technische Architektur-Entscheidung** für Projekt Aurora noch einmal strukturiert festhalten. Im Kickoff haben wir Azure als Präferenz genannt, aber ich möchte sicherstellen, dass wir das als bewusste Architectural Decision dokumentieren.

Ich habe ein **Architecture Decision Record (ADR)** Template im Confluence angelegt: `/projects/aurora/adr/001-cloud-provider`. Bitte tragt dort eure Argumente ein.

Hier meine Ausgangslage:

**Option A: Microsoft Azure**
- Müller Maschinenbau nutzt bereits Microsoft 365, Azure AD, und Dynamics 365
- Wir haben eine Microsoft Gold Partnership mit Zugang zu FastTrack-Support
- Azure Data Factory und Synapse Analytics sind für den Data-Platform-Use-Case gut geeignet
- Enterprise Agreement Pricing über den Kunden möglich

**Option B: Amazon Web Services (AWS)**
- Breiteres Service-Angebot im Data-Engineering-Bereich (Glue, Redshift, Lake Formation)
- Mehr Open-Source-Community-Support
- Unser Team hat generell mehr AWS-Erfahrung (6 von 8 Entwicklern)

**Option C: Google Cloud Platform (GCP)**
- BigQuery ist hervorragend für Analytics
- Allerdings: Kaum Enterprise-Erfahrung im Team, und der Kunde hat keine Google-Infrastruktur

Ich möchte bis **Freitag, 27.09.** eine finale Entscheidung treffen. Bitte gebt mir eure Einschätzung.

Sandra

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-09-25 10:15

Hi Sandra,

meine klare Empfehlung ist **Azure**. Hier meine Argumente aus technischer Sicht:

**1. Enterprise Integration**
Müller Maschinenbau hat ca. 1.200 Mitarbeiter in Azure AD. Wenn wir die Data Platform auf Azure bauen, können wir **Azure AD Conditional Access Policies** und **Managed Identities** nutzen, statt eigene Auth-Mechanismen zu bauen. Das spart uns mindestens 2-3 Wochen Entwicklungszeit und ist sicherer.

**2. Hybrid Connectivity**
Für die Übergangsphase, in der die Oracle DB noch On-Premise läuft, brauchen wir eine sichere Verbindung. Azure bietet **ExpressRoute** und **VPN Gateway**, die sich nahtlos in das bestehende Netzwerk-Setup von Müller Maschinenbau integrieren lassen. Laut meinem Gespräch mit deren IT-Leiter haben sie bereits einen Azure ExpressRoute Circuit für ihre Microsoft 365 Anbindung.

**3. Data Platform Stack**
Der Stack Azure Data Factory → Data Lake Storage Gen2 → Azure Synapse Analytics → Power BI ist ein bewährter End-to-End-Pfad. Ich habe das in ähnlicher Form bei Projekt Orion implementiert und es hat sich gut bewährt.

**4. Terraform Support**
Sowohl Azure als auch AWS haben exzellenten Terraform Support. Hier sehe ich keinen relevanten Unterschied.

Zum Thema AWS-Erfahrung: Ja, wir haben mehr AWS-Stunden im Team. Aber die Azure-Services, die wir hier brauchen (ADF, Synapse, AKS), sind gut dokumentiert und die Lernkurve ist manageable. Ich schätze 1-2 Wochen Ramp-up für die Kollegen, die bisher weniger Azure gemacht haben.

Gruß
Felix

---

## Message 3

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-09-25 13:42

Hallo zusammen,

aus Data-Engineering-Perspektive unterstütze ich Felix' Empfehlung für Azure. Hier meine Ergänzungen:

**Azure Data Factory** ist für unseren Use Case ideal:
- Über **90 vorgefertigte Connectors**, darunter Oracle, SAP, REST APIs, und Siemens SIMATIC
- **Mapping Data Flows** für serverlose Transformationen (Spark-basiert, aber managed)
- **Tumbling Window Triggers** für zeitbasierte Incremental Loads
- Integration mit **Azure Purview** für Data Lineage und Governance – das wird für Müller Maschinenbau langfristig wichtig, weil die unter DSGVO-Anforderungen arbeiten

Für die Analytical Layer würde ich **Azure Synapse Analytics** mit **Serverless SQL Pools** empfehlen:
- Wir zahlen nur für die Queries, die tatsächlich laufen (Pay-per-Query)
- Native Integration mit Azure Data Lake Storage Gen2 (Parquet, Delta Lake Format)
- **Synapse Link** für Near-Real-Time Analytics, falls Müller Maschinenbau das in Phase 2 braucht

Als Alternative zu Synapse für das Reporting könnten wir auch **Azure Databricks** in Betracht ziehen, aber das wäre Overkill für den aktuellen Scope und würde das Budget sprengen. Ich würde das als Option für Phase 2 vormerken, falls die Anforderungen an Machine Learning und Advanced Analytics wachsen.

Ein Punkt zu AWS: Ja, **AWS Glue** und **Redshift** sind ebenfalls stark, aber die Integration mit dem Microsoft-Ökosystem des Kunden wäre dann wesentlich aufwändiger. Wir müssten eigene Identity Federation bauen und hätten keinen nativen Power BI Support.

Grüße
Anna

---

## Message 4

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-09-26 16:30

Danke euch allen für die fundierten Einschätzungen.

Ich treffe hiermit die finale Entscheidung: **Wir gehen mit Microsoft Azure.**

Die Argumente sind überzeugend, insbesondere:
- Die bestehende Microsoft-Infrastruktur beim Kunden (Azure AD, M365, ExpressRoute)
- Unsere **Microsoft Gold Partnership**, die uns Zugang zu FastTrack Architects und priorisierten Support gibt
- Der durchgängige Data Platform Stack (ADF → ADLS Gen2 → Synapse → Power BI)
- Reduzierter Aufwand beim Identity Management

Ich habe das ADR unter `/projects/aurora/adr/001-cloud-provider` finalisiert und auf "Accepted" gesetzt. Bitte lest es euch durch und gebt ggf. noch Feedback.

**Nächste Schritte:**
1. Felix und Markus: Azure Subscription und Landing Zone aufsetzen (Sprint 1 Backlog)
2. Anna: Azure Data Factory und ADLS Gen2 Architektur dokumentieren
3. Lisa: Müller Maschinenbau über die Entscheidung informieren und die Enterprise Agreement Diskussion mit deren Einkauf starten
4. Tobias: Security Baseline für Azure gemäß unserem Security Policy Document (v2.3) erstellen

Dr. Schreiber habe ich bereits informiert – er unterstützt die Entscheidung.

Sandra

---

## Message 5

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-09-27 09:08

Moin zusammen,

kurz mein Input von der DevOps-Seite: Volle Zustimmung zu Azure.

Ein wichtiger Punkt, den ich ergänzen möchte: Für die **Container Orchestration** der Backend-Services (API Gateway, Data Processing Workers, Scheduling) empfehle ich **Azure Kubernetes Service (AKS)**.

Warum AKS statt z.B. Azure Container Apps oder App Services:
- Wir haben bereits Kubernetes-Know-how aus Projekt Orion und Projekt Helios
- **AKS** gibt uns volle Kontrolle über Scaling, Networking und RBAC
- Integration mit **Azure Container Registry (ACR)** für Image Management
- **Azure Monitor** und **Container Insights** für Observability out-of-the-box
- Wir können unsere bestehenden **Helm Charts** und **ArgoCD** Deployment-Workflows wiederverwenden

Für das **Monitoring** setze ich auf:
- **Grafana** (Azure Managed Grafana) für Dashboards
- **Prometheus** (via Azure Monitor managed Prometheus) für Metrics
- **Azure Log Analytics** für zentrales Logging

Ich habe im Tech Radar den Eintrag für AKS von "Assess" auf "Trial" aktualisiert, basierend auf unseren positiven Erfahrungen aus Projekt Orion.

Felix, lass uns Montag zusammensetzen und die Terraform-Module aufteilen. Ich erstelle schon mal das `aurora-infra` Repository auf GitHub.

Gruß
Markus
