---
thread_id: email_thread_002
subject: "Projekt Aurora – Sprint 1 Planning"
---

## Message 1

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-22 08:45

Guten Morgen Team,

nach dem erfolgreichen Kickoff letzte Woche starten wir jetzt mit der Sprint 1 Planning. Ich habe das Board in Jira unter `AURORA` angelegt und die ersten Epics erstellt.

**Sprint 1 (22.09. – 06.10.)** – Fokus: Foundation

Hier der vorgeschlagene Sprint Backlog:

**Infrastructure & DevOps (Markus, Felix)**
- [ ] Azure Subscription und Resource Groups einrichten
- [ ] Landing Zone nach Microsoft Cloud Adoption Framework aufsetzen
- [ ] CI/CD Pipeline (GitHub Actions → Azure) konfigurieren
- [ ] Terraform-Module für Basisinfrastruktur (VNet, Subnets, NSGs, Key Vault)

**Data Platform (Anna, Daniel)**
- [ ] Azure Data Factory Instanz provisionieren
- [ ] Erste Data Connectors: Oracle DB → Azure Data Lake Storage Gen2
- [ ] Schema-Mapping für die wichtigsten ERP-Tabellen (Aufträge, Kunden, Artikel)

**Frontend/UX (Katharina)**
- [ ] Wireframes für das Executive Dashboard
- [ ] Design System Setup (Figma, Component Library)

**Querschnitt**
- [ ] Development Environment Dokumentation
- [ ] Zugänge für alle Teammitglieder (Azure Portal, GitHub, Jira)

Das Daily Standup habe ich auf **09:15 Uhr** gelegt, immer über Teams. Sprint Review ist am **06.10. um 14:00 Uhr**, da wird auch Hans Müller dabei sein.

Story Points und Assignments bitte bis heute Nachmittag im Board eintragen.

Viele Grüße
Lisa

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-22 09:58

Hi Lisa,

guter Sprint Backlog. Zum Thema Infrastructure habe ich folgenden Vorschlag:

Ich würde gerne konsequent auf **Terraform** als Infrastructure-as-Code Tool setzen. Das hat mehrere Vorteile:

1. **Reproducibility:** Wir können die komplette Infrastruktur aus dem Code heraus in jeder Umgebung (Dev, Staging, Prod) identisch deployen.
2. **State Management:** Terraform State speichern wir in einem Azure Storage Account Backend – damit haben wir Locking und Versioning.
3. **Module Registry:** Wir haben intern schon Terraform-Module für Azure Landing Zones, die wir im letzten Projekt (Projekt Orion) entwickelt haben. Die können wir wiederverwenden.

Konkret schlage ich folgende Repo-Struktur vor:

```
aurora-infra/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/
│   ├── networking/
│   ├── data-platform/
│   ├── security/
│   └── monitoring/
└── .github/
    └── workflows/
        └── terraform-plan-apply.yml
```

Markus und ich können uns das aufteilen: Ich mache die Module für Networking und Data Platform, Markus übernimmt Security und Monitoring.

Was die CI/CD Pipeline angeht: Ich würde **GitHub Actions** mit dem `azure/login` Action verwenden, Authentifizierung über einen **Service Principal mit Federated Credentials** (kein Client Secret, wie es unser Security Policy Document vorschreibt).

@Markus: Passt das für dich?

Gruß
Felix

---

## Message 3

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-22 11:23

Hallo zusammen,

zum Thema **Data Connectors** habe ich mir Gedanken gemacht, in welcher Reihenfolge wir die Quellsysteme anbinden sollten.

**Priorität 1: ERP (Oracle 12c)**
Das ist der Kern des Ganzen. Die Auftragstabellen (`ORDERS`, `ORDER_ITEMS`, `CUSTOMERS`, `ARTICLES`) sind die wichtigsten Entitäten für das Reporting. Ich würde mit einem Full Load über Azure Data Factory starten und dann auf Incremental Load umstellen, sobald wir die Change Data Capture Mechanismen verstanden haben. Oracle 12c unterstützt LogMiner, das könnten wir für CDC nutzen.

**Priorität 2: MES (Manufacturing Execution System)**
Das MES von Müller Maschinenbau ist ein Siemens SIMATIC IT System, das Produktionsdaten über eine REST API bereitstellt. Die Anbindung ist technisch einfacher, aber die Datenvolumina sind höher (Sensor-Daten, Maschinenstatus, Qualitätsprüfungen). Ich schlage vor, das in Sprint 2 oder 3 anzugehen.

**Priorität 3: HR-Daten (SAP SuccessFactors)**
Wurde im Kickoff als Nice-to-have erwähnt. Würde ich erstmal zurückstellen.

Für die **Data Lake Architektur** auf Azure Data Lake Storage Gen2 schlage ich das Medallion-Konzept vor:
- **Bronze Layer:** Rohdaten 1:1 aus den Quellsystemen
- **Silver Layer:** Bereinigte, validierte Daten mit einheitlichem Schema
- **Gold Layer:** Aggregierte Business-Metriken für das Dashboard

Daniel, ich würde dich bitten, die ersten ADF Pipelines für den Bronze Layer zu bauen. Ich schicke dir die Dokumentation zu den Oracle-Tabellen.

Viele Grüße
Anna

---

## Message 4

**From:** Daniel Wolff <d.wolff@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-22 14:07

Hi zusammen,

danke für die Infos! Ich bin ready für Sprint 1.

Eine Frage zum **Development Environment Setup**: Ich bin noch relativ neu im Team und wollte sicherstellen, dass ich alles richtig aufsetze.

Was brauche ich konkret?
- Azure CLI + Terraform lokal installiert → Check
- GitHub Repo Zugang → Habe ich noch nicht, Lisa kannst du mich zum `aurora-infra` Repo einladen?
- Azure Portal Zugang → Muss Markus mir die Rolle "Contributor" auf der Dev Resource Group geben
- Oracle Client für lokale Tests → Welche Version? Brauche ich Oracle Instant Client oder den Full Client?
- VPN-Zugang zum Netzwerk von Müller Maschinenbau → Ist das schon eingerichtet?

Anna, ich fange gerne mit den ADF Pipelines an. Hast du schon ein Schema-Mapping Dokument oder soll ich das aus der Oracle-Dokumentation ableiten? Ich habe Erfahrung mit Azure Data Factory aus meinem vorherigen Projekt und kenne mich mit den Self-Hosted Integration Runtimes aus, die wir vermutlich für den Oracle-Zugriff brauchen werden.

Noch eine Frage an Felix: Im Tech Radar steht, dass wir für Python-Projekte **Poetry** statt pip verwenden sollen. Gilt das auch für die Data-Pipeline-Skripte, oder nutzen wir da ein anderes Setup?

Danke und Grüße
Daniel
