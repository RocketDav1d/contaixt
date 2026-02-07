---
thread_id: email_thread_009
subject: "FinSecure Portal – Anforderungsworkshop"
---

## Message 1

**From:** Thomas Krueger <t.krueger@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-01 18:45 CET

Hallo zusammen,

ich war heute den ganzen Tag mit Dr. Claudia Berger und ihrem Team bei FinSecure Bank vor Ort fuer den Anforderungsworkshop. Hier die Zusammenfassung der Key Findings:

**Kernfunktionalitaet:**
- Kundenportal fuer Privat- und Geschaeftskunden mit Self-Service-Funktionen (Kontoauszuege, Ueberweisungen, Dauerauftraege, Kreditanfragen)
- Dashboard mit Finanzuebersicht und personalisierten Insights
- Integriertes Dokumentenmanagement (Upload, Freigabe, Archiv)
- Secure Messaging zwischen Kunden und Beratern

**Technische Anforderungen (non-negotiable laut Dr. Berger):**
1. **2-Faktor-Authentifizierung** – TOTP und SMS als Second Factor, perspektivisch auch FIDO2/WebAuthn
2. **Audit Logging** – Jede Transaktion und jeder Datenzugriff muss lueckenlos geloggt werden. Retention Period mindestens 10 Jahre (BaFin-Anforderung)
3. **BaFin Compliance** – Insbesondere MaRisk und BAIT muessen eingehalten werden. Dr. Berger hat betont, dass die naechste BaFin-Pruefung Q2 2026 ansteht
4. **Accessible UI** – WCAG 2.1 AA Minimum, idealerweise AAA fuer zentrale Flows. FinSecure hat hierzu eine interne Policy

**Tech Stack (vom Kunden vorgegeben):**
- Frontend: React (TypeScript), muss in deren bestehendes Design System integriert werden
- Backend: Java Spring Boot, Anbindung an deren Core Banking System ueber REST-APIs
- Datenbank: PostgreSQL (bereits im Einsatz bei FinSecure)

**Budget & Timeline:**
- Gesamtbudget: EUR 280.000
- Go-Live Target: Ende Q1 2026
- Dr. Berger moechte nach 4 Wochen einen ersten Prototypen sehen

Das Budget ist ambitioniert fuer den Scope, aber ich denke machbar, wenn wir smart priorisieren. Lisa, kannst du bitte den Projektplan aufsetzen? Felix, ich wuerde mir wuenschen, dass du dir die technische Architektur ueberlegst – bitte unsere API Design Guidelines als Basis nehmen.

Ich habe Dr. Berger ein Follow-up fuer naechste Woche zugesagt. Bitte kommt bis Freitag mit euren Fragen und Einschaetzungen.

Beste Gruesse,
Thomas

## Message 2

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Thomas Krueger <t.krueger@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-02 08:22 CET

Danke Thomas, das klingt nach einem sehr produktiven Workshop.

Zwei Punkte, die mir sofort auffallen:

**PCI-DSS Scope:** Wenn das Portal Kreditkartendaten oder Zahlungsinformationen verarbeitet, muessen wir klaeren, ob wir in den PCI-DSS Scope fallen. Das hat massive Auswirkungen auf die Architektur – insbesondere auf Tokenization, Encryption at Rest und Network Segmentation. Koennen wir das mit Dr. Berger pruefen? Idealerweise haetten wir einen dedizierten Payment Service, der den PCI-Scope minimiert, anstatt das gesamte Portal PCI-compliant zu machen.

**Budget Reality Check:** EUR 280k bei dem Scope ist tight. Ich wuerde vorschlagen, dass wir ein klares MVP definieren. 2FA, Kontoauszuege und Secure Messaging fuer Phase 1, die erweiterten Features wie Kreditanfragen und Insights in Phase 2. Lisa, bitte kalkuliere beide Szenarien im Projektplan durch.

Felix, bei der Architektur bitte von Anfang an an Auditability denken. Jeder API Call muss einen Correlation-ID-Header bekommen, und wir brauchen ein zentrales Audit Event Log. Ich wuerde Spring Boot Actuator plus einen Custom Audit Event Publisher vorschlagen. Schau dir mal an, was wir beim DataHub-Projekt gemacht haben – da gab es aehnliche Requirements.

Tobias, ich moechte, dass du von Anfang an im Projekt involviert bist. Security by Design, nicht Security as Afterthought. Bitte erstelle ein Threat Model basierend auf den Anforderungen.

Beste Gruesse,
Sandra

## Message 3

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krueger <t.krueger@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>
**Date:** 2025-10-02 14:37 CET

Hallo zusammen,

Sandra, danke fuer den Hinweis bezueglich PCI-DSS – das ist definitiv ein kritischer Punkt. Ich werde das Threat Model diese Woche aufsetzen.

Zusaetzlich habe ich mehrere Compliance-Fragen, die wir dringend mit FinSecure klaeren muessen:

**Data Residency:**
- Wo muessen die Kundendaten physisch gespeichert werden? Bei einem Finanzinstitut unter BaFin-Aufsicht gibt es strenge Vorgaben bezueglich Datenverarbeitung und -speicherung. Wenn wir Cloud-Services nutzen (und das werden wir muessen), brauchen wir eine klare Aussage: nur EU? Nur Deutschland? Oder reicht ein Angemessenheitsbeschluss?
- Unsere Standard-Deployment-Pipeline laeuft ueber AWS eu-central-1 (Frankfurt), das sollte grundsaetzlich passen, aber ich moechte das explizit bestaetigt haben.

**Auslagerungsvertrag:**
- Gemaess MaRisk AT 9 muss FinSecure fuer wesentliche Auslagerungen einen entsprechenden Vertrag mit uns abschliessen. Das ist nicht nur eine Formalitaet – der Vertrag muss spezifische Kontrollrechte, Exit-Strategien und Informationspflichten enthalten. Thomas, bitte klare das mit unserer Rechtsabteilung und Dr. Berger.

**Incident Response:**
- Wir brauchen einen gemeinsamen Incident Response Plan. Bei einem Security Incident im Portal muss klar sein: Wer informiert wen, innerhalb welcher Fristen, und wie laeuft die Kommunikation mit der BaFin? Die Meldefrist fuer schwerwiegende IT-Sicherheitsvorfaelle betraegt 24 Stunden nach Kenntnisnahme.

**Penetration Testing:**
- Ich schlage vor, dass wir einen externen Pentest einplanen – mindestens vor dem Go-Live. Unser Security Policy Dokument schreibt das fuer alle kundenseitigen Anwendungen vor. Budget dafuer bitte einplanen (ca. EUR 15-20k).

Ich werde das Threat Model bis Ende naechster Woche liefern. STRIDE-basiert, fokussiert auf die Hauptangriffsvektoren fuer ein Banking-Portal.

Gruesse,
Tobias

## Message 4

**From:** Thomas Krueger <t.krueger@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>
**Date:** 2025-10-03 09:15 CET

Sehr gute Punkte von euch beiden.

Tobias, ich habe eben kurz mit Dr. Berger telefoniert und kann schon mal vorab beantworten:

**Data Residency:** FinSecure besteht auf Datenhaltung ausschliesslich in Deutschland. AWS eu-central-1 ist akzeptabel, aber alle Sub-Processors muessen ebenfalls in Deutschland oder mindestens in der EU sitzen. Dr. Berger schickt uns dazu ihre interne IT-Sicherheitsrichtlinie, damit wir genau wissen, welche Constraints gelten.

**PCI-DSS:** Gute Nachricht – das Portal wird keine Kreditkartendaten direkt verarbeiten. Zahlungen laufen ueber deren bestehenden Payment Provider (SIX Payment Services). Wir muessen lediglich sicherstellen, dass wir keine Kartennummern auch nur temporaer im Frontend oder in Logs speichern. Sandra, das reduziert unseren PCI-Scope erheblich.

**Pentest Budget:** Dr. Berger ist einverstanden, dass die Pentest-Kosten aus dem Gesamtbudget kommen. Sie hat sogar vorgeschlagen, ihren eigenen Security-Dienstleister (SecuAudit GmbH) einzubeziehen, da die schon ihren internen Pentest-Zyklus machen. Das wuerde Kosten sparen und die Akzeptanz des Reports bei der BaFin erhoehen.

**Auslagerungsvertrag:** Unsere Rechtsabteilung setzt sich naechste Woche mit dem Legal Team von FinSecure zusammen. Dr. Berger hat das bereits intern angestossen.

Lisa, wenn du den Projektplan machst: Bitte den Pentest als Meilenstein 2 Wochen vor Go-Live einplanen, und die Compliance-Abnahme als separaten Gate vor dem Release. Wir koennen es uns nicht leisten, hier Shortcuts zu nehmen.

Ich vereinbare fuer naechsten Mittwoch ein gemeinsames Kickoff-Meeting mit dem vollstaendigen FinSecure-Team. Bitte haltet euch den Nachmittag frei.

Gruesse,
Thomas
