---
thread_id: email_thread_014
subject: "MedTech – Dashboard UX Review"
---

## Message 1

**From:** Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**To:** Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-11-05 10:30

Hallo zusammen,

ich habe die ersten **Mockups für das MedTech Analytics Dashboard** fertiggestellt und würde euch bitten, diese zu reviewen. Die Figma-Datei liegt unter `/projects/medtech-analytics/ux/dashboard-v1` in unserem Design Space.

Hier eine Zusammenfassung der drei Hauptviews:

### 1. Overview Dashboard
Der Einstiegspunkt zeigt die wichtigsten KPIs auf einen Blick: **Gesamtpatientenzahl** (pseudonymisiert, versteht sich), **durchschnittliche Verweildauer**, **Top-10 Diagnosen nach ICD-10-Kategorie** und **Belegungsquoten** pro Klinik. Die Daten werden als Kombination aus Scorecards und einem Balkendiagramm visualisiert. Zeitraumfilter (7 Tage, 30 Tage, Quartal, Jahr) sind oben rechts platziert.

### 2. Diagnose-Explorer
Hier können Nutzer die **ICD-10-GM Kapitelstruktur** navigieren – von der Kapitel-Ebene (z.B. "IX – Krankheiten des Kreislaufsystems") bis runter zu den einzelnen Dreistellern und Vierstellern. Jede Ebene zeigt Häufigkeitsverteilungen als Treemap-Chart. Daneben gibt es einen **Zeitverlaufsgraph**, der die Entwicklung der selektierten Diagnosen über die letzten 12 Monate zeigt.

### 3. Klinikvergleich
Eine Vergleichsansicht, die bis zu drei Kliniken nebeneinander stellt. Verglichen werden: Fallzahlen, Case Mix Index, durchschnittliche Verweildauer und Wiederaufnahmerate innerhalb von 30 Tagen. Die Visualisierung nutzt Radar-Charts für den multidimensionalen Vergleich.

Farbschema folgt dem **MedTech Solutions Corporate Design** (Primärfarbe: #0D5C8F, Sekundär: #2EA8A0). Alle Visualisierungen sind WCAG 2.1 AA konform, inklusive Color Blind Safe Palettes für die Diagramme.

Ich habe bewusst auf **Dark Mode** verzichtet, da die Zielgruppe (Klinikmanagement, Controller) typischerweise in hellen Büroumgebungen arbeitet und der medizinische Kontext eher ein Clean/Light Design erwartet.

Robert, ich würde mich besonders über Feedback zu den KPIs freuen – sind das die richtigen Metriken für eure Stakeholder?

Viele Grüße
Katharina

---

## Message 2

**From:** Robert Engel <r.engel@medtech-solutions.de>
**To:** Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-11-06 11:15

Hallo Katharina,

erstmal großes Lob – die Mockups sehen professionell aus und treffen den Ton sehr gut. Das Farbschema passt perfekt zu unserem Branding, und die Treemap für die ICD-10-Navigation ist eine clevere Lösung.

Ich habe die Mockups gestern mit unserem **Medical Director Dr. Kerstin Bauer** und dem **Head of Controlling Thomas Wendt** durchgesprochen. Hier das gesammelte Feedback:

### Must-Haves (ohne geht's nicht live)

1. **Drill-Down Capability:** Die Stakeholder wollen von jeder Aggregation aus direkt in die darunterliegende Detailebene klicken können. Beispiel: Klick auf "Kreislauferkrankungen" im Overview → Aufschlüsselung nach ICD-10-Dreistellern → Klick auf einen Dreisteller → Liste der pseudonymisierten Encounters mit Verweildauer, Altersgruppe und Outcome. Das muss durchgehend funktionieren, auch im Klinikvergleich.

2. **PDF Export:** Jede View muss als **formatierter PDF-Report** exportierbar sein. Dr. Bauer braucht das für die monatlichen Aufsichtsratssitzungen. Der Export sollte das MedTech Logo, Zeitstempel, ausgewählte Filter und eine Legende enthalten. Idealerweise auch als **automatisierter Monatsreport**, der per E-Mail versendet wird.

3. **Zeitraumfilter mit Vergleich:** Neben dem einfachen Zeitraumfilter brauchen wir einen **Periodenvergleich** – also "Q3/2025 vs. Q3/2024". Das ist für die Controller essentiell, um Trends und Veränderungen zu erkennen.

### Nice-to-Haves

4. **FHIR Resource Preview:** Für die technisch affinen Nutzer wäre es hilfreich, wenn man bei einem Encounter die zugrunde liegende FHIR Resource als JSON anschauen könnte (natürlich pseudonymisiert). Das ist für Debugging und Datenqualitätsprüfung relevant.

5. **Custom Dashboard Builder:** Langfristig wäre ein Drag-and-Drop Dashboard Builder toll, wo Nutzer ihre eigenen Views zusammenstellen können. Das muss aber nicht im MVP sein.

Zum Thema **Charting:** Thomas Wendt hat speziell nachgefragt, ob wir auch **Sankey-Diagramme** für Patientenflüsse (Aufnahme → Station → Entlassung/Verlegung) darstellen können. Das wäre extrem wertvoll für die Prozessoptimierung.

Freue mich auf die nächste Iteration!

Beste Grüße
Robert

---

## Message 3

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-11-07 09:40

Hi zusammen,

ich möchte kurz zum Thema **Charting Library** Stellung nehmen, weil Roberts Feedback die Anforderungen nochmal deutlich erweitert hat.

Katharina, in deinen Mockups hast du die Visualisierungen library-agnostisch designed, aber im letzten UX-Sync hattest du **Chart.js** als erste Wahl erwähnt. Nach Roberts Feedback (Drill-Down, Sankey-Diagramme, Treemaps, Radar-Charts, PDF-Export) würde ich dringend empfehlen, auf **Apache ECharts** umzusteigen. Hier meine Argumentation:

### Warum ECharts statt Chart.js

1. **Sankey-Diagramme:** Chart.js hat dafür kein native Support. Man bräuchte ein Third-Party-Plugin (`chartjs-chart-sankey`), das nicht gut maintained ist und nur Basic Features bietet. ECharts hat **Sankey nativ** mit voller Interaktivität (Hover, Highlight, Tooltips mit Custom Content).

2. **Treemaps:** Gleiche Geschichte – Chart.js braucht ein Plugin, ECharts kann das out of the box. Und die ECharts Treemaps unterstützen **Multi-Level Drill-Down**, was perfekt zur ICD-10-Kapitelnavigation passt.

3. **Drill-Down generell:** ECharts hat ein ausgereiftes Event-System mit `click`, `datazoom`, `legendselectchanged` Events. Wir können damit den gesamten Drill-Down-Flow implementieren, ohne Custom Logic um die Library herumzubauen.

4. **PDF Export:** ECharts rendert auf Canvas **und** SVG. Für den PDF-Export können wir die SVG-Variante nehmen und mit einer Library wie **jsPDF** oder **Puppeteer** (server-side) hochauflösende PDFs generieren. Chart.js kann das prinzipiell auch, aber die SVG-Unterstützung ist bei ECharts deutlich besser.

5. **Performance:** Bei den Datenmengen, die Robert beschrieben hat (12 Millionen Observations), brauchen wir eine Library, die mit **Large Datasets** umgehen kann. ECharts hat `dataset`-basiertes Rendering und unterstützt progressive Loading. Chart.js wird bei >10.000 Datenpunkten spürbar langsam.

6. **Medical Visualizations:** ECharts ist im Healthcare-Bereich weit verbreitet (z.B. Johns Hopkins COVID Dashboard war ECharts-basiert). Es gibt eine aktive Community mit Healthcare-spezifischen Beispielen.

Die Bundle Size ist mit ~800KB (gzipped ~250KB) größer als Chart.js (~200KB), aber bei einem Analytics Dashboard, das ohnehin nicht auf mobile Performance optimiert sein muss, ist das vertretbar.

Ich habe einen kleinen **Proof of Concept** mit ECharts und den Mockup-Daten gebaut: `/projects/medtech-analytics/poc/echarts-demo`. Der Sankey-Chart für Patientenflüsse sieht wirklich gut aus.

Gruß
Felix

---

## Message 4

**From:** Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-11-08 08:50

Hallo zusammen,

Felix, du hast mich überzeugt – ich habe mir den ECharts PoC angeschaut und muss sagen, die Interaktivität ist wirklich eine andere Liga als Chart.js. Besonders der Sankey-Chart für die Patientenflüsse hat mich beeindruckt. Die Animationen und Hover-Effekte sind smooth und geben dem Dashboard einen sehr professionellen Look.

Ich habe daraufhin die **Mockups überarbeitet** und die revidierten Wireframes unter `/projects/medtech-analytics/ux/dashboard-v2` in Figma hochgeladen. Hier die wesentlichen Änderungen:

### Neue/Überarbeitete Views

1. **Overview Dashboard v2:** Der Drill-Down-Flow ist jetzt als **Breadcrumb-Navigation** oben visualisiert. Nutzer sehen immer, wo sie sich in der Datenhierarchie befinden (z.B. "Alle Kliniken → Klinikum Nordstadt → ICD-10 Kapitel IX → I25 Chronische ischämische Herzkrankheit"). Jeder Breadcrumb ist klickbar, um eine Ebene zurückzuspringen.

2. **Patientenfluss-View (NEU):** Ein dedizierter View mit dem Sankey-Diagramm. Links die Aufnahmeart (Notfall, Geplant, Verlegung), in der Mitte die Stationen, rechts der Outcome (Entlassung, Verlegung, Exitus). Filterbar nach Zeitraum, Klinik und ICD-10-Kapitel.

3. **PDF Report Template:** Ich habe ein Layout für den automatisierten Monatsreport entworfen. Enthält: Cover Page mit MedTech Logo und Berichtszeitraum, Executive Summary mit Top-5 KPIs, Detail-Seiten für jede Klinik, und einen Appendix mit der Datenbasis-Beschreibung.

4. **Periodenvergleich:** Der Zeitraumfilter hat jetzt einen Toggle "Vergleichsmodus". Wenn aktiv, erscheint ein zweiter Zeitraumwähler und alle Charts zeigen die Perioden nebeneinander (Side-by-Side für Balkendiagramme, Overlaid für Liniendiagramme).

### Accessibility Update

Ich habe die Color Palette nochmal überarbeitet, um auch bei den komplexeren ECharts-Visualisierungen die WCAG 2.1 AA Konformität sicherzustellen. Zusätzlich habe ich **Pattern Fills** als Alternative zu rein farbbasierten Unterscheidungen eingefügt – das ist im medizinischen Kontext besonders wichtig, da Ausdrucke oft in Schwarzweiß erfolgen.

Robert, ich würde vorschlagen, dass wir nächste Woche einen **30-minütigen Walkthrough** machen, bei dem ich die revidierten Wireframes live präsentiere. Wäre Dienstag oder Mittwoch möglich?

Felix, bezüglich der technischen Implementation: Können wir ein kurzes **Pairing** machen, um die ECharts-Konfiguration für den Drill-Down zu finalisieren? Ich will sicherstellen, dass die Animations und Transitions in meinen Designs auch technisch so umsetzbar sind.

Viele Grüße
Katharina
