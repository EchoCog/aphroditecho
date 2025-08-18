#!/bin/bash

# Deep Echo DevOps Management Script
# Unified management of infrastructure, deployments, and operations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="./devops.log"

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-west-2}"
CLUSTER_NAME="${CLUSTER_NAME:-deep-echo-$ENVIRONMENT}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    local required_tools=("terraform" "kubectl" "helm" "docker" "aws")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
    fi
    
    log "Prerequisites check passed"
}

# Infrastructure management
manage_infrastructure() {
    local action="$1"
    local env="${2:-$ENVIRONMENT}"
    
    log "Managing infrastructure: $action for environment $env"
    
    local tf_dir="$PROJECT_ROOT/infrastructure/terraform/environments/$env"
    
    if [ ! -d "$tf_dir" ]; then
        error "Terraform configuration not found for environment: $env"
    fi
    
    cd "$tf_dir"
    
    case "$action" in
        "plan")
            terraform init
            terraform plan
            ;;
        "apply")
            terraform init
            terraform plan -out=tfplan
            terraform apply tfplan
            rm -f tfplan
            ;;
        "destroy")
            terraform init
            terraform plan -destroy
            read -p "Are you sure you want to destroy infrastructure for $env? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                terraform destroy
            else
                log "Destroy cancelled"
            fi
            ;;
        "output")
            terraform output
            ;;
        *)
            error "Unknown infrastructure action: $action"
            ;;
    esac
    
    log "Infrastructure management completed: $action"
}

# Kubernetes cluster management
manage_cluster() {
    local action="$1"
    local env="${2:-$ENVIRONMENT}"
    
    log "Managing Kubernetes cluster: $action for environment $env"
    
    # Update kubeconfig
    aws eks update-kubeconfig --region "$AWS_REGION" --name "deep-echo-$env"
    
    case "$action" in
        "status")
            kubectl cluster-info
            kubectl get nodes
            kubectl get pods --all-namespaces
            ;;
        "deploy")
            deploy_application "$env"
            ;;
        "scale")
            local replicas="${3:-3}"
            kubectl scale deployment --all --replicas="$replicas"
            ;;
        "logs")
            local service="${3:-main-app}"
            kubectl logs -l app="deep-echo-$service" --tail=100 -f
            ;;
        "exec")
            local service="${3:-main-app}"
            local pod=$(kubectl get pods -l app="deep-echo-$service" -o jsonpath='{.items[0].metadata.name}')
            kubectl exec -it "$pod" -- /bin/bash
            ;;
        *)
            error "Unknown cluster action: $action"
            ;;
    esac
    
    log "Cluster management completed: $action"
}

# Application deployment
deploy_application() {
    local env="${1:-$ENVIRONMENT}"
    
    log "Deploying application to environment: $env"
    
    # Deploy with Helm
    local helm_dir="$PROJECT_ROOT/infrastructure/helm/deep-echo"
    local values_file="$helm_dir/values-$env.yaml"
    
    if [ ! -f "$values_file" ]; then
        values_file="$helm_dir/values.yaml"
    fi
    
    helm upgrade --install "deep-echo-$env" "$helm_dir" \
        --namespace "deep-echo-$env" \
        --create-namespace \
        --values "$values_file" \
        --set image.tag="${IMAGE_TAG:-latest}" \
        --set environment="$env" \
        --wait --timeout=10m
    
    # Verify deployment
    kubectl rollout status deployment/deep-echo-main -n "deep-echo-$env"
    
    log "Application deployment completed"
}

# Service mesh management
manage_service_mesh() {
    local action="$1"
    
    log "Managing service mesh: $action"
    
    local mesh_script="$PROJECT_ROOT/infrastructure/service-mesh/setup-istio.sh"
    
    case "$action" in
        "install")
            "$mesh_script" install
            ;;
        "configure")
            "$mesh_script" config
            ;;
        "verify")
            "$mesh_script" verify
            ;;
        "cleanup")
            "$mesh_script" cleanup
            ;;
        *)
            error "Unknown service mesh action: $action"
            ;;
    esac
    
    log "Service mesh management completed: $action"
}

# Monitoring setup
setup_monitoring() {
    local env="${1:-$ENVIRONMENT}"
    
    log "Setting up monitoring for environment: $env"
    
    # Deploy monitoring stack
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install Prometheus
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.retention=30d \
        --set grafana.adminPassword="deepecho123" \
        --wait
    
    # Apply custom alert rules
    kubectl apply -f "$PROJECT_ROOT/infrastructure/monitoring/rules/"
    
    log "Monitoring setup completed"
}

# Backup operations
manage_backups() {
    local action="$1"
    
    log "Managing backups: $action"
    
    local backup_script="$PROJECT_ROOT/infrastructure/backup/backup.sh"
    local recovery_script="$PROJECT_ROOT/infrastructure/backup/disaster-recovery.sh"
    
    case "$action" in
        "create")
            "$backup_script"
            ;;
        "list")
            "$recovery_script" list
            ;;
        "restore")
            local backup_name="${2:-latest}"
            "$recovery_script" auto "$backup_name"
            ;;
        "test")
            # Test backup and restore process
            "$backup_script"
            log "Backup test completed. Check logs for details."
            ;;
        *)
            error "Unknown backup action: $action"
            ;;
    esac
    
    log "Backup management completed: $action"
}

# Security operations
manage_security() {
    local action="$1"
    
    log "Managing security: $action"
    
    case "$action" in
        "scan")
            # Container security scanning
            local registry_script="$PROJECT_ROOT/infrastructure/registry/manage-registry.sh"
            "$registry_script" scan
            ;;
        "policies")
            # Apply security policies
            kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/security/"
            ;;
        "audit")
            # Security audit
            kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'
            ;;
        *)
            error "Unknown security action: $action"
            ;;
    esac
    
    log "Security management completed: $action"
}

# Chaos engineering
run_chaos_tests() {
    local test_type="${1:-suite}"
    
    log "Running chaos engineering tests: $test_type"
    
    local chaos_script="$PROJECT_ROOT/infrastructure/chaos/chaos-engineering.sh"
    "$chaos_script" "$test_type"
    
    log "Chaos engineering tests completed"
}

# Performance testing
run_performance_tests() {
    local target_url="${1:-http://localhost}"
    
    log "Running performance tests against: $target_url"
    
    local perf_script="$PROJECT_ROOT/infrastructure/testing/run-performance-tests.sh"
    TARGET_URL="$target_url" "$perf_script"
    
    log "Performance testing completed"
}

# Environment management
manage_environment() {
    local action="$1"
    local env="${2:-$ENVIRONMENT}"
    
    log "Managing environment: $action for $env"
    
    case "$action" in
        "create")
            # Create new environment
            manage_infrastructure "apply" "$env"
            manage_cluster "deploy" "$env"
            setup_monitoring "$env"
            ;;
        "destroy")
            # Destroy environment
            helm uninstall "deep-echo-$env" -n "deep-echo-$env" || true
            kubectl delete namespace "deep-echo-$env" || true
            manage_infrastructure "destroy" "$env"
            ;;
        "status")
            # Environment status
            echo "=== Infrastructure Status ==="
            manage_infrastructure "output" "$env"
            echo
            echo "=== Cluster Status ==="
            manage_cluster "status" "$env"
            ;;
        "update")
            # Update environment
            manage_infrastructure "apply" "$env"
            deploy_application "$env"
            ;;
        *)
            error "Unknown environment action: $action"
            ;;
    esac
    
    log "Environment management completed: $action"
}

# Health check
health_check() {
    log "Performing health check..."
    
    local health_status=0
    
    # Check infrastructure
    echo "=== Infrastructure Health ==="
    if terraform -chdir="$PROJECT_ROOT/infrastructure/terraform/environments/$ENVIRONMENT" show >/dev/null 2>&1; then
        echo "✅ Infrastructure state is valid"
    else
        echo "❌ Infrastructure state issues detected"
        health_status=1
    fi
    
    # Check cluster
    echo "=== Cluster Health ==="
    if kubectl cluster-info >/dev/null 2>&1; then
        echo "✅ Cluster is accessible"
        
        # Check node status
        local ready_nodes=$(kubectl get nodes --no-headers | awk '$2=="Ready"' | wc -l)
        local total_nodes=$(kubectl get nodes --no-headers | wc -l)
        echo "✅ Nodes: $ready_nodes/$total_nodes ready"
        
        # Check pod status
        local running_pods=$(kubectl get pods --all-namespaces --no-headers | awk '$4=="Running"' | wc -l)
        local total_pods=$(kubectl get pods --all-namespaces --no-headers | wc -l)
        echo "✅ Pods: $running_pods/$total_pods running"
    else
        echo "❌ Cluster is not accessible"
        health_status=1
    fi
    
    # Check application endpoints
    echo "=== Application Health ==="
    local endpoints=("http://localhost/api/status" "http://localhost:8000/health")
    for endpoint in "${endpoints[@]}"; do
        if curl -f "$endpoint" >/dev/null 2>&1; then
            echo "✅ $endpoint is responding"
        else
            echo "❌ $endpoint is not responding"
            health_status=1
        fi
    done
    
    if [ $health_status -eq 0 ]; then
        log "Health check passed ✅"
    else
        log "Health check failed ❌"
        exit 1
    fi
}

# Show usage
usage() {
    cat << EOF
Deep Echo DevOps Management Tool
===============================

Usage: $0 <command> [options]

Commands:
  
  Infrastructure:
    infra plan [env]          - Plan infrastructure changes
    infra apply [env]         - Apply infrastructure changes  
    infra destroy [env]       - Destroy infrastructure
    infra output [env]        - Show infrastructure outputs
    
  Cluster:
    cluster status [env]      - Show cluster status
    cluster deploy [env]      - Deploy application
    cluster scale [env] [n]   - Scale application
    cluster logs [env] [svc]  - Show service logs
    cluster exec [env] [svc]  - Execute shell in service
    
  Service Mesh:
    mesh install              - Install service mesh
    mesh configure            - Configure service mesh
    mesh verify               - Verify service mesh
    mesh cleanup              - Remove service mesh
    
  Operations:
    monitoring [env]          - Setup monitoring
    backup create             - Create backup
    backup restore [name]     - Restore from backup
    security scan             - Run security scans
    chaos [test_type]         - Run chaos tests
    performance [url]         - Run performance tests
    
  Environment:
    env create [env]          - Create new environment
    env destroy [env]         - Destroy environment
    env status [env]          - Show environment status
    env update [env]          - Update environment
    
  Utilities:
    health                    - Run health check
    help                      - Show this help

Environment Variables:
  ENVIRONMENT              - Target environment (default: dev)
  AWS_REGION              - AWS region (default: us-west-2)
  IMAGE_TAG               - Container image tag (default: latest)

Examples:
  $0 infra apply production
  $0 cluster deploy staging
  $0 env create dev
  $0 performance http://staging.deepecho.ai
  $0 health

EOF
}

# Main function
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi
    
    check_prerequisites
    
    case "${1:-help}" in
        "infra")
            manage_infrastructure "${2:-plan}" "${3:-$ENVIRONMENT}"
            ;;
        "cluster")
            manage_cluster "${2:-status}" "${3:-$ENVIRONMENT}" "${4:-}"
            ;;
        "mesh")
            manage_service_mesh "${2:-install}"
            ;;
        "monitoring")
            setup_monitoring "${2:-$ENVIRONMENT}"
            ;;
        "backup")
            manage_backups "${2:-create}" "${3:-}"
            ;;
        "security")
            manage_security "${2:-scan}"
            ;;
        "chaos")
            run_chaos_tests "${2:-suite}"
            ;;
        "performance")
            run_performance_tests "${2:-http://localhost}"
            ;;
        "env")
            manage_environment "${2:-status}" "${3:-$ENVIRONMENT}"
            ;;
        "health")
            health_check
            ;;
        "help"|*)
            usage
            ;;
    esac
}

# Run main function
main "$@"