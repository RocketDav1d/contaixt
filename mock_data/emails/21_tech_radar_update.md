---
thread_id: email_thread_021
subject: "Tech Radar Update Q4 2025"
---

## Message 1

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-01 09:15

Hallo zusammen,

es ist wieder soweit — wir stehen vor dem Q4 Tech Radar Review. Wie ihr wisst, aktualisieren wir den Tech Radar jedes Quartal, um sicherzustellen, dass unsere Technology Choices aktuell und strategisch sinnvoll bleiben.

Kurzer Reminder zu unseren Kategorien:
- **Adopt** — Produktionsreif, aktiv genutzt
- **Trial** — Vielversprechend, Einsatz in Pilotprojekten erlaubt
- **Assess** — Evaluierung läuft, noch kein produktiver Einsatz
- **Hold** — Nicht mehr für neue Projekte empfohlen

Ich bitte euch, bis Ende der Woche eure Vorschläge für Änderungen einzureichen. Bitte begründet jede Empfehlung kurz — idealerweise mit konkreten Erfahrungen aus unseren aktuellen Projekten (Aurora, MedTech Portal, etc.).

Das Tech Radar Dokument im Confluence ist der Single Point of Truth. Ich werde nach unserer Abstimmung alles konsolidieren und das Dokument updaten.

Noch ein Hinweis: Dr. Schreiber hat im letzten Leadership Meeting betont, dass wir beim Tech Radar stärker auf Total Cost of Ownership und Hiring-Relevanz achten sollen. Also bitte auch diese Aspekte berücksichtigen.

Freue mich auf eure Inputs!

Beste Grüße
Sandra

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-02 10:42

Hi Sandra, hi alle,

hier meine Vorschläge für das Q4 Update:

**1. Rust — Move von "Assess" zu "Trial"**
Wir haben im Aurora-Projekt den Document Parsing Service als Proof of Concept in Rust implementiert. Die Performance-Gains sind beeindruckend: 12x schneller als die Python-Variante beim Chunking großer PDFs, Memory Usage bei einem Bruchteil. Für performance-kritische Microservices sehe ich hier großes Potenzial. Daniel und ich haben in den letzten Monaten intensiv Rust gelernt, und ich denke, wir haben genug Expertise aufgebaut, um das in Trial zu bewegen.

**2. htmx — Move zu "Assess"**
Ich weiß, das klingt erstmal ungewöhnlich für uns als API-first Shop, aber für interne Tools und Admin-Dashboards könnte htmx extrem produktiv sein. Katharina und ich haben einen kleinen Prototype für das interne Projekt-Dashboard gebaut — die Developer Experience ist fantastisch, und wir sparen uns den ganzen React-Overhead für simple CRUD-Interfaces. Würde gerne eine formale Evaluierung starten.

**3. LangChain — Keep on "Hold"**
Nachdem wir beim Aurora-Projekt bewusst auf LangChain verzichtet und stattdessen direkt mit der OpenAI API gearbeitet haben, bin ich weiterhin überzeugt, dass LangChain für unsere Use Cases zu viel Abstraktion mitbringt. Unser eigener GraphRAG-Stack ist lean und transparent. Hold bleibt die richtige Kategorie.

Zum Thema Hiring-Relevanz: Rust-Entwickler sind aktuell extrem gefragt. Wenn wir Rust offiziell im Tech Radar haben, hilft das definitiv beim Recruiting.

VG
Felix

---

## Message 3

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-03 08:30

Hallo zusammen,

von der Data Engineering Seite habe ich folgende Vorschläge:

**1. Apache Iceberg — Move zu "Trial"**
Wir evaluieren Iceberg seit Q2 als Table Format für unseren Data Lakehouse Ansatz. Die Ergebnisse sind sehr vielversprechend: Schema Evolution funktioniert nahtlos, Time Travel Queries ermöglichen einfaches Debugging, und die Integration mit unserem bestehenden PostgreSQL/pgvector Setup über Trino ist machbar. Für das MedTech-Projekt brauchen wir ohnehin eine robuste Data Lakehouse Lösung, da die Datenmengen mit den medizinischen Dokumenten signifikant steigen werden. Ich würde vorschlagen, Iceberg im Q1 2026 als Pilot im MedTech-Kontext einzusetzen.

**2. dbt (data build tool) — Keep on "Adopt"**
Läuft stabil bei uns, keine Änderung nötig. Wir nutzen es für alle Data Transformations im Analytics Stack.

**3. Apache Kafka — Move von "Assess" zu "Trial"**
Mit dem Wachstum unserer Kunden und der steigenden Anzahl von Webhook-Events (Nango Syncs, Gmail Webhooks, etc.) stoßen wir mit unserer Postgres-basierten Job Queue an Skalierungsgrenzen. Kafka als Event Streaming Platform könnte uns helfen, das System resilienter zu machen. Allerdings ist der Operational Overhead nicht zu unterschätzen — daher vielleicht erstmal Confluent Cloud evaluieren?

Zum TCO-Aspekt: Iceberg ist Open Source und hat eine aktive Community. Confluent Cloud hat natürlich laufende Kosten, aber spart uns DevOps-Aufwand.

Beste Grüße
Anna

---

## Message 4

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-04 11:15

Hi zusammen,

aus der DevOps/Infra-Perspektive:

**1. Docker Compose (Production) — Move zu "Hold"**
Ja, ich weiß, Docker Compose ist bequem und wir nutzen es aktuell noch für kleinere Deployments. Aber für Production ist Kubernetes der richtige Weg — und das sage ich nicht nur, weil ich der K8s-Evangelist bin. Wir haben im letzten Quartal drei Incidents gehabt, die direkt auf fehlende Orchestrierung zurückzuführen waren: kein automatisches Rescheduling, keine Rolling Updates, kein vernünftiges Secret Management. Docker Compose bleibt natürlich für Local Development auf "Adopt".

**2. ArgoCD — Keep on "Adopt"**
Läuft stabil, GitOps-Workflow ist etabliert. Kein Änderungsbedarf.

**3. Terraform — Keep on "Adopt"**
Bewährt sich weiterhin für unser Infrastructure as Code. Wir sollten aber im Q1 OpenTofu evaluieren, falls HashiCorp die Lizenz weiter verschärft. Vielleicht OpenTofu auf "Assess" setzen?

Zu Annas Kafka-Vorschlag: Bin dabei. Confluent Cloud würde uns den operativen Aufwand ersparen. Ich kann das Infra-Setup für einen Pilot vorbereiten, wenn wir uns darauf einigen.

Und Felix, zum Thema Rust: Volle Zustimmung. Die Container Images für den Rust-Service sind winzig (< 20MB) verglichen mit unseren Python-Images (> 500MB). Das spart auch Cloud-Kosten.

Grüße
Markus

---

## Message 5

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>, Katharina Schmidt <k.schmidt@techvision-gmbh.de>, Daniel Wolff <d.wolff@techvision-gmbh.de>
**Date:** 2025-12-05 14:00

Hallo zusammen,

vielen Dank für eure ausführlichen Inputs! Ich habe alles konsolidiert. Hier die Zusammenfassung der Entscheidungen für den Tech Radar Q4 2025:

**Moves:**
- **Rust** → "Trial" (Performance-kritische Services, Pilot im Aurora-Kontext)
- **htmx** → "Assess" (Evaluierung für interne Tools, formaler PoC im Q1)
- **Apache Iceberg** → "Trial" (Data Lakehouse Pilot im MedTech-Projekt)
- **Apache Kafka (Confluent Cloud)** → "Trial" (Event Streaming als Ergänzung zur Postgres Job Queue)
- **Docker Compose (Production)** → "Hold" (nur noch für Local Dev, K8s für Production)
- **OpenTofu** → "Assess" (Terraform-Alternative evaluieren)

**Unchanged:**
- LangChain bleibt auf "Hold"
- dbt bleibt auf "Adopt"
- ArgoCD bleibt auf "Adopt"
- Terraform bleibt auf "Adopt"

Ich werde das Tech Radar Confluence-Dokument bis Freitag aktualisieren und die Änderungen im nächsten All-Hands am 12. Dezember vorstellen. Felix, kannst du bitte den Rust-PoC im Aurora-Kontext als Case Study dokumentieren? Das wäre super als Referenz.

Für Q1 2026 nehme ich mir vor, dass wir für jedes "Trial"-Item klare Success Criteria definieren, damit wir datenbasiert entscheiden können, ob etwas nach "Adopt" geht oder zurück auf "Assess".

Danke für die konstruktive Diskussion!

Beste Grüße
Sandra
