---
thread_id: email_thread_005
subject: "Aurora – Security Review & Penetration Test"
---

## Message 1

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-15 09:00

Hallo zusammen,

ich habe den **Security Review und Penetration Test** für die Aurora-Plattform abgeschlossen. Den vollständigen Report findet ihr im Confluence unter `/projects/aurora/security/pentest-report-2025-11`. Hier die Zusammenfassung:

**Scope:** API Gateway, Data Platform APIs, Dashboard-Anwendung, Azure Infrastructure

**Testmethodik:** Kombination aus automatisierten Scans (OWASP ZAP, Burp Suite Pro) und manuellen Tests. Durchgeführt gegen die Staging-Umgebung (`aurora-staging.techvision-gmbh.de`).

**Ergebnisse:**

| Severity | Anzahl | Status |
|----------|--------|--------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 2 | Open |
| Low | 4 | Open |
| Info | 8 | Acknowledged |

**Medium Findings:**

**M-001: Missing Rate Limiting on API Endpoints**
- **Betroffen:** `/api/v1/query`, `/api/v1/reports/generate`, `/api/v1/auth/login`
- **Beschreibung:** Die API-Endpoints haben kein Rate Limiting implementiert. Ein Angreifer könnte durch Brute-Force-Angriffe auf den Login-Endpoint oder durch übermäßige Query-Requests die Plattform überlasten (DoS).
- **CVSS Score:** 5.3 (Medium)
- **Empfehlung:** Rate Limiting via **Azure API Management** oder direkt im Application Layer (z.B. `slowapi` für FastAPI). Empfohlene Limits: 100 req/min für authentifizierte User, 10 req/min für Login-Versuche.

**M-002: Overly Permissive CORS Configuration**
- **Betroffen:** API Gateway Konfiguration
- **Beschreibung:** Die CORS-Policy erlaubt aktuell `Access-Control-Allow-Origin: *`. Das ist in der Staging-Umgebung gesetzt worden und muss vor Go-Live auf die spezifischen Domains eingeschränkt werden.
- **CVSS Score:** 4.7 (Medium)
- **Empfehlung:** CORS auf `https://aurora.mueller-maschinenbau.de` und `https://admin.aurora.techvision-gmbh.de` beschränken.

**Low Findings (Kurzfassung):**
- L-001: HTTP Security Headers unvollständig (fehlende `X-Content-Type-Options`, `X-Frame-Options`)
- L-002: Verbose Error Messages in Development Mode (Stack Traces sichtbar)
- L-003: Session Timeout zu lang (aktuell 24h, empfohlen 4h für inaktive Sessions)
- L-004: API-Dokumentation (Swagger UI) in Staging öffentlich zugänglich

Gemäß unserem **Security Policy Document (v2.3)** müssen alle Medium- und High-Findings vor einem Production Deployment behoben werden. Die Low-Findings sollten innerhalb von 30 Tagen nach Go-Live adressiert werden.

Ich bitte um Rückmeldung, wer die Findings übernimmt und bis wann sie behoben werden können.

Viele Grüße
Tobias

---

## Message 2

**From:** Felix Braun <f.braun@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-15 11:28

Hi Tobias,

danke für den gründlichen Report. Keine Critical oder High Findings ist schon mal ein gutes Zeichen.

Ich übernehme die beiden **Medium Findings**:

**M-001 (Rate Limiting):**
Ich implementiere das direkt im Application Layer mit **`slowapi`** (basiert auf `limits`). Für die FastAPI-Endpoints wird das wie folgt aussehen:
- `/api/v1/auth/login`: 10 Requests pro Minute pro IP
- `/api/v1/query`: 60 Requests pro Minute pro authentifiziertem User
- `/api/v1/reports/generate`: 20 Requests pro Minute (Report Generation ist resource-intensive)
- Alle anderen authentifizierten Endpoints: 120 Requests pro Minute

Zusätzlich werde ich einen **Custom Rate Limit Exceeded Handler** bauen, der ein korrektes `429 Too Many Requests` mit `Retry-After` Header zurückgibt.

**Geschätzter Aufwand:** 1-2 Tage

**M-002 (CORS):**
Das ist ein Quick Fix. Ich passe die CORS-Middleware in der FastAPI-Konfiguration an:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aurora.mueller-maschinenbau.de",
        "https://admin.aurora.techvision-gmbh.de"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```
**Geschätzter Aufwand:** 30 Minuten

Für die **Low Findings** schlage ich vor:
- L-001 und L-002: Übernehme ich mit, ist wenig Aufwand (Security Headers Middleware + Production Config)
- L-003: Markus, kannst du das Session Timeout in der Azure AD App Registration anpassen?
- L-004: Markus, Swagger UI in Staging/Prod hinter Auth setzen (über Ingress Config)

Ich erstelle Jira Tickets für alles und ziele darauf ab, die Medium Findings bis **Ende nächster Woche (22.11.)** zu haben.

Gruß
Felix

---

## Message 3

**From:** Tobias Fischer <t.fischer@techvision-gmbh.de>
**To:** Felix Braun <f.braun@techvision-gmbh.de>, Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-16 10:05

Hi Felix,

klingt gut. Noch ein Hinweis zum **OWASP Top 10 Compliance Check**, den ich parallel durchgeführt habe:

Wir sind bei **9 von 10 Kategorien compliant**. Die einzige offene Kategorie ist **A05:2021 – Security Misconfiguration**, was sich mit den beiden Medium Findings deckt (Rate Limiting und CORS).

Hier die Details für die Dokumentation:

| OWASP Top 10 Category | Status | Bemerkung |
|------------------------|--------|-----------|
| A01: Broken Access Control | Pass | Azure AD RBAC + API-Level Authorization |
| A02: Cryptographic Failures | Pass | TLS 1.3, AES-256 at rest |
| A03: Injection | Pass | SQLAlchemy ORM (parameterized), Input Validation |
| A04: Insecure Design | Pass | Threat Modeling durchgeführt |
| A05: Security Misconfiguration | Partial | M-001, M-002 offen |
| A06: Vulnerable Components | Pass | Dependabot aktiv, keine bekannten CVEs |
| A07: Auth Failures | Pass | Azure AD, MFA enforced |
| A08: Software/Data Integrity | Pass | Signed Container Images, Terraform State Lock |
| A09: Logging/Monitoring Failures | Pass | Azure Monitor, Grafana Alerting |
| A10: SSRF | Pass | No external URL fetching in application |

Für die **ISO 27001 Anforderungen** von Müller Maschinenbau benötige ich noch:
- Das Data Processing Agreement (DPA) – Lisa, hast du das schon mit der Rechtsabteilung geklärt?
- Den Nachweis der Azure SOC 2 Type II Zertifizierung – das kann ich über das Microsoft Trust Center ziehen
- Unsere interne **Information Security Policy** (Referenz: Security Policy Document v2.3) als Anlage zum Vertrag

Ich werde den finalen Security Assessment Report erstellen, sobald die Medium Findings behoben sind. Bitte informiert mich, wenn die Fixes deployed sind, damit ich den **Re-Test** durchführen kann.

Grüße
Tobias

---

## Message 4

**From:** Sandra Hoffmann <s.hoffmann@techvision-gmbh.de>
**To:** Tobias Fischer <t.fischer@techvision-gmbh.de>, Felix Braun <f.braun@techvision-gmbh.de>, Lisa Weber <l.weber@techvision-gmbh.de>, Markus Lang <m.lang@techvision-gmbh.de>
**Date:** 2025-11-17 08:47

Guten Morgen zusammen,

danke für den exzellenten Security Review, Tobias. Und Felix, danke für die schnelle Übernahme der Findings.

Mir ist es sehr wichtig, dass wir **alle Medium Findings vor dem Go-Live am 02.12. resolved haben**. Hier mein erwarteter Timeline:

1. **22.11.** – Felix hat die Fixes für M-001 und M-002 implementiert und deployed auf Staging
2. **25.11.** – Tobias führt den Re-Test durch
3. **26.11.** – Tobias gibt Security Clearance für Production Deployment
4. **28.11.** – Deployment auf Production (als Teil der Go-Live Vorbereitung)

Das gibt uns einen Buffer von 4 Tagen vor dem Go-Live am 02.12.

Felix, hältst du den **22.11.** für realistisch? Wenn es Abhängigkeiten oder Blocker gibt, möchte ich das jetzt wissen, nicht erst nächste Woche.

Bezüglich der **Low Findings**: Ich stimme zu, dass die innerhalb von 30 Tagen nach Go-Live adressiert werden können. Bitte aber trotzdem Jira Tickets erstellen, damit nichts vergessen wird.

Tobias, den finalen Security Assessment Report benötige ich spätestens am **27.11.**, damit ich ihn Hans Müller vor dem Go-Live vorlegen kann. Er hatte im letzten Steering Committee explizit danach gefragt.

Dr. Schreiber möchte außerdem, dass wir das **Pentest-Ergebnis** (keine Critical/High Findings) im nächsten Newsletter der TechVision GmbH als Qualitätsmerkmal erwähnen. Ich koordiniere das mit dem Marketing.

Viele Grüße
Sandra
