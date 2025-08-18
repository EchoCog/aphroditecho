#!/bin/bash

# Deep Echo Chaos Engineering Script
# Implements chaos engineering practices to test system resilience

set -euo pipefail

# Configuration
LOG_FILE="/var/log/deep-echo-chaos.log"
EXPERIMENT_DIR="/tmp/chaos_experiments"
RESULTS_DIR="infrastructure/chaos/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

# Initialize experiment environment
init_experiment() {
    mkdir -p "$EXPERIMENT_DIR" "$RESULTS_DIR"
    log "Chaos engineering experiment initialized"
}

# Record baseline metrics
record_baseline() {
    local experiment_name="$1"
    local baseline_file="$RESULTS_DIR/${experiment_name}_baseline_$TIMESTAMP.json"
    
    log "Recording baseline metrics..."
    
    # Get current system metrics
    cat > "$baseline_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "experiment": "$experiment_name",
    "baseline_metrics": {
        "response_time": $(curl -s -o /dev/null -w "%{time_total}" http://localhost:8000/api/status || echo "null"),
        "cpu_usage": $(docker stats --no-stream --format "{{.CPUPerc}}" | head -1 | sed 's/%//' || echo "null"),
        "memory_usage": $(docker stats --no-stream --format "{{.MemUsage}}" | head -1 || echo "null"),
        "active_containers": $(docker ps --format "{{.Names}}" | wc -l),
        "redis_connected_clients": $(redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r' || echo "null"),
        "load_balancer_healthy_backends": $(curl -s http://localhost:8000/health | jq '.healthy_backends' 2>/dev/null || echo "null")
    }
}
EOF
    
    log "Baseline metrics recorded: $baseline_file"
    echo "$baseline_file"
}

# Monitor system during experiment
monitor_system() {
    local experiment_name="$1"
    local duration="$2"
    local monitoring_file="$RESULTS_DIR/${experiment_name}_monitoring_$TIMESTAMP.json"
    
    log "Starting system monitoring for $duration seconds..."
    
    echo '{"experiment": "'$experiment_name'", "monitoring_data": [' > "$monitoring_file"
    
    local end_time=$(($(date +%s) + duration))
    local first_entry=true
    
    while [ $(date +%s) -lt $end_time ]; do
        if [ "$first_entry" = false ]; then
            echo "," >> "$monitoring_file"
        fi
        first_entry=false
        
        cat >> "$monitoring_file" << EOF
    {
        "timestamp": "$(date -Iseconds)",
        "metrics": {
            "response_time": $(curl -s -o /dev/null -w "%{time_total}" http://localhost:8000/api/status 2>/dev/null || echo "null"),
            "http_status": $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/status 2>/dev/null || echo "null"),
            "cpu_usage": $(docker stats --no-stream --format "{{.CPUPerc}}" deep-echo-main 2>/dev/null | sed 's/%//' || echo "null"),
            "memory_usage": $(docker stats --no-stream --format "{{.MemUsage}}" deep-echo-main 2>/dev/null || echo "null"),
            "error_rate": $(curl -s http://localhost:9090/api/v1/query?query=rate\(flask_http_request_exceptions_total\[1m\]\) 2>/dev/null | jq '.data.result[0].value[1]' 2>/dev/null || echo "null")
        }
    }
EOF
        
        sleep 5
    done
    
    echo ']}' >> "$monitoring_file"
    
    log "System monitoring completed: $monitoring_file"
    echo "$monitoring_file"
}

# Container failure experiment
experiment_container_failure() {
    local target_container="${1:-cognitive-service-1}"
    local duration="${2:-60}"
    
    log "Starting container failure experiment on $target_container"
    
    local baseline_file
    baseline_file=$(record_baseline "container_failure_$target_container")
    
    # Start monitoring in background
    monitor_system "container_failure_$target_container" $((duration + 30)) &
    local monitor_pid=$!
    
    # Kill the target container
    log "Killing container: $target_container"
    docker kill "deep-echo-$target_container" || log "Warning: Failed to kill container"
    
    # Wait for the specified duration
    sleep "$duration"
    
    # Container should auto-restart via Docker Compose restart policy
    log "Waiting for container auto-recovery..."
    local recovery_time=0
    while ! docker ps --filter "name=deep-echo-$target_container" --filter "status=running" | grep -q "$target_container" && [ $recovery_time -lt 120 ]; do
        sleep 5
        recovery_time=$((recovery_time + 5))
    done
    
    if [ $recovery_time -lt 120 ]; then
        log "Container recovered automatically in ${recovery_time}s"
    else
        log "Container failed to recover automatically"
    fi
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "Container failure experiment completed"
}

# Network partition experiment
experiment_network_partition() {
    local target_service="${1:-cognitive-service-1}"
    local duration="${2:-30}"
    
    log "Starting network partition experiment on $target_service"
    
    local baseline_file
    baseline_file=$(record_baseline "network_partition_$target_service")
    
    # Start monitoring
    monitor_system "network_partition_$target_service" $((duration + 20)) &
    local monitor_pid=$!
    
    # Create network partition using iptables
    log "Creating network partition for $target_service"
    local container_ip=$(docker inspect "deep-echo-$target_service" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
    
    # Block traffic to/from the container
    sudo iptables -A INPUT -s "$container_ip" -j DROP 2>/dev/null || log "Warning: Failed to add INPUT rule"
    sudo iptables -A OUTPUT -d "$container_ip" -j DROP 2>/dev/null || log "Warning: Failed to add OUTPUT rule"
    
    sleep "$duration"
    
    # Restore network connectivity
    log "Restoring network connectivity"
    sudo iptables -D INPUT -s "$container_ip" -j DROP 2>/dev/null || log "Warning: Failed to remove INPUT rule"
    sudo iptables -D OUTPUT -d "$container_ip" -j DROP 2>/dev/null || log "Warning: Failed to remove OUTPUT rule"
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "Network partition experiment completed"
}

# High CPU load experiment
experiment_cpu_stress() {
    local target_container="${1:-main-app}"
    local cpu_percent="${2:-80}"
    local duration="${3:-60}"
    
    log "Starting CPU stress experiment on $target_container"
    
    local baseline_file
    baseline_file=$(record_baseline "cpu_stress_$target_container")
    
    # Start monitoring
    monitor_system "cpu_stress_$target_container" $((duration + 20)) &
    local monitor_pid=$!
    
    # Create CPU stress
    log "Creating CPU stress ($cpu_percent% for ${duration}s)"
    docker exec "deep-echo-$target_container" bash -c "
        stress --cpu 1 --timeout ${duration}s &
        stress_pid=\$!
        echo 'CPU stress started with PID:' \$stress_pid
        wait \$stress_pid
    " 2>/dev/null || log "Warning: Failed to create CPU stress (stress tool may not be available)"
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "CPU stress experiment completed"
}

# Memory pressure experiment
experiment_memory_pressure() {
    local target_container="${1:-main-app}"
    local memory_mb="${2:-512}"
    local duration="${3:-60}"
    
    log "Starting memory pressure experiment on $target_container"
    
    local baseline_file
    baseline_file=$(record_baseline "memory_pressure_$target_container")
    
    # Start monitoring
    monitor_system "memory_pressure_$target_container" $((duration + 20)) &
    local monitor_pid=$!
    
    # Create memory pressure
    log "Creating memory pressure (${memory_mb}MB for ${duration}s)"
    docker exec "deep-echo-$target_container" bash -c "
        stress --vm 1 --vm-bytes ${memory_mb}M --timeout ${duration}s &
        stress_pid=\$!
        echo 'Memory stress started with PID:' \$stress_pid
        wait \$stress_pid
    " 2>/dev/null || log "Warning: Failed to create memory stress (stress tool may not be available)"
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "Memory pressure experiment completed"
}

# Redis failure experiment
experiment_redis_failure() {
    local duration="${1:-60}"
    
    log "Starting Redis failure experiment"
    
    local baseline_file
    baseline_file=$(record_baseline "redis_failure")
    
    # Start monitoring
    monitor_system "redis_failure" $((duration + 30)) &
    local monitor_pid=$!
    
    # Stop Redis
    log "Stopping Redis service"
    docker stop deep-echo-redis || log "Warning: Failed to stop Redis"
    
    sleep "$duration"
    
    # Restart Redis
    log "Restarting Redis service"
    docker start deep-echo-redis || log "Warning: Failed to restart Redis"
    
    # Wait for Redis to be ready
    local recovery_time=0
    while ! redis-cli ping >/dev/null 2>&1 && [ $recovery_time -lt 60 ]; do
        sleep 2
        recovery_time=$((recovery_time + 2))
    done
    
    log "Redis recovered in ${recovery_time}s"
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "Redis failure experiment completed"
}

# Load balancer experiment
experiment_load_balancer_failure() {
    local duration="${1:-60}"
    
    log "Starting load balancer failure experiment"
    
    local baseline_file
    baseline_file=$(record_baseline "lb_failure")
    
    # Start monitoring
    monitor_system "lb_failure" $((duration + 30)) &
    local monitor_pid=$!
    
    # Stop load balancer
    log "Stopping load balancer service"
    docker stop deep-echo-lb || log "Warning: Failed to stop load balancer"
    
    sleep "$duration"
    
    # Restart load balancer
    log "Restarting load balancer service"
    docker start deep-echo-lb || log "Warning: Failed to restart load balancer"
    
    # Wait for monitoring to complete
    wait $monitor_pid
    
    log "Load balancer failure experiment completed"
}

# Generate experiment report
generate_report() {
    local experiment_name="$1"
    local report_file="$RESULTS_DIR/${experiment_name}_report_$TIMESTAMP.md"
    
    log "Generating experiment report..."
    
    cat > "$report_file" << EOF
# Chaos Engineering Experiment Report

**Experiment**: $experiment_name  
**Date**: $(date)  
**Duration**: Various  

## Summary

This report contains the results of the chaos engineering experiment conducted on the Deep Tree Echo system.

## Metrics Collected

The following metrics were collected during the experiment:
- Response time
- HTTP status codes
- CPU usage
- Memory usage
- Error rates
- System availability

## Files Generated

EOF
    
    # List all files for this experiment
    find "$RESULTS_DIR" -name "*${experiment_name}*" -type f | while read -r file; do
        echo "- $(basename "$file")" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

## Analysis

### Key Observations

- System behavior during the experiment
- Recovery time and mechanism
- Impact on user experience
- Effectiveness of monitoring and alerting

### Recommendations

Based on the experiment results, consider the following improvements:

1. **Monitoring**: Enhance monitoring for early detection
2. **Alerting**: Improve alert thresholds and notification
3. **Recovery**: Optimize automatic recovery mechanisms
4. **Resilience**: Implement additional redundancy where needed

## Next Steps

- Review monitoring data for patterns
- Update incident response procedures
- Schedule follow-up experiments
- Implement improvements based on findings

EOF
    
    log "Experiment report generated: $report_file"
}

# Run comprehensive chaos test suite
run_test_suite() {
    log "Starting comprehensive chaos engineering test suite"
    
    init_experiment
    
    # Service failure tests
    experiment_container_failure "cognitive-service-1" 60
    sleep 30
    experiment_container_failure "main-app" 60
    sleep 30
    
    # Network tests
    experiment_network_partition "cognitive-service-1" 30
    sleep 30
    
    # Resource stress tests
    experiment_cpu_stress "main-app" 80 60
    sleep 30
    experiment_memory_pressure "main-app" 256 60
    sleep 30
    
    # Infrastructure failure tests
    experiment_redis_failure 60
    sleep 30
    experiment_load_balancer_failure 60
    
    # Generate comprehensive report
    generate_report "comprehensive_suite"
    
    log "Comprehensive chaos engineering test suite completed"
}

# Show usage
usage() {
    echo "Deep Echo Chaos Engineering Tool"
    echo "================================"
    echo
    echo "Usage: $0 <experiment_type> [options]"
    echo
    echo "Experiment types:"
    echo "  container-failure [container] [duration]  - Kill a container and test recovery"
    echo "  network-partition [service] [duration]    - Create network partition"
    echo "  cpu-stress [container] [percent] [duration] - Create CPU load"
    echo "  memory-pressure [container] [mb] [duration] - Create memory pressure"
    echo "  redis-failure [duration]                  - Stop Redis service"
    echo "  lb-failure [duration]                     - Stop load balancer"
    echo "  suite                                     - Run comprehensive test suite"
    echo
    echo "Examples:"
    echo "  $0 container-failure cognitive-service-1 60"
    echo "  $0 cpu-stress main-app 80 120"
    echo "  $0 suite"
}

# Main function
main() {
    case "${1:-}" in
        "container-failure")
            init_experiment
            experiment_container_failure "${2:-cognitive-service-1}" "${3:-60}"
            generate_report "container_failure"
            ;;
        "network-partition")
            init_experiment
            experiment_network_partition "${2:-cognitive-service-1}" "${3:-30}"
            generate_report "network_partition"
            ;;
        "cpu-stress")
            init_experiment
            experiment_cpu_stress "${2:-main-app}" "${3:-80}" "${4:-60}"
            generate_report "cpu_stress"
            ;;
        "memory-pressure")
            init_experiment
            experiment_memory_pressure "${2:-main-app}" "${3:-512}" "${4:-60}"
            generate_report "memory_pressure"
            ;;
        "redis-failure")
            init_experiment
            experiment_redis_failure "${2:-60}"
            generate_report "redis_failure"
            ;;
        "lb-failure")
            init_experiment
            experiment_load_balancer_failure "${2:-60}"
            generate_report "lb_failure"
            ;;
        "suite")
            run_test_suite
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"