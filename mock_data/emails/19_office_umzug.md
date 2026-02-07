---
thread_id: email_thread_019
subject: "Büro-Umzug München-Schwabing"
---

## Message 1

**From:** Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**To:** all@techvision-gmbh.de
**Date:** 2025-11-10 10:00

Liebes Team,

ich freue mich, euch offiziell mitteilen zu können: **Wir ziehen um!**

Nach intensiver Suche haben wir neue Büroräume in **München-Schwabing** gefunden, die perfekt zu unserem Wachstum passen. Hier die Details:

**Neues Büro:**
- **Adresse:** Leopoldstraße 140, 80804 München (4. OG)
- **Fläche:** 650 m² (aktuell: 380 m² – fast doppelt so viel Platz!)
- **Aufteilung:** Open-Space-Bereiche, 4 Meeting-Räume (davon 2 mit Videokonferenz-Setup), 2 Phone Booths, eine große Küche mit Lounge-Bereich, separater Serverraum
- **Lage:** Direkt an der U3/U6 Station Münchner Freiheit (2 Min. Fußweg), Tiefgaragenplätze verfügbar

**Warum der Umzug?**
Unser aktuelles Büro in der Theresienstraße platzt aus allen Nähten. Mit dem geplanten Teamwachstum 2026 (4-5 neue Stellen) hätten wir schlicht keinen Platz mehr. Außerdem fehlen uns dedizierte Räume für konzentriertes Arbeiten und vernünftige Meeting-Räume für Kundentermine.

**Mietkonditionen:**
- 5-Jahres-Mietvertrag mit Option auf Verlängerung
- Einzug ab 01.01.2026
- Der Umzug selbst ist geplant für das **Wochenende 10./11. Januar 2026**

Das neue Büro wird komplett renoviert übergeben. Wir werden es nach unseren Bedürfnissen einrichten – dazu wird es in den nächsten Wochen noch Input-Runden geben (Möbel, Ausstattung, Raumaufteilung).

Julia wird die Umzugslogistik koordinieren. Bitte wendet euch mit Fragen direkt an sie.

Ich bin wirklich begeistert von den neuen Räumen – die Leopoldstraße ist eine Top-Adresse und die Anbindung ist für alle besser als unser aktueller Standort.

Beste Grüße
Martin

## Message 2

**From:** Julia Meier <j.meier@techvision-gmbh.de>
**To:** all@techvision-gmbh.de
**Date:** 2025-11-12 09:30

Hallo zusammen,

wie Martin angekündigt hat, koordiniere ich den Umzug. Hier die **Logistik-Details und To-Dos**:

**Umzugswochenende: 10./11. Januar 2026 (Samstag/Sonntag)**

Wir haben die Umzugsfirma **Müller & Partner Büroumzüge** beauftragt. Die kümmern sich um den Transport aller Möbel, IT-Equipment und Unterlagen. Trotzdem brauche ich eure Mithilfe:

**Was ihr tun müsst (bis Freitag, 09.01.2026):**
1. **Persönliche Gegenstände** einpacken (Umzugskartons werden ab 06.01. bereitgestellt)
2. **Schreibtisch-Setup** dokumentieren: Bitte fotografiert euer Monitor-/Peripherie-Setup, damit wir es am neuen Standort korrekt aufbauen können
3. **Vertrauliche Unterlagen** persönlich mitnehmen (nicht im Umzugskarton!)
4. **Label-System:** Jeder Karton bekommt ein farbiges Label mit eurem Namen und der Zielzone im neuen Büro

**Raumaufteilung (Entwurf):**
- **Zone A (Fensterseite Süd):** Engineering Team (Dev, Data, DevOps) – ca. 12 Arbeitsplätze
- **Zone B (Fensterseite Nord):** Sales, Project Management – ca. 8 Arbeitsplätze
- **Zone C (Innenbereich):** GF, HR, Finance – ca. 6 Arbeitsplätze
- **Zone D:** Meeting-Räume, Phone Booths, Küche

**Neue Möbel (bestellt):**
- Höhenverstellbare Schreibtische für alle (Flexispot E7 Pro)
- Ergonomische Bürostühle (Herman Miller Aeron – ja, wirklich!)
- Collaboration-Möbel für die Lounge (Sofas, Whiteboards, TV-Screens)

**Wer am Umzugswochenende helfen kann:** Bitte tragt euch im Doodle ein (Link im Slack). Es gibt Pizza und Getränke, und ihr bekommt dafür einen zusätzlichen freien Tag als Ausgleich.

**Wichtig:** Am Montag, 12.01.2026, sollten alle am neuen Standort arbeitsfähig sein. Bitte plant entsprechend.

Bei Fragen: Slack-Channel #umzug-2026 (erstelle ich heute noch).

Viele Grüße
Julia

## Message 3

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Julia Meier <j.meier@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-11-13 11:15

Hallo Julia, Sandra, Tobias,

bevor wir den Umzug final planen, brauche ich Klarheit über die **IT-Infrastruktur im neuen Büro**. Das ist der kritische Pfad – ohne funktionierendes Netzwerk und Server können wir am 12.01. nicht arbeiten.

**Serverraum:**
- Wie groß ist der Serverraum in der Leopoldstraße? Wir brauchen Platz für mindestens ein 19"-Rack (aktuell: 2 Server, 1 NAS, Netzwerk-Equipment)
- Gibt es eine **Klimaanlage** im Serverraum? Das ist ein Must-Have.
- Stromversorgung: Brauchen wir eine **USV (unterbrechungsfreie Stromversorgung)**? Aktuell haben wir keine, aber beim Umzug wäre der richtige Zeitpunkt, das nachzuholen.
- Physischer Zugang: Nur mit Badge/Schlüssel, nicht für alle Mitarbeitenden zugänglich

**Netzwerk:**
- Welcher **Internet-Provider** ist am neuen Standort verfügbar? Wir brauchen mindestens symmetrisches **500 Mbit**, besser 1 Gbit. Für unsere Cloud-Workloads (Azure) und Video Calls ist das essentiell.
- Wird das Büro mit **strukturierter Verkabelung (Cat 6a oder besser)** übergeben, oder müssen wir das selbst verlegen lassen?
- **WLAN-Planung:** Bei 650 m² brauchen wir mindestens 4-5 Access Points (UniFi oder ähnlich). Ich würde gerne vorab einen Site Survey machen.

**VPN/Security (Tobias):**
- Tobias, müssen wir das Firewall-Setup anpassen? Aktuell läuft eine pfSense auf eigener Hardware. Wollen wir das am neuen Standort beibehalten oder auf eine Cloud Firewall (Azure Firewall) umsteigen?
- Die IP-Adressen werden sich ändern – das betrifft unsere Whitelist-Regeln bei diversen Services.

**Timeline:**
Idealerweise sollte das Netzwerk bis **08.01.2026** stehen und getestet sein. Das bedeutet, wir müssen den Internet-Anschluss **jetzt** bestellen – die Telekom braucht typischerweise 4-6 Wochen Vorlauf.

Können wir diese Woche noch einen Termin machen, um das alles durchzusprechen?

Grüße
Markus

## Message 4

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Markus Lang <m.lang@techvision-gmbh.de>, Julia Meier <j.meier@techvision-gmbh.de>, Tobias Fischer <t.fischer@techvision-gmbh.de>
**Date:** 2025-11-15 14:00

Hi Markus,

gute Punkte – ich habe die meisten Fragen klären können. Hier die Antworten:

**Internet-Anschluss: Bereits beauftragt!**
Ich habe mich schon vor zwei Wochen darum gekümmert (weil ich wusste, dass das der Bottleneck wird). Details:
- **Provider:** M-net (Münchner Glasfaser-Netz)
- **Anschluss:** Symmetrische **1 Gbit/s Glasfaser** (Fiber-to-the-Building)
- **Vertragsbeginn:** 15.12.2025 (4 Wochen vor Umzug – genug Zeit zum Testen)
- **Kosten:** 149 EUR/Monat (Business-Tarif mit fester IP und SLA)
- **Backup-Leitung:** Zusätzlich eine 100 Mbit/s 5G-Anbindung über Vodafone als Failover (29 EUR/Monat)

**Serverraum:**
- Raum ist ca. 8 m², klimatisiert (Split-Klima, separat steuerbar)
- Badge-Zugang – ich habe beim Vermieter angefragt, dass nur 3 Badges für den Serverraum programmiert werden (Markus, Tobias, Sandra)
- Steckdosen: 2x Schuko + 1x CEE 16A (sollte reichen)

**Netzwerk-Verkabelung:**
Der Vermieter hat das Büro mit **Cat 6a** verkabelt übergeben – ca. 40 Dosen verteilt auf alle Zonen. Patch-Panel und Switch-Platz sind im Serverraum vorgesehen. Wir brauchen noch:
- 1x 48-Port Managed Switch (ich bestelle einen UniFi USW-Pro-48-PoE)
- 5x UniFi U6 Enterprise Access Points
- 1x UniFi Dream Machine Pro als Router/Firewall

**USV:**
Ja, bitte eine USV für den Serverraum einplanen. Ich schlage eine APC Smart-UPS 1500VA vor – reicht für unsere Hardware und überbrückt ca. 15-20 Minuten bei Stromausfall. Kosten ca. 600 EUR.

Markus, kannst du den Hardware-Warenkorb zusammenstellen und mir bis Ende nächster Woche schicken? Dann bestelle ich alles zeitnah, damit es rechtzeitig da ist.

Tobias: Bezüglich Firewall – lass uns auf die UniFi-Lösung umsteigen. Die pfSense war gut, aber der UniFi-Stack ist einfacher zu managen und reicht für unsere Bedürfnisse. Whitelist-Updates müssen wir am Umzugswochenende machen, wenn die neue IP steht.

Grüße
Sandra
