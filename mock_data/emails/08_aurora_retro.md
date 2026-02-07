---
thread_id: email_thread_008
subject: "Projekt Aurora – Retrospektive"
---

## Message 1

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-12 08:30

Guten Morgen zusammen,

jetzt, da Projekt Aurora erfolgreich live ist und die Hypercare-Phase ruhig verläuft (keine P1-Incidents seit Go-Live!), möchte ich die **Projekt-Retrospektive** durchführen.

**Termin:** Montag, 15.12.2025, 14:00 – 16:00 Uhr
**Ort:** Großer Konferenzraum / Teams (für Remote-Teilnehmer)
**Format:** Start-Stop-Continue + Timeline Review

Zur Vorbereitung bitte ich euch, euch Gedanken zu den folgenden drei Kategorien zu machen:

1. **Was lief gut?** (Keep doing)
2. **Was lief nicht so gut?** (Stop doing / Improve)
3. **Was sollten wir beim nächsten Projekt anders machen?**

Als Input habe ich ein paar **Projekt-Kennzahlen** zusammengestellt:

| Metrik | Plan | Ist |
|--------|------|-----|
| Budget | 450.000 EUR | 438.500 EUR (97,4%) |
| Timeline | 12 Wochen | 11,5 Wochen |
| Sprints | 6 | 6 (Sprint 2 um 1 Woche verlängert) |
| Story Points | 340 (geschätzt) | 362 (delivered) |
| Bugs in Production | - | 2 (Minor) |
| Uptime seit Go-Live | 99,5% SLA | 99,97% |
| Kundenzufriedenheit | - | "Sehr zufrieden" (Feedback Hans Müller) |

Das sind starke Zahlen. Aber wir können immer besser werden. Schickt mir bitte vorab eure Punkte per E-Mail, damit ich die Retro moderieren kann.

Viele Grüße
Lisa

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-12 14:15

Hi Lisa,

hier meine Punkte für die Retro:

**Was lief gut:**

1. **Infrastructure as Code hat sich massiv ausgezahlt.** Durch Terraform konnten wir die komplette Infrastruktur in 3 Environments (Dev, Staging, Prod) konsistent deployen. Als wir in Sprint 4 das Networking-Setup ändern mussten (zusätzliche Subnet für die Integration Runtime), war das ein 15-Minuten-Change statt einem mehrtägigen manuellen Prozess.

2. **CI/CD Pipeline war von Anfang an stabil.** GitHub Actions mit den Terraform Plan/Apply Workflows haben ab Sprint 1 funktioniert. Wir hatten null Deployment-Failures auf Staging oder Prod. Der Workflow mit PR-basiertem Terraform Plan und manuellem Approve für Apply war genau richtig.

3. **Team-Kommunikation war exzellent.** Die Daily Standups und das War Room Format bei der Datenmigrations-Krise haben sehr gut funktioniert. Jeder wusste, wo er steht und wo Hilfe gebraucht wird.

4. **Security von Anfang an mitgedacht.** Tobias' frühzeitiger Security Review (Sprint 4 statt erst am Ende) hat uns die Zeit gegeben, die Findings sauber zu beheben. Kein Last-Minute-Security-Stress.

**Was lief nicht so gut:**

1. **Datenmigration wurde unterschätzt.** Wir haben im Sprint Planning nur 5 Story Points für den initialen Full Load eingeplant. Tatsächlich hat die Datenmigration inkl. Encoding-Probleme, Data Quality und Performance-Optimierung ca. **40 Story Points** verbraucht. Das hat Sprint 2 um eine Woche verlängert. Ehrlich gesagt hätte ich bei einem 20 Jahre alten Oracle-System misstrauischer sein müssen.

2. **Technical Debt bei den Data Connectors.** Einige der ADF Pipelines sind recht monolithisch geworden, weil wir unter Zeitdruck standen. Für Phase 2 sollten wir die refactoren und in kleinere, wiederverwendbare Module aufteilen.

3. **Dokumentation kam zu kurz.** Wir haben zwar gute ADRs geschrieben, aber die operative Dokumentation (Runbooks, Troubleshooting Guides) war erst am Ende des Projekts vollständig. In der Hypercare-Phase hat Daniel dreimal bei mir angerufen, weil er Infos nicht finden konnte, die nur in meinem Kopf waren.

**Vorschlag für zukünftige Projekte:**
- **Data Profiling als Standard-Sprint-0-Activity.** Bevor wir eine Migration planen, sollten wir immer ein systematisches Data Profiling der Quellsysteme machen. 2-3 Tage Invest am Anfang hätten uns 2 Wochen Aufwand in der Mitte gespart.

Gruß
Felix

---

## Message 3

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-13 09:42

Hallo zusammen,

ich schließe mich Felix' Punkten vollumfänglich an und ergänze aus der Data-Engineering-Perspektive:

**Was lief gut:**

1. **Medallion-Architektur war die richtige Entscheidung.** Die klare Trennung in Bronze, Silver und Gold Layer hat uns bei der Datenmigrations-Krise enorm geholfen. Weil der Bronze Layer immutable war, konnten wir die Cleanup-Logik im Silver Layer iterativ verbessern, ohne die Rohdaten zu gefährden.

2. **Data Quality Framework wird ein Asset.** Das YAML-basierte Validation Framework, das wir wegen der Encoding-Probleme gebaut haben, ist jetzt ein wiederverwendbares Tool, das wir in jedem zukünftigen Data-Projekt einsetzen können. Ich habe es bereits im internen Tech Radar unter "Adopt" vorgeschlagen.

3. **Daniel hat sich hervorragend entwickelt.** Als Junior Developer hat Daniel das Cleanup Script eigenständig geschrieben und dabei eine Qualität abgeliefert, die man von einem Senior erwartet. Sein Code war sauber, gut getestet und dokumentiert. Ich möchte das explizit hervorheben.

**Was lief nicht so gut:**

1. **Felix hat Recht: Data Profiling fehlte.** Hätten wir am Anfang 2-3 Tage in ein systematisches Profiling investiert (Encoding-Check, Referential Integrity Check, Datentyp-Analyse, NULL-Analyse), hätten wir die Probleme in Sprint 1 erkannt statt in Sprint 3. Das hätte uns den War Room und die Sprint-Verlängerung erspart.

2. **MES-Anbindung wurde zu spät angefangen.** Wir haben die Siemens SIMATIC REST API erst in Sprint 4 angebunden. Das war zu knapp. Die API hat einige Eigenheiten (Pagination, Rate Limiting, unübliche Fehler-Codes), die uns überrascht haben. Für Phase 2 sollten wir die MES-Anbindung in Sprint 1 priorisieren, nicht ans Ende schieben.

**Vorschläge:**

- **Data Profiling Checklist** als Standard-Artefakt im Project Charter aufnehmen. Für jedes Quellsystem: Encoding, Volumen, Datenqualität, Schema-Komplexität, Change Data Capture Fähigkeit.
- **Datenquellen-Onboarding als eigenen Sprint** einplanen – keine Infrastruktur-Aufgaben parallel, nur Fokus auf das Verstehen und Anbinden der Quellsysteme.
- **Pair Programming** für komplexe Data Pipelines standardisieren. Daniel und ich haben in Sprint 3 zusammen an den ADF Pipelines gearbeitet – das war produktiver und die Qualität war deutlich höher als Solo-Arbeit unter Zeitdruck.

Viele Grüße
Anna

---

## Message 4

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-14 10:30

Moin zusammen,

hier mein Input:

**Was lief gut:**

1. **Monitoring Setup hat sich am Go-Live-Tag bezahlt gemacht.** Während des DNS Cutover hatten wir einen kurzen Spike bei den API-Error-Rates (ca. 2 Minuten, bedingt durch DNS Propagation Delay). Das Grafana Dashboard hat das sofort angezeigt, und wir konnten im War Room live sehen, wie die Werte sich normalisierten. Ohne das Monitoring hätte das vermutlich zu einer kleinen Panik geführt.

2. **AKS Horizontal Pod Autoscaling** hat am Go-Live-Tag perfekt funktioniert. Als um 09:00 Uhr die Benutzer von Müller Maschinenbau anfingen, die Dashboards zu öffnen, skalierte AKS automatisch von 2 auf 5 Pods. Der Peak Load lag bei ca. 150 concurrent Users – alles smooth, keine spürbare Latenz-Verschlechterung.

3. **PagerDuty On-Call Rotation** war gut organisiert. In der ersten Woche nach Go-Live gab es nur 2 Alerts (beide Low Priority: ein Data Pipeline Retry und ein kurzer Latency Spike). Kein nächtlicher Einsatz nötig.

4. **Terraform Module Wiederverwendung** von Projekt Orion hat uns ca. 1 Woche Entwicklungszeit gespart. Besonders die Networking- und Security-Module konnten wir fast 1:1 übernehmen und mussten nur die Parameter anpassen.

**Was lief nicht so gut:**

1. **Log-Aggregation war anfangs zu verbose.** Wir haben in den ersten Tagen ca. **2 GB Logs pro Tag** generiert, weil die ADF Pipelines im DEBUG-Level geloggt haben. Das hat den Azure Log Analytics Workspace unnötig aufgebläht und kurzzeitig zu Kosten geführt, die nicht im Budget eingeplant waren. Lesson learned: Log-Level-Konfiguration gehört in die Go-Live Checklist.

2. **Kein Chaos Engineering.** Wir haben die Resilienz der Plattform nicht proaktiv getestet (z.B. Pod Kills, Node Failures, Network Partitions). Für Phase 2 schlage ich vor, dass wir **Azure Chaos Studio** oder **LitmusChaos** einführen, um die Ausfallsicherheit systematisch zu testen.

**Vorschlag:** Monitoring-Template als Terraform-Modul standardisieren (Grafana Dashboards + AlertManager Rules + PagerDuty Integration). Das können wir dann in jedem neuen Projekt innerhalb von 30 Minuten deployen statt wie hier in 2 Tagen manuell aufzusetzen.

Gruß
Markus

---

## Message 5

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-15 16:45

Liebe Kolleginnen und Kollegen,

vielen Dank für die ausführlichen und ehrlichen Retro-Beiträge. Die Session heute Nachmittag war sehr produktiv. Hier die Zusammenfassung der **Action Items**, die wir gemeinsam beschlossen haben:

**Action Items für TechVision (allgemein gültig):**

1. **Data Profiling als Sprint-0-Standard** (Owner: Anna Richter)
   - Anna erstellt eine **Data Profiling Checklist** als Template im Confluence.
   - Für jedes Projekt mit Datenmigration wird in Sprint 0 ein Data Profiling durchgeführt (Encoding, Volumen, Referential Integrity, NULL-Analyse, Change Data Capture).
   - Geschätzter Aufwand: 2-3 Tage pro Quellsystem.
   - **Deadline:** 10.01.2026

2. **Monitoring-as-Code Template** (Owner: Markus Lang)
   - Markus erstellt ein **Terraform-Modul** mit Grafana Dashboards, AlertManager Rules und PagerDuty Integration als wiederverwendbares Template.
   - Ziel: Monitoring Setup in 30 Minuten statt 2 Tagen.
   - **Deadline:** 17.01.2026

3. **Documentation-First Approach** (Owner: Felix Braun)
   - Ab sofort werden Runbooks und Troubleshooting Guides **parallel zur Implementierung** geschrieben, nicht erst am Ende.
   - Felix erstellt ein **Runbook Template** im Confluence.
   - **Deadline:** 10.01.2026

4. **Data Quality Framework als internes Produkt** (Owner: Anna Richter)
   - Das YAML-basierte Validation Framework wird aus dem Aurora-Repo extrahiert und als **eigenständiges internes Tool** im Tech Radar aufgenommen.
   - Anna schreibt die Dokumentation und Onboarding-Guides.
   - **Deadline:** 31.01.2026

5. **Pair Programming für komplexe Pipelines** (Owner: Lisa Weber)
   - In zukünftigen Projekten wird Pair Programming für komplexe Data Pipelines und kritische Infrastruktur-Changes **empfohlen** (nicht verpflichtend, aber ermutigt).
   - Wird in die TechVision Engineering Best Practices aufgenommen.

6. **Chaos Engineering Evaluation** (Owner: Markus Lang)
   - Markus evaluiert **Azure Chaos Studio** und **LitmusChaos** für einen Einsatz in Phase 2.
   - Ergebnis wird im Tech Radar dokumentiert.
   - **Deadline:** 17.01.2026

**Projekt-spezifische Action Items für Phase 2:**
- ADF Pipeline Refactoring (Felix + Daniel): Monolithische Pipelines in modulare, wiederverwendbare Einheiten aufteilen
- MES-Anbindung in Sprint 1 priorisieren (Anna)
- Log-Level-Konfiguration in die Go-Live Checklist aufnehmen (Markus)

Ich werde diese Action Items auch im **Steering Committee am 19.12.** vorstellen und mit Sandra und Dr. Schreiber besprechen, welche davon als unternehmensweite Standards übernommen werden.

Nochmals: Ihr seid ein fantastisches Team. Projekt Aurora war ein voller Erfolg, und die Learnings, die wir mitnehmen, machen uns für die Zukunft noch stärker.

Schöne Vorweihnachtszeit!

Viele Grüße
Lisa
