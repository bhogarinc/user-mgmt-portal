# TaskFlow System Architecture

## Executive Summary

TaskFlow is a real-time task management application built as a modern web application using a microservices-oriented architecture deployed on Azure Kubernetes Service (AKS). The system supports real-time collaboration through WebSocket connections, role-based access control, and comprehensive analytics.

---

## 1. Architecture Overview

### 1.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   End Users  │  │   Mobile     │  │  Third-Party │  │   Azure AD /    │ │
│  │  (Browser)   │  │    Apps      │  │   Systems    │  │   OAuth 2.0     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────────────────┘ │
└─────────┼─────────────────┼─────────────────┼──────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TASKFLOW PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Azure API Management                            │   │
│  │              (Rate Limiting, API Gateway, Caching)                   │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│  ┌───────────────────────────────┼─────────────────────────────────────┐   │
│  │                               ▼                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              Azure Kubernetes Service (AKS)                  │   │   │
│  │  │                                                              │   │   │
│  │  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │   │
│  │  │   │  API Gateway │  │  WebSocket   │  │  Analytics   │      │   │   │
│  │  │   │   Service    │  │   Service    │  │   Service    │      │   │   │
│  │  │   │   (FastAPI)  │  │  (Socket.io) │  │   (FastAPI)  │      │   │   │
│  │  │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │   │   │
│  │  │          │                 │                 │              │   │   │
│  │  │          ▼                 ▼                 ▼              │   │   │
│  │  │   ┌─────────────────────────────────────────────────────┐   │   │   │
│  │  │   │           Message Bus (Azure Service Bus)          │   │   │   │
│  │  │   └─────────────────────────────────────────────────────┘   │   │   │
│  │  │                                                              │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │   │  PostgreSQL  │  │    Redis     │  │ Azure Blob   │             │   │
│  │   │   Cluster    │  │   Cluster    │  │   Storage    │             │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Style: Modular Monolith with Microservices Capabilities

**Decision**: We adopt a **Modular Monolith** architecture that can evolve into microservices.

**Rationale**:
- **Development Velocity**: Single codebase enables faster initial development
- **Operational Simplicity**: Easier deployment and monitoring in early stages
- **Database Consistency**: Single PostgreSQL instance with schema separation
- **Migration Path**: Clear service boundaries allow future extraction to microservices

**Service Boundaries** (Modules):
1. **Core API Module**: Task management, user management, project management
2. **Real-time Module**: WebSocket handling for live updates
3. **Analytics Module**: Reporting, dashboards, metrics aggregation

---

## 2. Technology Stack Selection

### 2.1 Frontend Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| Framework | React 18 | Concurrent features, automatic batching, excellent ecosystem |
| Language | TypeScript 5.0 | Type safety, better developer experience, reduced runtime errors |
| Styling | TailwindCSS 3.4 | Utility-first, consistent design system, smaller bundle size |
| State Management | Zustand + TanStack Query | Lightweight global state, powerful server state management |
| UI Components | Radix UI + Tailwind | Accessible, unstyled primitives for custom theming |
| Real-time | Socket.io Client | Reliable WebSocket abstraction with fallbacks |
| Build Tool | Vite 5 | Fast HMR, optimized builds, native ESM support |
| Testing | Vitest + React Testing Library | Fast unit tests, user-centric testing approach |
| E2E Testing | Playwright | Cross-browser testing, reliable automation |

### 2.2 Backend Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| Framework | FastAPI 0.104+ | High performance, automatic OpenAPI docs, async support |
| Language | Python 3.11 | Modern syntax, performance improvements, great ecosystem |
| ORM | SQLAlchemy 2.0 | Mature, flexible, async support with asyncpg |
| Migrations | Alembic | Database versioning, works seamlessly with SQLAlchemy |
| Validation | Pydantic v2 | Fast validation, JSON Schema generation, type hints |
| Authentication | FastAPI-Users + JWT | battle-tested auth patterns, role management |
| WebSocket | Socket.io | Room management, namespace support, fallback mechanisms |
| Task Queue | Celery + Redis | Background job processing, periodic tasks |
| API Documentation | OpenAPI 3.1 | Auto-generated, interactive docs at `/docs` |

### 2.3 Database Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| Primary DB | PostgreSQL 15 | ACID compliance, JSON support, excellent performance |
| Connection Pool | PgBouncer | Efficient connection management for high concurrency |
| Cache Layer | Redis 7 | Sub-millisecond latency, pub/sub for real-time features |
| Search | PostgreSQL Full-Text | Built-in, no additional infrastructure needed |
| File Storage | Azure Blob Storage | Scalable, CDN integration, cost-effective |

### 2.4 Infrastructure Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| Cloud Provider | Microsoft Azure | Enterprise integration, strong Kubernetes support |
| Container Orchestration | AKS | Managed Kubernetes, auto-scaling, Azure integration |
| Container Registry | ACR | Geo-replication, vulnerability scanning |
| API Gateway | Azure API Management | Rate limiting, caching, developer portal |
| CDN | Azure Front Door | Global load balancing, WAF, DDoS protection |
| Secrets Management | Azure Key Vault | HSM-backed, fine-grained access control |
| Monitoring | Azure Monitor + Prometheus | Native Azure integration + open-source flexibility |
| Logging | Grafana Loki | Cost-effective, label-based indexing |

### 2.5 CI/CD Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| CI/CD Platform | GitHub Actions | Native GitHub integration, extensive marketplace |
| Infrastructure as Code | Terraform | Multi-cloud support, state management |
| GitOps | ArgoCD | Declarative deployments, drift detection |
| Image Scanning | Trivy | CVE detection, IaC security scanning |
| Code Quality | SonarQube | Static analysis, code coverage tracking |

---

## 3. Data Architecture

### 3.1 Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL SCHEMA DESIGN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   tenants    │────▶│   users      │◀────│    roles     │                │
│  │  (schema:    │     │  (schema:    │     │  (schema:    │                │
│  │   public)    │     │   public)    │     │   public)    │                │
│  └──────────────┘     └──────┬───────┘     └──────────────┘                │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   projects   │◀────│  workspaces  │────▶│    teams     │                │
│  │  (isolated   │     │  (schema per │     │  (isolated   │                │
│  │   per tenant)│     │   tenant)    │     │   per tenant)│                │
│  └──────┬───────┘     └──────────────┘     └──────────────┘                │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │    sprints   │────▶│    boards    │────▶│    tasks     │                │
│  │  (isolated   │     │  (isolated   │     │  (isolated   │                │
│  │   per tenant)│     │   per tenant)│     │   per tenant)│                │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                │
│                                                   │                         │
│                              ┌────────────────────┼────────────────────┐   │
│                              ▼                    ▼                    ▼   │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────┐ │
│  │   comments   │     │  attachments │     │   labels     │     │custom  │ │
│  │  (isolated   │     │  (isolated   │     │  (isolated   │     │fields  │ │
│  │   per tenant)│     │   per tenant)│     │   per tenant)│     │        │ │
│  └──────────────┘     └──────────────┘     └──────────────┘     └────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Multi-Tenancy Strategy: Schema-per-Tenant

**Decision**: Use PostgreSQL schema-per-tenant with row-level security (RLS) as a fallback.

**Benefits**:
- Strong data isolation between tenants
- Ability to customize schema per tenant (custom fields)
- Efficient backup/restore per tenant
- Query performance optimization per tenant

**Implementation**:
```sql
-- Tenant isolation using schemas
CREATE SCHEMA tenant_{tenant_id};

-- Row-level security as additional protection
ALTER TABLE tenant_{tenant_id}.tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant_{tenant_id}.tasks
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 3.3 Data Flow Diagrams

#### 3.3.1 Task Creation Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────▶│  API Gateway │────▶│  FastAPI     │────▶│  PostgreSQL  │
│          │     │  (Validation)│     │  (Business   │     │  (Persist)   │
└──────────┘     └──────────────┘     │   Logic)     │     └──────────────┘
                                      └──────┬───────┘            │
                                             │                    │
                                             ▼                    │
                                      ┌──────────────┐            │
                                      │    Redis     │◀───────────┘
                                      │  (Cache      │   (Invalidation)
                                      │   Update)    │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │  WebSocket   │────▶ Connected Clients
                                      │  (Broadcast) │      (Real-time Update)
                                      └──────────────┘
```

#### 3.3.2 Analytics Aggregation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│   Celery     │────▶│  Analytics   │────▶│   Redis      │
│  (Change     │     │   Worker     │     │  Aggregation │     │  (Cached     │
│   Events)    │     │  (Scheduled) │     │   Pipeline   │     │   Results)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                                                            │
       │                                                            ▼
       │                                                    ┌──────────────┐
       │                                                    │  Dashboard   │
       │                                                    │   (Read)     │
       ▼                                                    └──────────────┘
┌──────────────┐
│  Azure Blob  │
│  (Historical │
│   Data)      │
└──────────────┘
```

### 3.4 Caching Strategy

| Cache Layer | Technology | TTL | Use Case |
|-------------|------------|-----|----------|
| Application Cache | Redis | 5 min | User sessions, permissions |
| Query Cache | Redis | 10 min | Frequent queries, dashboard data |
| CDN Cache | Azure CDN | 1 hour | Static assets, API responses |
| Browser Cache | Service Worker | Variable | Offline support, app shell |

**Cache Invalidation Strategy**:
- **Write-through**: Update cache on write operations
- **Event-driven**: Invalidate using Redis pub/sub
- **Time-based**: TTL with background refresh

---

## 4. Integration Architecture

### 4.1 API Gateway Design

```yaml
# Azure API Management Policy
apiVersion: "2023-03-01"
name: taskflow-api
properties:
  format: openapi+json
  value: |
    openapi: 3.0.0
    info:
      title: TaskFlow API
      version: 1.0.0
    paths:
      /api/v1/tasks:
        get:
          summary: List tasks
          parameters:
            - name: X-Tenant-ID
              in: header
              required: true
          responses:
            200:
              description: Task list
      /api/v1/tasks/{id}:
        get:
          summary: Get task details
          responses:
            200:
              description: Task details
    
    # Rate Limiting Configuration
    x-ms-rate-limit:
      - calls: 100
        renewalPeriod: 60
      - calls: 1000
        renewalPeriod: 3600
```

### 4.2 External Service Integrations

| Service | Integration Type | Auth Method | Data Flow |
|---------|-----------------|-------------|-----------|
| Azure AD | OAuth 2.0 / SAML | Client Credentials | SSO, User sync |
| Slack | REST API + Webhooks | OAuth 2.0 | Notifications, commands |
| GitHub | REST API + Webhooks | GitHub Apps | Issue linking, PR status |
| Jira | REST API | API Token | Bidirectional sync |
| Google Calendar | REST API | OAuth 2.0 | Sprint scheduling |

### 4.3 Message Bus / Event Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT-DRIVEN ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Azure Service Bus (Topics)                        │   │
│  │                                                                      │   │
│  │   Topics:                                                            │   │
│  │   ├── taskflow.tasks.created                                         │   │
│  │   ├── taskflow.tasks.updated                                         │   │
│  │   ├── taskflow.tasks.deleted                                         │   │
│  │   ├── taskflow.sprints.started                                       │   │
│  │   ├── taskflow.sprints.ended                                         │   │
│  │   ├── taskflow.users.invited                                         │   │
│  │   └── taskflow.notifications.send                                    │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌──────────────┐           ┌──────────────┐           ┌──────────────┐    │
│  │  Analytics   │           │ Notification │           │   Search     │    │
│  │   Service    │           │   Service    │           │   Indexer    │    │
│  │  (Consumer)  │           │  (Consumer)  │           │  (Consumer)  │    │
│  └──────────────┘           └──────────────┘           └──────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────▶│  Azure AD    │────▶│  API Gateway │────▶│   FastAPI    │
│          │     │  (OAuth 2.0) │     │  (JWT Verify)│     │   (Validate  │
└──────────┘     └──────────────┘     └──────────────┘     │   Claims)    │
                                                           └──────┬───────┘
                                                                  │
                                                                  ▼
                                                           ┌──────────────┐
                                                           │   Redis      │
                                                           │  (Session    │
                                                           │   Store)     │
                                                           └──────────────┘

Token Structure (JWT):
{
  "sub": "user-uuid",
  "tid": "tenant-uuid",
  "roles": ["admin", "manager"],
  "permissions": ["tasks:create", "tasks:read"],
  "iat": 1704067200,
  "exp": 1704153600
}
```

---

## 5. Deployment Architecture

### 5.1 Environment Strategy

| Environment | Purpose | Database | Scaling | Monitoring |
|-------------|---------|----------|---------|------------|
| Development | Feature development | Single instance | 1 replica | Basic logs |
| Staging | Integration testing | Production clone | 2 replicas | Full stack |
| Production | Live traffic | HA cluster | Auto-scaling | Full stack + alerting |

### 5.2 Kubernetes Architecture

```yaml
# Namespace Structure
apiVersion: v1
kind: Namespace
metadata:
  name: taskflow-prod
  labels:
    environment: production
    app: taskflow
---
# Deployment Structure
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taskflow-api
  namespace: taskflow-prod
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: api
          image: taskflow.azurecr.io/api:v1.0.0
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
```

### 5.3 High Availability Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HIGH AVAILABILITY SETUP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Azure Traffic Manager                         │   │
│  │                    (Geographic Load Balancing)                       │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│         ┌──────────────────────┼──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │  West US 2   │      │  East US 2   │      │  West Europe │              │
│  │    AKS       │      │    AKS       │      │    AKS       │              │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘              │
│         │                     │                     │                       │
│         ▼                     ▼                     ▼                       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │  PostgreSQL  │      │  PostgreSQL  │      │  PostgreSQL  │              │
│  │  (Primary)   │◀────▶│  (Replica)   │◀────▶│  (Replica)   │              │
│  └──────────────┘      └──────────────┘      └──────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Monitoring and Observability Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OBSERVABILITY STACK                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Application │────▶│  OpenTelemetry│────▶│   Jaeger     │               │
│  │  (Instrumented)    │   Collector  │     │  (Tracing)   │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Prometheus  │◀────│  Metrics     │────▶│   Grafana    │                │
│  │  (Scraping)  │     │  Exporters   │     │  (Dashboards)│                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Application │────▶│   Loki       │────▶│   Grafana    │                │
│  │  Logs        │     │  (Aggregation)│     │  (Log Query) │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Azure       │────▶│  Application │────▶│  Alert Rules │                │
│  │  Monitor     │     │  Insights    │     │  (PagerDuty) │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Metrics**:
- **Application**: Request rate, error rate, latency (RED metrics)
- **Infrastructure**: CPU, memory, disk I/O, network
- **Business**: Active users, tasks created, sprint velocity

---

## 6. Security Architecture

### 6.1 Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY LAYERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Network Security                                                   │
│  ├── Azure DDoS Protection Standard                                          │
│  ├── Web Application Firewall (WAF)                                          │
│  ├── Network Security Groups (NSG)                                           │
│  └── Private Link for database access                                        │
│                                                                              │
│  Layer 2: Application Security                                               │
│  ├── Input validation and sanitization                                       │
│  ├── SQL injection prevention (parameterized queries)                        │
│  ├── XSS protection (CSP headers)                                            │
│  └── CSRF tokens                                                             │
│                                                                              │
│  Layer 3: Data Security                                                      │
│  ├── Encryption at rest (Azure-managed keys)                                 │
│  ├── Encryption in transit (TLS 1.3)                                         │
│  ├── Column-level encryption for PII                                         │
│  └── Regular backup encryption                                               │
│                                                                              │
│  Layer 4: Access Control                                                     │
│  ├── Role-based access control (RBAC)                                        │
│  ├── Attribute-based access control (ABAC) for fine-grained permissions      │
│  ├── Multi-factor authentication (MFA)                                       │
│  └── Regular access reviews                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 API Security

| Control | Implementation |
|---------|----------------|
| Authentication | JWT with RS256 signing |
| Authorization | OAuth 2.0 scopes + custom permissions |
| Rate Limiting | 100 req/min per user, 1000 req/hour per API key |
| Input Validation | Pydantic schemas + strict type checking |
| Output Encoding | JSON serialization with safe defaults |
| CORS | Whitelist-based with strict origins |

---

## 7. Scalability Considerations

### 7.1 Horizontal Scaling Strategy

| Component | Scaling Trigger | Max Replicas |
|-----------|-----------------|--------------|
| API Pods | CPU > 70% | 20 |
| WebSocket Pods | Connections > 1000/pod | 10 |
| Worker Pods | Queue depth > 100 | 10 |
| PostgreSQL | Read replicas | 5 |
| Redis | Cluster mode | 6 nodes |

### 7.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 200ms | Datadog APM |
| WebSocket Latency | < 50ms | Custom metrics |
| Page Load Time | < 2s | Lighthouse |
| Database Query Time (p99) | < 100ms | pg_stat_statements |
| Availability | 99.9% | Azure Monitor |

---

## 8. Disaster Recovery

### 8.1 RPO/RTO Targets

| Scenario | RPO | RTO |
|----------|-----|-----|
| Database failure | 5 minutes | 15 minutes |
| Region failure | 1 hour | 4 hours |
| Complete service loss | 1 hour | 2 hours |

### 8.2 Backup Strategy

- **PostgreSQL**: Continuous backup to Azure Blob Storage, point-in-time recovery
- **Redis**: Daily snapshots, AOF persistence
- **File Storage**: Geo-redundant storage (GRS)
- **Configuration**: GitOps with ArgoCD, state in Git

---

## 9. Architecture Decision Records

### ADR-001: Modular Monolith over Microservices
**Status**: Accepted
**Context**: Early-stage product requiring rapid iteration
**Decision**: Start with modular monolith, extract services when boundaries are clear
**Consequences**: Faster development, simpler operations, clear migration path

### ADR-002: PostgreSQL over NoSQL
**Status**: Accepted
**Context**: Complex relational data with ACID requirements
**Decision**: Use PostgreSQL with JSON support for flexibility
**Consequences**: Strong consistency, proven technology, JSON for schema evolution

### ADR-003: Azure over AWS/GCP
**Status**: Accepted
**Context**: Enterprise environment with existing Microsoft stack
**Decision**: Use Azure for all infrastructure
**Consequences**: Better AD integration, consistent billing, enterprise support

### ADR-004: Socket.io over native WebSocket
**Status**: Accepted
**Context**: Need for reliable real-time communication with fallback
**Decision**: Use Socket.io with Redis adapter
**Consequences**: Automatic reconnection, room management, broader browser support

---

## 10. Appendix

### A. Technology Versions
- React: 18.2.0
- TypeScript: 5.3.0
- FastAPI: 0.104.1
- Python: 3.11
- PostgreSQL: 15.4
- Redis: 7.2
- Kubernetes: 1.28

### B. Reference Links
- [C4 Model](https://c4model.com/)
- [Azure Well-Architected Framework](https://docs.microsoft.com/azure/architecture/framework/)
- [Twelve-Factor App](https://12factor.net/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

---

*Document Version: 1.0*
*Last Updated: 2024*
*Owner: System Architecture Team*
