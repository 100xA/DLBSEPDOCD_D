# DevOps Pipeline

A Django e-commerce application with a comprehensive 4-layer testing pipeline.

## Features

- **Django E-commerce App**: Product catalog and order management system
- **4-Layer Testing Pipeline**:
  1. **Static Analysis**: Code quality checks (flake8, black, isort)
  2. **Unit Tests**: Fast isolated testing with coverage reporting
  3. **Integration Tests**: Database and cache testing with Docker
  4. **Pipeline Validation**: CI/CD configuration verification
- **CI/CD**: GitHub Actions and Jenkins pipeline support
- **Docker Support**: Containerized testing environment

## Quick Start

### Prerequisites
- Python 3.11+
- uv package manager
- Docker & Docker Compose

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd devops-pipeline

# Install dependencies
uv sync

# Run all tests
./scripts/run_tests.sh
```

### Running Specific Test Layers
```bash
./scripts/run_tests.sh --layer 1  # Static checks
./scripts/run_tests.sh --layer 2  # Unit tests
./scripts/run_tests.sh --layer 3  # Integration tests
./scripts/run_tests.sh --layer 5  # Pipeline validation
```

## Project Structure

- `devops_pipeline/apps/` - Django applications (catalog, orders)
- `tests/` - Test suites (unit, integration)
- `scripts/run_tests.sh` - Main test runner
- `docker-compose.test.yml` - Test environment services
- `Jenkinsfile` - CI/CD pipeline definition
- `.github/workflows/` - GitHub Actions workflows

## CI/CD

### GitHub Actions
- **Main CI**: Runs on push to main/develop
- **PR Checks**: Quick validation on pull requests  
- **Release**: Production deployment on version tags

### Jenkins Pipeline
- 5-stage pipeline with quality gates
- Docker image building and deployment
- Kubernetes manifest validation

## Development

```bash
# Run Django server
python manage.py runserver

# Run specific tests
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# Code formatting
uv run black devops_pipeline/ tests/
uv run isort devops_pipeline/ tests/
```

## Apps

### Catalog App
- Product management with SKU, pricing, and inventory
- RESTful API endpoints

### Orders App  
- Order creation and management
- Redis caching for performance

## License

MIT License - see LICENSE file for details. 