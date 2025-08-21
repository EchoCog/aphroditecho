# Deep Echo DevOps Documentation

## Overview

This document provides comprehensive guidance for the DevOps implementation of the Deep Tree Echo WebVM-RWKV cognitive architecture platform. The DevOps framework implements advanced deployment strategies, automation, and infrastructure management to ensure reliable, scalable, and maintainable operations.

## Architecture

### DevOps Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│ GitHub Actions → Build → Test → Security Scan → Deploy     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Container Registry                           │
├─────────────────────────────────────────────────────────────┤
│ GHCR.io → Image Scanning → Signing → Versioning           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure as Code                       │
├─────────────────────────────────────────────────────────────┤
│ Terraform → AWS EKS → VPC → RDS → ElastiCache             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Container Orchestration                      │
├─────────────────────────────────────────────────────────────┤
│ Kubernetes → Helm → Istio Service Mesh → Auto-scaling     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│             Monitoring & Observability                     │
├─────────────────────────────────────────────────────────────┤
│ Prometheus → Grafana → Jaeger → AlertManager → Logs       │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

1. **Required Tools**:
   ```bash
   # Install required tools
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
   ```

2. **AWS Configuration**:
   ```bash
   aws configure
   export AWS_REGION=us-west-2
   ```

3. **Environment Setup**:
   ```bash
   export ENVIRONMENT=dev
   export GITHUB_TOKEN=your_github_token
   ```

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/EchoCog/deep-tree-echo-rkwv.git
   cd deep-tree-echo-rkwv
   chmod +x devops.sh
   ```

2. **Create Development Environment**:
   ```bash
   ./devops.sh env create dev
   ```

3. **Deploy Application**:
   ```bash
   ./devops.sh cluster deploy dev
   ```

4. **Verify Deployment**:
   ```bash
   ./devops.sh health
   ```

## CI/CD Pipeline

### GitHub Actions Workflows

#### Main CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Stages**:

1. **Security Scanning**:
   - CodeQL analysis for source code
   - Dependency vulnerability scanning
   - SARIF result uploads

2. **Testing & Quality**:
   - Multi-version Python testing (3.9, 3.10, 3.11)
   - Code formatting checks with Black
   - Linting with flake8
   - Security scanning with Bandit
   - Test coverage reporting

3. **Container Building**:
   - Multi-architecture builds (amd64, arm64)
   - Image security scanning with Trivy
   - Container registry publishing to GHCR

4. **Performance Testing**:
   - Artillery load testing
   - Performance metrics collection
   - Report generation

5. **Deployment**:
   - Staging deployment (automatic on main)
   - Production deployment (manual approval required)

#### Rollback Workflow (`.github/workflows/rollback.yml`)

**Features**:
- Manual trigger with environment selection
- Version validation
- Automated rollback execution
- Post-rollback verification
- Incident documentation

**Usage**:
```bash
# Trigger rollback via GitHub Actions
# Select environment: staging/production
# Specify rollback version (commit SHA or tag)
# Provide rollback reason
```

### Local CI/CD Testing

```bash
# Build and test locally
docker compose -f docker-compose.yml -f docker-compose.test.yml up --build

# Run security scans
./infrastructure/registry/manage-registry.sh scan

# Performance testing
./infrastructure/testing/run-performance-tests.sh
```

## Infrastructure as Code

### Terraform Architecture

#### Module Structure

```
infrastructure/terraform/
├── main.tf                 # Root module
├── variables.tf           # Variable definitions
├── outputs.tf            # Output definitions
├── modules/              # Reusable modules
│   ├── vpc/             # VPC and networking
│   ├── eks/             # EKS cluster
│   ├── rds/             # PostgreSQL database
│   ├── redis/           # ElastiCache Redis
│   ├── alb/             # Application Load Balancer
│   ├── s3/              # S3 buckets
│   └── monitoring/      # CloudWatch resources
└── environments/        # Environment-specific configs
    ├── dev/
    ├── staging/
    └── production/
```

#### Environment Management

**Development Environment**:
```bash
# Plan changes
./devops.sh infra plan dev

# Apply changes
./devops.sh infra apply dev

# Show outputs
./devops.sh infra output dev
```

**Production Environment**:
```bash
# Plan with approval
./devops.sh infra plan production

# Apply with confirmation
./devops.sh infra apply production

# Destroy (emergency only)
./devops.sh infra destroy production
```

#### Key Resources

1. **VPC and Networking**:
   - Multi-AZ VPC with public/private subnets
   - NAT gateways for egress
   - Security groups with least privilege

2. **EKS Cluster**:
   - Managed Kubernetes cluster
   - Auto-scaling node groups
   - IRSA for pod-level permissions

3. **Data Layer**:
   - PostgreSQL RDS with automated backups
   - ElastiCache Redis for caching
   - S3 buckets for storage and backups

4. **Load Balancing**:
   - Application Load Balancer
   - Target groups with health checks
   - SSL/TLS termination

## Container Orchestration

### Kubernetes Deployment

#### Namespace Organization

```bash
# Default namespace for main application
kubectl get pods -n default

# Monitoring namespace
kubectl get pods -n monitoring

# Istio system namespace
kubectl get pods -n istio-system
```

#### Helm Charts

**Installation**:
```bash
# Deploy to development
helm upgrade --install deep-echo-dev ./infrastructure/helm/deep-echo \
  --namespace deep-echo-dev \
  --create-namespace \
  --values infrastructure/helm/deep-echo/values.yaml \
  --set environment=dev

# Deploy to production
helm upgrade --install deep-echo-prod ./infrastructure/helm/deep-echo \
  --namespace deep-echo-prod \
  --create-namespace \
  --values infrastructure/helm/deep-echo/values-prod.yaml \
  --set environment=production
```

**Configuration Management**:
- Environment-specific values files
- Secret management with Kubernetes secrets
- ConfigMaps for application configuration
- Resource limits and requests

#### Auto-scaling

**Horizontal Pod Autoscaler**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: deep-echo-cognitive-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deep-echo-cognitive
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Cluster Autoscaler**:
- Automatic node provisioning
- Scale down unused nodes
- Multiple instance types and zones

### Service Mesh (Istio)

#### Installation

```bash
# Install Istio
./devops.sh mesh install

# Configure for Deep Echo
./devops.sh mesh configure

# Verify installation
./devops.sh mesh verify
```

#### Features

1. **Traffic Management**:
   - Load balancing algorithms
   - Circuit breakers
   - Retry policies
   - Canary deployments

2. **Security**:
   - mTLS between services
   - Authorization policies
   - Certificate management

3. **Observability**:
   - Distributed tracing
   - Service metrics
   - Access logs

#### Traffic Policies

```yaml
# Circuit breaker configuration
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: deep-echo-cognitive-dr
spec:
  host: deep-echo-cognitive-svc
  trafficPolicy:
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 30
```

## Monitoring and Observability

### Monitoring Stack

#### Prometheus Configuration

**Metrics Collection**:
- Application metrics from `/metrics` endpoints
- Kubernetes cluster metrics
- Node and container metrics
- Custom business metrics

**Alert Rules**:
```yaml
# High response time alert
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m])) > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High response time in Deep Echo application"
```

#### Grafana Dashboards

**Access**:
```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Access at http://localhost:3000
# Username: admin
# Password: deepecho123
```

**Key Dashboards**:
- Application performance metrics
- Infrastructure resource usage
- Database and cache performance
- Error rates and service health

#### Distributed Tracing

**Jaeger Setup**:
```bash
# Access Jaeger UI
kubectl port-forward -n istio-system svc/tracing 16686:80

# View traces at http://localhost:16686
```

**Trace Collection**:
- Automatic trace collection via Istio
- Application-level instrumentation
- Performance bottleneck identification

### Log Aggregation

**ELK Stack Integration**:
```bash
# Deploy ELK stack
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -n monitoring
helm install kibana elastic/kibana -n monitoring
helm install filebeat elastic/filebeat -n monitoring
```

**Log Sources**:
- Application logs
- Container logs
- Kubernetes audit logs
- Infrastructure logs

## Backup and Disaster Recovery

### Automated Backup System

#### Backup Components

**Database Backup**:
```bash
# Create backup
./infrastructure/backup/backup.sh

# List backups
./devops.sh backup list

# Restore from backup
./devops.sh backup restore backup_name
```

**Backup Includes**:
- PostgreSQL database dump
- Redis data snapshot
- Application configuration
- Kubernetes manifests
- Terraform state

#### Disaster Recovery

**Recovery Procedures**:
```bash
# Interactive recovery
./infrastructure/backup/disaster-recovery.sh interactive

# Automated recovery from latest backup
./infrastructure/backup/disaster-recovery.sh latest

# Recovery from specific backup
./infrastructure/backup/disaster-recovery.sh auto backup_name
```

**RTO/RPO Targets**:
- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 1 hour
- **Backup Frequency**: Every 6 hours
- **Backup Retention**: 30 days local, 90 days S3

### Business Continuity

**Multi-Region Setup**:
- Primary region: us-west-2
- Backup region: us-east-1
- Cross-region data replication
- DNS failover configuration

## Security

### Container Security

#### Image Scanning

```bash
# Scan images for vulnerabilities
./infrastructure/registry/manage-registry.sh scan

# View vulnerability report
cat infrastructure/registry/scan-results/vulnerability_report_*.md
```

**Scanning Tools**:
- Trivy for comprehensive vulnerability scanning
- Docker scan for native Docker integration
- SARIF reporting for GitHub integration

#### Image Signing

```bash
# Sign images with Cosign
./infrastructure/registry/manage-registry.sh sign

# Verify signatures
cosign verify ghcr.io/echocog/deep-tree-echo-rkwv:latest
```

### Runtime Security

**Security Policies**:
- Pod Security Standards enforcement
- Network policies for traffic isolation
- RBAC for least privilege access
- Service mesh security policies

**Security Scanning**:
```bash
# Run security audit
./devops.sh security audit

# Apply security policies
./devops.sh security policies
```

## Chaos Engineering

### Chaos Testing Framework

#### Available Tests

```bash
# Container failure testing
./infrastructure/chaos/chaos-engineering.sh container-failure cognitive-service-1 60

# Network partition testing
./infrastructure/chaos/chaos-engineering.sh network-partition main-app 30

# Resource stress testing
./infrastructure/chaos/chaos-engineering.sh cpu-stress main-app 80 120

# Infrastructure failure testing
./infrastructure/chaos/chaos-engineering.sh redis-failure 60

# Comprehensive test suite
./infrastructure/chaos/chaos-engineering.sh suite
```

#### Test Scenarios

1. **Service Failure Tests**:
   - Container crashes and restarts
   - Service unavailability
   - Dependency failures

2. **Network Tests**:
   - Network partitions
   - Latency injection
   - Packet loss simulation

3. **Resource Tests**:
   - CPU exhaustion
   - Memory pressure
   - Disk space issues

4. **Infrastructure Tests**:
   - Database failures
   - Cache unavailability
   - Load balancer issues

### Chaos Results Analysis

**Report Generation**:
- Automated test reports in Markdown
- Metrics collection during tests
- Recovery time measurement
- System behavior analysis

## Performance Testing

### Load Testing Framework

#### Artillery Configuration

```bash
# Run performance tests
./infrastructure/testing/run-performance-tests.sh

# Custom target testing
./devops.sh performance http://staging.deepecho.ai
```

**Test Scenarios**:
- Baseline performance measurement
- Sustained load testing
- Peak load testing
- Cache performance testing
- Cognitive processing testing

#### Performance Metrics

**Key Performance Indicators**:
- Response time (target: <100ms average)
- Throughput (target: >1000 req/min)
- Error rate (target: <1%)
- Cache hit rate (target: >50%)
- Auto-scaling effectiveness

**Monitoring During Tests**:
- Real-time system metrics
- Application performance metrics
- Database and cache performance
- Network and disk I/O

## Operational Procedures

### Daily Operations

```bash
# Morning health check
./devops.sh health

# Check application status
./devops.sh cluster status

# Review monitoring dashboards
# Access Grafana at http://localhost:3000

# Check for alerts
# Review AlertManager notifications
```

### Incident Response

**Incident Severity Levels**:
- **P0 (Critical)**: Complete outage, response within 15 minutes
- **P1 (High)**: Major feature down, response within 1 hour
- **P2 (Medium)**: Minor issues, response within 4 hours
- **P3 (Low)**: Cosmetic issues, response within 24 hours

**Response Procedures**:
1. Follow incident response runbook (`docs/runbooks/incident-response.md`)
2. Create incident channel for communication
3. Investigate using monitoring tools
4. Apply fixes or escalate as needed
5. Document resolution and lessons learned

### Maintenance Windows

**Scheduled Maintenance**:
- **Development**: Anytime
- **Staging**: Daily 02:00-04:00 UTC
- **Production**: Sunday 04:00-06:00 UTC

**Maintenance Procedures**:
1. Announce maintenance window
2. Create maintenance backup
3. Apply updates/patches
4. Verify system functionality
5. Update documentation

## Troubleshooting

### Common Issues

#### Application Not Responding

```bash
# Check pod status
kubectl get pods -l app=deep-echo-main

# Check logs
kubectl logs -l app=deep-echo-main --tail=100

# Restart deployment
kubectl rollout restart deployment/deep-echo-main
```

#### Database Connection Issues

```bash
# Check database connectivity
kubectl exec -it deployment/deep-echo-main -- pg_isready -h database-host

# Check database logs
kubectl logs -l app=postgresql

# Restart database connection pool
kubectl rollout restart deployment/deep-echo-main
```

#### Performance Degradation

```bash
# Check resource usage
kubectl top pods
kubectl top nodes

# Scale up if needed
kubectl scale deployment/deep-echo-cognitive --replicas=10

# Check metrics
# Access Grafana dashboards for detailed analysis
```

### Debug Commands

```bash
# Get shell in running container
./devops.sh cluster exec dev main-app

# Port forward for local debugging
kubectl port-forward svc/deep-echo-main 8000:8000

# Check service mesh configuration
istioctl proxy-config cluster deep-echo-main-pod

# Analyze traffic routing
istioctl analyze
```

## Best Practices

### Development Workflow

1. **Feature Development**:
   - Create feature branch
   - Develop with local testing
   - Run security scans locally
   - Submit pull request

2. **Testing**:
   - Automated CI/CD pipeline runs
   - Deploy to development environment
   - Run integration tests
   - Performance testing

3. **Deployment**:
   - Deploy to staging for final validation
   - Manual approval for production
   - Blue-green deployment strategy
   - Post-deployment verification

### Security Best Practices

1. **Container Security**:
   - Use minimal base images
   - Run as non-root user
   - Scan for vulnerabilities
   - Sign images with Cosign

2. **Kubernetes Security**:
   - Enable Pod Security Standards
   - Use Network Policies
   - Implement RBAC
   - Regular security audits

3. **Infrastructure Security**:
   - Encrypt data at rest and in transit
   - Use AWS IAM roles
   - Enable CloudTrail logging
   - Regular access reviews

### Monitoring Best Practices

1. **Alerting**:
   - Define clear alert thresholds
   - Avoid alert fatigue
   - Document response procedures
   - Regular alert review

2. **Dashboards**:
   - Focus on key metrics
   - Use consistent visualization
   - Enable drill-down capabilities
   - Regular dashboard updates

3. **Logging**:
   - Structured logging format
   - Appropriate log levels
   - Log correlation IDs
   - Log retention policies

## Appendices

### A. Tool Installation Scripts

```bash
# Install all required tools
./scripts/install-devops-tools.sh

# Install specific tools
./scripts/install-terraform.sh
./scripts/install-kubectl.sh
./scripts/install-helm.sh
```

### B. Configuration Templates

- Environment variable templates
- Kubernetes secret templates
- Terraform variable files
- Helm values files

### C. Runbook References

- [Incident Response Runbook](docs/runbooks/incident-response.md)
- [Deployment Runbook](docs/runbooks/deployment.md)
- [Backup Runbook](docs/runbooks/backup.md)
- [Security Runbook](docs/runbooks/security.md)

### D. Contact Information

| Role | Name | Email | Phone |
|------|------|-------|-------|
| DevOps Lead | DevOps Team | devops@deepecho.ai | +1-555-DEVOPS |
| On-call Engineer | Rotation | oncall@deepecho.ai | +1-555-ONCALL |
| Security Team | Security | security@deepecho.ai | +1-555-SECURITY |

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Owner**: DevOps Team  
**Next Review**: [Date + 3 months]