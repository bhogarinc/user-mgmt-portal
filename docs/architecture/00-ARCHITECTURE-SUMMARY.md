# System Architecture Summary

## User Management Portal

### Overview

The User Management Portal is a full-stack web application built with a **Modular Monolith** architecture. This approach provides the simplicity of a monolith with clear internal boundaries for maintainability.

---

## Architecture Decisions

### 1. Modular Monolith (Not Microservices)

**Why:**
- Small team size (2-4 developers)
- Single bounded context (user management)
- Simpler deployment and testing
- No distributed system complexity
- Cost-effective for initial scale

**Structure:**
```
backend/
├── api/           # API layer (routes, dependencies)
├── services/      # Business logic
├── models/        # Database models
├── schemas/       # Pydantic models
├── core/          # Shared utilities
└── db/            # Database configuration
```

### 2. Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Frontend** | React 18 + TypeScript | Performance, ecosystem, type safety |
| **Backend** | FastAPI + Python 3.11 | Async support, auto-docs, performance |
| **Database** | PostgreSQL 15 | ACID compliance, JSONB, full-text search |
| **Hosting** | Azure App Service | PaaS simplicity, auto-scaling |
| **Auth** | JWT (access + refresh) | Stateless, scalable, industry standard |

### 3. Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SECURITY ZONES                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Public     │    │     DMZ      │    │   Internal   │  │
│  │  (Internet)  │───▶│  (App Svc)   │───▶│  (Database)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                  │                      ▲         │
│         └──────────────────┴──────────────────────┘         │
│                     HTTPS/TLS 1.3 only                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Data Flow

```
User Registration:
  Browser → React → FastAPI → Validation → Password Hash → PostgreSQL → Audit Log

Authentication:
  Browser → Credentials → FastAPI → Verify → JWT Generate → Response + Tokens

Profile Update:
  Browser → JWT → FastAPI → Auth Check → Update DB → Audit Log → Response
```

---

## Key Components

### Authentication System
- **JWT Access Tokens**: 15-minute expiry
- **Refresh Tokens**: 7-day expiry
- **Password Security**: Bcrypt hashing with salt
- **Account Protection**: Lockout after 5 failed attempts

### RBAC (Role-Based Access Control)
- **Roles**: admin, manager, user
- **Permissions**: Granular permission system
- **Hierarchical**: admin > manager > user

### Audit Logging
- **Immutable Records**: Append-only audit trail
- **Tracked Events**: Login, CRUD operations, password changes
- **Compliance**: Security and regulatory requirements

---

## Scalability Roadmap

### Phase 1: Current (1K-10K users)
- Single Azure App Service instance
- Azure PostgreSQL Basic tier
- Optional Redis for sessions

### Phase 2: Growth (10K-50K users)
- Vertical scaling (B1 → B2 → B3)
- PostgreSQL read replicas
- CDN for static assets

### Phase 3: Scale (50K+ users)
- Horizontal scaling with load balancer
- Database optimization
- Separate audit service

---

## Documentation

Detailed architecture documentation:

1. [System Overview](./01-system-overview.md) - C4 diagrams and architecture style
2. [Technology Stack](./02-technology-stack.md) - Complete tech stack with versions
3. [Data Architecture](./03-data-architecture.md) - Database schema and data flow
4. [Integration Architecture](./04-integration-architecture.md) - API design and auth flow
5. [Deployment Architecture](./05-deployment-architecture.md) - Infrastructure and CI/CD

---

## Jira Tickets

Architecture work tracked in Jira:

- **BHOGAR-282**: System Overview and Container Design
- **BHOGAR-283**: Technology Stack Selection
- **BHOGAR-284**: Data Architecture and Database Design
- **BHOGAR-285**: Integration and API Design
- **BHOGAR-286**: Deployment and Infrastructure

---

*Document Version: 1.0*  
*Last Updated: 2024-01-25*  
*Owner: System Architect*
