---
thread_id: email_thread_001
subject: "Projekt Aurora – Kickoff Meeting"
---

## Message 1

**From:** Lisa Weber <l.weber@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-15 09:12

Hallo zusammen,

wie in der letzten Steering-Committee-Runde besprochen, starten wir offiziell mit **Projekt Aurora** für unseren Kunden Müller Maschinenbau AG. Ich habe den Kickoff für **Mittwoch, 17.09., 10:00 Uhr** im großen Konferenzraum angesetzt. Remote-Teilnahme über Teams ist natürlich auch möglich.

Hier eine kurze Zusammenfassung des Scopes laut Project Charter:

- **Migration** der bestehenden Legacy-ERP-Daten von On-Premise (Oracle DB auf Windows Server 2012 R2) in die Cloud
- **Aufbau einer modernen Data Platform** für Reporting und Analytics
- **Cloud Provider:** wird noch final entschieden, Präferenz liegt auf Azure (siehe Tech Radar Q3/2025)
- **Budget:** 450.000 EUR (genehmigt durch Dr. Schreiber und Hans Müller, CEO Müller Maschinenbau)
- **Timeline:** September 2025 bis Januar 2026, Go-Live geplant für Anfang Dezember

Ich habe die Project Charter als Confluence-Dokument unter `/projects/aurora/charter` abgelegt. Bitte lest euch das vor dem Kickoff durch, damit wir direkt in die Details einsteigen können.

Die Rollenverteilung sieht wie folgt aus:
- **Project Lead:** Lisa Weber
- **Tech Lead:** Felix Braun
- **Data Engineering Lead:** Anna Richter
- **DevOps:** Markus Lang
- **Security:** Tobias Fischer
- **UX/Frontend:** Katharina Schmidt
- **Development Support:** Daniel Wolff

Hans Müller von Müller Maschinenbau wird beim Kickoff remote dabei sein und die Business Requirements aus seiner Sicht vorstellen.

Bitte gebt mir kurz Bescheid, ob der Termin für alle passt.

Viele Grüße
Lisa

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-15 10:34

Hi Lisa,

Termin passt bei mir. Danke für die Zusammenfassung.

Ich habe mir die Project Charter schon angeschaut und hätte vorab ein paar technische Fragen, die wir beim Kickoff klären sollten:

1. **Legacy-System-Details:** Wissen wir genau, welche Oracle-Version läuft? Ich vermute 11g oder 12c, aber das macht für den Export einen erheblichen Unterschied. Außerdem: Windows Server 2012 R2 ist seit Oktober 2023 End of Life – gibt es dort noch Extended Security Updates, oder ist das ein zusätzlicher Druck für die Migration?

2. **Datenvolumen:** Die Project Charter spricht von "mehreren Millionen Datensätzen". Können wir das genauer quantifizieren? Für die Architektur der Data Platform brauche ich zumindest eine Größenordnung (Anzahl Tabellen, Gesamtvolumen in GB/TB, tägliches Wachstum).

3. **Schnittstellen:** Welche Systeme hängen aktuell an der Oracle DB? Wenn es SOAP oder REST APIs gibt, die direkt auf die DB zugreifen, müssen wir die Cutover-Strategie entsprechend planen.

4. **Compliance:** Laut unserem Security Policy Document (v2.3) müssen wir bei Cloud-Migrationen ein Data Classification Assessment durchführen. Tobias, hast du das schon initiiert?

Ich würde vorschlagen, dass wir für den Kickoff ein Technical Discovery Dokument vorbereiten, in dem wir diese Punkte systematisch abarbeiten.

Gruß
Felix

---

## Message 3

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Lisa Weber <l.weber@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-09-15 14:21

Hallo zusammen,

kurzes Update von meiner Seite: Ich kann den Termin am Mittwoch bestätigen.

Felix, zu deinen Fragen:

Bezüglich **Cloud Provider**: Wir gehen definitiv mit **Microsoft Azure**. Das ist nicht nur eine technische, sondern auch eine strategische Entscheidung. Wir haben seit Q2 eine **Microsoft Gold Partnership**, und Müller Maschinenbau nutzt bereits Microsoft 365 und Azure Active Directory. Das gibt uns exzellente Synergien bei Identity Management und Single Sign-On. Details dazu stehen auch im Tech Radar unter dem Eintrag "Cloud Providers".

Zum Thema **Oracle**: Müller Maschinenbau läuft auf **Oracle 12c Release 2** (12.2.0.1). Das Gesamtdatenvolumen liegt bei ca. **850 GB** verteilt auf etwa **340 Tabellen**, davon ~2 Millionen Datensätze allein in der Auftragstabelle. Die Oracle-Lizenz läuft im März 2026 aus – das ist also ein zusätzlicher Business Driver für die Migration.

Ich habe mit Hans Müller letzte Woche telefoniert und er hat betont, dass die **Reporting-Capabilities** der neuen Plattform der wichtigste Deliverable für sein Management Board sind. Aktuell erstellen die Controller von Müller Maschinenbau ihre Reports manuell in Excel – das ist natürlich nicht tragbar.

Lisa, bitte stelle sicher, dass wir beim Kickoff auch **Thomas Krüger** (Head of Sales) kurz einbinden. Er hat die Account Relationship zu Müller Maschinenbau und sollte über den Projektfortschritt im Bilde sein.

Freue mich auf den Kickoff!

Sandra
