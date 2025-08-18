#!/bin/bash

# Deep Tree Echo Scalability Demo
# Demonstrates the distributed architecture and performance capabilities

echo "🎭 Deep Tree Echo - Scalability Architecture Demo"
echo "=================================================="
echo ""

# Check if services are running
check_services() {
    echo "🔍 Checking if services are running..."
    
    if ! docker-compose ps | grep -q "Up"; then
        echo "❌ Services are not running. Please start them first:"
        echo "   ./quick-start.sh start"
        exit 1
    fi
    
    echo "✅ Services are running"
    echo ""
}

# Function to demonstrate load balancer
demo_load_balancer() {
    echo "🔄 Load Balancer Demo"
    echo "--------------------"
    
    echo "Getting service registry information..."
    curl -s http://localhost:8000/api/services | jq '.services' || echo "Load balancer not accessible"
    echo ""
    
    echo "Load balancer health check..."
    curl -s http://localhost:8000/health | jq '.' || echo "Health check failed"
    echo ""
}

# Function to demonstrate caching
demo_caching() {
    echo "💾 Caching System Demo"
    echo "---------------------"
    
    echo "Setting cache value..."
    curl -s -X POST http://localhost:8002/api/cache/demo-key \
        -H "Content-Type: application/json" \
        -d '{"key":"demo-key","value":"This is a cached value","ttl_seconds":300}' | jq '.'
    echo ""
    
    echo "Getting cache value..."
    curl -s http://localhost:8002/api/cache/demo-key | jq '.'
    echo ""
    
    echo "Cache statistics..."
    curl -s http://localhost:8002/api/cache/stats | jq '.overall'
    echo ""
}

# Function to demonstrate cognitive processing
demo_cognitive_processing() {
    echo "🧠 Cognitive Processing Demo"
    echo "----------------------------"
    
    echo "Creating cognitive session..."
    session_response=$(curl -s -X POST http://localhost/api/session -H "Content-Type: application/json" -d '{}')
    session_id=$(echo "$session_response" | jq -r '.session_id')
    echo "Session ID: $session_id"
    echo ""
    
    echo "Processing cognitive requests (demonstrating distributed processing)..."
    
    for i in {1..5}; do
        echo "Request $i:"
        curl -s -X POST http://localhost/api/process \
            -H "Content-Type: application/json" \
            -d "{\"session_id\":\"$session_id\",\"input\":\"Demo cognitive query number $i - how does distributed processing work?\"}" | \
            jq '{response_text: .response_text, processing_time_ms: .processing_time_ms, cache_hit: .cache_hit}'
        echo ""
        sleep 1
    done
}

# Function to demonstrate monitoring
demo_monitoring() {
    echo "📊 Monitoring and Metrics Demo"
    echo "------------------------------"
    
    echo "Main application metrics:"
    curl -s http://localhost/metrics | grep "deep_echo" | head -10
    echo ""
    
    echo "Load balancer metrics:"
    curl -s http://localhost:8000/metrics | grep "load_balancer" | head -5
    echo ""
    
    echo "Cache service metrics:"
    curl -s http://localhost:8002/metrics | grep "cache" | head -5
    echo ""
    
    echo "Cognitive service 1 metrics:"
    curl -s http://localhost:8001/metrics | grep "cognitive" | head -5
    echo ""
}

# Function to demonstrate auto-scaling trigger
demo_auto_scaling() {
    echo "📈 Auto-scaling Demo"
    echo "-------------------"
    
    echo "Current service instances:"
    docker-compose ps | grep cognitive-service
    echo ""
    
    echo "Triggering load to demonstrate auto-scaling..."
    echo "(In a real scenario, this would trigger scale-up based on thresholds)"
    
    # Simulate load
    for i in {1..10}; do
        session_response=$(curl -s -X POST http://localhost/api/session -H "Content-Type: application/json" -d '{}')
        session_id=$(echo "$session_response" | jq -r '.session_id')
        
        curl -s -X POST http://localhost/api/process \
            -H "Content-Type: application/json" \
            -d "{\"session_id\":\"$session_id\",\"input\":\"Load test query $i\"}" > /dev/null &
    done
    
    wait
    echo "✅ Load test completed (10 concurrent requests)"
    echo ""
}

# Function to show system status
show_system_status() {
    echo "🏥 System Status Overview"
    echo "------------------------"
    
    echo "System status:"
    curl -s http://localhost/api/status | jq '{
        status: .status,
        active_sessions: .active_sessions,
        total_requests: .metrics.total_requests,
        distributed_mode: .distributed_mode,
        distributed_services: .distributed_services
    }'
    echo ""
    
    echo "Docker container status:"
    docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
    echo ""
}

# Main demo flow
main() {
    echo "This demo will showcase the scalability features of Deep Tree Echo:"
    echo "1. Load balancer and service discovery"
    echo "2. Multi-level caching system"
    echo "3. Distributed cognitive processing"
    echo "4. Monitoring and metrics collection"
    echo "5. Auto-scaling capabilities"
    echo "6. System status overview"
    echo ""
    
    read -p "Press Enter to start the demo..."
    echo ""
    
    check_services
    
    demo_load_balancer
    echo "Press Enter to continue to caching demo..."
    read
    echo ""
    
    demo_caching
    echo "Press Enter to continue to cognitive processing demo..."
    read
    echo ""
    
    demo_cognitive_processing
    echo "Press Enter to continue to monitoring demo..."
    read
    echo ""
    
    demo_monitoring
    echo "Press Enter to continue to auto-scaling demo..."
    read
    echo ""
    
    demo_auto_scaling
    echo "Press Enter to see final system status..."
    read
    echo ""
    
    show_system_status
    
    echo "🎉 Demo completed!"
    echo ""
    echo "🌐 Access Points:"
    echo "   Main Application:     http://localhost"
    echo "   Load Balancer:        http://localhost:8000"
    echo "   Cache Service:        http://localhost:8002"
    echo "   Grafana Monitoring:   http://localhost:3000 (admin/deepecho123)"
    echo "   Prometheus:           http://localhost:9090"
    echo "   Jaeger Tracing:       http://localhost:16686"
    echo ""
    echo "To run performance tests: ./quick-start.sh test"
    echo "To scale services: ./quick-start.sh scale 5"
    echo "To view logs: ./quick-start.sh logs [service-name]"
}

# Run the demo
main "$@"