#!/bin/bash

# Deep Tree Echo Scalable Deployment Quick Start
# This script helps you get started with the distributed architecture

set -e

echo "🚀 Deep Tree Echo - Scalable Architecture Quick Start"
echo "===================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites satisfied"

# Function to display help
show_help() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    start           Start all services (default)
    stop            Stop all services
    restart         Restart all services
    logs            Show logs from all services
    status          Show status of all services
    test            Run performance tests
    scale           Scale cognitive services
    monitor         Open monitoring dashboard
    help            Show this help message

Examples:
    $0 start        # Start the distributed architecture
    $0 scale 3      # Scale to 3 cognitive service instances
    $0 test         # Run performance tests
    $0 logs lb      # Show load balancer logs

EOF
}

# Function to start services
start_services() {
    echo "🏗️  Starting Deep Tree Echo distributed architecture..."
    
    # Build and start services
    docker-compose up -d --build
    
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    echo "🎉 All services started successfully!"
    echo ""
    echo "🌐 Access Points:"
    echo "   Main Application:     http://localhost"
    echo "   Load Balancer:        http://localhost:8000"
    echo "   Cache Service:        http://localhost:8002"
    echo "   Cognitive Service 1:  http://localhost:8001"
    echo "   Cognitive Service 2:  http://localhost:8003"
    echo "   Grafana Monitoring:   http://localhost:3000 (admin/deepecho123)"
    echo "   Prometheus:           http://localhost:9090"
    echo "   Jaeger Tracing:       http://localhost:16686"
    echo ""
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping Deep Tree Echo services..."
    docker-compose down
    echo "✅ All services stopped"
}

# Function to restart services
restart_services() {
    echo "🔄 Restarting Deep Tree Echo services..."
    docker-compose restart
    echo "✅ All services restarted"
}

# Function to show logs
show_logs() {
    local service="$1"
    if [ -n "$service" ]; then
        echo "📋 Showing logs for service: $service"
        docker-compose logs -f "$service"
    else
        echo "📋 Showing logs for all services..."
        docker-compose logs -f
    fi
}

# Function to check service health
check_service_health() {
    echo "🏥 Checking service health..."
    
    services=(
        "http://localhost/health:Main Application"
        "http://localhost:8000/health:Load Balancer"
        "http://localhost:8002/health:Cache Service"
        "http://localhost:8001/health:Cognitive Service 1"
        "http://localhost:8003/health:Cognitive Service 2"
    )
    
    for service in "${services[@]}"; do
        url="${service%:*}"
        name="${service#*:}"
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "   ✅ $name"
        else
            echo "   ❌ $name (not responding)"
        fi
    done
}

# Function to show status
show_status() {
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    check_service_health
}

# Function to run performance tests
run_tests() {
    echo "🧪 Running performance tests..."
    
    if [ ! -f "./infrastructure/testing/run-performance-tests.sh" ]; then
        echo "❌ Performance test script not found"
        exit 1
    fi
    
    chmod +x ./infrastructure/testing/run-performance-tests.sh
    ./infrastructure/testing/run-performance-tests.sh
}

# Function to scale services
scale_services() {
    local count="$1"
    if [ -z "$count" ]; then
        count=3
    fi
    
    echo "📈 Scaling cognitive services to $count instances..."
    docker-compose up -d --scale cognitive-service-1="$count"
    echo "✅ Scaled to $count instances"
}

# Function to open monitoring
open_monitoring() {
    echo "📈 Opening monitoring dashboard..."
    
    if command_exists xdg-open; then
        xdg-open http://localhost:3000
    elif command_exists open; then
        open http://localhost:3000
    else
        echo "📊 Grafana monitoring available at: http://localhost:3000"
        echo "   Username: admin"
        echo "   Password: deepecho123"
    fi
}

# Function to clean up
cleanup() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo "✅ Cleanup completed"
}

# Main command processing
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    test)
        run_tests
        ;;
    scale)
        scale_services "$2"
        ;;
    monitor)
        open_monitoring
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac