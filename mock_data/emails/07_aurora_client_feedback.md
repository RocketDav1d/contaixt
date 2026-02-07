---
thread_id: email_thread_007
subject: "Re: Projekt Aurora – Go-Live Feedback"
---

## Message 1

**From:** Hans Müller <h.mueller@mueller-maschinenbau.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**CC:** Thomas Krüger <t.krueger@techvision-gmbh.de>
**Date:** 2025-12-05 10:22

Liebe Frau Weber, liebe Frau Hoffmann,

ich möchte Ihnen und dem gesamten TechVision-Team herzlich zum **erfolgreichen Go-Live von Projekt Aurora** gratulieren. Der Cutover am Dienstag lief reibungslos – unsere Mitarbeiter konnten ab 09:00 Uhr wie geplant mit der neuen Plattform arbeiten.

Das Feedback aus den ersten Tagen ist überwiegend **sehr positiv**:

**Was besonders gut ankommt:**
- Die **Executive Dashboards** sind ein enormer Fortschritt gegenüber unseren manuellen Excel-Reports. Mein CFO, Herr Dr. Becker, hat mir heute Morgen begeistert die Echtzeit-Umsatzübersicht gezeigt. Das hat uns beim alten System immer 2-3 Tage Vorlauf gekostet.
- Die **Datenqualität** im Silver Layer ist deutlich besser als in unserem alten Oracle-System. Die Bereinigung, die Ihr Team durchgeführt hat, war Gold wert.
- Das **Single Sign-On** über Azure AD funktioniert einwandfrei. Unsere Mitarbeiter können sich mit ihren bestehenden Microsoft-Zugangsdaten anmelden, ohne ein weiteres Passwort.
- Die **Mobile-Ansicht** der Dashboards auf Tablets ist für unsere Produktionsleiter sehr praktisch.

**Ein Punkt, den wir noch adressieren sollten:**
Einige Benutzer berichten, dass das **Haupt-Dashboard beim ersten Laden morgens relativ langsam** ist (ca. 8-10 Sekunden). Danach geht es schnell, aber der initiale Load scheint lang zu dauern. Das betrifft insbesondere das Dashboard mit den Produktionskennzahlen, das Daten aus der MES-Anbindung zieht. Ich vermute, dass es mit einem Cold Start oder Caching zusammenhängt, aber Ihre Experten können das sicher besser einschätzen.

Abgesehen davon sind wir mit dem Ergebnis **sehr zufrieden**. Das Projekt wurde im Zeit- und Budgetrahmen abgeliefert, was in meiner Erfahrung leider nicht selbstverständlich ist.

Ich würde gerne einen Termin für ein **Phase-2-Gespräch** vereinbaren. Wir haben intern bereits einige Ideen gesammelt, u.a.:
- Anbindung unseres SAP SuccessFactors HR-Systems
- Predictive Maintenance auf Basis der Sensor-Daten aus dem MES
- Erweiterung der Dashboards um Supply-Chain-KPIs

Wann passt es Ihnen für ein erstes Gespräch?

Mit freundlichen Grüßen
Hans Müller
CEO, Müller Maschinenbau AG

---

## Message 2

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Hans Müller <h.mueller@mueller-maschinenbau.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**CC:** Thomas Krüger <t.krueger@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-12-05 14:38

Lieber Herr Müller,

vielen herzlichen Dank für das positive Feedback! Das freut das gesamte Team sehr.

Zum Thema **Dashboard-Ladezeit**: Ich habe Felix und Katharina direkt in CC genommen. Wir vermuten tatsächlich einen **Cold Start** des Azure Synapse Serverless SQL Pools. Am Morgen, wenn die ersten Benutzer auf das Dashboard zugreifen, muss der Pool erst hochfahren, was einige Sekunden dauern kann.

Wir haben dafür mehrere Lösungsansätze:

1. **Warm-Up Query** – Ein automatisierter Job, der um 06:00 Uhr eine leichte Query gegen den Synapse Pool fährt, damit er "warm" ist, wenn die Benutzer kommen. Das können wir kurzfristig über eine Azure Function lösen.

2. **Caching Layer** – Wir können einen **Azure Redis Cache** zwischenschalten, der die häufigsten Dashboard-Queries cached. Felix schätzt den Aufwand auf ca. 2-3 Tage.

3. **Provisioned Synapse Pool** – Statt Serverless könnten wir einen dedizierten Pool verwenden, der immer läuft. Das wäre allerdings mit höheren laufenden Kosten verbunden (ca. 800-1.200 EUR/Monat).

Ich würde vorschlagen, dass wir **Option 1 sofort umsetzen** (kein zusätzlicher Aufwand im Rahmen der Hypercare-Phase) und **Option 2 als Quick Win** für nächste Woche einplanen. Damit sollte das Problem gelöst sein, ohne die monatlichen Kosten zu erhöhen.

Bezüglich **Phase 2**: Das freut uns sehr! Ich koordiniere mit Sandra und Thomas einen Termin. Wie wäre die **KW 51 (15.-19. Dezember)**? Ein halbtägiger Workshop, in dem wir Ihre Ideen durchsprechen und einen groben Scope definieren?

Viele Grüße
Lisa Weber

---

## Message 3

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Hans Müller <h.mueller@mueller-maschinenbau.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**CC:** Thomas Krüger <t.krueger@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-12-08 09:15

Lieber Herr Müller,

auch von meiner Seite herzlichen Glückwunsch und Dank für die exzellente Zusammenarbeit. Ein Projekt, das pünktlich und im Budget abgeliefert wird, ist keine Selbstverständlichkeit – das ist das Ergebnis guter Kommunikation auf beiden Seiten.

Zum Thema **Phase 2** habe ich einige strategische Gedanken:

Die von Ihnen genannten Themen passen hervorragend in unsere **TechVision Data & AI Roadmap**:

1. **SAP SuccessFactors Anbindung**: Wir haben bereits einen zertifizierten SAP-Connector für Azure Data Factory. Die Integration wäre vergleichsweise einfach und könnte als Quick Win den Wert der Plattform für Ihr HR-Team sofort steigern.

2. **Predictive Maintenance**: Das ist strategisch das spannendste Thema. Mit den Sensor-Daten aus dem SIMATIC MES und den historischen Wartungsdaten könnten wir ein **Machine-Learning-Modell** für vorausschauende Wartung trainieren. Hier würde ich **Azure Machine Learning** und **Azure Databricks** vorschlagen – beides hatten wir in Phase 1 bewusst ausgeklammert, um den Scope zu kontrollieren. Unser Data-Engineering-Team unter Anna Richter hat die nötige ML-Erfahrung.

3. **Supply-Chain-KPIs**: Das ließe sich gut in das bestehende Dashboard-Framework integrieren. Katharina Schmidt könnte die UX für die erweiterten Dashboards designen.

Ich schlage einen **Phase-2-Workshop am 17.12.** vor (ganzer Tag, 09:00–16:00). Wir könnten uns bei Ihnen in Sindelfingen treffen, damit wir die Plattform direkt mit Ihren Fachabteilungen durchsprechen können.

Dr. Schreiber wird ebenfalls teilnehmen – er hat großes Interesse an der Predictive-Maintenance-Lösung und sieht darin ein Referenzprojekt für TechVision.

Thomas Krüger wird in den nächsten Tagen einen **Rahmenvertrag für Phase 2** vorbereiten, damit wir Anfang Januar nahtlos weitermachen können.

Herzliche Grüße
Sandra Hoffmann
CTO, TechVision GmbH

---

## Message 4

**From:** Hans Müller <h.mueller@mueller-maschinenbau.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**CC:** Thomas Krüger <t.krueger@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-12-08 15:47

Liebe Frau Hoffmann,

der **17.12. passt hervorragend** für den Workshop. Ich lade von unserer Seite den Produktionsleiter (Herr Steiner), die IT-Leiterin (Frau Dr. Krause), und unseren CFO (Herr Dr. Becker) ein. So haben wir alle relevanten Stakeholder am Tisch.

Zum Thema **Predictive Maintenance**: Das ist auch für mich das spannendste Thema. Wir haben aktuell an unseren 12 CNC-Fräsmaschinen (DMG MORI) und 8 Drehmaschinen ungeplante Stillstandszeiten von ca. **3-4% der Produktionszeit**. Wenn wir das um auch nur die Hälfte reduzieren könnten, wäre das ein jährlicher Einspareffekt von geschätzt **250.000-350.000 EUR**. Das Business Case für Phase 2 schreibt sich also fast von selbst.

Zum **Dashboard-Performance-Thema**: Lisas Vorschlag mit dem Warm-Up Job klingt pragmatisch. Bitte setzen Sie das gerne direkt um. Ich habe auch von meinem IT-Team gehört, dass die Ladezeiten nach dem ersten Zugriff durchweg schnell sind – es scheint also wirklich nur der Cold Start zu sein.

Noch eine Anmerkung: Mein Aufsichtsrat hat mich gebeten, für die nächste Sitzung im Januar eine **Präsentation zum Projekt Aurora** vorzubereiten. Wäre es möglich, dass Sie uns dafür ein paar Slides mit den Key Metrics (Budget, Timeline, Datenqualitätsverbesserung, Reporting-Geschwindigkeit vs. alter Prozess) zuliefern? Das wäre ein guter Input und gleichzeitig eine Referenz für TechVision.

Ich freue mich auf den Workshop am 17.12.!

Mit freundlichen Grüßen
Hans Müller
