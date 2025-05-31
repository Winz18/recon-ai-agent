# Docker Deployment Guide

This document provides detailed instructions for deploying and managing the Recon AI-Agent using Docker in various environments.

## Table of Contents

- [Overview](#overview)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [Container Orchestration](#container-orchestration)
- [Security Hardening](#security-hardening)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Overview

The Recon AI-Agent Docker implementation provides:

- **Multi-platform support**: Linux, Windows, macOS
- **Isolated environment**: No host system dependencies
- **Consistent execution**: Same environment across all deployments
- **Security**: Non-root user execution and minimal attack surface
- **Scalability**: Easy horizontal scaling with container orchestration

## Development Environment

### Local Development Setup

1. **Clone and Build**
   ```bash
   git clone <repository-url>
   cd recon-ai-agent
   make build
   ```

2. **Development Configuration**
   ```bash
   # Create development environment file
   cp .env.example .env.dev
   
   # Edit with your development credentials
   GOOGLE_PROJECT_ID=dev-project-id
   GOOGLE_REGION=us-central1
   TARGET_DOMAIN=testdomain.local
   DEBUG=true
   ```

3. **Run Development Container**
   ```bash
   # Interactive development shell
   make dev-shell
   
   # Run with development settings
   docker run --rm -it \
     --env-file .env.dev \
     -v $(pwd):/app \
     -v $(pwd)/reports:/app/reports \
     recon-ai-agent \
     /bin/bash
   ```

### Hot Reloading for Development

```bash
# Mount source code for live editing
docker run --rm -it \
  --env-file .env.dev \
  -v $(pwd)/agents:/app/agents \
  -v $(pwd)/tools:/app/tools \
  -v $(pwd)/workflows:/app/workflows \
  -v $(pwd)/reports:/app/reports \
  recon-ai-agent \
  python main.py -d example.com --debug
```

## Production Deployment

### Single Server Deployment

#### 1. Environment Preparation

```bash
# Create production directory structure
mkdir -p /opt/recon-ai-agent/{config,credentials,reports,cache,logs}

# Set proper permissions
chown -R 1000:1000 /opt/recon-ai-agent
chmod 750 /opt/recon-ai-agent
```

#### 2. Production Configuration

Create `/opt/recon-ai-agent/config/.env.prod`:
```env
GOOGLE_PROJECT_ID=production-project-id
GOOGLE_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/recon-agent.log

# Performance
MAX_CONCURRENT_SCANS=3
CACHE_TTL=3600

# Security
SCAN_TIMEOUT=1800
RATE_LIMIT_PER_MINUTE=60
```

#### 3. Service Account Setup

```bash
# Copy service account key
cp service-account.json /opt/recon-ai-agent/credentials/
chmod 600 /opt/recon-ai-agent/credentials/service-account.json
```

#### 4. Docker Production Run

```bash
docker run -d \
  --name recon-ai-agent-prod \
  --restart unless-stopped \
  --env-file /opt/recon-ai-agent/config/.env.prod \
  -v /opt/recon-ai-agent/reports:/app/reports \
  -v /opt/recon-ai-agent/cache:/app/cache \
  -v /opt/recon-ai-agent/credentials:/app/credentials:ro \
  -v /opt/recon-ai-agent/logs:/app/logs \
  --memory="2g" \
  --cpus="1.0" \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  recon-ai-agent:latest \
  python main.py -d target-domain.com -w comprehensive
```

### Multi-Instance Deployment

For handling multiple concurrent scans:

```bash
# Start multiple instances with different target domains
for i in {1..3}; do
  docker run -d \
    --name recon-ai-agent-worker-$i \
    --restart unless-stopped \
    --env-file /opt/recon-ai-agent/config/.env.prod \
    -v /opt/recon-ai-agent/reports:/app/reports \
    -v /opt/recon-ai-agent/cache:/app/cache \
    -v /opt/recon-ai-agent/credentials:/app/credentials:ro \
    --memory="1.5g" \
    --cpus="0.5" \
    recon-ai-agent:latest \
    /bin/bash -c "while true; do sleep 30; done"
done
```

## Container Orchestration

### Docker Swarm Deployment

1. **Initialize Swarm**
   ```bash
   docker swarm init
   ```

2. **Create Stack Configuration** (`docker-stack.yml`):
   ```yaml
   version: '3.8'
   
   services:
     recon-ai-agent:
       image: recon-ai-agent:latest
       deploy:
         replicas: 3
         restart_policy:
           condition: on-failure
           delay: 5s
           max_attempts: 3
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
           reservations:
             memory: 512M
             cpus: '0.25'
       environment:
         - GOOGLE_PROJECT_ID_FILE=/run/secrets/google_project_id
         - GOOGLE_REGION=us-central1
       secrets:
         - google_project_id
         - service_account_key
       volumes:
         - reports:/app/reports
         - cache:/app/cache
       networks:
         - recon-network
   
     redis:
       image: redis:7-alpine
       deploy:
         replicas: 1
         placement:
           constraints:
             - node.role == manager
       volumes:
         - redis-data:/data
       networks:
         - recon-network
   
   secrets:
     google_project_id:
       external: true
     service_account_key:
       external: true
   
   volumes:
     reports:
       driver: local
     cache:
       driver: local
     redis-data:
       driver: local
   
   networks:
     recon-network:
       driver: overlay
       attachable: true
   ```

3. **Deploy Stack**
   ```bash
   # Create secrets
   echo "your-project-id" | docker secret create google_project_id -
   docker secret create service_account_key service-account.json
   
   # Deploy stack
   docker stack deploy -c docker-stack.yml recon-stack
   ```

### Kubernetes Deployment

1. **Namespace and ConfigMap**
   ```yaml
   # k8s/namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: recon-ai-agent
   
   ---
   # k8s/configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: recon-config
     namespace: recon-ai-agent
   data:
     GOOGLE_REGION: "us-central1"
     LOG_LEVEL: "INFO"
   ```

2. **Secret for Credentials**
   ```yaml
   # k8s/secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: recon-credentials
     namespace: recon-ai-agent
   type: Opaque
   data:
     service-account.json: <base64-encoded-service-account-key>
     google-project-id: <base64-encoded-project-id>
   ```

3. **Deployment**
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: recon-ai-agent
     namespace: recon-ai-agent
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: recon-ai-agent
     template:
       metadata:
         labels:
           app: recon-ai-agent
       spec:
         serviceAccountName: recon-service-account
         containers:
         - name: recon-ai-agent
           image: recon-ai-agent:latest
           env:
           - name: GOOGLE_PROJECT_ID
             valueFrom:
               secretKeyRef:
                 name: recon-credentials
                 key: google-project-id
           - name: GOOGLE_APPLICATION_CREDENTIALS
             value: "/etc/gcp/service-account.json"
           envFrom:
           - configMapRef:
               name: recon-config
           volumeMounts:
           - name: gcp-credentials
             mountPath: "/etc/gcp"
             readOnly: true
           - name: reports
             mountPath: "/app/reports"
           resources:
             requests:
               memory: "512Mi"
               cpu: "250m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           securityContext:
             runAsNonRoot: true
             runAsUser: 1000
             allowPrivilegeEscalation: false
             readOnlyRootFilesystem: true
         volumes:
         - name: gcp-credentials
           secret:
             secretName: recon-credentials
             items:
             - key: service-account.json
               path: service-account.json
         - name: reports
           persistentVolumeClaim:
             claimName: recon-reports-pvc
   ```

4. **Persistent Volume Claim**
   ```yaml
   # k8s/pvc.yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: recon-reports-pvc
     namespace: recon-ai-agent
   spec:
     accessModes:
       - ReadWriteMany
     resources:
       requests:
         storage: 10Gi
     storageClassName: standard
   ```

## Security Hardening

### Container Security

1. **Multi-stage Build for Production**
   ```dockerfile
   # Dockerfile.prod
   FROM python:3.12-slim as builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   FROM python:3.12-slim as runtime
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   WORKDIR /app
   
   # Copy only necessary files
   COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
   COPY --chown=appuser:appuser . .
   
   # Remove unnecessary packages
   RUN apt-get remove -y gcc g++ make && \
       apt-get autoremove -y && \
       rm -rf /var/lib/apt/lists/*
   
   USER appuser
   CMD ["python", "main.py", "--help"]
   ```

2. **Security Scanning**
   ```bash
   # Scan for vulnerabilities
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     -v $HOME/Library/Caches:/root/.cache/ \
     aquasec/trivy image recon-ai-agent:latest
   
   # Security best practices check
   docker run --rm -i hadolint/hadolint < Dockerfile
   ```

### Network Security

1. **Custom Bridge Network**
   ```bash
   # Create isolated network
   docker network create \
     --driver bridge \
     --subnet=172.20.0.0/16 \
     --ip-range=172.20.240.0/20 \
     recon-isolated
   
   # Run container in isolated network
   docker run --network recon-isolated recon-ai-agent
   ```

2. **Firewall Rules**
   ```bash
   # Allow only necessary outbound connections
   iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
   iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT   # DNS
   iptables -A OUTPUT -p udp --dport 53 -j ACCEPT   # DNS
   iptables -A OUTPUT -j DROP                       # Drop all other
   ```

## Monitoring and Logging

### Container Monitoring

1. **Health Checks**
   ```bash
   # Extended health check script
   docker run --rm \
     --health-cmd="python -c 'import main; print(\"healthy\")'" \
     --health-interval=30s \
     --health-timeout=10s \
     --health-retries=3 \
     recon-ai-agent
   ```

2. **Resource Monitoring**
   ```bash
   # Monitor container resource usage
   docker stats recon-ai-agent --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
   
   # Export metrics to file
   docker stats --no-stream --format "json" > container-stats.json
   ```

### Logging Configuration

1. **Centralized Logging**
   ```bash
   # Send logs to external system
   docker run -d \
     --log-driver=syslog \
     --log-opt syslog-address=tcp://log-server:514 \
     --log-opt tag="recon-ai-agent" \
     recon-ai-agent
   ```

2. **Log Rotation**
   ```bash
   # Configure log rotation
   docker run -d \
     --log-driver=json-file \
     --log-opt max-size=100m \
     --log-opt max-file=3 \
     recon-ai-agent
   ```

## Backup and Recovery

### Data Backup Strategy

1. **Volume Backup**
   ```bash
   # Backup reports and cache
   docker run --rm \
     -v recon_reports:/data \
     -v $(pwd)/backup:/backup \
     alpine tar czf /backup/reports-$(date +%Y%m%d).tar.gz /data
   
   # Backup script
   cat > backup.sh << 'EOF'
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/opt/backups/recon-ai-agent"
   
   mkdir -p $BACKUP_DIR
   
   # Stop container for consistent backup
   docker stop recon-ai-agent-prod
   
   # Backup volumes
   docker run --rm \
     -v recon_reports:/data/reports \
     -v recon_cache:/data/cache \
     -v $BACKUP_DIR:/backup \
     alpine tar czf /backup/recon-data-$DATE.tar.gz /data
   
   # Restart container
   docker start recon-ai-agent-prod
   
   # Cleanup old backups (keep 7 days)
   find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
   EOF
   
   chmod +x backup.sh
   ```

2. **Automated Backup with Cron**
   ```bash
   # Add to crontab
   echo "0 2 * * * /opt/scripts/backup.sh" | crontab -
   ```

### Disaster Recovery

1. **Container Recovery**
   ```bash
   # Pull latest image
   docker pull recon-ai-agent:latest
   
   # Restore from backup
   docker run --rm \
     -v recon_reports:/data/reports \
     -v recon_cache:/data/cache \
     -v /opt/backups/recon-ai-agent:/backup \
     alpine tar xzf /backup/recon-data-latest.tar.gz -C /
   
   # Restart services
   docker-compose up -d
   ```

2. **Configuration Recovery**
   ```bash
   # Backup configuration
   docker config create recon_config_backup config/.env.prod
   
   # Restore configuration
   docker config inspect recon_config_backup --pretty
   ```

## Troubleshooting

### Common Issues

1. **Memory Issues**
   ```bash
   # Increase container memory limit
   docker update --memory="4g" recon-ai-agent
   
   # Monitor memory usage
   docker exec recon-ai-agent free -h
   ```

2. **Permission Issues**
   ```bash
   # Fix volume permissions
   docker run --rm \
     -v recon_reports:/data \
     alpine chown -R 1000:1000 /data
   ```

3. **Network Connectivity**
   ```bash
   # Test external connectivity
   docker exec recon-ai-agent nslookup google.com
   docker exec recon-ai-agent curl -I https://www.google.com
   ```

### Debug Mode

```bash
# Run in debug mode
docker run --rm -it \
  --env-file .env \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/reports:/app/reports \
  recon-ai-agent \
  python main.py -d example.com -v 3

# Interactive debugging session
docker exec -it recon-ai-agent /bin/bash
```

### Performance Tuning

1. **Container Optimization**
   ```bash
   # Optimize for performance
   docker run -d \
     --cpus="2.0" \
     --memory="4g" \
     --memory-swap="4g" \
     --oom-kill-disable \
     recon-ai-agent
   ```

2. **Parallel Processing**
   ```bash
   # Enable parallel processing
   docker run --rm \
     --env-file .env \
     recon-ai-agent \
     python main.py -d example.com -w comprehensive --parallelism 4
   ```

This comprehensive deployment guide covers all aspects of running Recon AI-Agent in production environments with proper security, monitoring, and operational considerations. 