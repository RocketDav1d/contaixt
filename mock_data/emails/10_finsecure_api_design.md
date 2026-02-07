---
thread_id: email_thread_010
subject: "FinSecure – API Design: REST vs GraphQL"
---

## Message 1

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Daniel Wolff <d.wolff@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-10 10:15 CET

Hallo zusammen,

ich bin gerade dabei, die API-Architektur fuer das FinSecure Portal auszuarbeiten, und wollte eine Grundsatzfrage frueh klaeren: REST oder GraphQL?

Meine initiale Einschaetzung – und die deckt sich mit unseren API Design Guidelines – ist, dass wir fuer ein Banking-Portal auf REST setzen sollten. Hier meine Argumente:

**Pro REST:**
1. **Audit Trail:** Jeder Endpoint hat eine klar definierte Semantik. `POST /api/v1/transfers` ist eindeutig – ein Audit-Eintrag fuer diesen Call sagt exakt aus, was passiert ist. Bei GraphQL muessten wir die gesamte Query loggen und parsen, um zu verstehen, welche Daten gelesen oder mutiert wurden.
2. **Caching:** HTTP-Caching (ETags, Cache-Control) funktioniert out-of-the-box mit REST. Bei GraphQL muessen wir Application-Level Caching implementieren, was bei den Compliance-Anforderungen von FinSecure zusaetzliche Komplexitaet bedeutet.
3. **Security:** Rate Limiting und Authorization sind bei REST einfacher granular zu implementieren. Wir koennen pro Endpoint unterschiedliche Policies setzen. Bei GraphQL brauchen wir Query Complexity Analysis, um Abuse zu verhindern.
4. **Erfahrung des Kunden:** Das FinSecure-Team hat Erfahrung mit REST. Ihr Core Banking System exponiert REST-APIs. Das reduziert die Einarbeitungszeit und Integrationskomplexitaet erheblich.

Ich habe schon einen ersten Draft fuer die OpenAPI-Spec angefangen. Die Hauptressourcen waeren:
- `/api/v1/accounts` – Kontoinformationen
- `/api/v1/transactions` – Transaktionshistorie
- `/api/v1/transfers` – Ueberweisungen initiieren
- `/api/v1/documents` – Dokumentenmanagement
- `/api/v1/messages` – Secure Messaging

Daniel, ich weiss, du bist ein GraphQL-Fan – lass mich deine Perspektive hoeren, bevor ich weiter in die Detailspezifikation gehe.

Gruesse,
Felix

## Message 2

**From:** Daniel Wolff <d.wolff@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-10 14:40 CET

Hey Felix,

danke, dass du das frueh aufbringst. Ich moechte trotzdem mal den Case fuer GraphQL machen, weil ich glaube, dass wir da einige Vorteile verschenken wuerden:

**Pro GraphQL:**
1. **Frontend Flexibility:** Katharina und ich haben uns die UX-Mockups angeschaut. Das Dashboard soll Kontoinformationen, letzte Transaktionen, ungelesene Nachrichten und Dokumenten-Notifications auf einer Seite zeigen. Mit REST braeuchen wir dafuer 4-5 API Calls. Mit GraphQL machen wir einen einzigen Request und holen genau die Felder, die wir brauchen. Das ist besonders relevant fuer Mobile, wo wir spaeter eine App planen.
2. **Overfetching vermeiden:** Die Transaktionshistorie hat je nach View unterschiedliche Detailtiefe. In der Listenansicht brauchen wir nur Betrag, Datum und Empfaenger. In der Detailansicht kommen IBAN, Verwendungszweck, Status etc. dazu. Mit REST haben wir entweder ein fettes Response-Objekt oder muessen Field-Filtering selbst implementieren (was dann eh quasi GraphQL light ist).
3. **Starke Typisierung:** GraphQL Schema ist self-documenting. Mit TypeScript-Codegen generieren wir direkt typsichere Hooks. Das reduziert Frontend-Bugs massiv.
4. **Real-Time via Subscriptions:** Fuer das Secure Messaging brauchen wir sowieso eine Real-Time-Loesung. GraphQL Subscriptions waeren elegant, anstatt WebSockets separat zu implementieren.

Zum Thema Audit Trail: Apollo Server hat Plugins fuer Operation Logging. Wir koennten jede Query und Mutation mit Persisted Queries whitelisten – dann wissen wir exakt, welche Operations erlaubt sind, und der Audit Trail ist genauso klar wie bei REST.

Ich sage nicht, dass REST schlecht ist – aber ich finde, wir sollten die Entscheidung nicht nur auf Basis von "das kennen wir schon" treffen. Gerade fuer das komplexe Dashboard wuerde GraphQL uns viel Entwicklungszeit im Frontend sparen.

Was meint ihr?

Gruesse,
Daniel

## Message 3

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Daniel Wolff <d.wolff@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-11 09:30 CET

Daniel,

gute Argumente, besonders der Punkt mit dem Dashboard-Aggregation. Lass mich trotzdem kontern:

**Zum Thema Overfetching:** Das loesen wir mit Sparse Fieldsets (`?fields=amount,date,recipient`) oder dedizierten View-Models. Das ist deutlich einfacher zu implementieren und zu warten als ein vollstaendiges GraphQL-Setup mit Schema-Design, Resolver-Architektur und Dataloader-Pattern fuer N+1-Prevention.

**Zum Thema Dashboard:** Wir koennen einen dedizierten `/api/v1/dashboard/summary` Endpoint bauen, der genau die aggregierten Daten fuer die Hauptseite liefert. Das ist ein einzelner Call, hochperformant weil serverseitig optimiert, und trivial zu cachen. Die BFF-Pattern (Backend for Frontend) Idee ist genau dafuer gemacht.

**Zum Thema Audit:** Persisted Queries loesen das Problem nur teilweise. Bei einem BaFin-Audit muessen wir nachweisen koennen, welcher User wann welche Daten abgefragt hat. Bei REST ist das ein simpler Access Log Eintrag: `GET /api/v1/accounts/123/transactions?from=2025-01-01&to=2025-03-31 – User: johndoe – 200 OK`. Bei GraphQL muessten wir die gesamte Query parsen und interpretieren. Das ist machbar, aber unnecessary Complexity in einem Compliance-kritischen Projekt.

**Zum Thema Real-Time:** Fuer Secure Messaging wuerden wir sowieso WebSockets oder SSE separat implementieren, unabhaengig von REST vs. GraphQL. Spring Boot hat exzellenten WebSocket-Support. GraphQL Subscriptions ueber Spring Boot sind dagegen noch relativ unreif.

Dazu kommt: FinSecure hat ein bestehendes Monitoring- und Security-Setup, das auf REST-APIs ausgelegt ist. WAF-Regeln, API Gateway Policies, Rate Limiting – das alles funktioniert out-of-the-box mit REST. GraphQL durch deren Security-Infrastruktur zu schleusen wuerde zusaetzlichen Aufwand und Risiko bedeuten.

Ich bin immer offen fuer die beste technische Loesung, aber in diesem spezifischen Kontext – Banking, BaFin, bestehendes REST-Oekosystem beim Kunden – sehe ich REST klar im Vorteil.

Sandra, was ist deine Einschaetzung?

Gruesse,
Felix

## Message 4

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>
**Date:** 2025-10-12 08:05 CET

Guten Morgen,

ich habe mir eure Argumente in Ruhe durchgelesen. Beide Seiten haben valide Punkte, aber ich muss hier eine klare Entscheidung treffen:

**Wir gehen mit REST + OpenAPI Spec.**

Meine Begruendung:

1. **Compliance-Risiko minimieren:** Felix hat Recht – in einem BaFin-regulierten Umfeld ist Einfachheit ein Feature. Jede zusaetzliche Abstraktionsschicht, die wir zwischen Request und Audit Trail legen, ist ein potenzielles Compliance-Risiko. Unsere Security Policy schreibt klar vor, dass wir bei kundenseitigen Finanzanwendungen den technischen Stack so waehlen, dass Auditierbarkeit priorisiert wird.

2. **Kundenkompatibilitaet:** FinSecure's gesamte Infrastruktur ist REST-basiert. Wenn wir GraphQL einfuehren, muessen sie ihre WAF-Regeln, ihr API Gateway und ihr Monitoring anpassen. Das ist bei EUR 280k Budget nicht drin und wuerde den Go-Live gefaehrden.

3. **Team-Effizienz:** Wir haben 3 Monate bis zum Go-Live. Felix kennt REST im Spring Boot Kontext in- und auswendig. Die Lernkurve fuer GraphQL mit Spring Boot (insbesondere mit Netflix DGS oder Spring GraphQL) in einem Security-kritischen Kontext waere ein Risiko fuer die Timeline.

**Aber – Daniel, deine Punkte sind nicht verloren:**

- Felix, bitte baue den `/api/v1/dashboard/summary` BFF-Endpoint ein, den du vorgeschlagen hast. Das loest Daniels berechtigtes Concern bezueglich Multi-Request-Dashboard.
- Sparse Fieldsets (`?fields=...`) sollen fuer alle Listenendpoints unterstuetzt werden.
- Fuer Phase 2, wenn wir ueber die Mobile App sprechen, evaluieren wir GraphQL als API-Gateway-Layer vor den bestehenden REST-Services. Dann hat sich der REST-Layer bewaehrt, und wir koennen GraphQL als Frontend-Optimierung draufsetzen, ohne die Backend-Audit-Architektur zu aendern.

Felix, bitte finalisiere die OpenAPI Spec bis Ende naechster Woche. Ich moechte, dass wir die Spec mit Dr. Berger reviewen, bevor wir mit der Implementierung starten. Die Spec wird Teil der Vertragsdokumentation.

Daniel, ich schaetze es sehr, dass du proaktiv Alternativen einbringst. Keep challenging – genau das macht uns besser. Ich moechte, dass du den Review der OpenAPI Spec aus Frontend-Perspektive uebernimmst und sicherstellst, dass alle Views, die Katharina designed hat, mit den geplanten Endpoints abbildbar sind.

Gruesse,
Sandra
