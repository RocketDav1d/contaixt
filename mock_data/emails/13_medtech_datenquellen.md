---
thread_id: email_thread_013
subject: "MedTech Analytics – Datenquellen & Integration"
---

## Message 1

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-10-15 09:45

Hallo zusammen,

nach unserem initialen Scoping-Workshop letzte Woche habe ich mich intensiver mit der **Datenintegration für MedTech Analytics** auseinandergesetzt und möchte meinen vorgeschlagenen Ansatz mit euch teilen.

Basierend auf den Requirements sehe ich **HL7 FHIR** als zentralen Integrationsstandard. Konkret würde ich folgenden Ansatz vorschlagen:

1. **FHIR-basierte Ingestion Layer:** Wir bauen einen zentralen FHIR-Server (HAPI FHIR R4) als Datendrehscheibe. Alle Quellsysteme liefern ihre Daten über standardisierte FHIR Resources an. Das betrifft vor allem `Patient`, `Encounter`, `Observation`, `Condition` und `DiagnosticReport` Resources.

2. **Mapping & Transformation:** Für die Transformation der Quelldaten in FHIR-konforme Strukturen würde ich auf **FHIR Mapping Language** setzen, ergänzt durch Custom Transformers für die ICD-10-GM-Kodierungen. Die ICD-10-Codes brauchen wir vor allem für die Diagnose-Aggregationen im Dashboard.

3. **ETL Pipeline:** Apache Airflow als Orchestrator für die täglichen und Near-Realtime-Loads. Die Pipeline würde Daten aus den Quellsystemen extrahieren, über den FHIR-Server validieren und dann in unser Analytics Data Warehouse (PostgreSQL mit TimescaleDB Extension) laden.

4. **Terminologie-Service:** Für die einheitliche Kodierung brauchen wir einen lokalen Terminologie-Server, der SNOMED CT, ICD-10-GM und LOINC Codes auflösen kann.

Robert, für den nächsten Schritt bräuchte ich eine detaillierte Übersicht eurer bestehenden Systemlandschaft – insbesondere welche FHIR-Versionen die einzelnen Systeme unterstützen und ob es proprietäre Schnittstellen gibt, die wir berücksichtigen müssen.

Ich habe ein technisches Konzeptdokument unter `/projects/medtech-analytics/data-integration-concept` in Confluence angelegt.

Viele Grüße
Anna

---

## Message 2

**From:** Robert Engel <r.engel@medtech-solutions.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-10-15 14:22

Hallo Anna,

danke für den detaillierten Vorschlag – das klingt technisch sehr solide. Hier die Übersicht unserer bestehenden Datenlandschaft:

Wir haben aktuell **drei Krankenhaus-Systeme** angebunden, die alle unterschiedliche Reifegrade bei FHIR haben:

1. **Klinikum Nordstadt (KIS: SAP ISH):** Unterstützt **FHIR R4** vollständig. Das ist unser modernstes System, ca. 180.000 Patientendatensätze. Die FHIR API ist produktionsreif und liefert saubere `Patient`, `Encounter` und `Condition` Resources. ICD-10-GM Kodierung ist durchgehend vorhanden.

2. **St. Elisabeth Krankenhaus (KIS: ORBIS):** Läuft noch auf **FHIR STU3** und hat teilweise proprietäre Extensions. Circa 95.000 Patientendatensätze. Die `Observation` Resources sind leider nicht standardkonform – die Lab-Werte kommen in einem Custom Format. LOINC-Codes sind nur zu etwa 60% gemappt, der Rest sind Hausnummern.

3. **Universitätsklinikum Westfalen (KIS: Cerner Millennium):** Hat grundsätzlich **FHIR R4**, aber die Implementation ist sehr eingeschränkt. Nur Read-Only-Zugriff über Bulk FHIR Export ($export Operation). Größtes System mit ca. 420.000 Patientendatensätzen. ICD-10 ist vorhanden, aber die `DiagnosticReport` Resources fehlen komplett – die Befunde liegen als PDF in einem proprietären DMS.

Zusätzlich haben wir noch ein **Laborinformationssystem (LIS)** von Roche, das HL7 v2.x Messages (ADT, ORU) per MLLP liefert. Das müsste separat integriert werden.

Die Gesamtdatenmenge liegt bei ca. **695.000 Patientendatensätzen** mit insgesamt rund **12 Millionen Observations** über die letzten 5 Jahre. Tägliches Wachstum ist etwa 8.000-10.000 neue Observations.

Ich stelle euch den technischen Zugang zu den Testsystemen bis Ende der Woche bereit.

Beste Grüße
Robert Engel

---

## Message 3

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-10-16 08:30

Hallo zusammen,

bevor wir technisch weiter in die Tiefe gehen, muss ich hier **dringend die DSGVO-Thematik** adressieren. Ich habe mir Annas Konzept und Roberts Systemübersicht angeschaut, und es gibt mehrere kritische Punkte:

1. **Patientendaten sind besondere Kategorien personenbezogener Daten** (Art. 9 DSGVO). Wir reden hier über Gesundheitsdaten von fast 700.000 Patienten. Die Rechtsgrundlage für die Verarbeitung muss glasklar dokumentiert sein. Robert, habt ihr von allen drei Kliniken eine **Auftragsverarbeitungsvereinbarung (AVV)** gemäß Art. 28 DSGVO?

2. **Pseudonymisierung ist Pflicht**, nicht optional. Bevor irgendwelche Patientendaten unser Analytics System erreichen, müssen sie pseudonymisiert werden. Das betrifft alle direkt identifizierenden Merkmale: Name, Geburtsdatum, Adresse, Versichertennummer. Gemäß unserer **TechVision Data Protection Guidelines (v3.1)** ist bei Gesundheitsdaten mindestens **k-Anonymität mit k≥5** erforderlich.

3. **Datenhaltung und Löschkonzept:** Wir brauchen ein dokumentiertes Löschkonzept. Wie lange dürfen aggregierte Daten im Analytics Dashboard vorgehalten werden? Das muss mit den Datenschutzbeauftragten der Kliniken abgestimmt werden.

4. **Technische und organisatorische Maßnahmen (TOMs):** Für die FHIR-Server-Infrastruktur brauchen wir: Verschlüsselung at rest und in transit (TLS 1.3 minimum), Audit Logging aller Zugriffe, rollenbasierte Zugangskontrolle, und eine **Datenschutz-Folgenabschätzung (DSFA)** gemäß Art. 35 DSGVO – die ist bei Gesundheitsdaten in diesem Umfang zwingend.

5. **Standort der Datenverarbeitung:** Alle Server müssen in der EU stehen. Das gilt auch für Backup- und Disaster-Recovery-Standorte. Cloud Services von US-Anbietern sind nur mit entsprechenden EU-Datenresidenz-Guarantien zulässig.

Ich möchte hier niemanden ausbremsen, aber ohne saubere DSGVO-Compliance können wir dieses Projekt nicht starten. Ich schlage ein separates **Security & Privacy Review Meeting** vor, bevor wir mit der technischen Implementation beginnen.

Gruß
Tobias

---

## Message 4

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-10-17 10:15

Hallo Tobias,

absolut berechtigte Punkte – danke für die ausführliche Aufstellung. Ich habe mir Gedanken gemacht, wie wir die Pseudonymisierung technisch umsetzen können, und schlage folgende **Data Anonymization Pipeline** vor:

### Stufe 1: Pseudonymisierung am Eingang

Direkt im Ingestion Layer, **bevor** die Daten unseren FHIR-Server erreichen, implementieren wir einen **Pseudonymisierungs-Proxy**:

- Alle `Patient` Resources werden durch einen deterministischen Pseudonymisierungs-Service geleitet. Der Service generiert aus der Kombination Quellsystem + Patienten-ID ein **kryptografisches Pseudonym** (SHA-256 mit pepper). Die Zuordnungstabelle verbleibt ausschließlich beim jeweiligen Krankenhaus.
- Direkt identifizierende Attribute (Name, Adresse, Geburtsdatum, Versichertennummer) werden **entfernt oder generalisiert**. Geburtsdatum wird auf Geburtsjahrgang reduziert, Postleitzahl auf die ersten drei Stellen.
- ICD-10-Codes und LOINC-Codes bleiben erhalten, da sie für die Analytics essentiell sind und keine direkte Identifikation ermöglichen.

### Stufe 2: k-Anonymität-Validierung

Nach der Pseudonymisierung läuft ein **Validation Service**, der prüft, ob die k-Anonymität (k≥5) gewährleistet ist. Records, die unter den Schwellwert fallen (z.B. seltene Diagnosen in Kombination mit Altersgruppe und PLZ-Bereich), werden automatisch weiter generalisiert oder supprimiert.

### Stufe 3: Differential Privacy für Aggregationen

Für die Dashboard-Aggregationen implementieren wir zusätzlich **Differential Privacy** mit einem konfigurierbaren Epsilon-Wert. Das schützt gegen Re-Identifikation über statistische Angriffe, auch wenn jemand Zugang zu den aggregierten Daten bekommt.

### Audit Trail

Jeder Datenzugriff wird in einem separaten, append-only Audit Log protokolliert. Das Log erfasst: Wer hat wann auf welche pseudonymisierten Datensätze zugegriffen und warum (Purpose Binding gemäß DSGVO Art. 5 Abs. 1 lit. b).

Tobias, ich habe das Konzept unter `/projects/medtech-analytics/anonymization-pipeline` in Confluence dokumentiert. Kannst du das reviewen und mir Feedback geben? Für die DSFA würde ich vorschlagen, dass wir die gemeinsam erstellen – ich liefere den technischen Teil, du den rechtlichen.

Robert, wir bräuchten von den Kliniken die Information, ob sie den Pseudonymisierungs-Service selbst hosten möchten oder ob wir das übernehmen sollen. Das hat Auswirkungen auf die Architektur.

Viele Grüße
Anna

---

## Message 5

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Anna Richter <a.richter@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Robert Engel <r.engel@medtech-solutions.de>, Lisa Weber <l.weber@techvision-gmbh.de>
**Date:** 2025-10-18 09:00

Hallo zusammen,

ich habe sowohl Annas Integrationskonzept als auch die Anonymization Pipeline reviewed und möchte hier kurz das Go von meiner Seite geben – mit ein paar Ergänzungen.

**Zum Gesamtansatz:** Der dreistufige Anonymisierungsansatz von Anna ist genau richtig. Das Konzept entspricht unseren **TechVision Data Protection Guidelines (v3.1)** und geht an einigen Stellen sogar darüber hinaus, was bei Gesundheitsdaten absolut angemessen ist. Differential Privacy on top der k-Anonymität ist Best Practice und wird uns auch im Audit gut dastehen lassen.

**Zur Architektur:** Ich unterstütze den HAPI FHIR Server als zentrale Datendrehscheibe. Ein paar Punkte dazu:

1. **FHIR Version Harmonisierung:** Wir nehmen **FHIR R4 als Target**. Für das St. Elisabeth System (STU3) brauchen wir einen Konvertierungslayer. Anna, bitte schau dir die **HAPI FHIR Converter Library** an – die kann STU3→R4 Transformationen out of the box.

2. **HL7 v2.x Integration:** Für das Roche LIS würde ich einen **HL7 v2 to FHIR Converter** empfehlen. Microsoft hat da ein Open Source Tool auf GitHub, das wir evaluieren sollten. Das passt auch gut zu unserem Database Standards Document, in dem wir FHIR als primären Healthcare-Standard definiert haben.

3. **Infrastruktur:** Alle Komponenten laufen auf unserer **Azure Germany West Central** Region. Ich habe das bereits mit unserem Azure Account Manager abgeklärt – wir bekommen dedizierte Ressourcen mit EU-Datenresidenz-Garantie. Das deckt Tobias' Anforderung bezüglich Datenstandort ab.

4. **Timeline:** Ich schlage vor, dass wir die Anonymisierung Pipeline als **Sprint 1 Deliverable** priorisieren. Ohne die kommen wir nicht an echte Testdaten, und ohne echte Testdaten können wir das Dashboard nicht vernünftig entwickeln.

Tobias, bitte plane das Security & Privacy Review Meeting für nächste Woche ein. Ich möchte, dass wir die DSFA innerhalb von zwei Wochen abschließen, damit wir den Entwicklungsplan nicht gefährden.

Lisa, bitte update den Project Plan entsprechend – die Anonymisierungs-Pipeline wird ein eigener Workstream.

Beste Grüße
Sandra
