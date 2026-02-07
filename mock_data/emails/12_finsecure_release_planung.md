---
thread_id: email_thread_012
subject: "FinSecure Portal – Release-Planung Q1 2026"
---

## Message 1

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krueger <t.krueger@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-12-01 09:00 CET

Hallo zusammen,

nach dem erfolgreichen Pentest-Retest (alle Findings confirmed fixed – danke Felix und Daniel!) und der vorlaeufigen Freigabe durch Herrn Stein moechte ich jetzt die Release-Planung fuer Q1 2026 finalisieren.

**Release Plan – FinSecure Portal v1.0:**

**Phase 1: Final Hardening (01.12. – 20.12.2025)**
- Verbleibende Bug Fixes aus dem QA-Backlog (aktuell 14 Tickets, davon 3 mit Prio High)
- Performance-Optimierung: Felix hat im Load Test identifiziert, dass der `/api/v1/transactions` Endpoint bei >1000 Ergebnissen zu langsam ist (>3s Response Time). Target: <500ms fuer den 95th Percentile.
- Frontend Polish: Daniel arbeitet an den letzten UI-Anpassungen gemaess Katharinas Feedback aus dem UX-Testing
- Security Hardening: Tobias fuehrt den finalen Security Review durch

**Phase 2: Staging Freeze & UAT (06.01. – 17.01.2026)**
- Code Freeze am 06.01.
- User Acceptance Testing mit dem FinSecure-Team (Dr. Berger + 5 Fachtester)
- Regression Testing unsererseits (automatisiert + manuell)
- Accessibility Audit durch externen Dienstleister (barrierefreies-web.de)

**Phase 3: Soft Launch (20.01. – 31.01.2026)**
- Deployment auf Production
- Rollout an 500 Pilotnutzer (Auswahl durch FinSecure)
- Monitoring-Phase mit erhoehter Aufmerksamkeit (dediziertes War Room Setup)
- Daily Standups mit FinSecure waehrend der Pilotphase

**Phase 4: General Availability (03.02.2026)**
- Rollout an alle Kunden (ca. 45.000 aktive Online-Banking-Nutzer)
- Marketing-Begleitung durch FinSecure
- Uebergang in regulaeren Support-Modus

**Risiken & Abhaengigkeiten:**
1. Die formale Freigabe durch Dr. Berger steht noch aus (abhaengig vom finalen Sicherheitskonzept-Dokument, das Tobias gerade erstellt)
2. Das Accessibility Audit koennte Findings produzieren, die Nacharbeit erfordern. Buffer von 3 Tagen eingeplant.
3. Die Integration mit dem Core Banking System hat noch einen offenen Defect bei Dauerauftraegen (FinSecure-seitig). Ihr Entwicklungsteam hat den Fix fuer KW 51 zugesagt.

Bitte schaut euch den Plan an und gebt mir bis Mittwoch euer Feedback. Besonders wichtig: Gibt es Urlaubs- oder Abwesenheitsplaene ueber die Feiertage, die ich beruecksichtigen muss? Wir brauchen mindestens Felix oder Daniel als Bereitschaft zwischen den Jahren, falls im Staging kritische Issues auftreten.

Gruesse,
Lisa

## Message 2

**From:** Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Thomas Krueger <t.krueger@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-01 14:25 CET

Hallo Lisa,

danke fuer den ausfuehrlichen Plan. Hier mein Update zum UX-Testing, das wir letzte Woche mit 12 Testpersonen durchgefuehrt haben:

**UX-Testing Ergebnisse (Summary):**

Wir haben 5 Core User Journeys getestet:
1. Login + Dashboard-Navigation
2. Kontoauszug einsehen + filtern
3. Ueberweisung durchfuehren
4. Nachricht an Berater senden
5. Dokument hochladen und freigeben

**Gesamtergebnis: 92% Task Completion Rate** (Ziel war 85%, also deutlich uebererfuellt)

**Details pro Journey:**
- Login + Dashboard: 100% Completion, durchschnittlich 45 Sekunden. Die 2FA-Integration wurde als "unkompliziert" bewertet. Ein Tester hatte Schwierigkeiten mit der TOTP-App-Einrichtung, aber das ist ein Onboarding-Thema, kein Portal-Problem.
- Kontoauszug: 100% Completion. Filterung nach Zeitraum und Betrag wurde intuitiv gefunden. **Feedback:** Mehrere Tester wuenschten sich einen CSV-Export – ist das im Scope fuer v1.0?
- Ueberweisung: 83% Completion. **Problem identifiziert:** 2 von 12 Testern haben den "Bestaetigen"-Button nicht sofort gefunden, weil er below-the-fold war. Daniel, bitte den Button sticky machen oder die Formularlaenge reduzieren.
- Nachricht senden: 92% Completion. Funktioniert gut. Ein Tester hat die Attachment-Funktion nicht gefunden (Icon war zu klein). Daniel, bitte Icon-Groesse von 16px auf 24px erhoehen.
- Dokument hochladen: 83% Completion. **Problem:** Der Upload-Progress-Indicator war nicht sichtbar genug. Einige Tester dachten, der Upload haette nicht funktioniert und haben erneut geklickt. Brauchen wir einen prominenteren Progress Bar und Duplicate-Detection.

**Accessibility-Highlights:**
- Screen Reader Kompatibilitaet ist grundsaetzlich gegeben (wir haben mit NVDA und VoiceOver getestet)
- Keyboard Navigation funktioniert auf allen Core Flows
- **Problem:** Die Farbkontraste im Secondary Action Button (hellgrau auf weiss) erfuellen nicht WCAG AA. Das muss vor dem Accessibility Audit gefixt werden, sonst faellt es garantiert auf. Daniel, bitte den Kontrast auf mindestens 4.5:1 anpassen.

Insgesamt bin ich sehr zufrieden mit den Ergebnissen. Die 92% Completion Rate bei einem Banking-Portal ist wirklich gut – zum Vergleich: der Branchendurchschnitt liegt bei 78%. Die identifizierten Issues sind alle fixbar und sollten den Release-Plan nicht gefaehrden.

Ich bereite gerade den finalen UX-Report fuer Dr. Berger vor. Sie hatte explizit nach quantitativen Usability-Metriken gefragt.

Gruesse,
Katharina

## Message 3

**From:** Daniel Wolff <d.wolff@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**Date:** 2025-12-02 10:05 CET

Hey zusammen,

Katharina, danke fuer das detaillierte Feedback aus dem UX-Testing. Ich gehe die Punkte mal durch:

**Bereits eingeplante Frontend Polish Items:**

1. **Ueberweisungs-Button Sticky machen** – Bin ich schon dran. Ich implementiere einen Sticky Footer fuer das Ueberweisungsformular, der den "Pruefen & Bestaetigen"-Button immer sichtbar haelt. Geschaetzter Aufwand: 0.5 Tage. Werde gleichzeitig die Formularlaenge optimieren, indem ich die optionalen Felder (Verwendungszweck-Vorlage, Termin-Ueberweisung) in einen Collapsible-Bereich packe.

2. **Attachment-Icon vergroessern** – Easy Fix, aendere ich auf 24px und fuege einen Tooltip hinzu ("Datei anhaengen"). Schaetzung: 2 Stunden.

3. **Upload Progress Bar** – Ich ersetze die aktuelle Loesung (kleiner Spinner) durch eine richtige Progress Bar mit Prozentanzeige und Dateiname. Dazu kommt eine Duplicate-Detection: Wenn der gleiche Dateiname innerhalb von 60 Sekunden nochmal hochgeladen wird, zeigen wir eine Warnung ("Diese Datei wurde bereits hochgeladen. Erneut hochladen?"). Schaetzung: 1 Tag.

4. **Farbkontrast Secondary Button** – Ich passe das an. Aktuell ist der Button `#B0B0B0` auf `#FFFFFF` (Kontrast-Ratio 2.6:1). Ich wechsle auf `#595959` auf `#FFFFFF` (Kontrast-Ratio 7.0:1), das ist dann sogar WCAG AAA compliant. Ich pruefe gleichzeitig alle anderen UI-Elemente mit dem axe DevTools Plugin und fixe eventuelle weitere Kontrast-Issues. Schaetzung: 0.5 Tage.

**Zusaetzliche Items auf meiner Liste:**

5. **CSV-Export fuer Kontoauszuege** – Katharina, gute Frage ob das im Scope ist. Felix, ist der Backend-Endpoint dafuer schon implementiert? Wenn ja, brauche ich nur einen Download-Button im Frontend (0.5 Tage). Wenn nicht, muessen wir das mit Lisa und Thomas klaeren, ob es noch in v1.0 reinkommt.

6. **Loading States** – Ich habe bei meinem letzten Review gemerkt, dass einige Seiten beim Laden nur ein blankes Weiss zeigen, bevor die Daten da sind. Ich implementiere Skeleton Screens fuer Dashboard, Transaktionsliste und Nachrichteneingang. Das verbessert die Perceived Performance massiv. Schaetzung: 1 Tag.

7. **Error States** – Aktuell gibt es fuer Netzwerk-Fehler nur eine generische Alert-Box. Ich moechte dedizierte Error States pro Seitenbereich implementieren mit Retry-Button. Schaetzung: 0.5 Tage.

**Gesamtaufwand: ca. 4-5 Tage.**

Lisa, das passt in die Phase 1 Timeline, wenn ich morgen starte. Die Items 5-7 sind Nice-to-haves – wenn die Zeit knapp wird, priorisiere ich 1-4 und die Skeleton Screens (Item 6), weil die den groessten Impact auf die User Experience haben.

Zum Thema Bereitschaft ueber die Feiertage: Ich bin zwischen den Jahren da (verreise erst am 02.01.) und kann Bereitschaft uebernehmen.

Gruesse,
Daniel

## Message 4

**From:** Thomas Krueger <t.krueger@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-12-03 08:45 CET

Guten Morgen,

ich hatte gestern ein laengeres Telefonat mit Dr. Berger zur Release-Planung. Hier die wichtigsten Punkte:

**Soft Launch bestaetigt:**
Dr. Berger moechte definitiv mit einem Soft Launch starten. Sie hat intern 500 Pilotnutzer identifiziert – eine Mischung aus technikaffinen Privatkunden und ausgewaehlten Geschaeftskunden. Die Auswahl ist bewusst divers: verschiedene Altersgruppen, unterschiedliche Geraete (Desktop, Tablet, Mobile), und eine Gruppe von 20 Kunden mit Accessibility-Anforderungen (Screenreader-Nutzer, motorische Einschraenkungen). Das ist smart – so bekommen wir reales Feedback ueber alle Nutzergruppen hinweg.

**Pilotphase-Anforderungen von FinSecure:**
1. **Feedback-Mechanismus:** Dr. Berger moechte einen In-App-Feedback-Button waehrend der Pilotphase. Kunden sollen Screenshots machen und Kommentare hinterlassen koennen. Daniel, ist das schnell machbar? Dr. Berger schlaegt Hotjar oder ein aehnliches Tool vor – Tobias, bitte pruefen, ob das datenschutzkonform einsetzbar ist.
2. **Rollback-Plan:** Falls kritische Issues waehrend der Pilotphase auftreten, muss ein Rollback innerhalb von 30 Minuten moeglich sein. Felix, hast du das im Deployment-Setup beruecksichtigt?
3. **Success Metrics:** Dr. Berger definiert den Soft Launch als erfolgreich, wenn: Task Completion Rate >85% (real-world), keine kritischen Security Incidents, System Availability >99.5%, und NPS-Score der Pilotnutzer >30.
4. **Communication Plan:** FinSecure's Marketing-Team bereitet die Kommunikation an die Pilotnutzer vor. Sie brauchen von uns bis 10.01. eine Feature-Liste und Screenshots fuer die Einladungs-E-Mail.

**CSV-Export (Daniels Frage):**
Habe Dr. Berger direkt gefragt – ja, CSV-Export fuer Kontoauszuege ist ein Must-Have fuer v1.0. Ihre Geschaeftskunden brauchen das fuer die Buchhaltung. Felix, bitte den Backend-Endpoint priorisieren, falls noch nicht vorhanden.

**Zum Thema General Availability:**
Dr. Berger ist bereit, die GA um 1-2 Wochen zu verschieben, wenn die Pilotphase laenger dauert als geplant. Zitat: "Lieber eine Woche spaeter mit einem stabilen Portal als puenktlich mit Problemen." Das gibt uns etwas Puffer, aber ich moechte den 03.02. als Zieltermin beibehalten.

Lisa, bitte den In-App-Feedback-Button und den CSV-Export in den Plan aufnehmen. Ich schaetze, das sind zusammen ca. 2-3 Tage zusaetzlicher Aufwand. Passt das noch in Phase 1?

Sandra, ich wuerde vorschlagen, dass wir am Freitag ein kurzes Alignment-Meeting machen, um den finalen Plan zu verabschieden. 30 Minuten sollten reichen.

Gruesse,
Thomas
