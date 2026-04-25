# System Architecture Overview

## User Management Portal — C4 Architecture Documentation

---

## 1. System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER MANAGEMENT PORTAL                            │
│                              System Context                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                    ┌──────────────────────────┐
    │              │  HTTPS/REST        │                          │
    │   End User   │◄──────────────────►│  User Management Portal  │
    │  (Browser)   │                    │      (Web Application)   │
    │              │                    │                          │
    └──────────────┘                    └────────────┬─────────────┘
                                                     │
                                                     │ SQL/TCP
                                                     ▼
                                          ┌──────────────────────┐
                                          │   PostgreSQL 15      │
                                          │   (User Data Store)  │
                                          └──────────────────────┘
                                                     ▲
                                                     │ Audit Logs
                                          ┌──────────┴──────────┐
                                          │   Azure Monitor     │
                                          │  (Observability)    │
                                          └─────────────────────┘
```

### External Actors

| Actor | Description | Interaction |
|-------|-------------|-------------|
| **End User** | Portal users with various roles (admin, manager, viewer) | Access via web browser; performs CRUD on user data |
| **System Admin** | Infrastructure administrators | Deploy, monitor, and maintain the application |

### External Systems

| System | Purpose | Protocol |
|--------|---------|----------|
| **PostgreSQL 15** | Primary relational database | SQL/TCP 5432 |
| **Azure Monitor** | Logging, metrics, and alerting | HTTPS/REST |
| **Azure AD (Optional)** | SSO integration for enterprise | OAuth 2.0/OpenID Connect |

---

## 2. Container Diagram (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        USER MANAGEMENT PORTAL                                │
│                           Container View                                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐         ┌─────────────────────────────────────────────┐
│   Web Browser       │         │           Azure App Service                 │
│  (React SPA)        │         │  ┌─────────────────────────────────────┐   │
│                     │         │  │      Nginx (Reverse Proxy)          │   │
│  ┌───────────────┐  │ HTTPS   │  │  • Static file serving              │   │
│  │  React 18     │  │◄───────►│  │  • API routing (/api/*)             │   │
│  │  TypeScript   │  │  443    │  │  • SSL termination                  │   │
│  │  Tailwind CSS │  │         │  │  • Gzip compression                 │   │
│  └───────┬───────┘  │         │  └──────────────┬──────────────────────┘   │
│          │          │         │                 │                          │
│          │ API calls│         │                 ▼                          │
│          │ (JSON)   │         │  ┌─────────────────────────────────────┐   │
│          │          │         │  │     FastAPI Application             │   │
│          │          │         │  │  ┌─────────────────────────────┐    │   │
│          │          │         │  │  │  API Layer (Routes)         │    │   │
│          │          │         │  │  │  • /auth/* (JWT handling)   │    │   │
│          │          │         │  │  │  • /users/* (CRUD)          │    │   │
│          │          │         │  │  └─────────────────────────────┘    │   │
│          │          │         │  │  ┌─────────────────────────────┐    │   │
│          │          │         │  │  │  Service Layer (Business)   │    │   │
│          │          │         │  │  │  • AuthService              │    │   │
│          │          │         │  │  │  • UserService              │    │   │
│          │          │         │  │  │  • AuditService             │    │   │
│          │          │         │  │  └─────────────────────────────┘    │   │
│          │          │         │  │  ┌─────────────────────────────┐    │   │
│          │          │         │  │  │  Data Layer (SQLAlchemy)    │    │   │
│          │          │         │  │  │  • UserRepository           │    │   │
│          │          │         │  │  │  • AuditLogRepository       │    │   │
│          │          │         │  │  └─────────────────────────────┘    │   │
│          │          │         │  └─────────────────────────────────────┘   │
│          │          │         └─────────────────────────────────────────────┘
│          │          │                         │
│          │          │                         │ SQLAlchemy/AsyncPG
│          │          │                         ▼
│          │          │         ┌─────────────────────────────────────────────┐
│          │          │         │        Azure Database for PostgreSQL        │
│          │          │         │  ┌─────────────────────────────────────┐   │
│          │          │         │  │  • users table                      │   │
│          │          │         │  │  • audit_logs table                 │   │
│          │          │         │  │  • roles & permissions              │   │
│          │          │         │  │  • sessions (optional Redis)        │   │
│          │          │         │  └─────────────────────────────────────┘   │
│          │          │         └─────────────────────────────────────────────┘
│          │          │
│          │          │         ┌─────────────────────────────────────────────┐
│          │          │         │           Azure Monitor / App Insights      │
│          │          │         │  • Application logs                         │
│          │          │         │  • Performance metrics                      │
│          │          │         │  • Custom events (login, CRUD ops)          │
│          │          │         └─────────────────────────────────────────────┘
```

---

## 3. Architecture Style Justification

### Selected Architecture: **Modular Monolith**

We have chosen a **Modular Monolith** architecture over microservices for the following reasons:

#### ✅ Advantages for This Project

| Factor | Rationale |
|--------|-----------|
| **Team Size** | Small team (2-4 developers); microservices overhead not justified |
| **Complexity** | Single bounded context (user management); no complex service boundaries |
| **Deployment** | Simple deployment to Azure App Service; no orchestration complexity |
| **Data Consistency** | Single PostgreSQL database ensures ACID transactions across all operations |
| **Performance** | No network overhead between services; in-process method calls |
| **Development Velocity** | Faster development with single codebase; easier testing |
| **Cost** | Single Azure App Service instance vs. multiple containers/services |

#### 📊 Comparison Matrix

| Criteria | Modular Monolith | Microservices | Serverless |
|----------|-----------------|---------------|------------|
| Initial Complexity | Low | High | Medium |
| Operational Overhead | Low | High | Low |
| Scalability | Vertical + Limited Horizontal | Horizontal | Automatic |
| Data Consistency | Strong | Eventual | Depends |
| Team Autonomy | Low | High | Medium |
| Deployment Complexity | Low | High | Low |
| Cost (Small Scale) | Low | High | Medium |
| **Fit for UMP** | **✅ Excellent** | ❌ Overkill | ⚠️ Vendor lock-in |

#### 🏗️ Modular Structure Within Monolith

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── core/                   # Shared utilities
│   │   ├── config.py           # Environment configuration
│   │   ├── security.py         # JWT, password hashing
│   │   └── logging.py          # Structured logging
│   ├── api/                    # API layer (routes)
│   │   ├── deps.py             # FastAPI dependencies
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   └── users.py        # User management endpoints
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── audit_service.py
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── audit_log.py
│   │   └── base.py
│   ├── schemas/                # Pydantic models (DTOs)
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── common.py
│   └── db/                     # Database layer
│       ├── session.py          # Async session management
│       └── base_class.py       # Declarative base
```

---

## 4. Scalability Strategy

### Current Scale (B1 App Service Plan)
- **Users**: 1,000 - 10,000
- **Requests/day**: 10,000 - 100,000
- **Database**: Azure PostgreSQL — Basic tier

### Growth Path

```
Phase 1: Vertical Scaling (Current)
├── Upgrade App Service Plan: B1 → B2 → B3
├── Upgrade PostgreSQL: Basic → General Purpose
└── Add Redis caching for sessions

Phase 2: Read Replicas (50K+ users)
├── PostgreSQL read replica for reporting queries
├── CDN for static assets
└── Application Insights for performance monitoring

Phase 3: Horizontal Scaling (100K+ users)
├── Multiple App Service instances with load balancer
├── Database sharding by tenant (if multi-tenant)
├── Separate audit log service
└── Consider migration to microservices
```

---

## 5. Security Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURITY ZONES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Public    │    │   DMZ       │    │   Internal/Secure   │ │
│  │  (Internet) │───►│  (App Svc)  │───►│   (Database)        │ │
│  │             │    │             │    │                     │ │
│  │  • Browser  │    │  • Nginx    │    │  • PostgreSQL       │ │
│  │  • CDN      │    │  • FastAPI  │    │  • No public IP     │ │
│  │             │    │  • WAF      │    │  • Private endpoint │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                      ▲             │
│         │                  │                      │             │
│         └──────────────────┴──────────────────────┘             │
│                    HTTPS/TLS 1.3 only                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Decision Log

| ID | Decision | Alternatives | Rationale | Date |
|----|----------|--------------|-----------|------|
| ARCH-001 | Modular Monolith | Microservices, Serverless | Team size, complexity, cost | 2024-01 |
| ARCH-002 | Azure App Service | AKS, VMs | PaaS simplicity, auto-scaling | 2024-01 |
| ARCH-003 | PostgreSQL 15 | MySQL, SQL Server | JSON support, robustness, cost | 2024-01 |
| ARCH-004 | FastAPI | Django, Flask, Node.js | Performance, type safety, async | 2024-01 |
| ARCH-005 | React 18 | Vue, Angular | Ecosystem, team familiarity | 2024-01 |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-25  
**Owner**: System Architect  
**Review Cycle**: Quarterly
