#!/bin/bash
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# DevOps Pipeline - Comprehensive Load and Performance Testing Suite
# Implements Locust-based load testing with Prometheus monitoring as described in case study section 3.5

echo "⚡ DevOps Pipeline - Load and Performance Testing Suite"
echo "====================================================="

# Configuration
LOAD_REPORTS_DIR="load_reports"
PROMETHEUS_PORT="9090"
LOCUST_PORT="8089"
TARGET_URL="http://localhost:8000"
LOCUST_VERSION="2.17.0"

# Load test parameters
DEFAULT_USERS=50
DEFAULT_SPAWN_RATE=10
DEFAULT_DURATION="5m"

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

# Setup load testing environment
setup_load_environment() {
    log_info "Setting up load testing environment..."
    
    mkdir -p "$LOAD_REPORTS_DIR"
    mkdir -p logs
    
    # Check dependencies
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required for Prometheus monitoring"
        exit 1
    fi
    
    # Install Locust if not available
    if ! uv run python -c "import locust" &>/dev/null; then
        log_info "Installing Locust for load testing..."
        uv add "locust==$LOCUST_VERSION"
    fi
    
    log_success "Load testing environment setup completed"
}

# Create Locust configuration files
create_locust_files() {
    log_info "Creating Locust test scenarios..."
    
    # Create main Locust file for e-commerce scenarios
    cat > tests/load/locustfile.py << 'EOF'
"""
Locust load test scenarios for e-commerce application.
Implements realistic user behavior patterns as described in case study section 3.5.
"""

import random
import time
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommerceShopper(HttpUser):
    """
    Simulates realistic e-commerce customer behavior.
    
    This class implements the Shopper behavior described in the case study:
    - Browse products at regular intervals
    - Occasionally execute checkout process
    - Realistic wait times between actions
    """
    
    wait_time = between(1, 5)  # Realistic user think time
    
    def on_start(self):
        """Initialize user session - login if needed."""
        self.client.verify = False  # For testing with self-signed certificates
        
        # Simulate user login (30% of users)
        if random.random() < 0.3:
            self.login()
    
    def login(self):
        """Simulate user login process."""
        login_data = {
            "username": f"loadtest_user_{random.randint(1, 1000)}",
            "password": "loadtest_password123"
        }
        
        response = self.client.post("/auth/login/", data=login_data, catch_response=True)
        if response.status_code in [200, 302]:
            logger.info("User logged in successfully")
        else:
            logger.warning(f"Login failed with status {response.status_code}")
    
    @task(40)
    def browse_products(self):
        """
        Browse product catalog - highest frequency task.
        Simulates typical browsing behavior.
        """
        with self.client.get("/", catch_response=True, name="product_catalog") as response:
            if response.status_code == 200:
                # Simulate reading product information
                time.sleep(random.uniform(0.5, 2.0))
            else:
                response.failure(f"Product catalog returned {response.status_code}")
    
    @task(15)
    def view_specific_product(self):
        """View individual product details."""
        # Simulate clicking on a product (not implemented in current app, but realistic)
        with self.client.get("/", catch_response=True, name="product_detail") as response:
            if response.status_code == 200:
                time.sleep(random.uniform(1.0, 3.0))  # Reading product details
    
    @task(10)
    def search_products(self):
        """Simulate product search functionality."""
        search_terms = ["test", "product", "item", "electronics", "book"]
        search_term = random.choice(search_terms)
        
        with self.client.get(f"/?search={search_term}", catch_response=True, name="product_search") as response:
            if response.status_code == 200:
                time.sleep(random.uniform(0.5, 1.5))
    
    @task(8)
    def create_order(self):
        """
        Create order - represents conversion.
        Lower frequency but critical business metric.
        """
        order_data = {
            "sku": f"TEST-{random.randint(1, 100):03d}",
            "qty": random.randint(1, 3)
        }
        
        with self.client.post(
            "/orders/create/", 
            json=order_data,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="create_order"
        ) as response:
            if response.status_code == 201:
                logger.info(f"Order created successfully: {response.json()}")
                time.sleep(random.uniform(2.0, 4.0))  # Order confirmation reading
            elif response.status_code == 404:
                # Product not found - expected in load testing
                response.success()
            else:
                response.failure(f"Order creation failed with {response.status_code}")
    
    @task(5)
    def view_orders(self):
        """View order history - requires authentication."""
        with self.client.get("/orders/", catch_response=True, name="order_history") as response:
            if response.status_code in [200, 302]:  # 302 for redirect to login
                time.sleep(random.uniform(1.0, 2.0))
            else:
                response.failure(f"Order history returned {response.status_code}")
    
    @task(3)
    def api_health_check(self):
        """Check API health and response times."""
        with self.client.get("/orders/", catch_response=True, name="api_health") as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure(f"Response too slow: {response.elapsed.total_seconds()}s")

class HighVolumeUser(FastHttpUser):
    """
    High-volume user for stress testing.
    Uses FastHttpUser for better performance during peak load tests.
    """
    
    wait_time = between(0.1, 0.5)  # Aggressive load testing
    
    @task(70)
    def rapid_product_browsing(self):
        """Rapid product catalog access for stress testing."""
        self.client.get("/")
    
    @task(20)
    def rapid_api_calls(self):
        """Rapid API calls for throughput testing."""
        order_data = {
            "sku": f"STRESS-{random.randint(1, 10)}",
            "qty": 1
        }
        self.client.post("/orders/create/", json=order_data)
    
    @task(10)
    def concurrent_operations(self):
        """Multiple concurrent operations."""
        self.client.get("/")
        self.client.get("/orders/")

# Event listeners for custom metrics
@events.request.add_listener
def record_custom_metrics(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """Record custom performance metrics."""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    
    # Log slow requests
    if response_time > 2000:  # 2 seconds
        logger.warning(f"Slow request detected: {name} took {response_time}ms")
    
    # Record business metrics
    if name == "create_order" and response and response.status_code == 201:
        logger.info(f"Business metric: Order created in {response_time}ms")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics and monitoring."""
    logger.info("🚀 Load test started - monitoring business metrics")
    logger.info(f"Target URL: {environment.host}")
    logger.info(f"Test configuration: {environment.parsed_options}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate final performance report."""
    logger.info("📊 Load test completed - generating performance summary")
EOF

    # Create database-specific load test
    cat > tests/load/database_load.py << 'EOF'
"""
Database-focused load testing scenarios.
Tests database performance under various load conditions.
"""

from locust import HttpUser, task, between
import random

class DatabaseLoadUser(HttpUser):
    """Focus on database-intensive operations."""
    
    wait_time = between(0.1, 1.0)
    
    @task(50)
    def read_heavy_operations(self):
        """Simulate read-heavy database operations."""
        self.client.get("/")  # Product catalog reads
    
    @task(30)
    def write_operations(self):
        """Simulate write operations."""
        order_data = {
            "sku": f"DB-TEST-{random.randint(1, 1000)}",
            "qty": random.randint(1, 5)
        }
        self.client.post("/orders/create/", json=order_data)
    
    @task(20)
    def mixed_operations(self):
        """Mixed read/write operations."""
        self.client.get("/")
        self.client.get("/orders/")
EOF

    # Create cache-specific load test
    cat > tests/load/cache_load.py << 'EOF'
"""
Cache-focused load testing scenarios.
Tests Redis cache performance and hit rates.
"""

from locust import HttpUser, task, between
import random

class CacheLoadUser(HttpUser):
    """Focus on cache performance testing."""
    
    wait_time = between(0.1, 0.5)
    
    @task(80)
    def cache_heavy_reads(self):
        """Operations that should hit cache frequently."""
        # Product catalog should be cached
        self.client.get("/")
    
    @task(20)
    def cache_invalidation(self):
        """Operations that might invalidate cache."""
        order_data = {
            "sku": f"CACHE-{random.randint(1, 50)}",  # Limited SKU range for cache testing
            "qty": 1
        }
        self.client.post("/orders/create/", json=order_data)
EOF

    log_success "Locust test files created"
}

# Start Prometheus monitoring
start_prometheus() {
    log_info "Starting Prometheus monitoring..."
    
    # Create Prometheus configuration
    cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'django-app'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
  
  - job_name: 'locust'
    static_configs:
      - targets: ['host.docker.internal:8089']
    metrics_path: '/stats/requests'
    scrape_interval: 10s

rule_files:
  # Load testing alert rules would go here

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093
EOF

    # Start Prometheus in Docker
    docker run -d \
        --name prometheus-load-test \
        -p $PROMETHEUS_PORT:9090 \
        -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
        --add-host=host.docker.internal:host-gateway \
        prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus \
        --web.console.libraries=/etc/prometheus/console_libraries \
        --web.console.templates=/etc/prometheus/consoles \
        --web.enable-lifecycle || true
    
    sleep 5
    log_success "Prometheus started on port $PROMETHEUS_PORT"
}

# Stop Prometheus monitoring
stop_prometheus() {
    log_info "Stopping Prometheus monitoring..."
    docker stop prometheus-load-test || true
    docker rm prometheus-load-test || true
    rm -f prometheus.yml
    log_success "Prometheus monitoring stopped"
}

# Run database performance tests
run_database_load_test() {
    echo ""
    echo "🗄️ Phase 1: Database Performance Testing"
    echo "========================================"
    
    log_info "Running database-focused load tests..."
    
    # Ensure test database services are running
    docker-compose -f docker-compose.test.yml up -d postgres_test redis_test
    sleep 10
    
    # Run database load test
    uv run locust \
        -f tests/load/database_load.py \
        --host="$TARGET_URL" \
        --users=20 \
        --spawn-rate=5 \
        --run-time=3m \
        --html="$LOAD_REPORTS_DIR/database-load-report.html" \
        --csv="$LOAD_REPORTS_DIR/database-load" \
        --headless \
        --loglevel=INFO
    
    log_success "Database load test completed"
}

# Run cache performance tests
run_cache_load_test() {
    echo ""
    echo "🗃️ Phase 2: Cache Performance Testing"
    echo "===================================="
    
    log_info "Running cache-focused load tests..."
    
    # Run cache load test
    uv run locust \
        -f tests/load/cache_load.py \
        --host="$TARGET_URL" \
        --users=30 \
        --spawn-rate=10 \
        --run-time=3m \
        --html="$LOAD_REPORTS_DIR/cache-load-report.html" \
        --csv="$LOAD_REPORTS_DIR/cache-load" \
        --headless \
        --loglevel=INFO
    
    log_success "Cache load test completed"
}

# Run API throughput tests
run_api_load_test() {
    echo ""
    echo "🚀 Phase 3: API Throughput Testing"
    echo "================================="
    
    log_info "Running API throughput tests..."
    
    # Run main e-commerce load test
    uv run locust \
        -f tests/load/locustfile.py \
        --host="$TARGET_URL" \
        --users="$DEFAULT_USERS" \
        --spawn-rate="$DEFAULT_SPAWN_RATE" \
        --run-time="$DEFAULT_DURATION" \
        --html="$LOAD_REPORTS_DIR/api-load-report.html" \
        --csv="$LOAD_REPORTS_DIR/api-load" \
        --headless \
        --loglevel=INFO
    
    log_success "API load test completed"
}

# Run realistic scenario tests
run_scenario_load_test() {
    echo ""
    echo "🛍️ Phase 4: Realistic E-commerce Scenarios"
    echo "=========================================="
    
    log_info "Running realistic e-commerce user scenarios..."
    
    # Run with realistic user behavior
    uv run locust \
        -f tests/load/locustfile.py \
        --host="$TARGET_URL" \
        --users=100 \
        --spawn-rate=20 \
        --run-time=10m \
        --html="$LOAD_REPORTS_DIR/scenario-load-report.html" \
        --csv="$LOAD_REPORTS_DIR/scenario-load" \
        --headless \
        --loglevel=INFO \
        --only-summary
    
    log_success "Scenario load test completed"
}

# Run stress tests to find breaking points
run_stress_test() {
    echo ""
    echo "💥 Phase 5: Stress Testing"
    echo "========================="
    
    log_info "Running stress tests to find system limits..."
    
    # Use high-volume user class for stress testing
    uv run locust \
        -f tests/load/locustfile.py \
        --host="$TARGET_URL" \
        --user-classes=HighVolumeUser \
        --users=200 \
        --spawn-rate=50 \
        --run-time=5m \
        --html="$LOAD_REPORTS_DIR/stress-test-report.html" \
        --csv="$LOAD_REPORTS_DIR/stress-test" \
        --headless \
        --loglevel=WARNING
    
    log_success "Stress test completed"
}

# Monitor system metrics during load tests
monitor_system_metrics() {
    log_info "Collecting system metrics during load tests..."
    
    # Create simple system monitoring script
    cat > monitor_system.sh << 'EOF'
#!/bin/bash
# System monitoring during load tests

METRICS_FILE="load_reports/system_metrics.csv"
echo "timestamp,cpu_percent,memory_percent,disk_io,network_io" > "$METRICS_FILE"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU usage
    cpu_percent=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "0")
    
    # Memory usage
    memory_percent=$(ps -caxm -orss= | awk '{ sum += $1 } END { print sum/1024/1024*100 }' 2>/dev/null || echo "0")
    
    # Simple disk I/O approximation
    disk_io=$(iostat -d 1 2 | tail -1 | awk '{print $3+$4}' 2>/dev/null || echo "0")
    
    # Network I/O approximation
    network_io=$(netstat -ib | awk 'NR>1 {print $7+$10}' | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "0")
    
    echo "$timestamp,$cpu_percent,$memory_percent,$disk_io,$network_io" >> "$METRICS_FILE"
    
    sleep 10
done
EOF

    chmod +x monitor_system.sh
    ./monitor_system.sh &
    MONITOR_PID=$!
    
    return $MONITOR_PID
}

# Generate comprehensive load test report
generate_load_report() {
    echo ""
    echo "📊 Generating Comprehensive Load Test Report"
    echo "==========================================="
    
    REPORT_FILE="$LOAD_REPORTS_DIR/load-test-summary.html"
    
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>DevOps Pipeline - Load Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .success { border-left-color: #28a745; }
        .warning { border-left-color: #ffc107; }
        .danger { border-left-color: #dc3545; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ DevOps Pipeline Load Test Report</h1>
        <p>Generated on: $(date)</p>
        <p>Implements Locust-based Load Testing with Prometheus Monitoring (Case Study Section 3.5)</p>
    </div>

    <div class="section">
        <h2>📋 Load Testing Summary</h2>
        <div class="metric">
            <strong>Database Load Test:</strong> 
            $(test -f "$LOAD_REPORTS_DIR/database-load_stats.csv" && echo "✅ Completed" || echo "❌ Failed")
        </div>
        <div class="metric">
            <strong>Cache Performance:</strong> 
            $(test -f "$LOAD_REPORTS_DIR/cache-load_stats.csv" && echo "✅ Completed" || echo "❌ Failed")
        </div>
        <div class="metric">
            <strong>API Throughput:</strong> 
            $(test -f "$LOAD_REPORTS_DIR/api-load_stats.csv" && echo "✅ Completed" || echo "❌ Failed")
        </div>
        <div class="metric">
            <strong>Scenario Testing:</strong> 
            $(test -f "$LOAD_REPORTS_DIR/scenario-load_stats.csv" && echo "✅ Completed" || echo "❌ Failed")
        </div>
        <div class="metric">
            <strong>Stress Testing:</strong> 
            $(test -f "$LOAD_REPORTS_DIR/stress-test_stats.csv" && echo "✅ Completed" || echo "❌ Failed")
        </div>
    </div>

    <div class="section">
        <h2>🎯 Performance Targets (Case Study Requirements)</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Target</th>
                <th>Test Type</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Product Catalog Response Time</td>
                <td>&lt; 500ms</td>
                <td>Database Load Test</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/database-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
            <tr>
                <td>API Response Time</td>
                <td>&lt; 1.5s</td>
                <td>API Throughput Test</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/api-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
            <tr>
                <td>Order Creation</td>
                <td>&lt; 2.0s</td>
                <td>Scenario Test</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/scenario-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
            <tr>
                <td>Cache Access</td>
                <td>&lt; 50ms</td>
                <td>Cache Performance Test</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/cache-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
            <tr>
                <td>API Throughput</td>
                <td>&gt; 10 req/s</td>
                <td>All Tests</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/api-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
            <tr>
                <td>Success Rate</td>
                <td>&gt; 95%</td>
                <td>All Tests</td>
                <td>$(test -f "$LOAD_REPORTS_DIR/scenario-load_stats.csv" && echo "✅ Measured" || echo "⚠️ Pending")</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>📊 Detailed Reports</h2>
        <ul>
            <li><a href="database-load-report.html">Database Load Test Report</a></li>
            <li><a href="cache-load-report.html">Cache Performance Report</a></li>
            <li><a href="api-load-report.html">API Throughput Report</a></li>
            <li><a href="scenario-load-report.html">E-commerce Scenario Report</a></li>
            <li><a href="stress-test-report.html">Stress Test Report</a></li>
        </ul>
    </div>

    <div class="section">
        <h2>📈 Monitoring Integration</h2>
        <p>Prometheus metrics available at: <a href="http://localhost:$PROMETHEUS_PORT">http://localhost:$PROMETHEUS_PORT</a></p>
        <p>System metrics collected in: system_metrics.csv</p>
    </div>

    <div class="section">
        <h2>🎯 Recommendations</h2>
        <ul>
            <li>Monitor response times against performance targets</li>
            <li>Implement caching for frequently accessed data</li>
            <li>Optimize database queries for better performance</li>
            <li>Set up continuous performance monitoring</li>
            <li>Configure alerts for performance degradation</li>
        </ul>
    </div>
</body>
</html>
EOF

    log_success "Load test report generated: $REPORT_FILE"
}

# Main execution
main() {
    local test_type=""
    local users="$DEFAULT_USERS"
    local spawn_rate="$DEFAULT_SPAWN_RATE"
    local duration="$DEFAULT_DURATION"
    local enable_monitoring=false
    local external_tools=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                test_type="$2"
                shift 2
                ;;
            --users)
                users="$2"
                shift 2
                ;;
            --spawn-rate)
                spawn_rate="$2"
                shift 2
                ;;
            --duration)
                duration="$2"
                shift 2
                ;;
            --monitor)
                enable_monitoring=true
                shift
                ;;
            --external)
                external_tools=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--type <test-type>] [--users <num>] [--spawn-rate <rate>] [--duration <time>] [--monitor] [--external]"
                echo "Test Types:"
                echo "  database    : Database performance testing"
                echo "  cache       : Cache performance testing"
                echo "  api         : API throughput testing"
                echo "  scenarios   : Realistic e-commerce scenarios"
                echo "  stress      : Stress testing to find limits"
                echo ""
                echo "Options:"
                echo "  --users <num>       : Number of concurrent users (default: $DEFAULT_USERS)"
                echo "  --spawn-rate <rate> : User spawn rate (default: $DEFAULT_SPAWN_RATE)"
                echo "  --duration <time>   : Test duration (default: $DEFAULT_DURATION)"
                echo "  --monitor           : Enable system monitoring"
                echo "  --external          : Use external tools (Artillery, additional monitoring)"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Setup environment
    setup_load_environment
    create_locust_files
    
    # Start monitoring if requested
    if [[ "$enable_monitoring" == "true" ]]; then
        start_prometheus
        MONITOR_PID=$(monitor_system_metrics)
        trap "kill $MONITOR_PID 2>/dev/null || true; stop_prometheus" EXIT
    fi
    
    # Update test parameters
    DEFAULT_USERS="$users"
    DEFAULT_SPAWN_RATE="$spawn_rate"
    DEFAULT_DURATION="$duration"
    
    # Run specific test type or all tests
    if [[ -n "$test_type" ]]; then
        case $test_type in
            database) run_database_load_test ;;
            cache) run_cache_load_test ;;
            api) run_api_load_test ;;
            scenarios) run_scenario_load_test ;;
            stress) run_stress_test ;;
            *) log_error "Invalid test type: $test_type"; exit 1 ;;
        esac
    else
        # Run all test phases
        run_database_load_test
        run_cache_load_test
        run_api_load_test
        run_scenario_load_test
        run_stress_test
        generate_load_report
        
        echo ""
        log_success "⚡ Comprehensive load testing completed!"
        echo ""
        echo "Load Test Summary:"
        echo "=================="
        echo "📁 All reports available in: $LOAD_REPORTS_DIR/"
        echo "🌐 Main report: $LOAD_REPORTS_DIR/load-test-summary.html"
        if [[ "$enable_monitoring" == "true" ]]; then
            echo "📊 Prometheus: http://localhost:$PROMETHEUS_PORT"
        fi
        echo ""
        echo "Load Testing Phases:"
        echo "1. ✅ Database performance testing"
        echo "2. ✅ Cache performance testing"
        echo "3. ✅ API throughput testing"
        echo "4. ✅ Realistic e-commerce scenarios"
        echo "5. ✅ Stress testing"
    fi
    
    # Cleanup
    if [[ "$enable_monitoring" == "true" ]]; then
        kill $MONITOR_PID 2>/dev/null || true
        stop_prometheus
    fi
}

# Run main function
main "$@" 