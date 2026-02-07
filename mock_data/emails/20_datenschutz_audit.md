---
thread_id: email_thread_020
subject: "DSGVO-Audit Vorbereitung Q1 2026"
---

## Message 1

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-20 08:00

Hallo zusammen,

ich möchte euch frühzeitig informieren: Wir haben für **Q1 2026 ein externes DSGVO-Audit** durch den **TÜV Rheinland** beauftragt. Das Audit ist für die **Kalenderwoche 10 (03.-07. März 2026)** geplant und umfasst eine vollständige Prüfung unserer Datenschutz-Compliance nach DSGVO.

**Warum jetzt?**
1. Unser letztes Audit war 2023 – ein regelmäßiger 2-3-Jahres-Rhythmus ist Best Practice
2. Mit dem Aurora-Projekt verarbeiten wir zunehmend personenbezogene Daten aus externen Quellen (Gmail, Notion)
3. Mehrere unserer Enterprise-Kunden verlangen ein aktuelles Audit-Zertifikat
4. Der Büro-Umzug ändert unsere physischen Sicherheitsmaßnahmen – das muss dokumentiert werden

**Scope des Audits:**
- Verarbeitungsverzeichnis (Art. 30 DSGVO) – Vollständigkeit und Aktualität
- Technische und organisatorische Maßnahmen (TOMs) – Art. 32 DSGVO
- Datenschutz-Folgenabschätzungen (DPIAs) – insbesondere für KI/ML-Verarbeitung
- Auftragsverarbeitungsverträge (AVVs) – mit allen Sub-Processorn (OpenAI, Azure, Nango, Neo4j)
- Betroffenenrechte – Prozesse für Auskunft, Löschung, Portabilität
- Mitarbeiterdatenschutz – HR-Prozesse, Bewerberdaten
- Incident Response – Meldeprozesse bei Datenpannen

**Vorbereitung – Checkliste:**

Ich habe eine Checkliste erstellt, die wir bis **Ende Februar 2026** abarbeiten müssen. Die Verantwortlichkeiten verteile ich in einer separaten Mail, aber vorab die Kernbereiche:

| # | Thema | Status | Verantwortlich |
|---|-------|--------|----------------|
| 1 | Verarbeitungsverzeichnis aktualisieren | In Arbeit | Tobias |
| 2 | TOMs dokumentieren (inkl. neues Büro) | Offen | Tobias + Markus |
| 3 | DPIA für Aurora/GraphRAG-Pipeline | Offen | Tobias + Sandra |
| 4 | AVVs prüfen (OpenAI, Azure, Nango) | In Arbeit | Tobias |
| 5 | HR-Datenprozesse dokumentieren | Offen | Julia |
| 6 | Löschkonzept überprüfen | Offen | Tobias + Anna |
| 7 | Mitarbeiter-Schulung Datenschutz | Offen | Tobias + Julia |
| 8 | Incident Response Plan testen | Offen | Tobias + Markus |

**Kosten:**
Das TÜV-Audit kostet ca. 8.500 EUR (5 Tage, 2 Auditoren). Bei erfolgreichem Abschluss erhalten wir ein Zertifikat, das 2 Jahre gültig ist. Das ist eine gute Investition, besonders für das Enterprise Sales.

Ich bitte alle Verantwortlichen, mir bis **28. November** eine erste Statuseinschätzung zu geben. Dann erstelle ich einen detaillierten Vorbereitungsplan.

Grüße
Tobias

## Message 2

**From:** Julia Meier <j.meier@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-21 10:30

Hallo Tobias,

danke für den Heads-Up – gut, dass wir frühzeitig anfangen. Hier mein Status zu den HR-relevanten Themen:

**Punkt 5 – HR-Datenprozesse:**
Ich kann beruhigen: Unsere HR-Datenprozesse sind größtenteils bereits dokumentiert. Im Zuge der Einführung von Personio letztes Jahr haben wir eine umfassende Dokumentation erstellt. Folgendes ist vorhanden:

- **Bewerbermanagement:** Datenschutzerklärung im Bewerbungsformular, automatische Löschung abgelehnter Bewerbungen nach 6 Monaten (DSGVO-konform), Einwilligung für Talent Pool (12 Monate)
- **Personalakte:** Zugriffsrechte klar definiert (nur HR + direkte Vorgesetzte für Performance-Daten), verschlüsselte Speicherung in Personio
- **Lohnabrechnung:** Auftragsverarbeitung mit DATEV dokumentiert (AVV vorhanden)
- **Zeiterfassung:** Dokumentiert, Betriebsrat-Equivalent (Mitarbeitergremium) hat zugestimmt
- **Mitarbeiter-Onboarding:** Datenschutzbelehrung ist Teil des Onboarding-Prozesses (Unterschrift wird eingeholt)

**Was noch fehlt / aktualisiert werden muss:**
- Die Dokumentation zum **Remote-Work-Setup** ist lückenhaft. Seit Corona erlauben wir Home Office, aber die datenschutzrechtlichen Regelungen (z.B. Bildschirmsperre, VPN-Pflicht, keine Verarbeitung auf privaten Geräten) sind nicht formalisiert. Ich erstelle bis Ende Dezember eine **Home-Office-Datenschutzrichtlinie**.
- Die **Löschfristen für Bewerberdaten** im Talent Pool müssen wir nochmal prüfen – ich bin nicht sicher, ob 12 Monate noch dem aktuellen Stand der Rechtsprechung entspricht.

**Punkt 7 – Mitarbeiter-Schulung:**
Die letzte Datenschutzschulung war im März 2025. Ich schlage vor, eine Auffrischung für alle Mitarbeitenden im **Januar 2026** zu machen – idealerweise als Teil des "Neues Büro"-Onboardings. Tobias, kannst du die Schulungsunterlagen aktualisieren? Ich kümmere mich um die Organisation (Termin, Raum, Anwesenheitsliste).

Grüße
Julia

## Message 3

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-22 14:15

Hi Tobias,

zum Thema **technische Maßnahmen (TOMs)** und **DPIA** habe ich einige Fragen:

**TOMs – Aktuelle technische Sicherheitsmaßnahmen:**
Können wir die bestehende TOMs-Dokumentation als Basis nehmen und ergänzen? Ich möchte sicherstellen, dass wir alle aktuellen Maßnahmen erfasst haben. Hier mein Überblick über das, was wir implementiert haben:

*Verschlüsselung:*
- Data at Rest: PostgreSQL mit AES-256 (Azure-managed), Neo4j Aura encryption enabled
- Data in Transit: TLS 1.3 für alle API-Verbindungen, mTLS zwischen internen Services (noch nicht – das steht auf der K8s-Migration-Roadmap)
- Backups: Verschlüsselt (Azure Backup Vault)

*Zugriffskontrolle:*
- API: JWT-basierte Authentifizierung, Workspace-basierte Autorisierung
- Infrastruktur: Azure AD mit MFA für alle Admin-Zugänge
- Database: Separate Credentials pro Service, keine Shared Accounts
- Code: GitHub Branch Protection, PR-Reviews required

*Logging und Monitoring:*
- API-Zugriffslogs (aktuell nur in Container-Logs – wird mit K8s-Migration verbessert)
- Azure Activity Logs für Infrastruktur-Änderungen
- Noch kein SIEM-System (sollten wir das einplanen?)

**DPIA für Aurora/GraphRAG:**
Das ist der spannendste Punkt. Unsere Pipeline verarbeitet E-Mails und Notion-Dokumente, die potenziell personenbezogene Daten enthalten. Die DPIA muss mindestens abdecken:
- Welche personenbezogenen Daten werden extrahiert (Entitäten: Personen, E-Mail-Adressen)?
- Wie werden diese in der Knowledge Graph gespeichert?
- Welche Rechtsgrundlage nutzen wir (berechtigtes Interesse vs. Einwilligung)?
- Wie wird das Recht auf Löschung über die gesamte Pipeline umgesetzt (Chunks, Embeddings, Graph-Nodes)?

Besonders der letzte Punkt ist technisch komplex: Wenn ein User die Löschung seiner Daten verlangt, müssen wir nicht nur das Originaldokument löschen, sondern auch alle Chunks, Embeddings und Graph-Einträge, die daraus entstanden sind. Haben wir dafür einen automatisierten Prozess?

Tobias, können wir nächste Woche einen Workshop-Termin (3-4 Stunden) für die DPIA machen? Ich bringe Felix mit, der die technischen Details der Pipeline erklären kann.

Grüße
Sandra

## Message 4

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>
**Date:** 2025-11-23 09:45

Hi Tobias,

zu den TOMs und dem Incident Response Plan von der Infrastruktur-Seite:

**Punkt 2 – TOMs (Infrastruktur-Perspektive):**
Ergänzend zu Sandras Auflistung hier die Infrastruktur-Maßnahmen, die ich dokumentieren werde:

*Netzwerk-Sicherheit:*
- Azure Virtual Network mit Network Security Groups (NSGs) – nur benötigte Ports offen
- Kein direkter SSH-Zugang zu Production-Systemen (nur über Azure Bastion)
- DNS über Azure Private DNS Zones (kein Public DNS für interne Services)
- Nach K8s-Migration: Kubernetes Network Policies für Pod-to-Pod-Traffic

*Backup und Recovery:*
- PostgreSQL: Tägliche automatische Backups (Azure), 30 Tage Retention
- Neo4j Aura: Automatische Backups (managed by Neo4j)
- Code: GitHub mit Branch Protection, kein Force Push auf main
- **RPO:** 24 Stunden (aktuell), Ziel: 1 Stunde (nach K8s-Migration mit WAL-Shipping)
- **RTO:** 4 Stunden (aktuell), Ziel: 30 Minuten

*Patch Management:*
- Docker Images: Weekly Rebuilds mit aktuellen Base Images
- OS-Level: Azure-managed Updates für AKS Nodes (nach Migration)
- Dependencies: Dependabot für Python-Packages (automatische PRs)

**Punkt 8 – Incident Response Plan:**
Ich schlage vor, dass wir nicht nur den Plan dokumentieren, sondern auch einen **Tabletop Exercise** durchführen. Szenario: "Ein Mitarbeiter-Laptop mit Zugang zu Production wurde gestohlen." Wir gehen den gesamten Meldeprozess durch:
1. Erkennung und Erstbewertung
2. Eindämmung (Zugänge sperren, Secrets rotieren)
3. Untersuchung (Logs prüfen)
4. Meldung an Aufsichtsbehörde (72-Stunden-Frist!)
5. Benachrichtigung betroffener Personen
6. Dokumentation und Lessons Learned

Den Tabletop Exercise könnten wir im Januar machen – dann haben wir ein frisches Ergebnis für die Auditoren.

**Neues Büro:**
Die TOMs für das neue Büro (physische Sicherheit) muss ich nach dem Umzug dokumentieren:
- Zutrittskontrolle (Badge-System)
- Serverraum (separater Badge-Zugang, nur 3 Personen)
- Clean-Desk-Policy
- Besucherregelung

Grüße
Markus

## Message 5

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-25 10:00

Hallo zusammen,

vielen Dank für die schnellen und ausführlichen Rückmeldungen! Ich fasse den aktuellen Stand zusammen und teile den **detaillierten Audit-Vorbereitungsplan** mit Zeitschiene und Verantwortlichkeiten.

**Aktualisierter Status:**

| # | Thema | Status | Verantwortlich | Deadline |
|---|-------|--------|----------------|----------|
| 1 | Verarbeitungsverzeichnis | In Arbeit (70%) | Tobias | 31.01.2026 |
| 2 | TOMs Dokumentation | In Arbeit (40%) | Tobias + Markus + Sandra | 15.02.2026 |
| 3 | DPIA Aurora/GraphRAG | Workshop geplant | Tobias + Sandra + Felix | 31.01.2026 |
| 4 | AVVs prüfen | In Arbeit (60%) | Tobias | 31.12.2025 |
| 5 | HR-Datenprozesse | Größtenteils fertig (80%) | Julia | 31.01.2026 |
| 6 | Löschkonzept | Offen – technisch komplex | Tobias + Anna + Felix | 15.02.2026 |
| 7 | Datenschutz-Schulung | Geplant für Januar | Tobias + Julia | 31.01.2026 |
| 8 | Incident Response Test | Tabletop Exercise geplant | Tobias + Markus | 15.02.2026 |

**Kritische Punkte, die besondere Aufmerksamkeit brauchen:**

**1. Löschkonzept für die GraphRAG-Pipeline (Punkt 6):**
Sandra hat das richtig identifiziert – das ist unser größtes Risiko im Audit. Aktuell haben wir **keinen automatisierten Löschprozess**, der über die gesamte Pipeline greift. Wenn ein Betroffener Löschung verlangt, müssten wir manuell:
- Dokument aus PostgreSQL löschen
- Alle zugehörigen Chunks und Embeddings identifizieren und löschen
- Alle Entity-Nodes und Relationships in Neo4j finden und entfernen
- Prüfen, ob Entities auch in anderen Dokumenten vorkommen (dann dürfen sie nicht gelöscht werden)

**Action Item:** Felix und Anna, bitte entwickelt bis Ende Januar einen **automatisierten Lösch-Workflow** als API-Endpoint (`DELETE /v1/documents/{id}/gdpr-delete`). Der muss kaskadierend über alle Stores laufen und ein Löschprotokoll erstellen.

**2. DPIA-Workshop:**
Sandra, der Workshop ist angesetzt für **Dienstag, 02.12.2025, 13:00-17:00 Uhr**. Teilnehmer: Tobias, Sandra, Felix, Anna. Ich habe eine DPIA-Vorlage vom BfDI (Bundesbeauftragter für Datenschutz) vorbereitet, die wir als Grundlage nehmen.

**3. AVV mit OpenAI:**
Das ist ein heikler Punkt. OpenAI bietet einen Data Processing Addendum (DPA) an, aber die Datenverarbeitung findet in den USA statt. Seit dem EU-US Data Privacy Framework ist das grundsätzlich möglich, aber wir müssen dokumentieren, dass OpenAI auf der DPF-Liste steht und welche Daten wir übermitteln. Ich kläre das mit unserem externen Datenschutzanwalt (Kanzlei Schuster & Partner).

**4. Audit-Schedule (KW 10):**

| Tag | Thema | Beteiligte |
|-----|-------|------------|
| Mo, 03.03. | Eröffnung, Verarbeitungsverzeichnis, AVVs | Tobias, Martin |
| Di, 04.03. | TOMs, Infrastruktur-Review, Serverraum-Begehung | Tobias, Markus, Sandra |
| Mi, 05.03. | DPIA, KI/ML-Verarbeitung, Löschkonzept | Tobias, Sandra, Felix |
| Do, 06.03. | HR-Prozesse, Mitarbeiterdatenschutz, Schulungsnachweise | Tobias, Julia |
| Fr, 07.03. | Incident Response, Abschlussgespräch, Findings | Tobias, Martin |

**An alle:** Bitte haltet euch die genannten Tage frei. Die TÜV-Auditoren werden auch Stichproben machen und einzelne Mitarbeitende befragen – seid also vorbereitet.

Martin: Ich brauche deine Unterschrift auf dem Audit-Vertrag. Liegt bei dir auf dem Schreibtisch (oder im neuen Büro auf dem noch nicht existierenden Schreibtisch – je nachdem, wann du unterschreibst).

Grüße
Tobias
