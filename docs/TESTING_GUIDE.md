# Sicherheits- und Lasttest Leitfaden

Dieser Leitfaden beschreibt die umfassenden Sicherheits- und Lasttests für die Django E-Commerce-Anwendung.

## Übersicht

Die Teststruktur ist in zwei Hauptkategorien unterteilt:

1. **Sicherheitstests** - Schutz vor Bedrohungen und Vulnerabilities
2. **Lasttests** - Performance und Skalierbarkeit unter Last

## Sicherheitstests

### 🔒 Test-Kategorien

#### 1. Authentifizierung und Autorisierung
```bash
# Alle Authentifizierungstests ausführen
uv run pytest tests/security/test_authentication.py -v

# Spezifische Tests
uv run pytest tests/security/test_authentication.py::AuthenticationSecurityTests::test_unauthenticated_access_to_protected_endpoints -v
```

**Getestete Bereiche:**
- Endpunkt-Zugriffskontrolle
- Benutzer-Datenisolation  
- Session-Management
- Passwort-Sicherheitsanforderungen
- Brute-Force-SchutDabei ist es wichtig, mögliche Herausforderungen nicht außer Acht zu lassen. So müssen etwa bestehende Prozesse und Strukturen angepasst werden, um die neuen Möglichkeiten effektiv zu nutzen. Auch der Schulungsbedarf der Mitarbeitenden und der zusätzliche Wartungsaufwand für die Testskripte sollten berücksichtigt werden.

z

#### 2. Input-Validierung und Datensanitization
```bash
# Alle Input-Validierungstests ausführen
uv run pytest tests/security/test_input_validation.py -v

# Spezifische Kategorien
uv run pytest tests/security/test_input_validation.py::InputValidationSecurityTests -v
uv run pytest tests/security/test_input_validation.py::DataSanitizationTests -v
```

**Getestete Bereiche:**
- JSON-Eingabevalidierung
- SQL-Injection-Schutzp
- XSS-Schutz (Cross-Site Scripting)
- CSRF-Schutz (Cross-Site Request Forgery)
- Unicode und Encoding-Handling

### 🛡️ OWASP Top 10 Compliance

Die Tests decken alle OWASP Top 10 Sicherheitsrisiken ab:

| OWASP | Risiko | Tests |
|-------|--------|-------|
| A01 | Broken Access Control | ✅ Autorisierungstests |
| A02 | Cryptographic Failures | ✅ Krypto-Einstellungen |
| A03 | Injection | ✅ SQL-Injection-Schutz |
| A04 | Insecure Design | ✅ Design-Sicherheit |
| A05 | Security Misconfiguration | ✅ Django-Einstellungen |
| A06 | Vulnerable Components | ✅ Dependency-Scanning |
| A07 | Authentication Failures | ✅ Auth-Tests |
| A08 | Software Integrity | ✅ Integritätsprüfungen |
| A09 | Logging Failures | ✅ Logging-Sicherheit |
| A10 | SSRF | ✅ SSRF-Schutz |

### 🚀 Sicherheitstests ausführen

```bash
# Automatisiertes Sicherheitstest-Skript
./scripts/run_security_tests.sh

# Mit Penetrationstests
./scripts/run_security_tests.sh --penetration

# Nur OWASP-Checks
./scripts/run_security_tests.sh --owasp-only
```

## Lasttests

### ⚡ Test-Kategorien

#### 1. Datenbank-Performance
```bash
# Datenbank-Performance-Tests
uv run pytest tests/load/test_performance.py::DatabasePerformanceTests -v -s
```

**Getestete Bereiche:**
- Produktkatalog-Query-Performance
- Gleichzeitige Bestellerstellung
- Datenbankverbindungspool
- Große Datensätze

#### 2. Cache-Performance (Redis)
```bash
# Cache-Performance-Tests  
uv run pytest tests/load/test_performance.py::CachePerformanceTests -v -s
```

**Getestete Bereiche:**
- Cache-Schreibperformance
- Cache-Leseperformance
- Bestellcaching unter Last
- Memory-Usage-Pattern

#### 3. API-Load-Tests
```bash
# API-Load-Tests
uv run pytest tests/load/test_performance.py::APILoadTests -v -s
```

**Getestete Bereiche:**
- API-Durchsatz
- Langzeit-Lasttests  
- Memory-Leak-Erkennung

#### 4. Realistische E-Commerce-Szenarien
```bash
# E-Commerce-Szenarien
uv run pytest tests/load/test_load_scenarios.py::EcommerceLoadScenarios -v -s
```

**Szenarien:**
- 🛍️ Black Friday Traffic-Surge
- 👥 Normales Browsing-Verhalten
- 📱 Mobile App API-Usage
- 📦 Inventory-Depletion-Tests
- 🔥 Cache-Warming

### 📊 Performance-Ziele

| Metrik | Zielwert | Test |
|--------|----------|------|
| Produktkatalog Response Time | < 500ms | `test_product_list_query_performance` |
| API Response Time | < 1.5s | `test_api_throughput` |
| Bestellerstellung | < 2.0s | `test_concurrent_order_creation` |
| Cache-Zugriff | < 50ms | `test_cache_read_performance` |
| API-Durchsatz | > 10 req/s | `test_api_throughput` |
| Success Rate | > 95% | Alle Load Tests |

### 🚀 Lasttests ausführen

```bash
# Automatisiertes Lasttest-Skript
./scripts/run_load_tests.sh

# Spezifische Test-Typen
./scripts/run_load_tests.sh --type database
./scripts/run_load_tests.sh --type cache  
./scripts/run_load_tests.sh --type api
./scripts/run_load_tests.sh --type scenarios

# Mit externen Tools (Artillery, Locust)
./scripts/run_load_tests.sh --external

# Mit System-Monitoring
./scripts/run_load_tests.sh --monitor
```

## Test-Umgebung Setup

### Voraussetzungen

```bash
# Python-Umgebung
uv sync

# Docker für Datenbank und Cache
docker-compose -f docker-compose.test.yml up -d

# Optionale externe Tools
npm install -g artillery    # für Artillery.js Load Tests  
pip install locust          # für Locust Load Tests
pip install safety          # für Security Vulnerability Scanning
```

### Konfiguration

#### Test-Einstellungen
```python
# devops_pipeline/settings/test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'devops_test',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6380/0',
    }
}
```

#### Docker Test Services
```yaml
# docker-compose.test.yml  
services:
  postgres_test:
    image: postgres:16
    ports: ["5433:5432"]
    
  redis_test:
    image: redis:7
    ports: ["6380:6379"]
```

## Kontinuierliche Tests

### CI/CD Integration

```yaml
# .github/workflows/security-tests.yml
name: Security Tests
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Security Tests
        run: ./scripts/run_security_tests.sh
```

```yaml
# .github/workflows/load-tests.yml  
name: Load Tests
on: [push]
jobs:
  load:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4  
      - name: Run Load Tests
        run: ./scripts/run_load_tests.sh --type api
```

### Jenkins Pipeline

```groovy
// Jenkinsfile - Security & Load Tests
pipeline {
    agent any
    stages {
        stage('Security Tests') {
            steps {
                sh './scripts/run_security_tests.sh'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'security_reports',
                    reportFiles: '*.html',
                    reportName: 'Security Test Report'
                ])
            }
        }
        stage('Load Tests') {
            steps {
                sh './scripts/run_load_tests.sh --type scenarios'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true, 
                    keepAll: true,
                    reportDir: 'load_reports',
                    reportFiles: '*.html',
                    reportName: 'Load Test Report'
                ])
            }
        }
    }
}
```

## Monitoring und Alerting

### Metriken sammeln

```bash
# System-Performance während Load Tests
./scripts/run_load_tests.sh --monitor

# Generierte Metriken ansehen
cat load_test_metrics.csv
```

### Prometheus Integration

```python
# Beispiel: Django Prometheus Metriken
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@REQUEST_LATENCY.time()
def create_order(request):
    REQUEST_COUNT.inc()
    # ... view logic
```

## Berichterstattung

### Automatische Reports

Die Test-Skripte generieren automatisch detaillierte Berichte:

- **Sicherheitsbericht:** `security_report_YYYYMMDD_HHMMSS.md`
- **Lasttest-Bericht:** `load_test_report_YYYYMMDD_HHMMSS.md`

### Report-Inhalte

#### Sicherheitsbericht
- Durchgeführte Tests und Ergebnisse
- OWASP Top 10 Compliance
- Gefundene Vulnerabilities
- Empfohlene Sicherheitsverbesserungen
- Konfigurationsempfehlungen

#### Lasttest-Bericht  
- Performance-Metriken
- Durchsatz-Statistiken
- Response-Time-Analysen
- System-Resource-Usage
- Bottleneck-Identifikation
- Skalierungsempfehlungen

## Best Practices

### Sicherheitstests

1. **Regelmäßige Ausführung:** Mindestens bei jedem Release
2. **Vollständige Abdeckung:** Alle OWASP Top 10 Kategorien testen
3. **Penetrationstests:** Regelmäßige externe Security Audits
4. **Dependency Scanning:** Kontinuierliche Überwachung von Vulnerabilities

### Lasttests

1. **Realistische Szenarien:** Tests basierend auf echten Nutzungsmustern
2. **Graduelle Steigerung:** Stufenweise Lasterhöhung
3. **Baseline etablieren:** Performance-Metriken vor Änderungen dokumentieren
4. **Monitoring:** Kontinuierliche Überwachung in Produktion

### Testdaten

```python
# Beispiel: Realistische Testdaten generieren
def create_test_data():
    """Erstelle realistische Testdaten für Load Tests."""
    
    # 1000 Benutzer
    users = [
        User.objects.create_user(
            username=f"user{i:04d}",
            email=f"user{i:04d}@example.com",
            password="test_password123"
        ) for i in range(1000)
    ]
    
    # 500 Produkte in verschiedenen Kategorien
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
    products = []
    for i in range(500):
        category = random.choice(categories)
        product = Product.objects.create(
            sku=f"{category[:3].upper()}-{i:04d}",
            name=f"{category} Product {i}",
            price=Decimal(f"{random.uniform(10, 500):.2f}"),
            stock=random.randint(1, 100)
        )
        products.append(product)
    
    return users, products
```

## Troubleshooting

### Häufige Probleme

#### Sicherheitstests
- **CSRF-Token-Fehler:** Stellen Sie sicher, dass Tests korrekte CSRF-Tokens verwenden
- **Authentication-Fehler:** Überprüfen Sie Test-User-Credentials
- **Database-Isolation:** Verwenden Sie TransactionTestCase für DB-Tests

#### Lasttests  
- **Timeout-Fehler:** Erhöhen Sie Timeout-Werte für Stress-Tests
- **Memory-Issues:** Monitoren Sie RAM-Usage während Tests
- **Database-Connections:** Konfigurieren Sie Connection-Pooling korrekt

#### Performance-Probleme
```python
# Django Debug Toolbar für Performance-Analyse
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Query-Optimierung
from django.db import connection
print(connection.queries)  # Alle SQL-Queries anzeigen
```

### Debugging

```bash
# Verbose Test Output
uv run pytest tests/security/ -v -s --tb=long

# Einzelnen Test debuggen
uv run pytest tests/load/test_performance.py::DatabasePerformanceTests::test_concurrent_order_creation -v -s --pdb

# Coverage Report
uv run pytest tests/security/ --cov=devops_pipeline --cov-report=html
```

## Fazit

Diese umfassende Test-Suite stellt sicher, dass die Django E-Commerce-Anwendung sowohl sicher als auch performant ist. Durch regelmäßige Ausführung dieser Tests können Sicherheitslücken frühzeitig erkannt und Performance-Probleme proaktiv angegangen werden.

Für weitere Informationen oder spezifische Testanforderungen, konsultieren Sie die Inline-Dokumentation in den Testdateien oder kontaktieren Sie das DevOps-Team. 