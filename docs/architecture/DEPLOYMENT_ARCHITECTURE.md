# Deployment Architecture

## Overview

This document describes the deployment architecture for the User Management Portal on Microsoft Azure.

---

## Infrastructure Components

### 1. Azure Resource Group

**Name:** `bhogarai-gf`  
**Location:** `Central US`  
**Purpose:** Logical container for all application resources

### 2. App Service Plan

**SKU:** Premium V2 P1V2  
**Features:**
- Auto-scaling: 2-10 instances
- Custom domains and SSL
- Staging slots for blue-green deployment
- Docker container support

### 3. Azure Database for PostgreSQL

**Tier:** Flexible Server  
**Configuration:**
- Compute: 2 vCores
- Storage: 32 GB
- Backup: Geo-redundant (35 days retention)
- High Availability: Zone redundant
- SSL: Enforced

### 4. Azure Cache for Redis

**Tier:** Standard C1  
**Configuration:**
- Cache Size: 1 GB
- SSL: Enabled
- Data Persistence: AOF

### 5. Azure Blob Storage

**Tier:** Standard LRS  
**Containers:**
- `avatars` - User profile images
- `exports` - Data export files
- `documents` - User documents
- `static` - Static web assets

### 6. Azure Front Door

**Tier:** Standard  
**Features:**
- Global load balancing
- WAF with managed rules
- SSL termination
- URL rewriting
- Health probes

### 7. Azure Key Vault

**Tier:** Standard  
**Secrets:**
- Database connection strings
- JWT signing keys
- API keys (SendGrid, etc.)
- Azure AD client secrets

### 8. Application Insights

**Type:** Workspace-based  
**Features:**
- Application Performance Monitoring (APM)
- Distributed tracing
- Custom metrics and events
- Alert rules

---

## Deployment Environments

### Development

```yaml
Environment:
  Name: Development
  URL: https://dev-bhogarai-gf-app.azurewebsites.net
  
App Service:
  Instances: 1
  Always On: false
  
Database:
  Tier: Burstable B1ms
  Backup: Local redundant
  
Features:
    - Debug logging enabled
    - Swagger UI accessible
    - Test data seeded
```

### Staging

```yaml
Environment:
  Name: Staging
  URL: https://staging-bhogarai-gf-app.azurewebsites.net
  
App Service:
  Instances: 2
  Always On: true
  
Database:
  Tier: General Purpose
  Backup: Geo-redundant
  
Features:
    - Production-like configuration
    - Automated smoke tests
    - Performance testing allowed
```

### Production

```yaml
Environment:
  Name: Production
  URL: https://bhogarai-gf-app.azurewebsites.net
  Custom Domain: https://app.usermgmt.io
  
App Service:
  Instances: Auto-scale (2-10)
  Always On: true
  Health Checks: Enabled
  
Database:
  Tier: General Purpose
  High Availability: Zone redundant
  Backup: Geo-redundant
  Read Replicas: 1
  
Features:
    - CDN enabled (Azure Front Door)
    - WAF protection
    - Real-user monitoring
    - 99.9% SLA
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AZURE_WEBAPP_NAME: bhogarai-gf-app
  AZURE_RESOURCE_GROUP: bhogarai-gf
  ACR_REGISTRY: usermgmtacr.azurecr.io

jobs:
  # ==========================================
  # Phase 1: Test
  # ==========================================
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run linting
        working-directory: ./backend
        run: |
          flake8 app tests
          black --check app tests
          isort --check-only app tests
      
      - name: Run type checking
        working-directory: ./backend
        run: mypy app
      
      - name: Run tests with coverage
        working-directory: ./backend
        run: |
          pytest --cov=app --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: './frontend/package-lock.json'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run linting
        working-directory: ./frontend
        run: npm run lint
      
      - name: Run type checking
        working-directory: ./frontend
        run: npm run type-check
      
      - name: Run tests
        working-directory: ./frontend
        run: npm run test:ci
      
      - name: Build
        working-directory: ./frontend
        run: npm run build

  # ==========================================
  # Phase 2: Security Scan
  # ==========================================
  security-scan:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # ==========================================
  # Phase 3: Build & Push
  # ==========================================
  build-backend:
    runs-on: ubuntu-latest
    needs: security-scan
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to ACR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.ACR_REGISTRY }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.ACR_REGISTRY }}/ump-backend:${{ github.sha }}
            ${{ env.ACR_REGISTRY }}/ump-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-frontend:
    runs-on: ubuntu-latest
    needs: security-scan
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to ACR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.ACR_REGISTRY }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.ACR_REGISTRY }}/ump-frontend:${{ github.sha }}
            ${{ env.ACR_REGISTRY }}/ump-frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ==========================================
  # Phase 4: Deploy to Staging
  # ==========================================
  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build-backend, build-frontend]
    environment:
      name: Staging
      url: https://staging-bhogarai-gf-app.azurewebsites.net
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to staging slot
        run: |
          az webapp config container set \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --slot staging \
            --docker-custom-image-name ${{ env.ACR_REGISTRY }}/ump-backend:${{ github.sha }}
      
      - name: Run smoke tests
        run: |
          curl -f https://staging-bhogarai-gf-app.azurewebsites.net/health || exit 1

  # ==========================================
  # Phase 5: Deploy to Production
  # ==========================================
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment:
      name: Production
      url: https://app.usermgmt.io
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Swap slots
        run: |
          az webapp deployment slot swap \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --slot staging \
            --target-slot production
      
      - name: Verify deployment
        run: |
          curl -f https://app.usermgmt.io/health || exit 1
      
      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          text: 'Production deployment completed: ${{ github.sha }}'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## Docker Configuration

### Backend Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    image: ${ACR_REGISTRY}/ump-backend:${IMAGE_TAG:-latest}
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_PRIVATE_KEY=${JWT_PRIVATE_KEY}
      - JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - APP_ENV=production
      - LOG_LEVEL=info
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  celery-worker:
    image: ${ACR_REGISTRY}/ump-backend:${IMAGE_TAG:-latest}
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - APP_ENV=production
    depends_on:
      - redis
    deploy:
      replicas: 2

  celery-beat:
    image: ${ACR_REGISTRY}/ump-backend:${IMAGE_TAG:-latest}
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - APP_ENV=production
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

---

## Monitoring & Alerting

### Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Response Time (P95) | > 500ms | Scale up |
| Error Rate | > 1% | Page on-call |
| CPU Usage | > 80% | Scale up |
| Memory Usage | > 85% | Investigate |
| Database Connections | > 80% | Connection pooling |
| Disk Space | > 85% | Clean up logs |

### Alerts

```yaml
# Azure Monitor Alert Rules
alerts:
  high_response_time:
    condition: response_time_p95 > 500ms
    severity: Warning
    action: Scale up App Service
    
  high_error_rate:
    condition: error_rate > 1%
    severity: Critical
    action: Page on-call engineer
    
  database_cpu:
    condition: db_cpu_percent > 80
    severity: Warning
    action: Review slow queries
    
  failed_health_check:
    condition: health_check_failures > 0
    severity: Critical
    action: Immediate investigation
```

---

## Rollback Procedure

### Automatic Rollback

If health checks fail after deployment:
```bash
# Swap back to previous slot
az webapp deployment slot swap \
  --name bhogarai-gf-app \
  --resource-group bhogarai-gf \
  --slot production \
  --target-slot staging
```

### Manual Rollback

```bash
# 1. Identify last known good image
LAST_GOOD_IMAGE=$(az webapp config container show \
  --name bhogarai-gf-app \
  --resource-group bhogarai-gf \
  --query linuxFxVersion -o tsv)

# 2. Revert to previous image
az webapp config container set \
  --name bhogarai-gf-app \
  --resource-group bhogarai-gf \
  --docker-custom-image-name $LAST_GOOD_IMAGE

# 3. Restart app service
az webapp restart \
  --name bhogarai-gf-app \
  --resource-group bhogarai-gf
```

---

## Security Considerations

1. **Secrets Management**: All secrets stored in Azure Key Vault
2. **Network Security**: Private endpoints for database, NSG rules
3. **Container Security**: Non-root containers, minimal images
4. **Vulnerability Scanning**: Trivy scans in CI/CD
5. **WAF**: Azure Front Door with OWASP rules
6. **SSL**: TLS 1.3 enforced, certificates auto-renewed

---

*Last Updated: January 2024*  
*Owner: DevOps Team*
