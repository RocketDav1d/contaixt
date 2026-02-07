---
thread_id: email_thread_006
subject: "Aurora – Go-Live Vorbereitung & Checklist"
---

## Message 1

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-11-25 08:00

Guten Morgen Team,

der Go-Live für Projekt Aurora rückt näher. Ich habe die **Go-Live Checklist** erstellt und als Confluence-Seite unter `/projects/aurora/go-live-checklist` abgelegt. Hier die Zusammenfassung der kritischen Items:

**1. Infrastructure & DNS (Markus)**
- [ ] Production Azure Resources finalisiert und Terraform State locked
- [ ] DNS Cutover vorbereitet: `aurora.mueller-maschinenbau.de` → Azure Front Door Endpoint
- [ ] SSL/TLS Zertifikate (Let's Encrypt oder Azure Managed Certificate) installiert
- [ ] CDN Cache-Regeln konfiguriert
- [ ] Azure DDoS Protection Standard aktiviert

**2. Monitoring & Alerting (Markus)**
- [ ] Grafana Dashboards für alle kritischen Metriken (API Latency, Error Rate, DB Connections, AKS Pod Health)
- [ ] PagerDuty Integration für On-Call Alerting
- [ ] Runbook für häufige Incident-Szenarien erstellt
- [ ] Uptime Monitoring (Synthetic Checks) auf Production-Endpoints

**3. Security (Tobias, Felix)**
- [ ] Alle Medium Pentest Findings resolved und Re-Test bestanden
- [ ] Production CORS Policy konfiguriert (nur erlaubte Origins)
- [ ] Rate Limiting auf allen API-Endpoints aktiv
- [ ] Azure Key Vault: Alle Secrets rotiert und Production-Werte gesetzt
- [ ] Security Assessment Report an Müller Maschinenbau übergeben

**4. Data Migration (Anna, Daniel)**
- [ ] Final Full Load durchgeführt und validiert
- [ ] Delta Load für den Cutover-Zeitraum getestet
- [ ] Data Quality Report erstellt (Quarantäne-Datensätze dokumentiert)
- [ ] Rollback-Plan für Datenmigration getestet

**5. Application (Felix, Daniel, Katharina)**
- [ ] Alle Feature Branches gemerged und Release Branch erstellt
- [ ] End-to-End Tests auf Staging bestanden
- [ ] Performance Tests: Dashboard Ladezeit < 3 Sekunden
- [ ] User Acceptance Testing (UAT) durch Müller Maschinenbau abgeschlossen

**6. Rollback Plan**
- [ ] Terraform Rollback getestet (Infrastructure as Code → vorherige Version)
- [ ] Datenbank-Rollback Prozedur dokumentiert
- [ ] DNS Rollback auf alte IP möglich (TTL auf 300 Sekunden gesetzt)
- [ ] Kommunikationsplan für Rollback-Szenario erstellt

**Go-Live Zeitplan (02.12.2025):**
- 06:00 – Maintenance Window beginnt, alte Anwendung wird in Read-Only versetzt
- 06:30 – Finaler Delta Load der letzten Datenänderungen
- 07:00 – Data Validation auf der neuen Plattform
- 07:30 – DNS Cutover
- 08:00 – Smoke Tests auf Production
- 08:30 – Freigabe für Endbenutzer
- 09:00 – Go/No-Go Entscheidung (Rollback-Fenster bis 12:00)

Bitte aktualisiert eure Items in der Checklist bis **Donnerstag, 27.11.** mit dem aktuellen Status.

Viele Grüße
Lisa

---

## Message 2

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-11-25 10:45

Hi Lisa,

von der Infrastructure- und Monitoring-Seite sind wir **Go-Live-ready**. Hier mein Status-Update:

**Infrastructure:**
- Terraform State ist locked, alle Production Resources sind deployed und getestet
- DNS Cutover ist vorbereitet. Der `CNAME`-Record für `aurora.mueller-maschinenbau.de` liegt bei deren DNS-Provider (IONOS). Ich habe mit dem IT-Team von Müller Maschinenbau einen **Runbook für den DNS Switch** abgestimmt. TTL ist auf **300 Sekunden** gesetzt, sodass die Propagation maximal 5 Minuten dauert.
- SSL-Zertifikat über **Azure Front Door Managed Certificate** – automatische Verlängerung, kein manueller Aufwand.
- **Azure DDoS Protection Standard** ist auf dem VNet aktiviert.
- AKS Cluster läuft auf **3 Nodes** (Standard_D4s_v3) mit **Horizontal Pod Autoscaling** (min: 2, max: 10 Pods pro Deployment).

**Monitoring & Alerting:**
- **Grafana Dashboards** sind fertig. Ich habe 4 Dashboards erstellt:
  1. **API Overview**: Request Rate, Latency (p50, p95, p99), Error Rate, Status Codes
  2. **Data Platform**: ADF Pipeline Runs, Data Lake Usage, Synapse Query Performance
  3. **Infrastructure**: AKS Node/Pod Metrics, CPU/Memory, Disk I/O
  4. **Business Metrics**: Active Users, Report Generations, Data Freshness
- **PagerDuty** Integration ist live. On-Call Rotation für die erste Woche nach Go-Live:
  - Mo/Di: Felix Braun
  - Mi/Do: Markus Lang
  - Fr/Sa/So: Felix Braun
- **Alerting Rules** konfiguriert: API Error Rate > 5% (Critical), Latency p99 > 5s (Warning), AKS Pod Restarts > 3 (Warning), Data Pipeline Failure (Critical)
- **Synthetic Monitoring**: Azure Application Insights Availability Tests laufen alle 5 Minuten gegen die Health-Endpoints.

Alles grün von meiner Seite.

Gruß
Markus

---

## Message 3

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-11-26 09:12

Hi zusammen,

Status-Update von der Application-Seite:

**Security Findings:**
- **M-001 (Rate Limiting):** Implementiert, deployed auf Staging, **Re-Test durch Tobias bestanden** am 25.11. Das `slowapi` Middleware funktioniert wie erwartet. Im Load Test haben wir verifiziert, dass die Rate Limits korrekt greifen und `429 Too Many Requests` Responses zurückgegeben werden.
- **M-002 (CORS):** Fix deployed, Re-Test bestanden. CORS ist jetzt auf die beiden erlaubten Origins beschränkt.
- **L-001 (Security Headers):** Implementiert via Custom Middleware. `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000`, `Content-Security-Policy` sind jetzt gesetzt.
- **L-002 (Verbose Errors):** Production Config setzt `DEBUG=False`, Stack Traces werden nur noch geloggt, nicht an den Client zurückgegeben.

Tobias hat den **finalen Security Assessment Report** gestern freigegeben. Alle Medium Findings sind resolved.

**Application Status:**
- Release Branch `release/1.0.0` ist erstellt
- End-to-End Tests auf Staging: **47/47 passed**
- Performance Test: Dashboard Ladezeit im Durchschnitt **1.8 Sekunden** (unter dem Zielwert von 3 Sekunden)
- UAT durch Müller Maschinenbau am 24.11. erfolgreich abgeschlossen. Hans Müller hat 3 Minor Feedback Items gegeben, die als Post-Go-Live Improvements getracked werden.

Von meiner Seite: **Go** für den Go-Live am 02.12.

Gruß
Felix

---

## Message 4

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-11-26 14:30

Hallo zusammen,

Status-Update zur Datenmigration:

**Migration Status:**
- **Final Full Load** wurde am 23.11. durchgeführt. Dank der Optimierungen (Partitioned Copy, upgesizete VM auf `Standard_D16s_v3`) hat der Full Load nur noch **2 Stunden 40 Minuten** gedauert – deutlich innerhalb unseres 4-Stunden-Wartungsfensters.
- **Datenvolumen:** 2.147.832 Datensätze in der `ORDERS`-Tabelle, 847 GB Gesamtvolumen über alle Tabellen.
- **Delta Load** wurde getestet und funktioniert zuverlässig. Am Go-Live-Tag fahren wir um 06:30 den letzten Delta Load, um die Änderungen seit dem Full Load nachzuziehen.

**Data Quality:**
- Das **Data Quality Framework** (YAML-basierte Validation Rules) ist in Betrieb und hat den Full Load validiert.
- **Ergebnis:** 97.2% der Datensätze sind sauber durchgegangen (Silver Layer). 2.8% sind in der Quarantäne-Tabelle gelandet.
- Die **42 nicht-konvertierbaren Datensätze** habe ich mit Hans Müllers Controller-Team geklärt – das sind alte Testdaten, die gelöscht werden können.
- Der **Data Quality Report** liegt im Confluence unter `/projects/aurora/data-quality-report`.

**Rollback-Plan:**
- Im Rollback-Fall können wir den Oracle-Export vom 23.11. innerhalb von 3 Stunden zurückspielen. Die alte Anwendung bleibt in einem Read-Only Modus verfügbar, bis der Rollback abgeschlossen wäre.
- Daniel hat den Rollback-Prozess am 22.11. in der Dev-Umgebung getestet – funktioniert einwandfrei.

Von der Data-Seite: **Go** für den Go-Live.

Viele Grüße
Anna

---

## Message 5

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**CC:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Thomas Krüger <t.krueger@techvision-gmbh.de>, Hans Müller <h.mueller@mueller-maschinenbau.de>
**Date:** 2025-11-28 16:00

Liebe Kolleginnen und Kollegen, lieber Herr Müller,

basierend auf den Status-Updates aller Workstreams kann ich die **finale Go/No-Go Entscheidung** für Projekt Aurora verkünden:

**Ergebnis: GO**

Alle Checklist-Items sind erfüllt:
- Infrastructure & DNS: Ready (Markus)
- Monitoring & Alerting: Ready (Markus)
- Security: All Findings resolved, Assessment Report freigegeben (Tobias, Felix)
- Data Migration: Complete, Validation passed (Anna, Daniel)
- Application: Release 1.0.0 ready, UAT passed (Felix, Daniel, Katharina)
- Rollback Plan: Dokumentiert und getestet

**Go-Live: Dienstag, 02.12.2025, 06:00 Uhr MEZ**

**War Room Setup:**
- Teams-Channel "Aurora Go-Live" ist ab 05:45 besetzt
- Vor-Ort im Büro: Lisa, Felix, Markus
- Remote: Anna, Daniel, Tobias, Katharina
- Hans Müller und sein IT-Team sind ab 07:00 auf Standby für den Smoke Test

**Eskalationspfad:**
1. Lisa Weber (Project Lead)
2. Sandra Hoffmann (CTO)
3. Dr. Martin Schreiber (CEO) – nur im Extremfall

Ich möchte an dieser Stelle dem gesamten Team für die hervorragende Arbeit in den letzten 11 Wochen danken. Trotz der Herausforderungen bei der Datenmigration haben wir den Timeline eingehalten und liefern eine Plattform, auf die wir stolz sein können.

Herr Müller, wir melden uns am Dienstag nach dem erfolgreichen Cutover. Für Rückfragen stehe ich jederzeit zur Verfügung.

Viele Grüße
Lisa Weber
Project Lead, Projekt Aurora
TechVision GmbH
