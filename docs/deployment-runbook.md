# Deployment Runbook: Marketing Multi-Agent System

## Overview

This runbook provides comprehensive instructions for deploying and operating the Marketing Multi-Agent System in production environments.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │  Agent Manager  │
│    (nginx)      │────│   (FastAPI)     │────│    (Docker)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌────────┼────────┐
                       │        │        │
              ┌────────▼──┐ ┌───▼───┐ ┌──▼────────┐
              │ Lead      │ │Engage-│ │Campaign   │
              │ Triage    │ │ment   │ │Optimization│
              │ Agent     │ │Agent  │ │Agent      │
              └───────────┘ └───────┘ └───────────┘
                       │        │        │
              ┌────────▼────────▼────────▼────────┐
              │         Memory Layer              │
              │  Redis │ PostgreSQL │ ChromaDB │ Neo4j │
              └───────────────────────────────────┘
```

## Prerequisites

### System Requirements
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Memory**: Minimum 16GB RAM, Recommended 32GB+
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ NVMe
- **Network**: Minimum 1Gbps, Recommended 10Gbps

### Software Dependencies
- Docker 24.0+ and Docker Compose 2.0+
- Python 3.9+ (for development/debugging)
- nginx 1.20+ (for load balancing)
- SSL certificates (Let's Encrypt recommended)

### External Services
- Redis Cluster (for short-term memory)
- PostgreSQL 14+ (for long-term memory)
- ChromaDB or Pinecone (for vector embeddings)
- Neo4j 5.0+ (for knowledge graphs)

## Pre-Deployment Setup

### 1. Environment Configuration

Create production environment file:

```bash
# /opt/marketing-agents/.env.production
ENVIRONMENT=production
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security
JWT_SECRET_KEY=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# Database Connections
REDIS_URL=redis://redis-cluster:6379/0
POSTGRES_URL=postgresql://user:password@postgres-cluster:5432/marketing_agents
CHROMA_HOST=http://chromadb:8001
NEO4J_URI=bolt://neo4j-cluster:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=production-password

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_BURST=100

# Agent Configuration
MAX_CONCURRENT_LEADS=100
MEMORY_CONSOLIDATION_INTERVAL=300
HEALTH_CHECK_INTERVAL=30
```

### 2. Docker Configuration

Create `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  marketing-agents:
    image: marketing-agents:latest
    ports:
      - "8000:8000"
    environment:
      - ENV_FILE=/app/.env.production
    volumes:
      - ./logs:/app/logs
      - ./.env.production:/app/.env.production
    depends_on:
      - redis
      - postgres
      - chromadb
      - neo4j
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: marketing_agents
      POSTGRES_USER: agents_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    restart: unless-stopped

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - marketing-agents
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  chromadb_data:
  neo4j_data:
```

## Deployment Steps

### 1. Initial Deployment

```bash
# 1. Clone repository
git clone https://github.com/company/marketing-multi-agent-system.git
cd marketing-multi-agent-system

# 2. Create production directory
sudo mkdir -p /opt/marketing-agents
sudo chown $USER:$USER /opt/marketing-agents
cp -r . /opt/marketing-agents/
cd /opt/marketing-agents

# 3. Build production image
docker build -t marketing-agents:latest -f Dockerfile.production .

# 4. Create environment file
cp .env.example .env.production
# Edit .env.production with production values

# 5. Initialize databases
docker-compose -f docker-compose.production.yml up -d postgres redis
sleep 30
docker-compose -f docker-compose.production.yml exec postgres psql -U agents_user -d marketing_agents -f /docker-entrypoint-initdb.d/init.sql

# 6. Start all services
docker-compose -f docker-compose.production.yml up -d

# 7. Verify deployment
curl -f http://localhost:8000/health
```

### 2. SSL Certificate Setup

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Update nginx configuration for SSL
sudo nano /opt/marketing-agents/nginx.conf
sudo docker-compose -f docker-compose.production.yml restart nginx
```

### 3. Monitoring Setup

```bash
# Install Prometheus and Grafana
curl -LO https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xzf prometheus-2.40.0.linux-amd64.tar.gz
sudo mv prometheus-2.40.0.linux-amd64/prometheus /usr/local/bin/

# Create monitoring configuration
sudo mkdir -p /opt/monitoring
sudo tee /opt/monitoring/prometheus.yml > /dev/null <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'marketing-agents'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
EOF

# Start Prometheus
nohup prometheus --config.file=/opt/monitoring/prometheus.yml --storage.tsdb.path=/opt/monitoring/data &
```

## Operations

### Daily Operations

#### Health Checks
```bash
# Check system health
curl -f http://localhost:8000/health

# Check agent status
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/agents/status

# Check database connections
docker-compose -f docker-compose.production.yml exec marketing-agents python -c "
from memory_systems.memory_manager import MemoryManager
import asyncio
async def test():
    mm = MemoryManager()
    await mm.initialize()
    print('Memory systems:', mm.config)
asyncio.run(test())
"
```

#### Log Monitoring
```bash
# Application logs
docker-compose -f docker-compose.production.yml logs -f marketing-agents

# Agent interaction logs
tail -f /opt/marketing-agents/logs/agent_interactions.log

# Error logs
tail -f /opt/marketing-agents/logs/errors.log | grep ERROR
```

#### Performance Monitoring
```bash
# Check resource usage
docker stats

# Monitor active connections
ss -tuln | grep :8000

# Check memory usage
free -h
df -h
```

### Backup Procedures

#### Database Backups
```bash
#!/bin/bash
# /opt/marketing-agents/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

# PostgreSQL backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U agents_user marketing_agents > $BACKUP_DIR/postgres_$DATE.sql

# Redis backup
docker-compose -f docker-compose.production.yml exec redis redis-cli SAVE
docker cp $(docker-compose -f docker-compose.production.yml ps -q redis):/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Neo4j backup
docker-compose -f docker-compose.production.yml exec neo4j neo4j-admin database dump --to-path=/backups neo4j > $BACKUP_DIR/neo4j_$DATE.dump

# ChromaDB backup
docker cp $(docker-compose -f docker-compose.production.yml ps -q chromadb):/chroma/chroma $BACKUP_DIR/chromadb_$DATE/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "chromadb_*" -mtime +30 -exec rm -rf {} \;
```

### Scaling Procedures

#### Horizontal Scaling
```bash
# Scale application instances
docker-compose -f docker-compose.production.yml up -d --scale marketing-agents=3

# Update nginx upstream configuration
sudo tee /opt/marketing-agents/nginx-upstream.conf > /dev/null <<EOF
upstream marketing_agents {
    server marketing-agents_marketing-agents_1:8000;
    server marketing-agents_marketing-agents_2:8000;
    server marketing-agents_marketing-agents_3:8000;
}
EOF

# Reload nginx
sudo docker-compose -f docker-compose.production.yml exec nginx nginx -s reload
```

#### Database Scaling
```bash
# Redis cluster setup
docker-compose -f docker-compose.redis-cluster.yml up -d

# PostgreSQL read replicas
docker-compose -f docker-compose.postgres-cluster.yml up -d

# Update connection strings in .env.production
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage by component
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Restart memory-intensive services
docker-compose -f docker-compose.production.yml restart chromadb
```

#### 2. Database Connection Issues
```bash
# Check database connectivity
docker-compose -f docker-compose.production.yml exec marketing-agents python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://user:pass@postgres:5432/marketing_agents')
    print('Connected to PostgreSQL')
    await conn.close()
asyncio.run(test())
"
```

#### 3. Agent Communication Failures
```bash
# Check agent status
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/agents/status

# Restart agent services
docker-compose -f docker-compose.production.yml restart marketing-agents
```

### Emergency Procedures

#### Complete System Restart
```bash
#!/bin/bash
# /opt/marketing-agents/scripts/emergency-restart.sh

echo "Emergency system restart initiated..."

# Stop all services
docker-compose -f docker-compose.production.yml down

# Clean up orphaned containers
docker container prune -f

# Restart core services first
docker-compose -f docker-compose.production.yml up -d postgres redis
sleep 30

# Start remaining services
docker-compose -f docker-compose.production.yml up -d

# Verify health
sleep 60
curl -f http://localhost:8000/health || echo "Health check failed!"
```

#### Rollback Procedure
```bash
#!/bin/bash
# /opt/marketing-agents/scripts/rollback.sh

PREVIOUS_VERSION=$1

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Usage: ./rollback.sh <version>"
    exit 1
fi

# Stop current services
docker-compose -f docker-compose.production.yml down

# Rollback to previous image
docker tag marketing-agents:$PREVIOUS_VERSION marketing-agents:latest

# Start services
docker-compose -f docker-compose.production.yml up -d

echo "Rollback to version $PREVIOUS_VERSION completed"
```

## Security Considerations

### Access Control
- Use strong JWT secrets
- Implement API rate limiting
- Regular security updates
- Network segmentation

### Monitoring
- Log all API access
- Monitor for suspicious patterns
- Set up alerting for anomalies
- Regular security audits

### Data Protection
- Encrypt data at rest
- Use TLS for all communications
- Regular backup testing
- GDPR compliance measures

## Performance Optimization

### Database Tuning
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### Application Tuning
```python
# uvicorn optimization
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
```

## Maintenance Schedule

### Daily
- Check system health
- Monitor error logs
- Verify backup completion

### Weekly
- Security updates
- Performance review
- Log rotation

### Monthly
- Full system backup
- Security audit
- Capacity planning review

### Quarterly
- Disaster recovery test
- Performance benchmarking
- Architecture review

## Contact Information

**Primary On-Call**: DevOps Team (devops@company.com)
**Secondary**: Backend Team (backend@company.com)
**Emergency**: CTO (cto@company.com)

**Escalation Matrix**:
1. DevOps Engineer (15 minutes)
2. Senior DevOps Engineer (30 minutes)
3. DevOps Manager (60 minutes)
4. CTO (120 minutes)
