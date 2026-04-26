# System Architecture - User Management Portal

## Executive Summary

This document defines the complete system architecture for the User Management Portal, a comprehensive web application featuring authentication, RBAC, user profile management, and admin capabilities.

---

## 1. Architecture Overview

### 1.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL USERS                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   End Users  │  │    Admins    │  │ API Clients  │  │  IdP (Azure) │     │
│  │  (Web/Mobile)│  │  (Dashboard) │  │  (External)  │  │   (SSO)      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
                              ┌─────▼─────┐
                              │  CDN/WAF  │
                              │ (Azure FD)│
                              └─────┬─────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │  React    │   │  FastAPI  │   │  Static   │
              │  Frontend │   │  Backend  │   │  Assets   │
              │ (SPA)     │   │ (REST API)│   │ (Storage) │
              └─────┬─────┘   └─────┬─────┘   └───────────┘
                    │               │
                    │         ┌─────┴─────┐
                    │         │  Redis    │
                    │         │  Cache    │
                    │         └───────────┘
                    │               │
              ┌─────▼───────────────▼─────┐
              │      PostgreSQL           │
              │    (Primary Database)     │
              └───────────────────────────┘
```

### 1.2 Container Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           AZURE APP SERVICE                                 │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      Frontend Container                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  React App   │  │  Redux Store │  │  Axios Client│             │    │
│  │  │  (Vite)      │  │  (RTK)       │  │  (API Calls) │             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ React Router │  │  MUI Theme   │  │  Formik/Yup  │             │    │
│  │  │  (v6)        │  │  (Dark/Light)│  │  (Validation)│             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      Backend Container                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  FastAPI     │  │  Pydantic    │  │  SQLAlchemy  │             │    │
│  │  │  (Main App)  │  │  (Models)    │  │  (ORM)       │             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  Auth Module │  │  RBAC Engine │  │  API Routes  │             │    │
│  │  │  (JWT/OAuth) │  │  (Casbin)    │  │  (Routers)   │             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ Alembic      │  │  Celery      │  │  Email       │             │    │
│  │  │ (Migrations) │  │  (Tasks)     │  │  (SendGrid)  │             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                          AZURE MANAGED SERVICES                             │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  PostgreSQL      │  │  Redis Cache     │  │  Blob Storage    │          │
│  │  (Flexible Server)│  │  (Azure Cache)   │  │  (Static Assets) │          │
│  │  • Users DB      │  │  • Session Store │  │  • Avatars       │          │
│  │  • Audit Logs    │  │  • Rate Limiting │  │  • Documents     │          │
│  │  • RBAC Data     │  │  • API Caching   │  │  • Exports       │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  App Insights    │  │  Log Analytics   │  │  Key Vault       │          │
│  │  (Monitoring)    │  │  (Centralized)   │  │  (Secrets)       │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Architecture Style: Modular Monolith

**Decision**: Modular Monolith with Clean Architecture

**Justification**:
- **Team Size**: Small team (3-5 developers) - microservices overhead not justified
- **Complexity**: Single bounded context (user management) - no need for service decomposition
- **Deployment**: Azure App Service excels at single-container deployment
- **Performance**: In-process communication eliminates network latency
- **Future**: Well-defined modules allow extraction to microservices if needed

---

## 2. Technology Stack Selection

### 2.1 Frontend Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Framework | React | 18.x | Industry standard, large ecosystem |
| Build Tool | Vite | 5.x | Fast HMR, optimized builds |
| State Management | Redux Toolkit (RTK) | 2.x | Predictable state, RTK Query for API |
| UI Library | Material-UI (MUI) | 5.x | Comprehensive component library |
| Routing | React Router | 6.x | Declarative routing |
| Forms | Formik + Yup | 2.x | Form handling + validation |
| HTTP Client | Axios | 1.x | Interceptors, request/response transforms |
| Auth | MSAL React | 2.x | Azure AD integration |
| Testing | Vitest + RTL | 1.x | Fast testing, React Testing Library |

### 2.2 Backend Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Language | Python | 3.11+ | FastAPI ecosystem, type hints |
| Framework | FastAPI | 0.104+ | Async, auto-docs, Pydantic |
| ORM | SQLAlchemy | 2.x | Mature, async support |
| Migrations | Alembic | 1.12+ | SQLAlchemy migrations |
| Auth | python-jose | 3.3+ | JWT handling |
| RBAC | Casbin | 1.33+ | Policy-based access control |
| Validation | Pydantic | 2.x | Data validation, settings |
| Async Tasks | Celery | 5.3+ | Background jobs |
| Broker | Redis | 7.x | Celery broker + cache |
| Email | SendGrid | 6.x | Transactional emails |

### 2.3 Database Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Primary DB | PostgreSQL 15 | ACID compliance, JSON support, Row-level security |
| Cache Layer | Redis 7 | Session storage, API caching, rate limiting |
| Search | PostgreSQL FTS | Built-in full-text search (users, logs) |
| Audit | PostgreSQL + Triggers | Immutable audit trail |

### 2.4 Infrastructure Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Cloud | Microsoft Azure | Enterprise integration, cost optimization |
| Compute | App Service (Linux) | Managed platform, auto-scaling |
| Database | Azure Database for PostgreSQL | Managed, backups, HA |
| Cache | Azure Cache for Redis | Managed Redis cluster |
| Storage | Azure Blob Storage | Static assets, user uploads |
| CDN | Azure Front Door | Global CDN, WAF, SSL |
| Secrets | Azure Key Vault | Secure secret management |
| Monitoring | Application Insights | APM, distributed tracing |
| CI/CD | GitHub Actions | Native GitHub integration |

---

## 3. Data Architecture

### 3.1 Database Schema Overview

```sql
-- Core User Management Schema

-- Users table with soft delete
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}'
);

-- Organizations for multi-tenancy
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Organization membership
CREATE TABLE user_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    is_default BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- Roles for RBAC
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Role assignments
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, role_id, organization_id)
);

-- Audit logs (partitioned by month)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    ip_address INET,
    user_agent TEXT,
    old_values JSONB,
    new_values JSONB,
    metadata JSONB
) PARTITION BY RANGE (timestamp);

-- Sessions for tracking
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id, timestamp DESC);
CREATE INDEX idx_user_orgs_user ON user_organizations(user_id);
CREATE INDEX idx_user_orgs_org ON user_organizations(organization_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

### 3.2 Data Flow Diagrams

#### Authentication Flow
```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────▶│  FastAPI     │────▶│  PostgreSQL  │────▶│  Redis   │
│          │     │  /auth/login │     │  (validate)  │     │ (session)│
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
     │                  │                     │                  │
     │                  │                     │                  │
     │◀─────────────────┼─────────────────────┼──────────────────┘
     │    JWT Tokens    │                     │
     │                  │                     │
     │◀─────────────────┘  Return user data   │
     │
     │  [Subsequent Requests]
     │
     ├──────────────────────────────────────────────────────────────▶
     │                    Bearer Token + Refresh Token
```

#### User Profile Update Flow
```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────▶│  FastAPI     │────▶│  Validation  │────▶│  Update  │
│  (Form)  │     │  /users/me   │     │  (Pydantic)  │     │  (SQLA)  │
└──────────┘     └──────────────┘     └──────────────┘     └────┬─────┘
     │                                                            │
     │                                                            ▼
     │                                                     ┌──────────┐
     │                                                     │  Audit   │
     │                                                     │  Logger  │
     │                                                     └────┬─────┘
     │                                                            │
     │◀───────────────────────────────────────────────────────────┘
     │                    Updated Profile + Event
```

### 3.3 Caching Strategy

| Cache Type | Key Pattern | TTL | Use Case |
|------------|-------------|-----|----------|
| Session | `session:{token_hash}` | 24h | User authentication state |
| User Profile | `user:{id}:profile` | 1h | Frequently accessed profiles |
| Permissions | `user:{id}:perms:{org}` | 15m | RBAC permission cache |
| Rate Limit | `ratelimit:{ip}:{endpoint}` | 1m | API rate limiting |
| API Response | `api:{endpoint}:{params_hash}` | 5m | Expensive queries |

### 3.4 Data Migration Approach

1. **Schema Migrations**: Alembic with version control
2. **Data Migrations**: Python scripts with dry-run capability
3. **Rollback Strategy**: Database snapshots + down migrations
4. **Zero-Downtime**: Blue-green deployment with connection draining

---

## 4. Integration Architecture

### 4.1 API Gateway Design

Azure Front Door serves as the API Gateway:

```yaml
# Front Door Configuration
front_door:
  frontend_endpoints:
    - name: api
      host_name: api.usermgmt.io
    - name: app
      host_name: app.usermgmt.io
  
  routing_rules:
    - name: api-routes
      patterns: ['/api/*', '/auth/*']
      backend: app-service-backend
      forwarding_protocol: HttpsOnly
      
    - name: static-assets
      patterns: ['/static/*', '/assets/*']
      backend: blob-storage-backend
      caching: enabled
      
    - name: spa-fallback
      patterns: ['/*']
      backend: app-service-backend
      custom_fragment: /index.html
  
  waf_policy:
    enabled: true
    mode: Prevention
    rules:
      - SQLInjectionProtection
      - XSSProtection
      - RateLimiting: 1000req/min
```

### 4.2 External Service Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| Azure AD | OAuth 2.0 / OIDC | Enterprise SSO |
| SendGrid | REST API | Transactional emails |
| Azure Monitor | OpenTelemetry | Observability |
| GitHub OAuth | OAuth 2.0 | Social login |

### 4.3 Authentication Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User   │────▶│   Client    │────▶│   FastAPI   │────▶│  Azure AD   │
│         │     │   (React)   │     │   (OAuth)   │     │  (IdP)      │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
     │                                                           │
     │                                                           │
     │                    ┌────────────────────────────────────────┘
     │                    │ Authorization Code + PKCE
     │                    │
     │◀───────────────────┘
     │    ID Token + Access Token
     │
     │  [API Calls]
     │
     ├──────────────────────────────────────────────────────────────▶
     │                  Bearer Token (JWT)
```

### 4.4 JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id-123"
  },
  "payload": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "org": "org-uuid",
    "roles": ["admin", "user"],
    "permissions": ["users:read", "users:write"],
    "iat": 1699999999,
    "exp": 1700003599,
    "jti": "unique-token-id"
  }
}
```

---

## 5. Deployment Architecture

### 5.1 Environment Strategy

| Environment | Purpose | Data | Scaling |
|-------------|---------|------|---------|
| Development | Feature development | Synthetic | 1 instance |
| Staging | Integration testing | Anonymized prod | 2 instances |
| Production | Live users | Production | Auto-scale 2-10 |

### 5.2 Azure Resource Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RESOURCE GROUP                                  │
│                           bhogarai-gf (CentralUS)                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AZURE APP SERVICE PLAN                            │   │
│  │                        (Premium V2 P1V2)                             │   │
│  │                                                                     │   │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐   │   │
│  │   │  App Service    │    │  App Service    │    │  Deployment  │   │   │
│  │   │  (Production)   │    │  (Staging Slot) │    │  Slots       │   │   │
│  │   │  bhogarai-gf-app│    │  -staging       │    │  (Blue/Green)│   │   │
│  │   └────────┬────────┘    └─────────────────┘    └──────────────┘   │   │
│  │            │                                                        │   │
│  │            ▼                                                        │   │
│  │   ┌─────────────────┐    ┌─────────────────┐                        │   │
│  │   │  Container Reg  │    │  Docker Compose │                        │   │
│  │   │  (ACR)          │    │  (Multi-container)                      │   │
│  │   └─────────────────┘    └─────────────────┘                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  PostgreSQL     │  │  Redis Cache    │  │  Blob Storage   │             │
│  │  (Flexible Svr) │  │  (Standard C1)  │  │  (Standard LRS) │             │
│  │  • 2 vCores     │  │  • 1 GB         │  │  • Hot tier     │             │
│  │  • 32 GB        │  │  • SSL enabled  │  │  • CDN enabled  │             │
│  │  • Geo-redundant│  │  • Persistence  │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Key Vault      │  │  App Insights   │  │  Front Door     │             │
│  │  (Standard)     │  │  (Workspace-based)│  │  (Standard)     │             │
│  │  • Secrets      │  │  • APM          │  │  • WAF          │             │
│  │  • Certificates │  │  • Logs         │  │  • CDN          │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Docker Compose Configuration

```yaml
version: '3.8'

services:
  frontend:
    image: ${ACR_LOGIN_SERVER}/ump-frontend:${IMAGE_TAG}
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=https://api.usermgmt.io
      - REACT_APP_AUTH_AUTHORITY=${AZURE_AD_AUTHORITY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    image: ${ACR_LOGIN_SERVER}/ump-backend:${IMAGE_TAG}
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    image: ${ACR_LOGIN_SERVER}/ump-backend:${IMAGE_TAG}
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - backend

  celery-beat:
    image: ${ACR_LOGIN_SERVER}/ump-backend:${IMAGE_TAG}
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - backend
```

### 5.4 CI/CD Pipeline Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Push    │────▶│  GitHub      │────▶│  Build &     │────▶│  Push to     │
│  to main │     │  Actions     │     │  Test        │     │  ACR         │
└──────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                   │
                                                                   ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Notify  │◀────│  Health      │◀────│  Swap        │◀────│  Deploy to   │
│  Slack   │     │  Check       │     │  Slots       │     │  Staging     │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 5.5 Monitoring Stack

| Layer | Tool | Metrics |
|-------|------|---------|
| Infrastructure | Azure Monitor | CPU, Memory, Disk, Network |
| Application | Application Insights | Response time, Error rate, Dependencies |
| Logs | Log Analytics | Structured logs, Query analysis |
| APM | OpenTelemetry | Distributed tracing, Spans |
| Alerts | Azure Alerts | P95 latency > 500ms, Error rate > 1% |
| Dashboard | Grafana | Custom business metrics |

---

## 6. Security Architecture

### 6.1 Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: PERIMETER                                                         │
│  • Azure Front Door with WAF                                                │
│  • DDoS Protection Standard                                                 │
│  • Geo-blocking (optional)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: NETWORK                                                           │
│  • Private endpoints for database                                           │
│  • NSG rules restricting traffic                                            │
│  • Service endpoints for Azure services                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 3: APPLICATION                                                       │
│  • JWT validation with RS256                                                │
│  • Input validation (Pydantic)                                              │
│  • SQL injection prevention (ORM)                                           │
│  • XSS protection (CSP headers)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4: DATA                                                              │
│  • Encryption at rest (TDE)                                                 │
│  • Encryption in transit (TLS 1.3)                                          │
│  • Column-level encryption for PII                                          │
│  • Row-level security (RLS)                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 5: IDENTITY                                                          │
│  • Azure AD integration                                                     │
│  • MFA enforcement                                                          │
│  • Password policies (NIST guidelines)                                      │
│  • Session management                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Classification

| Classification | Data Types | Protection |
|----------------|-----------|------------|
| Critical | Passwords, MFA secrets | Hashed (Argon2), Encrypted |
| Sensitive | Email, Phone, PII | Encrypted at rest, Access logging |
| Internal | Roles, Permissions | Access control, Audit logs |
| Public | Organization names | Standard protection |

---

## 7. Scalability & Performance

### 7.1 Horizontal Scaling Strategy

- **Stateless Design**: No session state in application memory
- **Database Read Replicas**: For read-heavy operations
- **Redis Cluster**: Distributed caching
- **CDN**: Static asset caching

### 7.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (P95) | < 200ms | Application Insights |
| Page Load Time | < 2s | Lighthouse |
| Database Query Time (P95) | < 50ms | Query Store |
| Concurrent Users | 10,000 | Load Testing |
| Availability | 99.9% | Azure SLA |

---

## 8. Disaster Recovery

### 8.1 RPO/RTO Targets

| Component | RPO | RTO | Strategy |
|-----------|-----|-----|----------|
| Database | 1 hour | 4 hours | Geo-redundant backups |
| Application | 0 | 15 min | Multi-region deployment |
| Files/Assets | 24 hours | 4 hours | Geo-redundant storage |

### 8.2 Backup Strategy

- **Database**: Automated daily backups + point-in-time recovery (35 days)
- **Code**: GitHub repository with branch protection
- **Configuration**: Infrastructure as Code (Terraform)
- **Secrets**: Azure Key Vault with soft-delete

---

## 9. Decision Log

| Date | Decision | Alternatives | Rationale |
|------|----------|--------------|-----------|
| 2024-01 | Modular Monolith | Microservices | Team size, complexity |
| 2024-01 | FastAPI | Django, Flask | Performance, async, modern |
| 2024-01 | PostgreSQL | MySQL, Mongo | ACID, JSON support, Azure native |
| 2024-01 | React + MUI | Vue, Angular | Ecosystem, Azure integration |
| 2024-01 | Azure App Service | AKS, VMs | Managed platform, cost |
| 2024-01 | Casbin RBAC | Custom implementation | Policy-based, flexible |

---

## 10. Appendix

### A. API Rate Limits

| Endpoint Type | Rate Limit | Burst |
|--------------|------------|-------|
| Authentication | 10 req/min | 20 |
| General API | 1000 req/min | 2000 |
| Admin Operations | 100 req/min | 200 |
| Export/Download | 10 req/min | 20 |

### B. Compliance Considerations

- **GDPR**: Right to erasure, data portability
- **SOC 2**: Access controls, audit logging
- **ISO 27001**: Security controls, risk management

---

*Document Version: 1.0*
*Last Updated: 2024-01*
*Owner: System Architecture Team*
