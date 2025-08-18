#!/bin/bash

# Deep Echo Disaster Recovery Script
# Automated disaster recovery system for the Deep Tree Echo application

set -euo pipefail

# Configuration
S3_BUCKET="${S3_BUCKET:-deep-echo-backups}"
ENVIRONMENT="${ENVIRONMENT:-production}"
RECOVERY_DIR="${RECOVERY_DIR:-/recovery}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-deepecho}"
DB_USER="${DB_USER:-deepecho}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Logging
LOG_FILE="/var/log/deep-echo-recovery.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

# List available backups
list_backups() {
    log "Listing available backups..."
    
    aws s3 ls "s3://$S3_BUCKET/$ENVIRONMENT/" --recursive | \
        grep "\.tar\.gz$" | \
        sort -k1,2 -r | \
        head -20
}

# Download backup from S3
download_backup() {
    local backup_name="$1"
    local download_path="$RECOVERY_DIR/$backup_name"
    
    log "Downloading backup: $backup_name"
    
    mkdir -p "$(dirname "$download_path")"
    
    aws s3 cp "s3://$S3_BUCKET/$ENVIRONMENT/$backup_name" "$download_path" \
        || error "Failed to download backup"
    
    log "Backup downloaded to: $download_path"
    echo "$download_path"
}

# Extract backup
extract_backup() {
    local backup_file="$1"
    local extract_dir="$RECOVERY_DIR/extracted_$(basename "$backup_file" .tar.gz)"
    
    log "Extracting backup..."
    
    mkdir -p "$extract_dir"
    tar -xzf "$backup_file" -C "$extract_dir" --strip-components=1 \
        || error "Failed to extract backup"
    
    log "Backup extracted to: $extract_dir"
    echo "$extract_dir"
}

# Validate backup integrity
validate_backup() {
    local backup_dir="$1"
    
    log "Validating backup integrity..."
    
    # Check required files exist
    [ -f "$backup_dir/backup_metadata.json" ] || error "Metadata file missing"
    [ -f "$backup_dir/database_backup.sql" ] || error "Database backup missing"
    
    # Validate metadata
    local backup_type=$(jq -r '.backup_type' "$backup_dir/backup_metadata.json" 2>/dev/null || echo "unknown")
    [ "$backup_type" = "full" ] || log "Warning: Backup type is $backup_type, not full"
    
    # Check database backup integrity if possible
    if command -v pg_restore >/dev/null 2>&1; then
        pg_restore --list "$backup_dir/database_backup.sql" > /dev/null 2>&1 \
            || error "Database backup is corrupted"
    fi
    
    log "Backup validation completed successfully"
}

# Stop services
stop_services() {
    log "Stopping Deep Echo services..."
    
    # Stop Docker Compose services
    if [ -f "docker-compose.yml" ]; then
        docker compose down || log "Warning: Failed to stop some services"
    fi
    
    # Stop Kubernetes services if kubectl is available
    if command -v kubectl >/dev/null 2>&1; then
        kubectl scale deployment --all --replicas=0 -n deep-echo 2>/dev/null || log "Warning: Failed to scale down Kubernetes deployments"
    fi
    
    log "Services stopped"
}

# Backup current state before recovery
backup_current_state() {
    log "Creating backup of current state before recovery..."
    
    local pre_recovery_backup="$RECOVERY_DIR/pre_recovery_backup_$TIMESTAMP"
    mkdir -p "$pre_recovery_backup"
    
    # Backup current database if accessible
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" 2>/dev/null; then
        log "Backing up current database..."
        PGPASSWORD="$DB_PASSWORD" pg_dump \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --format=custom \
            --file="$pre_recovery_backup/current_database.sql" \
            || log "Warning: Failed to backup current database"
    fi
    
    # Backup current configuration
    if [ -d "config" ]; then
        cp -r config "$pre_recovery_backup/" || log "Warning: Failed to backup config"
    fi
    
    log "Current state backed up to: $pre_recovery_backup"
}

# Restore database
restore_database() {
    local backup_dir="$1"
    local db_backup_file="$backup_dir/database_backup.sql"
    
    log "Restoring database from backup..."
    
    # Wait for database to be ready
    local retries=30
    while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" && [ $retries -gt 0 ]; do
        log "Waiting for database to be ready... ($retries retries left)"
        sleep 10
        ((retries--))
    done
    
    [ $retries -gt 0 ] || error "Database is not accessible"
    
    # Drop existing database and recreate (DANGEROUS - use with caution)
    if [ "${FORCE_RESTORE:-false}" = "true" ]; then
        log "Force restore enabled - dropping existing database"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true
    fi
    
    # Restore database
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --if-exists \
        --verbose \
        "$db_backup_file" \
        || error "Database restore failed"
    
    log "Database restore completed"
}

# Restore Redis
restore_redis() {
    local backup_dir="$1"
    local redis_backup_file="$backup_dir/redis_backup.rdb"
    
    if [ ! -f "$redis_backup_file" ]; then
        log "No Redis backup found, skipping Redis restore"
        return
    fi
    
    log "Restoring Redis from backup..."
    
    # Stop Redis temporarily
    docker compose stop redis || log "Warning: Failed to stop Redis"
    
    # Replace Redis data file
    docker cp "$redis_backup_file" $(docker ps -aq --filter "name=deep-echo-redis"):/data/dump.rdb \
        || log "Warning: Failed to restore Redis backup"
    
    # Start Redis
    docker compose start redis || error "Failed to start Redis"
    
    # Wait for Redis to be ready
    local retries=30
    while ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1 && [ $retries -gt 0 ]; do
        log "Waiting for Redis to be ready... ($retries retries left)"
        sleep 5
        ((retries--))
    done
    
    log "Redis restore completed"
}

# Restore configuration
restore_configuration() {
    local backup_dir="$1"
    local config_backup_dir="$backup_dir/config"
    
    if [ ! -d "$config_backup_dir" ]; then
        log "No configuration backup found, skipping configuration restore"
        return
    fi
    
    log "Restoring configuration from backup..."
    
    # Backup current config
    if [ -d "config" ]; then
        mv config "config.backup.$TIMESTAMP" || log "Warning: Failed to backup current config"
    fi
    
    # Restore configuration
    cp -r "$config_backup_dir" . || error "Configuration restore failed"
    
    # Restore environment file
    if [ -f "$config_backup_dir/.env" ]; then
        cp "$config_backup_dir/.env" . || log "Warning: Failed to restore .env file"
    fi
    
    log "Configuration restore completed"
}

# Start services
start_services() {
    log "Starting Deep Echo services..."
    
    # Start Docker Compose services
    if [ -f "docker-compose.yml" ]; then
        docker compose up -d || error "Failed to start services"
    fi
    
    # Scale up Kubernetes services if kubectl is available
    if command -v kubectl >/dev/null 2>&1; then
        kubectl scale deployment --all --replicas=3 -n deep-echo 2>/dev/null || log "Warning: Failed to scale up Kubernetes deployments"
    fi
    
    log "Services started"
}

# Verify recovery
verify_recovery() {
    log "Verifying recovery..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Verification attempt $attempt of $max_attempts"
        
        # Check main application health
        if curl -f http://localhost:8000/api/status >/dev/null 2>&1; then
            log "Main application is responding"
            
            # Check database connectivity
            if curl -f http://localhost:8000/api/health/database >/dev/null 2>&1; then
                log "Database connectivity verified"
                
                # Check Redis connectivity
                if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
                    log "Redis connectivity verified"
                    log "Recovery verification completed successfully"
                    return 0
                fi
            fi
        fi
        
        sleep 10
        ((attempt++))
    done
    
    error "Recovery verification failed - services are not responding correctly"
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Send notification via webhook (customize as needed)
    if [ -n "${WEBHOOK_URL:-}" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"Deep Echo Recovery $status: $message\"}" \
            || log "Failed to send notification"
    fi
    
    log "Notification sent: $status - $message"
}

# Interactive recovery
interactive_recovery() {
    echo "Deep Echo Disaster Recovery Tool"
    echo "================================="
    echo
    
    # List available backups
    echo "Available backups:"
    list_backups
    echo
    
    # Get backup selection
    read -p "Enter backup filename to restore (or 'latest' for most recent): " backup_choice
    
    if [ "$backup_choice" = "latest" ]; then
        backup_choice=$(aws s3 ls "s3://$S3_BUCKET/$ENVIRONMENT/" --recursive | \
            grep "\.tar\.gz$" | \
            sort -k1,2 -r | \
            head -1 | \
            awk '{print $4}')
        echo "Selected latest backup: $backup_choice"
    fi
    
    # Confirm recovery
    echo
    echo "WARNING: This will replace the current system with the backup!"
    echo "Current data will be backed up before restoration."
    echo
    read -p "Are you sure you want to proceed? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Recovery cancelled"
        exit 0
    fi
    
    # Perform recovery
    perform_recovery "$backup_choice"
}

# Automated recovery
perform_recovery() {
    local backup_name="$1"
    
    log "Starting disaster recovery process..."
    send_notification "STARTED" "Disaster recovery started for backup: $backup_name"
    
    # Download and extract backup
    local backup_file
    backup_file=$(download_backup "$backup_name")
    
    local backup_dir
    backup_dir=$(extract_backup "$backup_file")
    
    # Validate backup
    validate_backup "$backup_dir"
    
    # Stop services and backup current state
    stop_services
    backup_current_state
    
    # Restore components
    restore_database "$backup_dir"
    restore_redis "$backup_dir"
    restore_configuration "$backup_dir"
    
    # Start services and verify
    start_services
    sleep 30  # Give services time to start
    verify_recovery
    
    # Cleanup
    rm -rf "$backup_dir" "$backup_file"
    
    send_notification "SUCCESS" "Disaster recovery completed successfully"
    log "Disaster recovery process completed successfully"
}

# Main function
main() {
    case "${1:-interactive}" in
        "interactive")
            interactive_recovery
            ;;
        "auto")
            if [ -z "${2:-}" ]; then
                error "Backup name required for automated recovery"
            fi
            perform_recovery "$2"
            ;;
        "latest")
            local latest_backup=$(aws s3 ls "s3://$S3_BUCKET/$ENVIRONMENT/" --recursive | \
                grep "\.tar\.gz$" | \
                sort -k1,2 -r | \
                head -1 | \
                awk '{print $4}')
            perform_recovery "$latest_backup"
            ;;
        "list")
            list_backups
            ;;
        *)
            echo "Usage: $0 [interactive|auto <backup_name>|latest|list]"
            echo
            echo "  interactive  - Interactive recovery mode (default)"
            echo "  auto         - Automated recovery with specified backup"
            echo "  latest       - Recover from the latest backup"
            echo "  list         - List available backups"
            exit 1
            ;;
    esac
}

# Error handling
trap 'send_notification "FAILED" "Disaster recovery failed"; exit 1' ERR

# Check prerequisites
command -v aws >/dev/null 2>&1 || error "aws cli not found"
command -v jq >/dev/null 2>&1 || error "jq not found"

# Run main function
main "$@"