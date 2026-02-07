---
thread_id: email_thread_004
subject: "Aurora – Probleme bei der Datenmigration"
---

## Message 1

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-10-08 07:52

Guten Morgen zusammen,

ich muss leider ein **ernstes Problem bei der Datenmigration** melden, das wir gestern Abend beim ersten Full Load der ERP-Daten entdeckt haben.

**Problem 1: Encoding Issues**
Die Oracle DB von Müller Maschinenbau verwendet **NLS_CHARACTERSET = WE8ISO8859P1** (Latin1). Unsere Azure Data Lake Storage und Synapse setzen auf **UTF-8**. Bei der Migration über Azure Data Factory treten **Encoding-Fehler** bei allen Datensätzen auf, die deutsche Sonderzeichen (ä, ö, ü, ß) oder französische Akzente (è, é, ê) enthalten.

Betroffene Tabellen:
- `CUSTOMERS` – Firmenname, Ansprechpartner, Adressfelder (~35% der Datensätze betroffen)
- `ARTICLES` – Artikelbeschreibungen (~20% betroffen)
- `ORDERS` – Kommentarfelder (~15% betroffen)

Ich habe einen ersten Workaround getestet: Ein **Pre-Copy Script** in der ADF Pipeline, das `CONVERT()` auf die relevanten Spalten anwendet. Das funktioniert für die meisten Fälle, aber bei ca. **2.400 Datensätzen** in der `CUSTOMERS`-Tabelle gibt es Zeichen, die weder in Latin1 noch in UTF-8 gültig sind – vermutlich Datenmüll aus historischen manuellen Eingaben.

**Problem 2: Performance**
Der Full Load der `ORDERS`-Tabelle (2.1 Millionen Datensätze, ca. 180 GB) hat über die Self-Hosted Integration Runtime **14 Stunden** gedauert. Das ist deutlich zu langsam für ein Go-Live-Szenario, in dem wir maximal ein Wartungsfenster von 4 Stunden haben.

Ich brauche Unterstützung:
- Felix: Können wir die ADF Pipeline parallelisieren (Partitioned Read über `ORDER_ID` Ranges)?
- Daniel: Kannst du dir die Encoding-Probleme genauer anschauen und ein Cleanup Script schreiben?
- Markus: Ist die Self-Hosted Integration Runtime auf einer ausreichend dimensionierten VM? Aktuell läuft sie auf einer `Standard_D4s_v3` (4 vCPUs, 16 GB RAM).

Ich habe die detaillierten Logs in Azure Monitor unter dem Workspace `aurora-dev-logs` abgelegt.

Viele Grüße
Anna

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-10-08 09:34

Hi Anna,

danke für die ausführliche Analyse. Das Encoding-Problem kenne ich leider von anderen Oracle-Migrationen.

Ich habe mir die Logs angeschaut und **zusätzlich ein weiteres Problem** gefunden:

**Problem 3: Corrupted Records**
Bei der Validierung des Bronze Layer habe ich festgestellt, dass ca. **3% der ~2 Millionen Datensätze** in der `ORDERS`-Tabelle **inkonsistente Foreign Keys** haben. Konkret:
- 41.203 Datensätze referenzieren `CUSTOMER_ID`s, die in der `CUSTOMERS`-Tabelle nicht existieren
- 12.847 Datensätze haben `ORDER_DATE` Werte, die vor 1990 liegen (das Unternehmen wurde 1995 gegründet)
- 8.391 Datensätze haben `NULL` in Pflichtfeldern (`TOTAL_AMOUNT`, `STATUS`)

Das deutet auf **historischen Datenmüll** hin, der über die Jahre akkumuliert wurde. Die Oracle DB hatte offensichtlich keine Foreign Key Constraints auf Datenbankebene aktiviert – die Validierung lief nur in der Anwendungsschicht.

Zum Thema **Performance**: Ja, wir können den Full Load über **Partitioned Copy** in ADF parallelisieren. Ich schlage vor:
- Partitionierung nach `ORDER_ID` Ranges (z.B. 10 Partitionen à 200k Datensätze)
- **Parallel Degree: 8** in der ADF Copy Activity
- Das sollte die Ladezeit auf ca. 2-3 Stunden reduzieren

@Markus: Bitte scale die Integration Runtime VM auf mindestens `Standard_D8s_v3` (8 vCPUs, 32 GB RAM) hoch. Besser wäre `Standard_D16s_v3` für den Full Load.

Wir sollten heute Nachmittag ein **War Room Meeting** machen, um die Probleme systematisch anzugehen. Lisa, kannst du das einrichten?

Gruß
Felix

---

## Message 3

**From:** Daniel Wolff <d.wolff@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-10-09 11:18

Hallo zusammen,

ich habe gestern Abend und heute Morgen an einem **Cleanup Script** für die Encoding- und Data-Quality-Probleme gearbeitet. Das Script liegt im Repo unter `aurora-data/scripts/data_cleanup.py`.

Hier ist, was es macht:

**1. Encoding Cleanup (`--mode=encoding`)**
- Erkennt automatisch die Quell-Kodierung pro Spalte mittels `chardet`-Library
- Konvertiert von Latin1/Windows-1252 nach UTF-8
- Für nicht-konvertierbare Zeichen: Ersetzung durch Unicode Replacement Character (U+FFFD) und Logging in eine Audit-Tabelle
- Ergebnis: Von den 2.400 problematischen Datensätzen konnte ich **2.358 sauber konvertieren**. Die restlichen 42 haben tatsächlich binären Datenmüll in den Text-Feldern.

**2. Data Quality Cleanup (`--mode=quality`)**
- Orphaned Foreign Keys: Mapping auf einen `UNKNOWN_CUSTOMER` Platzhalter-Datensatz (nach Rücksprache mit dem Kunden klärbar)
- Ungültige Datumswerte: Auf `NULL` setzen und in einer `data_quality_issues`-Tabelle protokollieren
- NULL-Pflichtfelder: `TOTAL_AMOUNT` auf 0.00 setzen, `STATUS` auf 'UNKNOWN'

**Felix, könntest du bitte ein Code Review machen?** Besonders die Encoding-Erkennung und das Error Handling würde ich gerne von dir prüfen lassen. Der PR ist unter `aurora-data#47` offen.

Ein paar offene Fragen:
- Sollen wir die bereinigten Datensätze im Bronze Layer überschreiben oder als separate Version im Silver Layer ablegen?
- Wie gehen wir mit den 42 nicht-konvertierbaren Datensätzen um? Mein Vorschlag: In eine Quarantäne-Tabelle verschieben und mit dem Kunden klären.

Grüße
Daniel

---

## Message 4

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Daniel Wolff <d.wolff@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-10-09 14:45

Hi Daniel,

super Arbeit mit dem Cleanup Script! Ich habe den PR kurz überflogen und es sieht solide aus.

Zu deinen Fragen:

**Bronze vs. Silver Layer:** Auf keinen Fall den Bronze Layer überschreiben! Das ist unser **Single Source of Truth** und muss immutable bleiben. Die Bereinigung gehört in den **Silver Layer** – genau dafür haben wir die Medallion-Architektur. Im Bronze Layer liegen die Rohdaten exakt so, wie sie aus der Oracle DB kommen. Die Transformation und Bereinigung passiert in der Bronze-to-Silver Pipeline.

**Quarantäne-Tabelle:** Gute Idee. Ich würde das formalisieren und eine generische **Data Quality Pipeline** vorschlagen:

```
Bronze → Validation Rules → Silver (valid) + Quarantine (invalid)
```

Die Validation Rules definieren wir als **YAML-Konfiguration**, z.B.:

```yaml
tables:
  orders:
    rules:
      - column: CUSTOMER_ID
        type: foreign_key
        reference: customers.CUSTOMER_ID
        on_fail: quarantine
      - column: ORDER_DATE
        type: date_range
        min: "1995-01-01"
        max: "2025-12-31"
        on_fail: quarantine
      - column: TOTAL_AMOUNT
        type: not_null
        on_fail: default
        default_value: 0.00
```

So können wir die Regeln pro Tabelle konfigurieren, ohne Code zu ändern. Das macht das System auch für zukünftige Datenquellen (MES, SAP) wiederverwendbar.

Ich schreibe den **Data Quality Framework** als eigenes Modul und integriere es in die ADF Pipeline. Schätzung: 3-4 Tage.

Grüße
Anna

---

## Message 5

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**CC:** Anna Richter <a.richter@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-10-10 08:15

Hallo Sandra,

ich möchte dich über ein **Timeline-Risiko** bei Projekt Aurora informieren.

**Situation:** Bei der ersten Datenmigration sind erhebliche Datenqualitätsprobleme aufgetreten (Encoding-Fehler, korrupte Datensätze, Performance-Probleme). Details siehe Thread unten.

**Impact:** Das Team schätzt den zusätzlichen Aufwand auf **8-12 Personentage** für:
- Data Cleanup Script und Code Review (Daniel + Felix): 3 PT
- Data Quality Framework (Anna): 4 PT
- Integration Runtime Optimization und Performance Tuning (Markus + Felix): 2-3 PT
- Klärung der Quarantäne-Datensätze mit dem Kunden (Lisa + Anna): 1-2 PT

**Auswirkung auf Timeline:** Sprint 2 wird voraussichtlich **1 Woche länger** brauchen. Der Go-Live-Termin Anfang Dezember ist noch machbar, aber der Buffer ist jetzt deutlich kleiner.

**Mitigations-Maßnahmen:**
1. War Room Meeting hat gestern stattgefunden, klarer Action Plan steht
2. Daniel und Anna arbeiten parallel an Cleanup und Data Quality Framework
3. Markus optimiert die Infrastructure (größere VM, Parallelisierung)
4. Ich habe mit Hans Müller einen Termin für Donnerstag, um die Datenqualitätsprobleme und die Quarantäne-Datensätze zu besprechen

Soll ich das auch im nächsten **Steering Committee** am 15.10. auf die Agenda setzen?

Viele Grüße
Lisa
