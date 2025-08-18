#!/bin/bash

# Performance testing script for Deep Tree Echo
# Tests various load scenarios and collects metrics

set -e

NGINX_URL="http://localhost"
RESULTS_DIR="./test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Starting Deep Tree Echo Performance Testing"
echo "Timestamp: $TIMESTAMP"

# Create results directory
mkdir -p "$RESULTS_DIR/$TIMESTAMP"

# Function to run test and collect metrics
run_test() {
    local test_name="$1"
    local config_file="$2"
    local duration="$3"
    
    echo "📊 Running test: $test_name"
    
    # Run Artillery test
    docker run --rm \
        --network deep-tree-echo-rkwv_deep-echo-network \
        -v "$(pwd)/infrastructure/testing:/scripts" \
        artilleryio/artillery:latest \
        run "/scripts/$config_file" \
        --output "/scripts/$RESULTS_DIR/$TIMESTAMP/${test_name}_results.json"
    
    # Generate HTML report
    docker run --rm \
        -v "$(pwd)/infrastructure/testing:/scripts" \
        artilleryio/artillery:latest \
        report "/scripts/$RESULTS_DIR/$TIMESTAMP/${test_name}_results.json" \
        --output "/scripts/$RESULTS_DIR/$TIMESTAMP/${test_name}_report.html"
    
    echo "✅ Test completed: $test_name"
}

# Function to collect system metrics during test
collect_metrics() {
    local test_name="$1"
    local duration="$2"
    
    echo "📈 Collecting system metrics for: $test_name"
    
    # Collect Docker stats
    timeout "$duration" docker stats \
        --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
        > "$RESULTS_DIR/$TIMESTAMP/${test_name}_docker_stats.log" &
    
    # Collect Prometheus metrics
    curl -s "http://localhost:9090/api/v1/query_range?query=up&start=$(date -d '5 minutes ago' +%s)&end=$(date +%s)&step=15" \
        > "$RESULTS_DIR/$TIMESTAMP/${test_name}_prometheus_metrics.json" || true
}

# Function to check service health before testing
check_services() {
    echo "🔍 Checking service health..."
    
    services=(
        "http://localhost/health:Main App"
        "http://localhost:8000/health:Load Balancer"
        "http://localhost:8002/health:Cache Service"
        "http://localhost:8001/health:Cognitive Service 1"
        "http://localhost:8003/health:Cognitive Service 2"
    )
    
    for service in "${services[@]}"; do
        url="${service%:*}"
        name="${service#*:}"
        
        if curl -s -f "$url" > /dev/null; then
            echo "✅ $name is healthy"
        else
            echo "❌ $name is not responding"
            exit 1
        fi
    done
}

# Function to warm up services
warmup_services() {
    echo "🔥 Warming up services..."
    
    # Create a session and make a few requests
    session_response=$(curl -s -X POST "$NGINX_URL/api/session" -H "Content-Type: application/json" -d '{}')
    session_id=$(echo "$session_response" | jq -r '.session_id')
    
    if [ "$session_id" != "null" ]; then
        echo "Created warmup session: $session_id"
        
        # Make some warmup requests
        for i in {1..5}; do
            curl -s -X POST "$NGINX_URL/api/process" \
                -H "Content-Type: application/json" \
                -d "{\"session_id\":\"$session_id\",\"input\":\"Warmup request $i\"}" > /dev/null
        done
        
        echo "Warmup completed"
    else
        echo "Failed to create warmup session"
    fi
}

# Main testing sequence
main() {
    # Pre-test checks
    check_services
    warmup_services
    
    echo "📋 Test Plan:"
    echo "1. Baseline Performance Test (5 minutes)"
    echo "2. Sustained Load Test (10 minutes)"
    echo "3. Peak Load Test (5 minutes)"
    echo "4. Cache Performance Test (3 minutes)"
    echo "5. Cognitive Processing Test (7 minutes)"
    
    # Test 1: Baseline Performance
    echo -e "\n🧪 Test 1: Baseline Performance"
    collect_metrics "baseline" "300" &
    metrics_pid=$!
    run_test "baseline" "baseline-test.yml" "300"
    kill $metrics_pid 2>/dev/null || true
    
    # Wait between tests
    echo "⏳ Cooling down for 30 seconds..."
    sleep 30
    
    # Test 2: Sustained Load
    echo -e "\n🧪 Test 2: Sustained Load"
    collect_metrics "sustained_load" "600" &
    metrics_pid=$!
    run_test "sustained_load" "load-test.yml" "600"
    kill $metrics_pid 2>/dev/null || true
    
    # Wait between tests
    echo "⏳ Cooling down for 30 seconds..."
    sleep 30
    
    # Test 3: Peak Load
    echo -e "\n🧪 Test 3: Peak Load"
    collect_metrics "peak_load" "300" &
    metrics_pid=$!
    run_test "peak_load" "peak-load-test.yml" "300"
    kill $metrics_pid 2>/dev/null || true
    
    # Test 4: Cache Performance
    echo -e "\n🧪 Test 4: Cache Performance"
    collect_metrics "cache_performance" "180" &
    metrics_pid=$!
    run_test "cache_performance" "cache-test.yml" "180"
    kill $metrics_pid 2>/dev/null || true
    
    # Test 5: Cognitive Processing
    echo -e "\n🧪 Test 5: Cognitive Processing"
    collect_metrics "cognitive_processing" "420" &
    metrics_pid=$!
    run_test "cognitive_processing" "cognitive-test.yml" "420"
    kill $metrics_pid 2>/dev/null || true
    
    # Generate summary report
    generate_summary_report
    
    echo -e "\n🎉 Performance testing completed!"
    echo "Results saved to: $RESULTS_DIR/$TIMESTAMP"
    echo "Open the HTML reports in a browser to view detailed results."
}

# Function to generate summary report
generate_summary_report() {
    echo "📊 Generating summary report..."
    
    summary_file="$RESULTS_DIR/$TIMESTAMP/summary_report.md"
    
    cat > "$summary_file" << EOF
# Deep Tree Echo Performance Test Summary

**Test Date:** $(date)
**Test Duration:** $(date -d @$(($(date +%s) - start_time)) -u +%H:%M:%S)

## Test Results

### Baseline Performance
- Configuration: Low load, baseline measurements
- Results: See baseline_report.html

### Sustained Load
- Configuration: Sustained load over 10 minutes
- Results: See sustained_load_report.html

### Peak Load  
- Configuration: High load burst testing
- Results: See peak_load_report.html

### Cache Performance
- Configuration: Cache-focused testing
- Results: See cache_performance_report.html

### Cognitive Processing
- Configuration: Cognitive service stress testing
- Results: See cognitive_processing_report.html

## System Metrics

Docker stats and Prometheus metrics are available in the corresponding log files.

## Key Performance Indicators

1. **Response Time**: Target < 100ms average
2. **Throughput**: Target > 1000 requests/minute
3. **Error Rate**: Target < 1%
4. **Cache Hit Rate**: Target > 50%
5. **Auto-scaling**: Verify scaling events

## Recommendations

Based on the test results, review the following:
- Response time trends under load
- Cache hit rates and effectiveness
- Auto-scaling behavior
- Resource utilization patterns
- Error rates and failure modes

EOF

    echo "Summary report generated: $summary_file"
}

# Record start time
start_time=$(date +%s)

# Run the tests
main "$@"