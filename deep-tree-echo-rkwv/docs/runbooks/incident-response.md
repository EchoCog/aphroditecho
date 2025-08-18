# Deep Echo Incident Response Runbook

## Overview

This runbook provides step-by-step procedures for responding to incidents in the Deep Tree Echo WebVM-RWKV system.

## Incident Severity Levels

### Critical (P0)
- Complete system outage
- Data loss or corruption
- Security breach
- Response time: **15 minutes**

### High (P1)
- Major feature unavailable
- Significant performance degradation
- Response time: **1 hour**

### Medium (P2)
- Minor feature unavailable
- Moderate performance issues
- Response time: **4 hours**

### Low (P3)
- Cosmetic issues
- Enhancement requests
- Response time: **24 hours**

## Initial Response Checklist

1. **Acknowledge the incident** (within 5 minutes)
2. **Assess severity** using the levels above
3. **Notify stakeholders** based on severity
4. **Create incident channel** (#incident-YYYY-MM-DD-HH-MM)
5. **Start incident timeline** in shared document
6. **Begin investigation** using this runbook

## Common Incident Scenarios

### 1. Application Not Responding

**Symptoms:**
- HTTP 5xx errors
- Timeouts
- Health checks failing

**Investigation Steps:**
```bash
# Check application health
curl -f http://localhost:8000/api/status

# Check container status
docker ps --filter "name=deep-echo"

# Check container logs
docker compose logs --tail=100 main-app

# Check system resources
docker stats --no-stream

# Check load balancer status
curl http://localhost:8000/health
```

**Resolution Steps:**
1. **Restart application containers:**
   ```bash
   docker compose restart main-app
   ```

2. **If restart fails, check resource constraints:**
   ```bash
   # Check memory usage
   free -h
   
   # Check disk space
   df -h
   
   # Check CPU usage
   top -bn1 | head -20
   ```

3. **Scale up if resource constrained:**
   ```bash
   docker compose up --scale cognitive-service=5 -d
   ```

4. **Check for recent deployments:**
   ```bash
   git log --oneline -10
   docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
   ```

### 2. Database Connection Issues

**Symptoms:**
- Database connection errors
- Slow queries
- Connection pool exhaustion

**Investigation Steps:**
```bash
# Check database connectivity
docker exec deep-echo-postgres pg_isready

# Check database logs
docker compose logs postgres --tail=100

# Check active connections
docker exec deep-echo-postgres psql -U deepecho -c "SELECT count(*) FROM pg_stat_activity;"

# Check for long-running queries
docker exec deep-echo-postgres psql -U deepecho -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

**Resolution Steps:**
1. **Restart database if safe:**
   ```bash
   docker compose restart postgres
   ```

2. **Kill long-running queries:**
   ```bash
   docker exec deep-echo-postgres psql -U deepecho -c "SELECT pg_terminate_backend(PID);"
   ```

3. **Scale connection pool:**
   - Update `max_connections` in PostgreSQL config
   - Restart database service

### 3. Redis Connection Issues

**Symptoms:**
- Cache misses
- Session issues
- Redis connection errors

**Investigation Steps:**
```bash
# Check Redis connectivity
redis-cli ping

# Check Redis memory usage
redis-cli info memory

# Check connected clients
redis-cli info clients

# Check for Redis errors
docker compose logs redis --tail=100
```

**Resolution Steps:**
1. **Restart Redis:**
   ```bash
   docker compose restart redis
   ```

2. **Clear Redis if corrupted:**
   ```bash
   redis-cli flushall
   ```

3. **Check Redis configuration:**
   ```bash
   redis-cli config get maxmemory
   redis-cli config get maxmemory-policy
   ```

### 4. High CPU/Memory Usage

**Symptoms:**
- Slow response times
- Container restarts
- Resource alerts

**Investigation Steps:**
```bash
# Check container resource usage
docker stats --no-stream

# Check system load
uptime
htop

# Check memory usage per container
docker exec deep-echo-main ps aux --sort=-%mem | head -10

# Check for memory leaks
docker exec deep-echo-main cat /proc/meminfo
```

**Resolution Steps:**
1. **Scale horizontally:**
   ```bash
   docker compose up --scale cognitive-service=5 -d
   ```

2. **Restart memory-intensive services:**
   ```bash
   docker compose restart cognitive-service-1 cognitive-service-2
   ```

3. **Enable resource limits:**
   - Update docker-compose.yml with resource limits
   - Restart services

### 5. Load Balancer Issues

**Symptoms:**
- Uneven load distribution
- Backend health check failures
- 502/503 errors

**Investigation Steps:**
```bash
# Check load balancer status
curl http://localhost:8000/health

# Check backend health
curl http://localhost:8001/health  # cognitive-service-1
curl http://localhost:8003/health  # cognitive-service-2

# Check load balancer logs
docker compose logs load-balancer --tail=100
```

**Resolution Steps:**
1. **Restart load balancer:**
   ```bash
   docker compose restart load-balancer
   ```

2. **Remove unhealthy backends:**
   ```bash
   # Restart problematic backend services
   docker compose restart cognitive-service-1
   ```

3. **Check service discovery:**
   - Verify service registration
   - Check DNS resolution

## Escalation Procedures

### When to Escalate

- **Unable to resolve within SLA time**
- **Requires infrastructure changes**
- **Security implications**
- **Data integrity concerns**

### Escalation Contacts

1. **On-call Engineer**: +1-XXX-XXX-XXXX
2. **Engineering Manager**: manager@company.com
3. **Infrastructure Team**: infra-team@company.com
4. **Security Team**: security@company.com

## Post-Incident Procedures

### 1. Service Restoration
- Verify all systems are operational
- Run health checks and smoke tests
- Monitor for 30 minutes post-resolution

### 2. Communication
- Update status page
- Notify stakeholders of resolution
- Close incident channel

### 3. Post-Mortem (for P0/P1 incidents)
- Schedule post-mortem meeting within 48 hours
- Document timeline and root cause
- Identify action items and owners
- Update runbooks based on learnings

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-call Engineer | John Doe | +1-555-0001 | john@company.com |
| Engineering Manager | Jane Smith | +1-555-0002 | jane@company.com |
| Infrastructure Lead | Bob Johnson | +1-555-0003 | bob@company.com |
| Security Lead | Alice Brown | +1-555-0004 | alice@company.com |

## Monitoring and Alerting

### Key Dashboards
- **Main Dashboard**: http://localhost:3000/d/main
- **Infrastructure**: http://localhost:3000/d/infrastructure
- **Application Metrics**: http://localhost:3000/d/application

### Alert Channels
- **#alerts-critical**: Critical alerts (P0)
- **#alerts-warning**: Warning alerts (P1/P2)
- **#alerts-info**: Informational alerts (P3)

## Useful Commands Reference

### Docker Commands
```bash
# View all containers
docker ps -a

# View container logs
docker compose logs [service-name] --tail=100 -f

# Restart service
docker compose restart [service-name]

# Scale service
docker compose up --scale [service-name]=3 -d

# Execute command in container
docker exec -it [container-name] bash

# View container resource usage
docker stats --no-stream [container-name]
```

### System Commands
```bash
# Check system resources
free -h
df -h
top -bn1

# Check network connectivity
netstat -tuln
ss -tuln

# Check process information
ps aux | grep [process-name]
pgrep -f [process-name]
```

### Database Commands
```bash
# Connect to PostgreSQL
docker exec -it deep-echo-postgres psql -U deepecho

# Check database size
SELECT pg_size_pretty(pg_database_size('deepecho'));

# View active connections
SELECT * FROM pg_stat_activity;

# Kill connection
SELECT pg_terminate_backend(pid);
```

### Redis Commands
```bash
# Connect to Redis
redis-cli

# Check memory usage
INFO memory

# Check connected clients
INFO clients

# Monitor commands
MONITOR

# Clear all data (use with caution)
FLUSHALL
```

## Recovery Procedures

### Quick Recovery Checklist
1. **Check service status**: `docker ps`
2. **Restart failed services**: `docker compose restart [service]`
3. **Check logs**: `docker compose logs [service] --tail=100`
4. **Verify connectivity**: `curl http://localhost:8000/api/status`
5. **Monitor metrics**: Check Grafana dashboards
6. **Test functionality**: Run smoke tests

### Full System Recovery
If complete system failure:

1. **Stop all services**: `docker compose down`
2. **Check system resources**: `free -h`, `df -h`
3. **Start infrastructure**: `docker compose up -d redis postgres`
4. **Start applications**: `docker compose up -d`
5. **Verify recovery**: Run full test suite
6. **Monitor stability**: Watch for 30 minutes

## Testing and Validation

### Health Check Endpoints
- **Main App**: `GET /api/status`
- **Load Balancer**: `GET /health`
- **Cognitive Service**: `GET /health`
- **Cache Service**: `GET /health`

### Smoke Tests
```bash
# Quick smoke test script
#!/bin/bash
echo "Running smoke tests..."

# Test main application
curl -f http://localhost:8000/api/status || echo "Main app failed"

# Test cognitive processing
curl -f -X POST http://localhost:8000/api/cognitive_process \
  -H "Content-Type: application/json" \
  -d '{"input": "test"}' || echo "Cognitive processing failed"

# Test caching
curl -f http://localhost:8002/health || echo "Cache service failed"

echo "Smoke tests completed"
```

## Documentation Updates

After each incident:
1. Update this runbook with new procedures
2. Document new failure modes
3. Add new monitoring requirements
4. Update contact information
5. Review and update escalation procedures

---

**Last Updated**: [Date]  
**Version**: 1.0  
**Owner**: Infrastructure Team