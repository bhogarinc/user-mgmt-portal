# Deployment Architecture

## User Management Portal — Infrastructure & Deployment Strategy

---

## 1. Environment Strategy

### 1.1 Environment Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONMENT STRATEGY                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┐
│   Aspect    │  Local/Dev  │    Test     │   Staging   │    Production       │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Purpose     │ Development │ CI/CD tests │ Pre-prod    │ Live application    │
│             │ & debugging │ validation  │ validation  │ serving real users  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Data        │ Local       │ Ephemeral   │ Anonymized  │ Real production     │
│             │ PostgreSQL  │ test DB     │ production  │ data                │
│             │ + seed data │             │ snapshot    │                     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ App Service │ Docker      │ N/A         │ B1 Plan     │ B1/B2 Plan          │
│ Plan        │ Compose     │ (ephemeral) │ (1 instance)│ (1-2 instances)     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Database    │ Docker      │ GitHub      │ Azure       │ Azure PostgreSQL    │
│             │ PostgreSQL  │ Actions     │ PostgreSQL  │ GP tier             │
│             │             │ service     │ Basic tier  │                     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Secrets     │ .env file   │ GitHub      │ Azure Key   │ Azure Key Vault     │
│             │ (gitignored)│ Secrets     │ Vault       │ (production SKUs)   │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Deploy      │ Manual      │ Auto on PR  │ Auto on     │ Manual approval     │
│ Trigger     │ docker-compose│           │ main merge  │ or scheduled        │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ Monitoring  │ Console     │ Test        │ Azure       │ Azure Monitor +     │
│             │ logs        │ artifacts   │ Monitor     │ Alerts              │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ URL         │ localhost   │ N/A         │ staging.    │ app.usermgmt.       │
│             │ :3000/:8000 │             │ usermgmt.io │ example.com         │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### 1.2 Environment Configuration

```python
# core/config.py
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Application
    APP_NAME: str = "User Management Portal"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis (optional caching)
    REDIS_URL: Optional[str] = None
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "ump-api"
    JWT_AUDIENCE: str = "ump-client"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Azure
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = None
    
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@usermgmt.example.com"
    FRONTEND_URL: str = "http://localhost:3000"
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
```

---

## 2. Azure Infrastructure Architecture

### 2.1 Resource Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AZURE INFRASTRUCTURE DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              RESOURCE GROUP                                   │
│                         rg-user-mgmt-portal                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        AZURE APP SERVICE                            │   │
│  │                      (ump-production-app)                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  Docker Container (Linux)                                   │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │   │
│  │  │  │   Nginx     │  │   FastAPI   │  │  React Static Files │ │   │   │
│  │  │  │   :80/:443  │  │    :8000    │  │    /app/static      │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  Configuration:                                                     │   │
│  │  • Plan: B1 (Basic) → B2 (scaling)                                  │   │
│  │  • Instances: 1-2 (auto-scale)                                      │   │
│  │  • Always On: Enabled                                               │   │
│  │  • HTTPS Only: Enabled                                              │   │
│  │  • Min TLS: 1.2                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ Managed Identity                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE DATABASE FOR POSTGRESQL                    │   │
│  │                      (ump-production-db)                            │   │
│  │                                                                     │   │
│  │  Configuration:                                                     │   │
│  │  • Tier: General Purpose (production) / Basic (staging)             │   │
│  │  • Version: 15                                                      │   │
│  │  • Compute: Burstable B1ms                                          │   │
│  │  • Storage: 32GB                                                    │   │
│  │  • Backup: Geo-redundant                                            │   │
│  │  • Private Endpoint: Enabled                                        │   │
│  │                                                                     │   │
│  │  Firewall:                                                          │   │
│  │  • Allow Azure Services: Yes                                        │   │
│  │  • App Service IP: Whitelisted                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ Private Link                            │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      AZURE KEY VAULT                                │   │
│  │                    (ump-production-kv)                              │   │
│  │                                                                     │   │
│  │  Secrets:                                                           │   │
│  │  • database-url                                                     │   │
│  │  • jwt-secret-key                                                   │   │
│  │  • sendgrid-api-key                                                 │   │
│  │  • appinsights-connection-string                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE CONTAINER REGISTRY                         │   │
│  │                      (umpproductionacr)                             │   │
│  │                                                                     │   │
│  │  Images:                                                            │   │
│  │  • user-mgmt-portal:latest                                          │   │
│  │  • user-mgmt-portal:{commit-sha}                                    │   │
│  │                                                                     │   │
│  │  Geo-replication: Enabled (production)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE MONITOR / LOG ANALYTICS                    │   │
│  │                                                                     │   │
│  │  • Application Insights (APM)                                       │   │
│  │  • Log Analytics Workspace                                          │   │
│  │  • Custom dashboards                                                │   │
│  │  • Alert rules                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE STORAGE ACCOUNT (Optional)                 │   │
│  │                                                                     │   │
│  │  • Static website hosting (if needed)                               │   │
│  │  • Backup storage                                                   │   │
│  │  • Log archival                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              NETWORKING                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  • Virtual Network (optional for advanced networking)                       │
│  • Private Endpoints for database access                                    │
│  • Azure Front Door (optional for global CDN)                               │
│  • DDoS Protection Standard (recommended for production)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Azure ARM/Bicep Template

```bicep
// infrastructure/main.bicep
@description('Environment name')
param environment string = 'production'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Database administrator password')
@secure()
param dbAdminPassword string

// Variables
var appName = 'ump-${environment}'
var dbName = '${appName}-db'
var acrName = '${appName}acr'
var kvName = '${appName}-kv'

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Azure Database for PostgreSQL
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: dbName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: 'umpadmin'
    administratorLoginPassword: dbAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

// Database firewall rule for Azure services
resource postgresFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgresServer
  name: 'AllowAllAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Azure Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
    size: 'B1'
    family: 'B'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    zoneRedundant: false
  }
}

// App Service
resource appService 'Microsoft.Web/sites@2022-09-01' = {
  name: '${appName}-app'
  location: location
  kind: 'app,linux,container'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'DOCKER|${containerRegistry.properties.loginServer}/user-mgmt-portal:latest'
      appSettings: [
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${containerRegistry.properties.loginServer}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: containerRegistry.listCredentials().username
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'DATABASE_URL'
          value: '@Microsoft.KeyVault(VaultName=${kvName};SecretName=database-url)'
        }
        {
          name: 'JWT_SECRET_KEY'
          value: '@Microsoft.KeyVault(VaultName=${kvName};SecretName=jwt-secret-key)'
        }
      ]
      alwaysOn: true
      httpLoggingEnabled: true
      detailedErrorLoggingEnabled: true
      requestTracingEnabled: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      http20Enabled: true
    }
    httpsOnly: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${appName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    RetentionInDays: 90
    PublicNetworkAccessForIngestion: 'Enabled'
    PublicNetworkAccessForQuery: 'Enabled'
  }
}

// Outputs
output appServiceDefaultHostName string = appService.properties.defaultHostName
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
```

---

## 3. Container Orchestration

### 3.1 Docker Configuration

```dockerfile
# Dockerfile (Production Multi-stage)
# ===========================================

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci --only=production

# Build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Dependencies
FROM python:3.11-slim AS python-deps
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY backend/pyproject.toml backend/poetry.lock ./

# Install dependencies (no dev, no virtualenv)
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Stage 3: Production
FROM python:3.11-slim AS production
WORKDIR /app

# Security: Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set environment
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Change ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```yaml
# docker-compose.yml (Local Development)
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: umpuser
      POSTGRES_PASSWORD: umppass
      POSTGRES_DB: user_mgmt
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U umpuser -d user_mgmt"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile.dev
    environment:
      DATABASE_URL: postgresql+asyncpg://umpuser:umppass@db:5432/user_mgmt
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: dev-secret-key-change-in-production
      ENVIRONMENT: development
      DEBUG: "true"
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    environment:
      VITE_API_URL: http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

---

## 4. CI/CD Pipeline

### 4.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ==========================================
  # TEST JOB
  # ==========================================
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      # Backend Tests
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt
      
      - name: Install backend dependencies
        working-directory: backend
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run backend tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://testuser:testpass@localhost:5432/testdb
          JWT_SECRET_KEY: test-secret-key
          ENVIRONMENT: test
        run: |
          pytest --cov=app --cov-report=xml --cov-report=html -v
      
      - name: Upload backend coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml
          flags: backend
          name: backend-coverage
      
      # Frontend Tests
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Run frontend tests
        working-directory: frontend
        run: npm run test:ci
      
      - name: Run frontend lint
        working-directory: frontend
        run: npm run lint
      
      - name: Build frontend
        working-directory: frontend
        run: npm run build

  # ==========================================
  # SECURITY SCAN
  # ==========================================
  security:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
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
  # BUILD & PUSH
  # ==========================================
  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
      image_digest: ${{ steps.build.outputs.digest }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal
          tags: |
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

  # ==========================================
  # DEPLOY TO STAGING
  # ==========================================
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to Staging
        uses: azure/webapps-deploy@v3
        with:
          app-name: 'ump-staging-app'
          images: '${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal:sha-${{ github.sha }}'
      
      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://ump-staging-app.azurewebsites.net/api/health || exit 1

  # ==========================================
  # DEPLOY TO PRODUCTION
  # ==========================================
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to Production
        uses: azure/webapps-deploy@v3
        with:
          app-name: 'ump-production-app'
          images: '${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal:sha-${{ github.sha }}'
      
      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://ump-production-app.azurewebsites.net/api/health || exit 1
      
      - name: Notify deployment
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 User Management Portal deployed to production",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Successful*\nCommit: ${{ github.sha }}\nBy: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 5. Monitoring and Logging

### 5.1 Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA COLLECTION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Application Logs          Metrics              Traces                      │
│       │                       │                    │                        │
│       ▼                       ▼                    ▼                        │
│  ┌─────────┐            ┌─────────┐         ┌─────────┐                    │
│  │Structured│           │Prometheus│        │OpenTele-│                    │
│  │ Logging │            │  Client │        │  metry  │                    │
│  │ (JSON)  │            │ (StatsD)│        │  SDK    │                    │
│  └────┬────┘            └────┬────┘         └────┬────┘                    │
│       │                       │                    │                        │
│       └───────────────────────┼────────────────────┘                        │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE MONITOR / APPLICATION INSIGHTS             │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │ Log         │  │ Metrics     │  │ Distributed │  │ Live      │ │   │
│  │  │ Analytics   │  │ Explorer    │  │ Tracing     │  │ Metrics   │ │   │
│  │  │ Workspace   │  │             │  │             │  │ Stream    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ALERTING & DASHBOARDS                       │   │
│  │                                                                     │   │
│  │  • Email alerts              • Azure Dashboards                     │   │
│  │  • SMS alerts (critical)     • Grafana (optional)                   │   │
│  │  • Webhook integrations      • Power BI reports                     │   │
│  │  • PagerDuty integration                                            │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Metrics

| Category | Metric | Threshold | Alert |
|----------|--------|-----------|-------|
| **Availability** | App Service availability | < 99.9% | Critical |
| | API response time (p95) | > 500ms | Warning |
| | Error rate (5xx) | > 1% | Critical |
| **Performance** | Database connection pool | > 80% | Warning |
| | CPU utilization | > 80% | Warning |
| | Memory utilization | > 85% | Warning |
| **Security** | Failed login attempts | > 10/min | Warning |
| | JWT validation failures | > 5% | Critical |
| **Business** | Active users | Anomaly | Info |
| | User registrations | Drop > 50% | Warning |

### 5.3 Logging Configuration

```python
# core/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler

from app.core.config import settings


def setup_logging():
    """Configure structured logging."""
    
    log_format = (
        '%(asctime)s %(levelname)s %(name)s '
        '%(message)s %(pathname)s %(lineno)d '
        '%(funcName)s %(request_id)s %(user_id)s'
    )
    
    formatter = jsonlogger.JsonFormatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler (production)
    if settings.is_production:
        file_handler = RotatingFileHandler(
            '/var/log/app/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    if settings.is_production:
        root_logger.addHandler(file_handler)
    
    # Azure Log Analytics (if configured)
    if settings.APPINSIGHTS_CONNECTION_STRING:
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
        
        logger_provider = LoggerProvider()
        exporter = AzureMonitorLogExporter(
            connection_string=settings.APPINSIGHTS_CONNECTION_STRING
        )
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(exporter)
        )
        
        azure_handler = LoggingHandler(logger_provider=logger_provider)
        azure_handler.setLevel(logging.WARNING)
        root_logger.addHandler(azure_handler)
```

---

## 6. Scaling Strategy

### 6.1 Auto-scaling Configuration

```python
# Azure CLI commands for auto-scaling setup

# Enable auto-scaling on App Service Plan
az monitor autoscale create \
    --resource-group rg-user-mgmt-portal \
    --name ump-autoscale \
    --resource $(az appservice plan show --name ump-production-plan --resource-group rg-user-mgmt-portal --query id -o tsv) \
    --min-count 1 \
    --max-count 3 \
    --count 1

# Scale up rule: CPU > 70%
az monitor autoscale rule create \
    --resource-group rg-user-mgmt-portal \
    --autoscale-name ump-autoscale \
    --condition "Percentage CPU > 70 avg 5m" \
    --scale out 1

# Scale down rule: CPU < 30%
az monitor autoscale rule create \
    --resource-group rg-user-mgmt-portal \
    --autoscale-name ump-autoscale \
    --condition "Percentage CPU < 30 avg 10m" \
    --scale in 1
```

### 6.2 Scaling Thresholds

| Metric | Scale Out | Scale In | Max Instances |
|--------|-----------|----------|---------------|
| CPU | > 70% | < 30% | 3 |
| Memory | > 80% | < 40% | 3 |
| Requests/min | > 1000 | < 200 | 3 |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-25  
**Owner**: System Architect  
**Next Review**: 2024-04-25
