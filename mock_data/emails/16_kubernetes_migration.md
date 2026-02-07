---
thread_id: email_thread_016
subject: "Interne Plattform – Kubernetes Migration"
---

## Message 1

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>
**Date:** 2025-10-01 09:15

Hallo zusammen,

ich möchte ein Thema anstoßen, das uns schon länger beschäftigt: die Migration unserer internen Plattform-Services von Docker Compose auf Kubernetes. Aktuell laufen unsere Staging- und Production-Environments auf drei dedizierten VMs mit Docker Compose. Das funktioniert grundsätzlich, aber wir stoßen zunehmend an Grenzen:

**Aktuelle Pain Points:**
- Kein automatisches Scaling bei Last-Spitzen (gerade das Aurora-Projekt wird hier zum Problem)
- Rolling Updates sind manuell und fehleranfällig
- Secret Management über .env-Files ist ein Security-Risiko (Tobias hat das auch schon angemerkt)
- Kein vernünftiges Health Monitoring mit automatischem Restart
- Resource Isolation zwischen Services ist praktisch nicht vorhanden

**Mein Vorschlag:**
Wir migrieren schrittweise auf einen Managed Kubernetes Cluster. Konkret denke ich an Azure Kubernetes Service (AKS), weil wir ohnehin schon Azure-Infrastruktur nutzen. Der Plan wäre:

1. **Helm Charts** für alle Services erstellen (API, Worker, PostgreSQL, Neo4j)
2. **Namespace-Trennung** nach Environments: `dev`, `staging`, `production`
3. **Resource Limits und Requests** pro Service definieren (CPU/Memory)
4. **Horizontal Pod Autoscaler** für API und Worker
5. **Sealed Secrets** oder Azure Key Vault für Secret Management

Ich habe bereits einen Proof of Concept mit unserer API in einem lokalen k3d-Cluster gemacht – läuft einwandfrei. Die Helm Charts für den API-Service habe ich auch schon als Draft vorbereitet.

Kostenabschätzung für AKS: ca. 800-1.200 EUR/Monat für einen 3-Node-Cluster (Standard_D2s_v3), abhängig vom Scaling. Das ist vergleichbar mit unseren aktuellen VM-Kosten, aber mit deutlich mehr Flexibilität.

Können wir das in der nächsten Architektur-Runde besprechen? Ich würde gerne einen detaillierten Migration Plan vorstellen.

Grüße
Markus

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Markus Lang <m.lang@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>
**Date:** 2025-10-02 10:30

Hi Markus,

grundsätzlich bin ich absolut dafür – die Pain Points mit Docker Compose kann ich nur bestätigen. Besonders das Deployment ist jedes Mal ein Abenteuer. Letzte Woche hatten wir wieder den Fall, dass ein `docker compose up -d` auf Staging einen Service gekillt hat, der eigentlich nicht neu gestartet werden sollte.

Ein paar Fragen/Anmerkungen zur Local Dev Experience:

**Lokale Entwicklung:**
Du hast k3d erwähnt – wie sieht der Workflow für Entwickler aus? Aktuell starten wir einfach `docker compose up` und haben alles lokal am Laufen. Kubernetes lokal kann schnell komplex werden. Ich habe Erfahrung mit **kind** (Kubernetes in Docker) und fand das für lokale Zwecke ganz brauchbar, aber der Ressourcenverbrauch auf dem MacBook ist nicht ohne.

Mein Vorschlag wäre ein **Hybrid-Ansatz**:
- **Lokal:** Weiterhin Docker Compose für die tägliche Entwicklung (schnell, lightweight, bekannt)
- **CI/CD + Staging + Prod:** Kubernetes mit Helm Charts
- **Skaffold** oder **Tilt** als Bridge zwischen lokalem Code und K8s-Cluster für Integration Testing

So müssen nicht alle Devs Kubernetes-Expertise aufbauen, nur um lokal zu entwickeln. Wer will, kann natürlich einen lokalen k3d/kind-Cluster aufsetzen.

**Helm Charts:**
Können wir die als Monorepo-Structure unter `/infrastructure/helm/` anlegen? Dann haben wir alles versioniert und können über ArgoCD oder Flux GitOps machen.

**Database-Migration:**
Wie handeln wir PostgreSQL und Neo4j? Managed Services (Azure Database for PostgreSQL, Neo4j Aura) oder als StatefulSets im Cluster? Ich würde stark zu Managed tendieren – Datenbanken in K8s zu betreiben ist immer noch tricky.

Bin auf jeden Fall dabei, wenn es um die technische Umsetzung geht!

Viele Grüße
Felix

## Message 3

**From:** Anna Richter <a.richter@techvision-gmbh.de>
**To:** Markus Lang <m.lang@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>
**Date:** 2025-10-02 14:45

Hallo alle,

aus Data-Engineering-Sicht habe ich noch ein paar Punkte, die wir berücksichtigen sollten:

**Batch Jobs und CronJobs:**
Wir haben mehrere Data Pipelines, die aktuell als Cron Jobs auf den VMs laufen (Nango-Syncs, Embedding-Reprocessing, DB-Backups). Kubernetes hat native CronJob-Ressourcen – das wäre ein großer Fortschritt gegenüber dem aktuellen Setup mit crontab-Files, die niemand versioniert.

**Resource Management für ML-Workloads:**
Unsere Embedding-Jobs sind ziemlich resource-hungry. Mit Kubernetes könnten wir dedizierte Node Pools für compute-intensive Workloads einrichten. Das wäre auch für zukünftige ML-Pipelines relevant, falls wir irgendwann eigene Modelle fine-tunen wollen.

**Monitoring und Observability:**
Können wir im Zuge der Migration auch gleich ein vernünftiges Monitoring-Stack aufsetzen? Ich denke an:
- **Prometheus + Grafana** für Metrics (gibt's fertige Helm Charts)
- **Loki** für Log-Aggregation (ersetzt unser aktuelles `docker logs`-Chaos)
- **Jaeger** oder **Tempo** für Distributed Tracing

Das würde uns enorm helfen, Performance-Bottlenecks in der Pipeline zu identifizieren. Aktuell fliegen wir da komplett blind.

Ich unterstütze Felix' Vorschlag mit Managed Databases. Unsere pgvector-Instanz braucht spezielle Extensions – da ist Azure Database for PostgreSQL Flexible Server ideal, weil pgvector dort supported wird.

Grüße
Anna

## Message 4

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Markus Lang <m.lang@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>
**Date:** 2025-10-03 16:00

Hi Team,

danke für die ausführliche Diskussion – ich bin überzeugt, dass die K8s-Migration der richtige Schritt ist. Hier meine Entscheidungen:

**Budget: Approved.**
Ich habe mit Martin und Petra gesprochen. Wir haben Budget für:
- **AKS Cluster:** bis zu 1.500 EUR/Monat (inkl. Buffer für Scaling)
- **Azure Database for PostgreSQL Flexible Server:** ca. 300 EUR/Monat (General Purpose, 4 vCores)
- **Neo4j Aura Professional:** ca. 200 EUR/Monat
- **Einmalige Setup-Kosten:** bis zu 5.000 EUR für externe Beratung falls nötig

Das ergibt ca. 2.000 EUR/Monat laufende Kosten – das ist ein Uplift von ca. 600 EUR gegenüber den aktuellen VM-Kosten, aber die Vorteile (Autoscaling, Reliability, Security) rechtfertigen das absolut.

**Entscheidungen:**
1. **Managed Databases** – ja, definitiv. Kein PostgreSQL oder Neo4j im Cluster.
2. **Hybrid Local Dev** – Felix' Vorschlag mit Docker Compose lokal und K8s für Staging/Prod finde ich pragmatisch und richtig.
3. **Monitoring Stack** – Annas Vorschlag mit Prometheus/Grafana/Loki nehmen wir mit rein. Das ist überfällig.
4. **GitOps mit ArgoCD** – bitte von Anfang an einplanen.

**Anforderung:**
Markus, bitte erstelle einen detaillierten Migration Plan mit Timeline. Ich möchte, dass wir das bis Ende Q1 2026 abgeschlossen haben. Security-Review durch Tobias muss vor dem Go-Live passieren.

Wer braucht Kubernetes-Schulung? Bitte bei Julia melden, wir können ein Team-Training organisieren.

Beste Grüße
Sandra

## Message 5

**From:** Markus Lang <m.lang@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Anna Richter <a.richter@techvision-gmbh.de>
**Date:** 2025-10-05 11:20

Hallo zusammen,

danke für das Go-Ahead, Sandra! Hier ist der Migration-Timeline über 3 Monate:

**Phase 1 – Foundation (Oktober 2025):**
- Woche 1-2: AKS Cluster Setup, Networking (VNet, Subnets, NSGs), Azure AD Integration
- Woche 2-3: Helm Chart Development für alle Services (API, Worker, Ingress)
- Woche 3-4: CI/CD Pipeline umbauen (GitHub Actions → Build → Push to ACR → ArgoCD Deploy)
- Parallel: Managed Database Setup (PostgreSQL Flexible Server + Neo4j Aura)

**Phase 2 – Migration Staging (November 2025):**
- Woche 1-2: Staging Environment auf K8s deployen, Smoke Tests
- Woche 2-3: Monitoring Stack (Prometheus, Grafana, Loki) installieren und konfigurieren
- Woche 3-4: Load Testing und Performance Tuning (Resource Limits, HPA-Thresholds)
- Security Review mit Tobias (Network Policies, Pod Security Standards, RBAC)

**Phase 3 – Production Go-Live (Dezember 2025/Januar 2026):**
- Woche 1: Production Cluster aufsetzen (separater Cluster, nicht Staging!)
- Woche 2: Daten-Migration (pgvector-Daten, Neo4j-Graph)
- Woche 3: Canary Deployment – 10% Traffic auf K8s, 90% auf alte Infra
- Woche 4: Vollständige Migration, alte VMs dekommissionieren

**Verantwortlichkeiten:**
- **Markus (Lead):** Cluster Setup, Helm Charts, CI/CD, Networking
- **Felix:** Application-Level Anpassungen, Health Checks, Graceful Shutdown
- **Anna:** Database Migration, CronJob-Definitionen, Monitoring Dashboards
- **Tobias:** Security Review (Phase 2, Woche 4)

Ich habe ein Confluence-Page erstellt mit allen Details: [K8s Migration Plan](https://techvision.atlassian.net/wiki/k8s-migration). Bitte reviewt das und gebt Feedback bis Ende der Woche.

Felix, können wir Donnerstag ein kurzes Pairing machen für die Helm Charts? Ich würde gerne dein Feedback zur Chart-Struktur einholen.

Grüße
Markus
