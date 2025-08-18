#!/bin/bash

# Container Registry Management Script for Deep Echo
# Manages container images, security scanning, and lifecycle

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
NAMESPACE="${NAMESPACE:-echocog}"
PROJECT="${PROJECT:-deep-tree-echo-rkwv}"
LOG_FILE="/var/log/registry-management.log"

# Image configurations
declare -A IMAGES=(
    ["main"]="$REGISTRY/$NAMESPACE/$PROJECT"
    ["microservice"]="$REGISTRY/$NAMESPACE/$PROJECT-microservice"
    ["monitoring"]="$REGISTRY/$NAMESPACE/$PROJECT-monitoring"
)

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
    
    command -v docker >/dev/null 2>&1 || error "docker not found"
    command -v crane >/dev/null 2>&1 || log "Warning: crane not found (install with: go install github.com/google/go-containerregistry/cmd/crane@latest)"
    command -v trivy >/dev/null 2>&1 || log "Warning: trivy not found (install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin)"
    command -v cosign >/dev/null 2>&1 || log "Warning: cosign not found (install with: go install github.com/sigstore/cosign/cmd/cosign@latest)"
    
    log "Prerequisites check completed"
}

# Build and tag images
build_images() {
    local tag="${1:-latest}"
    local build_args="${2:-}"
    
    log "Building images with tag: $tag"
    
    # Build main application image
    log "Building main application image..."
    docker build \
        -t "${IMAGES[main]}:$tag" \
        -t "${IMAGES[main]}:$(date +%Y%m%d-%H%M%S)" \
        $build_args \
        -f Dockerfile .
    
    # Build microservice image
    log "Building microservice image..."
    docker build \
        -t "${IMAGES[microservice]}:$tag" \
        -t "${IMAGES[microservice]}:$(date +%Y%m%d-%H%M%S)" \
        $build_args \
        -f Dockerfile.microservice .
    
    log "Images built successfully"
}

# Scan images for security vulnerabilities
scan_images() {
    local tag="${1:-latest}"
    local results_dir="infrastructure/registry/scan-results"
    
    mkdir -p "$results_dir"
    
    log "Scanning images for vulnerabilities..."
    
    for image_name in "${!IMAGES[@]}"; do
        local image="${IMAGES[$image_name]}:$tag"
        log "Scanning $image..."
        
        # Trivy scan
        if command -v trivy >/dev/null 2>&1; then
            trivy image \
                --format json \
                --output "$results_dir/${image_name}_trivy_$(date +%Y%m%d).json" \
                "$image" || log "Warning: Trivy scan failed for $image"
            
            # Also generate table format for easier reading
            trivy image \
                --format table \
                --output "$results_dir/${image_name}_trivy_$(date +%Y%m%d).txt" \
                "$image" || log "Warning: Trivy table scan failed for $image"
        fi
        
        # Docker scan (if available)
        docker scan "$image" > "$results_dir/${image_name}_docker_scan_$(date +%Y%m%d).txt" 2>&1 || \
            log "Warning: Docker scan not available or failed for $image"
    done
    
    log "Security scanning completed. Results in: $results_dir"
}

# Sign images with cosign
sign_images() {
    local tag="${1:-latest}"
    
    if ! command -v cosign >/dev/null 2>&1; then
        log "Warning: cosign not available, skipping image signing"
        return
    fi
    
    log "Signing images with cosign..."
    
    for image_name in "${!IMAGES[@]}"; do
        local image="${IMAGES[$image_name]}:$tag"
        log "Signing $image..."
        
        # Sign the image
        cosign sign "$image" || log "Warning: Failed to sign $image"
    done
    
    log "Image signing completed"
}

# Push images to registry
push_images() {
    local tag="${1:-latest}"
    
    log "Pushing images to registry..."
    
    for image_name in "${!IMAGES[@]}"; do
        local image="${IMAGES[$image_name]}:$tag"
        local timestamped_image="${IMAGES[$image_name]}:$(date +%Y%m%d-%H%M%S)"
        
        log "Pushing $image..."
        docker push "$image" || error "Failed to push $image"
        
        log "Pushing $timestamped_image..."
        docker push "$timestamped_image" || error "Failed to push $timestamped_image"
    done
    
    log "Images pushed successfully"
}

# List image versions
list_images() {
    local image_name="${1:-}"
    
    log "Listing image versions..."
    
    if [ -n "$image_name" ] && [ -n "${IMAGES[$image_name]:-}" ]; then
        # List specific image
        local image="${IMAGES[$image_name]}"
        log "Tags for $image:"
        
        if command -v crane >/dev/null 2>&1; then
            crane ls "$image" | head -20
        else
            log "Warning: crane not available, cannot list tags"
        fi
    else
        # List all images
        for name in "${!IMAGES[@]}"; do
            local image="${IMAGES[$name]}"
            echo "=== $name ($image) ==="
            
            if command -v crane >/dev/null 2>&1; then
                crane ls "$image" | head -10
            else
                echo "Tags not available (crane not installed)"
            fi
            echo
        done
    fi
}

# Clean up old images
cleanup_images() {
    local keep_count="${1:-10}"
    
    log "Cleaning up old images (keeping $keep_count latest)..."
    
    for image_name in "${!IMAGES[@]}"; do
        local image="${IMAGES[$image_name]}"
        log "Cleaning up $image..."
        
        if command -v crane >/dev/null 2>&1; then
            # Get all tags except 'latest'
            local tags=$(crane ls "$image" | grep -v "^latest$" | sort -r)
            local count=0
            
            echo "$tags" | while read -r tag; do
                count=$((count + 1))
                if [ $count -gt $keep_count ]; then
                    log "Deleting old tag: $image:$tag"
                    crane delete "$image:$tag" || log "Warning: Failed to delete $image:$tag"
                fi
            done
        else
            log "Warning: crane not available, cannot clean up $image"
        fi
    done
    
    # Clean up local images
    log "Cleaning up local Docker images..."
    docker image prune -f --filter "until=72h" || log "Warning: Failed to prune local images"
    
    log "Cleanup completed"
}

# Generate vulnerability report
generate_vulnerability_report() {
    local results_dir="infrastructure/registry/scan-results"
    local report_file="$results_dir/vulnerability_report_$(date +%Y%m%d).md"
    
    log "Generating vulnerability report..."
    
    cat > "$report_file" << EOF
# Container Vulnerability Report

**Generated**: $(date)  
**Registry**: $REGISTRY  
**Namespace**: $NAMESPACE  

## Summary

This report contains vulnerability scan results for all Deep Echo container images.

## Images Scanned

EOF
    
    for image_name in "${!IMAGES[@]}"; do
        echo "### $image_name" >> "$report_file"
        echo "" >> "$report_file"
        echo "**Image**: ${IMAGES[$image_name]}" >> "$report_file"
        echo "" >> "$report_file"
        
        # Include Trivy results if available
        local trivy_file="$results_dir/${image_name}_trivy_$(date +%Y%m%d).json"
        if [ -f "$trivy_file" ]; then
            local high_vulns=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$trivy_file" 2>/dev/null || echo "0")
            local critical_vulns=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$trivy_file" 2>/dev/null || echo "0")
            
            echo "**Critical Vulnerabilities**: $critical_vulns" >> "$report_file"
            echo "**High Vulnerabilities**: $high_vulns" >> "$report_file"
            echo "" >> "$report_file"
            echo "Detailed scan results: \`${image_name}_trivy_$(date +%Y%m%d).json\`" >> "$report_file"
        else
            echo "No vulnerability scan results available." >> "$report_file"
        fi
        
        echo "" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

## Recommendations

### High Priority
- Review and patch CRITICAL vulnerabilities immediately
- Update base images to latest secure versions
- Implement automated vulnerability scanning in CI/CD

### Medium Priority
- Address HIGH severity vulnerabilities
- Regular security updates for dependencies
- Container image hardening

### Monitoring
- Set up automated vulnerability alerts
- Regular security scanning schedule
- Track vulnerability trends over time

## Files Generated

All detailed scan results are available in the \`$results_dir\` directory.

---
**Generated by**: Deep Echo Container Registry Management  
**Report Date**: $(date)
EOF
    
    log "Vulnerability report generated: $report_file"
}

# Registry health check
health_check() {
    log "Performing registry health check..."
    
    # Check if we can authenticate with the registry
    if docker login "$REGISTRY" --username="$GITHUB_ACTOR" --password="$GITHUB_TOKEN" 2>/dev/null; then
        log "✅ Registry authentication successful"
    else
        log "❌ Registry authentication failed"
    fi
    
    # Check if we can pull a test image
    for image_name in "${!IMAGES[@]}"; do
        local image="${IMAGES[$image_name]}:latest"
        log "Checking accessibility of $image..."
        
        if docker manifest inspect "$image" >/dev/null 2>&1; then
            log "✅ $image is accessible"
        else
            log "❌ $image is not accessible"
        fi
    done
    
    log "Registry health check completed"
}

# Show image information
show_image_info() {
    local image_name="${1:-}"
    local tag="${2:-latest}"
    
    if [ -z "$image_name" ] || [ -z "${IMAGES[$image_name]:-}" ]; then
        echo "Available images:"
        for name in "${!IMAGES[@]}"; do
            echo "  - $name: ${IMAGES[$name]}"
        done
        return
    fi
    
    local image="${IMAGES[$image_name]}:$tag"
    
    log "Image information for $image:"
    
    # Basic image info
    if command -v crane >/dev/null 2>&1; then
        echo "=== Image Manifest ==="
        crane manifest "$image" | jq '.' || echo "Failed to get manifest"
        echo
        
        echo "=== Image Config ==="
        crane config "$image" | jq '.' || echo "Failed to get config"
        echo
    fi
    
    # Docker inspect if local
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "=== Local Image Info ==="
        docker image inspect "$image" | jq '.[0] | {Id, Created, Size, Config: .Config}'
    fi
}

# Main function
main() {
    case "${1:-help}" in
        "build")
            check_prerequisites
            build_images "${2:-latest}" "${3:-}"
            ;;
        "scan")
            check_prerequisites
            scan_images "${2:-latest}"
            generate_vulnerability_report
            ;;
        "sign")
            check_prerequisites
            sign_images "${2:-latest}"
            ;;
        "push")
            check_prerequisites
            push_images "${2:-latest}"
            ;;
        "deploy")
            check_prerequisites
            build_images "${2:-latest}" "${3:-}"
            scan_images "${2:-latest}"
            sign_images "${2:-latest}"
            push_images "${2:-latest}"
            generate_vulnerability_report
            ;;
        "list")
            list_images "${2:-}"
            ;;
        "cleanup")
            cleanup_images "${2:-10}"
            ;;
        "health")
            health_check
            ;;
        "info")
            show_image_info "${2:-}" "${3:-latest}"
            ;;
        "help"|*)
            echo "Deep Echo Container Registry Management"
            echo "======================================"
            echo
            echo "Usage: $0 <command> [options]"
            echo
            echo "Commands:"
            echo "  build [tag] [build_args]   - Build container images"
            echo "  scan [tag]                 - Scan images for vulnerabilities"
            echo "  sign [tag]                 - Sign images with cosign"
            echo "  push [tag]                 - Push images to registry"
            echo "  deploy [tag] [build_args]  - Full build, scan, sign, and push pipeline"
            echo "  list [image_name]          - List image versions"
            echo "  cleanup [keep_count]       - Clean up old images (default: keep 10)"
            echo "  health                     - Check registry health"
            echo "  info [image_name] [tag]    - Show detailed image information"
            echo "  help                       - Show this help message"
            echo
            echo "Environment Variables:"
            echo "  REGISTRY      - Container registry URL (default: ghcr.io)"
            echo "  NAMESPACE     - Registry namespace (default: echocog)"
            echo "  PROJECT       - Project name (default: deep-tree-echo-rkwv)"
            echo "  GITHUB_TOKEN  - GitHub token for authentication"
            echo "  GITHUB_ACTOR  - GitHub username for authentication"
            echo
            echo "Examples:"
            echo "  $0 build v1.2.0"
            echo "  $0 deploy latest --no-cache"
            echo "  $0 list main"
            echo "  $0 cleanup 5"
            ;;
    esac
}

# Run main function
main "$@"