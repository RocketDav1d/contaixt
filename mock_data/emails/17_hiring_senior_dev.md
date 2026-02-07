---
thread_id: email_thread_017
subject: "Hiring – Senior Backend Developer"
---

## Message 1

**From:** Julia Meier <j.meier@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-10-20 09:00

Hallo zusammen,

wie in der letzten Teamleiter-Runde besprochen, habe ich die Stellenausschreibung für den/die **Senior Backend Developer:in (m/w/d)** finalisiert. Hier die Key Points:

**Position: Senior Backend Developer (Python/FastAPI)**
- **Team:** Platform Engineering, Reports to Sandra
- **Standort:** München-Schwabing (Hybrid, 3 Tage Office / 2 Tage Remote)
- **Gehaltsbandbreite:** 75.000 – 90.000 EUR (je nach Erfahrung)
- **Start:** Zum nächstmöglichen Zeitpunkt, idealerweise Q1 2026

**Must-Have Requirements:**
- 5+ Jahre Erfahrung in Python Backend-Entwicklung
- Sehr gute Kenntnisse in FastAPI oder vergleichbaren async Frameworks
- Erfahrung mit PostgreSQL und SQLAlchemy (idealerweise async)
- Solides Verständnis von RESTful API Design und OpenAPI/Swagger
- Erfahrung mit Docker und CI/CD Pipelines
- Fließend Deutsch und Englisch

**Nice-to-Have:**
- Erfahrung mit Kubernetes
- Kenntnisse in Graph-Datenbanken (Neo4j)
- Erfahrung mit Vector Databases (pgvector, Pinecone, Weaviate)
- Background in NLP oder Machine Learning

**Recruiting Channels:**
Ich werde die Stelle auf folgenden Plattformen posten:
- LinkedIn (Sponsored Post, Budget 500 EUR)
- StepStone
- Indeed
- Stack Overflow Jobs
- Python-Community Slack Channels (PyMunich, PyCon DE)

Außerdem werde ich unser Employee Referral Program pushen – 3.000 EUR Prämie für erfolgreiche Vermittlung.

Sandra, Felix: Bitte schaut euch die Anforderungen nochmal an und gebt mir bis morgen Feedback. Ich würde die Stelle gerne Ende dieser Woche live schalten.

Die Interview Pipeline ist wie üblich: HR Screening → Technical Interview → Team Fit → Offer.

Viele Grüße
Julia

## Message 2

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Julia Meier <j.meier@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-10-21 11:15

Hi Julia,

die Ausschreibung sieht gut aus! Ich möchte aber ein paar Punkte ergänzen, die mir wichtig sind:

**Zusätzliche Must-Have Requirements:**
Bitte nimm noch **Erfahrung mit Event-Driven Architecture** als Must-Have auf. Wir bauen gerade unsere gesamte Pipeline auf ein Event-basiertes Modell um (Job Queue mit Postgres, perspektivisch evtl. Kafka oder NATS). Der/die neue Kolleg:in muss mit Patterns wie Event Sourcing, CQRS oder zumindest Message Queues vertraut sein.

Außerdem wäre mir wichtig:
- **Erfahrung mit async Python** (asyncio, nicht nur FastAPI, sondern wirklich tiefes Verständnis von Concurrency Patterns)
- **Testing-Mindset** – wir wollen unsere Test Coverage deutlich verbessern. Erfahrung mit pytest, pytest-asyncio und Mocking von externen Services ist wichtig.

**Zur Gehaltsbandbreite:**
75k-90k finde ich für München etwas knapp, besonders wenn wir jemanden mit Event-Driven-Erfahrung suchen. Können wir die Obergrenze auf **95.000 EUR** anheben? Martin, was meinst du? Im aktuellen Markt müssen wir competitiv sein, sonst verlieren wir gute Kandidat:innen an die großen Tech-Companies.

**Nice-to-Have Ergänzung:**
- Erfahrung mit **OpenAI API / LLM Integration** (wird immer relevanter für unser Produkt)
- Contributions zu Open-Source-Projekten (zeigt Engagement und Code-Qualität)

**Team Setup:**
Die Person würde primär am Aurora-Projekt arbeiten und eng mit Felix und Anna zusammenarbeiten. Langfristig soll sie das Backend-Team als Tech Lead verstärken, wenn wir weiter wachsen.

Grüße
Sandra

## Message 3

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Julia Meier <j.meier@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-10-22 14:30

Hi Julia, Sandra,

ich stimme Sandra bei allen Punkten zu – besonders Event-Driven Architecture ist ein Muss. Wir haben aktuell einige komplexe Race Conditions in der Job Pipeline, die jemand mit solidem Async-Verständnis sofort erkennen würde.

**Technical Interview:**
Ich übernehme gerne die technischen Interviews! Hier mein Vorschlag für das Format:

**Teil 1: Live Coding (45 Min)**
- Eine praxisnahe Aufgabe: Einen async FastAPI Endpoint bauen, der Jobs in eine Queue schreibt und Ergebnisse pollt
- Fokus auf: Code-Qualität, Error Handling, Typing, async Patterns
- Kein Whiteboard-Algorithmus-Quatsch – wir wollen sehen, wie die Person tatsächlich arbeitet

**Teil 2: System Design (30 Min)**
- Szenario: "Design eine Document Processing Pipeline, die Dokumente chunkt, embeddet und in einer Graph-DB speichert"
- Das ist quasi unser Produkt – so sehen wir sofort, ob die Person mit den Konzepten vertraut ist
- Bewertungskriterien: Skalierbarkeit, Fehlerbehandlung, Idempotenz, Monitoring

**Teil 3: Code Review (15 Min)**
- Ich bereite einen PR mit absichtlichen Schwachstellen vor (Security, Performance, Error Handling)
- Die Person soll den Code reviewen und Verbesserungen vorschlagen

Ich werde die Aufgaben in einem privaten GitHub Repo vorbereiten. Soll ich auch ein Bewertungsformular erstellen, damit wir Kandidat:innen konsistent vergleichen können?

Sandra: Ja, 95k Obergrenze finde ich richtig. Gute Leute kosten gutes Geld, und es ist günstiger als 6 Monate mit unbesetzter Stelle zu arbeiten.

Grüße
Felix

## Message 4

**From:** Julia Meier <j.meier@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Dr. Martin Schreiber <m.schreiber@techvision-gmbh.de>
**Date:** 2025-10-25 10:00

Hallo zusammen,

kurzes Update zum Recruiting-Status – die Stelle ist seit Montag live und wir haben bereits 47 Bewerbungen erhalten! Nach dem ersten HR-Screening (CV-Check, Qualifikationsabgleich, Gehaltsvorstellungen) habe ich **drei vielversprechende Kandidat:innen** identifiziert:

**Kandidat 1: Dr. Kai Lehmann**
- Aktuell: Senior Software Engineer bei Celonis (München), 6 Jahre Erfahrung
- Stack: Python, FastAPI, Kafka, PostgreSQL, Kubernetes
- Highlight: Hat bei Celonis die Event-Processing-Pipeline mitgebaut (>1M Events/Tag)
- Gehaltsvorstellung: 88.000 EUR
- Verfügbarkeit: 3 Monate Kündigungsfrist → Start April 2026
- Eindruck: Sehr stark auf dem Papier, perfekter Match für Event-Driven Requirements

**Kandidatin 2: Nadia Petrov**
- Aktuell: Backend Lead bei einem Startup (Berlin), 7 Jahre Erfahrung
- Stack: Python, Django/FastAPI, RabbitMQ, PostgreSQL, Docker, AWS
- Highlight: Hat zwei Backend-Teams aufgebaut (5+ Devs), Open-Source-Contributor (httpx, pydantic)
- Gehaltsvorstellung: 92.000 EUR
- Verfügbarkeit: 1 Monat Kündigungsfrist → Start Dezember 2025
- Eindruck: Leadership-Erfahrung, Open-Source-Engagement beeindruckend. Umzug nach München ist für sie kein Problem.

**Kandidat 3: Jonas Herrera**
- Aktuell: Software Engineer bei Siemens Digital Industries (Erlangen), 5 Jahre Erfahrung
- Stack: Python, aiohttp/FastAPI, Redis Streams, PostgreSQL, Neo4j (!), Azure
- Highlight: Arbeitet bereits mit Graph-Datenbanken und hat Erfahrung mit pgvector
- Gehaltsvorstellung: 82.000 EUR
- Verfügbarkeit: 2 Monate Kündigungsfrist → Start Januar 2026
- Eindruck: Neo4j- und pgvector-Erfahrung ist ein Unicorn-Match für uns. Etwas weniger Senior, aber perfekter Stack-Fit.

**Nächste Schritte:**
Ich schlage vor, alle drei zu Technical Interviews einzuladen. Felix, kannst du nächste Woche drei Slots freihalten (jeweils 90 Min)?

Martin hat die Gehaltsobergrenze von 95k übrigens abgenickt – danke Sandra für den Push.

Die restlichen 44 Bewerbungen waren leider nicht auf dem gewünschten Level – viele hatten keine async Python-Erfahrung oder waren zu junior.

Viele Grüße
Julia
