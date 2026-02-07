---
thread_id: email_thread_015
subject: "MedTech – Performance-Probleme Dashboard Queries"
---

## Message 1

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>
**Date:** 2025-11-25 08:15

Hallo zusammen,

ich muss leider ein **Performance-Problem** eskalieren, das uns aktuell beim MedTech Analytics Dashboard blockiert.

Seit wir letzte Woche die Testdaten aus allen drei Kliniken in die Staging-Umgebung geladen haben (ca. 695.000 pseudonymisierte Patientendatensätze, 12 Mio Observations), sind die **Dashboard Queries inakzeptabel langsam**. Hier die konkreten Zahlen aus meinem Profiling:

### Betroffene Queries

1. **ICD-10 Aggregation** (Diagnose-Explorer View): **5.2 Sekunden**
   ```sql
   SELECT icd10_code, icd10_chapter, COUNT(DISTINCT patient_pseudo_id) as patient_count,
          AVG(length_of_stay) as avg_los
   FROM encounters e
   JOIN conditions c ON e.encounter_id = c.encounter_id
   WHERE e.clinic_id IN (1,2,3) AND e.admission_date BETWEEN '2025-01-01' AND '2025-09-30'
   GROUP BY icd10_code, icd10_chapter
   ORDER BY patient_count DESC;
   ```
   Der `EXPLAIN ANALYZE` zeigt einen **Sequential Scan** auf der `conditions`-Tabelle (2.8 Mio Rows) und einen **Hash Join** mit `encounters`, der 1.2 GB Memory verbraucht.

2. **Klinikvergleich mit Periodenvergleich**: **7.8 Sekunden**
   Die Query muss zwei Zeiträume parallel aggregieren und dann Cross-Joinen. Das explodiert die Intermediate Results.

3. **Sankey Patientenfluss**: **6.1 Sekunden**
   Hier ist das Problem die dreifache Self-Join auf `encounters` (Aufnahme → Stationsverlegungen → Entlassung). Bei 695k Patienten mit durchschnittlich 3.2 Stationswechseln pro Aufenthalt erzeugt das Millionen von Zwischenergebnissen.

4. **Monatsreport-Generierung** (alle KPIs auf einmal): **23 Sekunden**
   Das ist eine Kombination aus allen oben genannten Queries plus weitere Aggregationen.

Die Zielwerte laut unserer **nicht-funktionalen Anforderungen** sind: <500ms für einzelne Dashboard-Queries, <3s für den Monatsreport. Wir sind also um **Faktor 10-25 drüber**.

Ich habe das Datenbankschema nochmal mit unserem **Database Standards Document** abgeglichen und vermute, dass wir bei der initialen Schema-Erstellung einige Indexes vergessen haben. Anna, kannst du dir das mal anschauen? Du kennst das Datenmodell am besten.

Gruß
Felix

---

## Message 2

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>
**Date:** 2025-11-25 14:30

Hi Felix,

ich habe mir die Staging-Datenbank angeschaut und das Problem ist ziemlich klar. Hier meine Analyse und der Lösungsvorschlag:

### Root Cause Analysis

1. **Fehlende Indexes:** Die `conditions`-Tabelle hat nur einen Primary Key Index. Es fehlen:
   - Composite Index auf `(encounter_id, icd10_code)` – der wird für den JOIN und GROUP BY gebraucht
   - Index auf `icd10_chapter` – für die Kapitel-Aggregation im Diagnose-Explorer
   - Partial Index auf `encounters(clinic_id, admission_date)` – für die Zeitraumfilterung

2. **Fehlende Partitionierung:** Die `observations`-Tabelle mit 12 Mio Rows ist nicht partitioniert. Bei zeitbasierten Queries (die häufigste Query-Pattern) muss PostgreSQL immer die gesamte Tabelle scannen. Wir sollten **Range Partitioning nach observation_date** einführen (monatliche Partitionen).

3. **Kein Query Plan Caching:** Die häufigsten Aggregationen werden bei jedem Seitenaufruf komplett neu berechnet. Das ist bei Daten, die sich nur einmal täglich ändern (Batch-Load über die FHIR Pipeline), völlig unnötig.

### Lösungsvorschlag

#### Sofortmaßnahmen (heute)

```sql
-- Composite Indexes für conditions
CREATE INDEX CONCURRENTLY idx_conditions_encounter_icd10
    ON conditions(encounter_id, icd10_code);
CREATE INDEX CONCURRENTLY idx_conditions_icd10_chapter
    ON conditions(icd10_chapter);

-- Covering Index für encounters Zeitraumfilter
CREATE INDEX CONCURRENTLY idx_encounters_clinic_admission
    ON encounters(clinic_id, admission_date)
    INCLUDE (patient_pseudo_id, length_of_stay, discharge_type);

-- Index für Sankey-Query (Stationsverlegungen)
CREATE INDEX CONCURRENTLY idx_transfers_encounter_sequence
    ON station_transfers(encounter_id, transfer_sequence)
    INCLUDE (station_id, transfer_date);
```

#### Materialized Views (diese Woche)

Für die Dashboard-Aggregationen schlage ich **Materialized Views** vor, die einmal täglich nach dem Batch-Load refreshed werden:

```sql
-- MV für ICD-10 Aggregation
CREATE MATERIALIZED VIEW mv_icd10_aggregation AS
SELECT clinic_id, icd10_code, icd10_chapter,
       date_trunc('month', admission_date) as admission_month,
       COUNT(DISTINCT patient_pseudo_id) as patient_count,
       AVG(length_of_stay) as avg_los,
       COUNT(*) as encounter_count
FROM encounters e
JOIN conditions c ON e.encounter_id = c.encounter_id
GROUP BY clinic_id, icd10_code, icd10_chapter, date_trunc('month', admission_date);

-- MV für Patientenfluss-Sankey
CREATE MATERIALIZED VIEW mv_patient_flow AS
SELECT clinic_id,
       date_trunc('month', admission_date) as admission_month,
       admission_type, first_station, last_station, discharge_type,
       COUNT(DISTINCT patient_pseudo_id) as patient_count,
       AVG(length_of_stay) as avg_los
FROM (
    SELECT e.clinic_id, e.admission_date, e.admission_type,
           e.patient_pseudo_id, e.length_of_stay, e.discharge_type,
           FIRST_VALUE(st.station_id) OVER (PARTITION BY e.encounter_id ORDER BY st.transfer_sequence) as first_station,
           LAST_VALUE(st.station_id) OVER (PARTITION BY e.encounter_id ORDER BY st.transfer_sequence
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as last_station
    FROM encounters e
    JOIN station_transfers st ON e.encounter_id = st.encounter_id
) sub
GROUP BY clinic_id, date_trunc('month', admission_date),
         admission_type, first_station, last_station, discharge_type;
```

#### Refresh-Strategie

Der Materialized View Refresh wird in die **Airflow DAG** integriert, direkt nach dem täglichen FHIR-Import. Geschätzte Refresh-Dauer: ca. 45 Sekunden pro View bei aktuellem Datenvolumen.

#### Observations-Partitionierung (nächste Woche)

Die Tabellen-Partitionierung implementiere ich als separate Alembic Migration. Das erfordert einen kurzen Maintenance-Window, da die bestehende Tabelle umgebaut werden muss. Voraussichtliche Dauer: ca. 15 Minuten.

Felix, ich erstelle jetzt die Alembic Migration für die Indexes. Kannst du die danach auf Staging deployen und die Queries nochmal benchmarken?

Viele Grüße
Anna

---

## Message 3

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>
**Date:** 2025-11-27 16:45

Hi Anna,

kurzes Update: Ich habe sowohl die **Indexes als auch die Materialized Views** auf der Staging-Umgebung deployed und intensiv getestet. Die Ergebnisse sind **spektakulär**.

### Benchmark-Ergebnisse (vorher → nachher)

| Query | Vorher | Nachher | Verbesserung |
|-------|--------|---------|--------------|
| ICD-10 Aggregation | 5.2s | **85ms** | 61x schneller |
| Klinikvergleich + Periodenvergleich | 7.8s | **142ms** | 55x schneller |
| Sankey Patientenfluss | 6.1s | **67ms** | 91x schneller |
| Monatsreport (komplett) | 23.0s | **195ms** | 118x schneller |

Alle Werte sind Durchschnitt über 100 Runs mit warmem Cache. Auch Cold Cache Werte liegen unter 500ms. Wir sind damit **deutlich unter den nicht-funktionalen Anforderungen** (<500ms für Einzel-Queries, <3s für Monatsreport).

### Was genau den Unterschied gemacht hat

1. **Indexes allein** haben die ICD-10 Aggregation schon von 5.2s auf 1.1s gebracht (Sequential Scan → Index Scan). Aber bei den komplexeren Queries (Klinikvergleich, Sankey) war der Effekt weniger dramatisch – da kamen wir auf 2-3s.

2. **Materialized Views** waren der eigentliche Game Changer. Da das Dashboard ohnehin nur tagesaktuelle Daten zeigt, ist der Zugriff auf vorberechnete Aggregationen perfekt. Die Queries auf die MVs sind im Grunde einfache SELECTs mit WHERE-Filtern auf schon aggregierte Daten.

3. **Covering Index** auf `encounters` hat den Klinikvergleich nochmal beschleunigt, weil PostgreSQL die `length_of_stay` und `discharge_type` direkt aus dem Index lesen kann (Index-Only Scan).

### Refresh-Performance

Der `REFRESH MATERIALIZED VIEW CONCURRENTLY` dauert:
- `mv_icd10_aggregation`: 28 Sekunden
- `mv_patient_flow`: 41 Sekunden

Da wir `CONCURRENTLY` verwenden, blockiert der Refresh keine laufenden Queries. Ich habe das in den Airflow DAG integriert – der Refresh startet automatisch nach dem FHIR-Import um 03:00 Uhr.

### Nächste Schritte

1. Die **Observations-Partitionierung** steht noch aus. Bei den aktuellen Query-Zeiten ist das nicht mehr dringend, aber für die Skalierbarkeit (Robert hat erwähnt, dass im nächsten Jahr zwei weitere Kliniken dazukommen) sollten wir das trotzdem umsetzen.

2. Ich habe ein **Dashboard Performance Monitoring** in Grafana eingerichtet. Alle Dashboard Queries werden jetzt mit Execution Time und Query Plan geloggt. Alert bei >500ms.

Anna, exzellente Analyse – die fehlenden Indexes hätten uns ohne dich noch tagelang beschäftigt. Die Migration ist unter `/alembic/versions/003_medtech_performance_indexes.py` eingecheckt.

Gruß
Felix

---

## Message 4

**From:** Robert Engel <r.engel@medtech-solutions.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-11-28 10:20

Hallo Felix, hallo Anna,

ich habe gestern Nachmittag die Staging-Umgebung intensiv getestet und kann die Performance-Verbesserung aus **Nutzerperspektive** voll bestätigen. Das Dashboard fühlt sich jetzt so an, wie man es von einem modernen Analytics Tool erwartet – **instant Response bei jedem Klick**.

Ein paar konkrete Beobachtungen:

1. **Diagnose-Explorer:** Der Drill-Down von ICD-10-Kapitel bis zum Viersteller ist jetzt komplett flüssig. Vorher hatte ich bei jedem Klick einen spürbaren Loading-Spinner (teilweise 5-6 Sekunden), jetzt ist das Ergebnis da, bevor ich überhaupt realisiere, dass ich geklickt habe. Dr. Bauer wird begeistert sein.

2. **Sankey-Diagramm:** Die Patientenfluss-Visualisierung, die letzte Woche praktisch unbenutzbar war (ewig langer Ladevorgang, Browser ist fast eingefroren), funktioniert jetzt einwandfrei. Auch wenn ich zwischen verschiedenen Zeiträumen und Kliniken wechsle, kommt die Antwort sofort.

3. **Monatsreport:** Ich habe den automatisierten PDF-Export getestet – der komplette Report mit allen Kliniken und allen KPIs wird in **unter 3 Sekunden** generiert (inklusive PDF-Rendering). Das ist für den monatlichen Aufsichtsratsbericht von Dr. Bauer absolut ausreichend.

4. **Periodenvergleich:** Auch der Q3/2025 vs. Q2/2025 Vergleich ist jetzt flüssig. Die Side-by-Side Charts laden ohne merkliche Verzögerung.

Ich habe das Feedback zusammen mit Screenshots an **Thomas Wendt** (Head of Controlling) und **Dr. Kerstin Bauer** (Medical Director) weitergeleitet. Thomas hat zurückgeschrieben: *"Endlich ein Analytics Tool, das nicht langsamer ist als mein Excel."* – Ich denke, das ist das größte Kompliment, das ein Controller machen kann.

Von unserer Seite ist die Staging-Umgebung damit **abgenommen** für den nächsten Schritt Richtung UAT. Lisa, wann können wir den User Acceptance Test mit den Klinik-Controllern starten?

Nochmals danke an Anna und Felix für die schnelle Analyse und Umsetzung. Die Turnaround-Zeit von Problem-Report bis Fix in unter drei Tagen ist beeindruckend.

Beste Grüße
Robert Engel
