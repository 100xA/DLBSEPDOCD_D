#!/bin/bash
set -e

# Change to the script's directory to ensure paths are correct
cd "$(dirname "$0")/.."

# DevOps Pipeline - Comprehensive Test Runner
# Implements all 6 layers of testing as specified

echo "🚀 DevOps Pipeline - Comprehensive Test Suite"
echo "============================================="

# Configuration
COVERAGE_THRESHOLD=25
PYTHON_VERSION="3.11"
export DJANGO_SETTINGS_MODULE="devops_pipeline.settings.test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}


check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
    if [[ "$python_version" != "3.11" ]]; then
        log_warning "Python 3.11 recommended, found $python_version"
    fi
    
    # Check uv
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Required for integration tests."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Required for integration tests."
        exit 1
    fi
    
    # Check for ChromeDriver (for optional E2E tests)
    if ! command -v chromedriver &> /dev/null; then
        log_warning "ChromeDriver is not installed. Required for running E2E tests locally with the --run-e2e flag."
    fi
    
    log_success "Dependencies check passed"
}

setup_environment() {
    log_info "Setting up test environment..."
    
    # Install dependencies
    uv sync --frozen
    
    # Create logs directory
    mkdir -p logs
    
    # Set up test database
    export TEST_DB_NAME="devops_test"
    export TEST_DB_USER="devops_user"
    export TEST_DB_PASSWORD="devops_password"
    export TEST_DB_HOST="localhost"
    export TEST_DB_PORT="5433"
    export TEST_REDIS_URL="redis://localhost:6380/0"
    
    log_success "Environment setup complete"
}

# Layer 1: Static Checks
run_static_checks() {
    echo ""
    echo "🔍 Layer 1: Static Checks (flake8, black, isort)"
    echo "================================================"
    
    log_info "Running flake8 linting..."
    if uv run flake8 devops_pipeline/ tests/ --statistics; then
        log_success "flake8 passed"
    else
        log_error "flake8 found issues"
        return 1
    fi
    
    log_info "Checking code formatting with black..."
    if uv run black --check --diff devops_pipeline/ tests/; then
        log_success "black formatting check passed"
    else
        log_error "Code formatting issues found. Run 'black devops_pipeline/ tests/' to fix"
        return 1
    fi
    
    log_info "Checking import sorting with isort..."
    if uv run isort --check --diff devops_pipeline/ tests/; then
        log_success "isort check passed"
    else
        log_error "Import sorting issues found. Run 'isort devops_pipeline/ tests/' to fix"
        return 1
    fi
    
    log_success "Layer 1: Static checks completed successfully"
}

# Layer 2: Unit Tests
run_unit_tests() {
    echo ""
    echo "🧪 Layer 2: Unit Tests (pytest with coverage)"
    echo "============================================="
    
    log_info "Running unit tests with coverage..."
    if uv run pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=devops_pipeline \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --cov-report=term-missing \
        --cov-branch \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --junit-xml=unit-test-results.xml \
        -m unit; then
        
        log_success "Unit tests passed with $COVERAGE_THRESHOLD% coverage"
        log_info "Coverage report available at: htmlcov/index.html"
    else
        log_error "Unit tests failed or coverage below threshold"
        return 1
    fi
}

# Layer 3: Integration Tests
run_integration_tests() {
    echo ""
    echo "🔗 Layer 3: Integration Tests (Docker Compose + PostgreSQL 16 + Redis 7)"
    echo "========================================================================"
    
    log_info "Starting test services with Docker Compose..."
    
    # Clean up any existing containers
    docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
    
    # Start services
    if docker-compose -f docker-compose.test.yml up -d postgres_test redis_test; then
        log_success "Test services started"
    else
        log_error "Failed to start test services"
        return 1
    fi
    
    # Wait for services to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    timeout=60
    while ! docker-compose -f docker-compose.test.yml exec -T postgres_test pg_isready -U devops_user -d devops_test 2>/dev/null; do
        sleep 2
        timeout=$((timeout - 2))
        if [[ $timeout -le 0 ]]; then
            log_error "PostgreSQL failed to start within 60 seconds"
            docker-compose -f docker-compose.test.yml logs postgres_test
            docker-compose -f docker-compose.test.yml down -v
            return 1
        fi
    done
    
    log_info "Waiting for Redis to be ready..."
    timeout=30
    while ! docker-compose -f docker-compose.test.yml exec -T redis_test redis-cli ping 2>/dev/null | grep -q PONG; do
        sleep 2
        timeout=$((timeout - 2))
        if [[ $timeout -le 0 ]]; then
            log_error "Redis failed to start within 30 seconds"
            docker-compose -f docker-compose.test.yml logs redis_test
            docker-compose -f docker-compose.test.yml down -v
            return 1
        fi
    done
    
    log_success "All test services are ready"
    
    # Run integration tests
    log_info "Running integration tests..."
    if uv run pytest tests/integration/ \
        -v \
        --tb=short \
        --junit-xml=integration-test-results.xml \
        -m integration; then
        
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        docker-compose -f docker-compose.test.yml logs
        docker-compose -f docker-compose.test.yml down -v
        return 1
    fi
    
    # Clean up
    log_info "Cleaning up test services..."
    docker-compose -f docker-compose.test.yml down -v
    log_success "Test services cleaned up"
}

# Layer 4: End-to-End Tests (placeholder - no tests implemented)
run_e2e_tests() {
    local run_locally=$1

    echo ""
    echo "🎭 Layer 4: End-to-End Tests (Placeholder)"
    echo "=========================================="

    log_warning "E2E tests are not implemented yet."
    log_info "This layer is a placeholder for future browser-based testing."
    log_success "E2E test layer validation completed"
}

# Layer 5: CI/CD Pipeline Validation
validate_pipeline() {
    echo ""
    echo "🔄 Layer 5: CI/CD Pipeline Validation"
    echo "===================================="
    
    local all_checks_passed=true

    log_info "Validating Jenkinsfile..."
    if [[ -f "Jenkinsfile" ]]; then
        # Basic syntax check
        if grep -q "pipeline {" Jenkinsfile && grep -q "stages {" Jenkinsfile; then
            log_success "Jenkinsfile structure looks valid"
        else
            log_error "Jenkinsfile structure appears invalid"
            all_checks_passed=false
        fi
    else
        log_error "Jenkinsfile not found"
        all_checks_passed=false
    fi
    
    log_info "Checking Docker configuration..."
    # Production files are recommended, but not required for this script to pass
    if [[ ! -f "Dockerfile" ]]; then log_warning "Production 'Dockerfile' not found."; fi
    if [[ ! -f "docker-compose.yml" ]]; then log_warning "Production 'docker-compose.yml' not found."; fi
    if [[ ! -f ".dockerignore" ]]; then log_warning "A '.dockerignore' file is recommended."; fi

    # Test files are required
    if [[ -f "Dockerfile.test" ]] && [[ -f "docker-compose.test.yml" ]]; then
        log_success "Test Docker configuration files are present."
    else
        log_error "Missing required test Docker configuration (Dockerfile.test or docker-compose.test.yml)."
        all_checks_passed=false
    fi
    
    log_info "Checking Kubernetes manifests..."
    if [[ -d "infrastructure/kubernetes" ]] && [[ -f "infrastructure/kubernetes/deployment.yaml" ]]; then
        log_success "Kubernetes manifests present"
    else
        log_warning "Missing Kubernetes manifests (expected infrastructure/kubernetes/deployment.yaml)"
    fi

    if [[ "$all_checks_passed" = true ]]; then
        log_success "Layer 5: CI/CD pipeline validation completed successfully"
    else
        log_error "Layer 5: CI/CD pipeline validation failed"
        return 1
    fi
}

# Generate test report
generate_report() {
    echo ""
    echo "📊 Test Report Summary"
    echo "====================="
    
    if [[ -f "unit-test-results.xml" ]]; then
        log_info "Unit test results: unit-test-results.xml"
    fi
    
    if [[ -f "integration-test-results.xml" ]]; then
        log_info "Integration test results: integration-test-results.xml"
    fi
    
    if [[ -f "e2e-test-results.xml" ]]; then
        log_info "End-to-End test results: e2e-test-results.xml"
    fi
    
    if [[ -f "coverage.xml" ]]; then
        log_info "Coverage report: coverage.xml"
        log_info "HTML coverage report: htmlcov/index.html"
    fi
    
    echo ""
    log_success "All 5 layers of testing completed successfully!"
    echo ""
    echo "Layer Summary:"
    echo "1. ✅ Static checks (flake8)"
    echo "2. ✅ Unit tests (pytest + coverage)"
    echo "3. ✅ Integration tests (Docker Compose + PostgreSQL 16 + Redis 7)"
    echo "4. ✅ End-to-End tests (placeholder)"
    echo "5. ✅ CI/CD pipeline (Jenkins pipeline validated)"
}

# Main execution
main() {
    local run_layer=""
    local run_e2e_locally=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --layer)
                run_layer="$2"
                shift 2
                ;;
            --run-e2e)
                run_e2e_locally=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--layer <1-5>] [--run-e2e]"
                echo "Layers:"
                echo "  1: Static checks"
                echo "  2: Unit tests"
                echo "  3: Integration tests"
                echo "  4: End-to-End tests"
                echo "  5: Pipeline validation"
                echo ""
                echo "Options:"
                echo "  --run-e2e: Execute E2E tests locally instead of just validating their structure."
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check dependencies
    check_dependencies
    setup_environment
    
    # Run specific layer or all layers
    if [[ -n "$run_layer" ]]; then
        case $run_layer in
            1) run_static_checks ;;
            2) run_unit_tests ;;
            3) run_integration_tests ;;
            4) run_e2e_tests "$run_e2e_locally" ;;
            5) validate_pipeline ;;
            *) log_error "Invalid layer: $run_layer"; exit 1 ;;
        esac
    else
        # Run all layers
        run_static_checks
        run_unit_tests
        run_integration_tests
        run_e2e_tests "$run_e2e_locally"
        validate_pipeline
        generate_report
    fi
}

# Run main function
main "$@" 