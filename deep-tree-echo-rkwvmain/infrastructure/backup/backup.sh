#!/bin/bash

# Deep Echo Backup Script
# Automated backup system for the Deep Tree Echo application

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
S3_BUCKET="${S3_BUCKET:-deep-echo-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENVIRONMENT="${ENVIRONMENT:-production}"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-deepecho}"
DB_USER="${DB_USER:-deepecho}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Logging
LOG_FILE="/var/log/deep-echo-backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

# Create backup directory
create_backup_dir() {
    local backup_path="$BACKUP_DIR/$ENVIRONMENT/$TIMESTAMP"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# Backup PostgreSQL database
backup_database() {
    local backup_path="$1"
    local db_backup_file="$backup_path/database_backup.sql"
    
    log "Starting database backup..."
    
    # Use pg_dump with custom format for better compression and features
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="$db_backup_file" \
        || error "Database backup failed"
    
    # Create a plain SQL backup for easier inspection
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --file="$backup_path/database_backup_plain.sql" \
        || error "Plain database backup failed"
    
    log "Database backup completed: $db_backup_file"
    
    # Verify backup integrity
    pg_restore --list "$db_backup_file" > /dev/null || error "Database backup verification failed"
    log "Database backup verification successful"
}

# Backup Redis data
backup_redis() {
    local backup_path="$1"
    local redis_backup_file="$backup_path/redis_backup.rdb"
    
    log "Starting Redis backup..."
    
    # Create Redis backup using BGSAVE
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    
    # Wait for backup to complete
    while [ "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" = "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy the RDB file
    docker cp $(docker ps --filter "name=deep-echo-redis" --format "{{.ID}}"):/data/dump.rdb "$redis_backup_file" \
        || error "Redis backup failed"
    
    log "Redis backup completed: $redis_backup_file"
}

# Backup application configuration
backup_config() {
    local backup_path="$1"
    local config_backup_dir="$backup_path/config"
    
    log "Starting configuration backup..."
    
    mkdir -p "$config_backup_dir"
    
    # Backup environment files
    if [ -f ".env" ]; then
        cp .env "$config_backup_dir/"
    fi
    
    # Backup configuration files
    if [ -d "config" ]; then
        cp -r config/* "$config_backup_dir/"
    fi
    
    # Backup Docker Compose files
    cp docker-compose.yml "$config_backup_dir/" || true
    cp docker-compose.override.yml "$config_backup_dir/" 2>/dev/null || true
    
    # Backup Kubernetes manifests
    if [ -d "infrastructure/kubernetes" ]; then
        cp -r infrastructure/kubernetes "$config_backup_dir/"
    fi
    
    # Backup Terraform state (if exists)
    if [ -f "infrastructure/terraform/terraform.tfstate" ]; then
        cp infrastructure/terraform/terraform.tfstate "$config_backup_dir/"
    fi
    
    log "Configuration backup completed: $config_backup_dir"
}

# Backup application logs
backup_logs() {
    local backup_path="$1"
    local logs_backup_dir="$backup_path/logs"
    
    log "Starting logs backup..."
    
    mkdir -p "$logs_backup_dir"
    
    # Backup application logs
    if [ -d "logs" ]; then
        cp -r logs/* "$logs_backup_dir/" || true
    fi
    
    # Export container logs
    docker compose logs --no-color > "$logs_backup_dir/container_logs.txt" 2>/dev/null || true
    
    log "Logs backup completed: $logs_backup_dir"
}

# Create backup metadata
create_metadata() {
    local backup_path="$1"
    local metadata_file="$backup_path/backup_metadata.json"
    
    log "Creating backup metadata..."
    
    cat > "$metadata_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "environment": "$ENVIRONMENT",
    "backup_type": "full",
    "components": [
        "database",
        "redis",
        "configuration",
        "logs"
    ],
    "database": {
        "host": "$DB_HOST",
        "port": "$DB_PORT",
        "name": "$DB_NAME"
    },
    "redis": {
        "host": "$REDIS_HOST",
        "port": "$REDIS_PORT"
    },
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "size_bytes": $(du -sb "$backup_path" | cut -f1)
}
EOF
    
    log "Backup metadata created: $metadata_file"
}

# Compress backup
compress_backup() {
    local backup_path="$1"
    local compressed_file="$backup_path.tar.gz"
    
    log "Compressing backup..."
    
    tar -czf "$compressed_file" -C "$(dirname "$backup_path")" "$(basename "$backup_path")" \
        || error "Backup compression failed"
    
    # Remove uncompressed directory
    rm -rf "$backup_path"
    
    log "Backup compressed: $compressed_file"
    echo "$compressed_file"
}

# Upload to S3
upload_to_s3() {
    local backup_file="$1"
    local s3_key="$ENVIRONMENT/$(basename "$backup_file")"
    
    log "Uploading backup to S3..."
    
    aws s3 cp "$backup_file" "s3://$S3_BUCKET/$s3_key" \
        --storage-class STANDARD_IA \
        || error "S3 upload failed"
    
    log "Backup uploaded to S3: s3://$S3_BUCKET/$s3_key"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Clean local backups
    find "$BACKUP_DIR/$ENVIRONMENT" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete || true
    
    # Clean S3 backups
    aws s3 ls "s3://$S3_BUCKET/$ENVIRONMENT/" | while read -r line; do
        createDate=$(echo "$line" | awk '{print $1" "$2}')
        createDate=$(date -d "$createDate" +%s)
        olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
        
        if [[ $createDate -lt $olderThan ]]; then
            fileName=$(echo "$line" | awk '{print $4}')
            aws s3 rm "s3://$S3_BUCKET/$ENVIRONMENT/$fileName"
            log "Deleted old backup: $fileName"
        fi
    done
}

# Test backup restore (verification)
test_restore() {
    local backup_file="$1"
    
    log "Testing backup restore capability..."
    
    # This is a basic test - in production, you might want to restore to a test environment
    local test_dir="/tmp/backup_test_$TIMESTAMP"
    mkdir -p "$test_dir"
    
    # Extract backup
    tar -xzf "$backup_file" -C "$test_dir" || error "Backup extraction test failed"
    
    # Verify files exist
    local extracted_dir="$test_dir/$(basename "$backup_file" .tar.gz)"
    [ -f "$extracted_dir/database_backup.sql" ] || error "Database backup file missing"
    [ -f "$extracted_dir/backup_metadata.json" ] || error "Metadata file missing"
    
    # Cleanup test
    rm -rf "$test_dir"
    
    log "Backup restore test passed"
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Send notification via webhook (customize as needed)
    if [ -n "${WEBHOOK_URL:-}" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"Deep Echo Backup $status: $message\"}" \
            || log "Failed to send notification"
    fi
    
    # Log notification
    log "Notification sent: $status - $message"
}

# Main backup function
main() {
    log "Starting Deep Echo backup process..."
    
    # Check prerequisites
    command -v pg_dump >/dev/null 2>&1 || error "pg_dump not found"
    command -v redis-cli >/dev/null 2>&1 || error "redis-cli not found"
    command -v aws >/dev/null 2>&1 || error "aws cli not found"
    
    local backup_path
    backup_path=$(create_backup_dir)
    
    # Perform backups
    backup_database "$backup_path"
    backup_redis "$backup_path"
    backup_config "$backup_path"
    backup_logs "$backup_path"
    create_metadata "$backup_path"
    
    # Compress and upload
    local compressed_file
    compressed_file=$(compress_backup "$backup_path")
    
    # Test restore capability
    test_restore "$compressed_file"
    
    # Upload to S3
    upload_to_s3 "$compressed_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send success notification
    send_notification "SUCCESS" "Backup completed successfully at $TIMESTAMP"
    
    log "Backup process completed successfully"
}

# Error handling
trap 'send_notification "FAILED" "Backup process failed"; exit 1' ERR

# Run main function
main "$@"