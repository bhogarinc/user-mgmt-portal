# System Architecture — User Management Portal

## Executive Summary

This document provides a comprehensive overview of the system architecture for the **User Management Portal (UMP)** — a full-stack web application for user registration, authentication, profile management, and role-based access control.

---

## 1. Architecture Overview

### 1.1 System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER MANAGEMENT PORTAL                          │
│                        System Context                                │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                   ┌──────────────────────────────┐
│   │              │   HTTPS/REST      │                              │
│   │   End User   │◄─────────────────►│  User Management Portal      │
│   │  (Browser)   │                   │      (Web Application)       │
│   │              │                   │                              │
│   └──────────────┘                   └──────────────┬───────────────┘
│                                                    │
│                                                    │ SQL/TCP
│                                                    ▼
│                                      ┌──────────────────────────────┐
│                                      │   PostgreSQL 15              │
│                                      │   (User Data Store)          │
│                                      └──────────────────────────────┘
```

### 1.2 Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AZURE APP SERVICE                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Nginx (Reverse Proxy)                    │   │
│  │         • Static file serving (React SPA)                   │   │
│  │         • API routing (/api/* → FastAPI)                    │   │
│  │         • SSL termination                                   │   │
│  └─────────────────────────┬───────────────────────────────────┘   │
│                            │                                        │
│         ┌──────────────────┴──────────────────┐                    │
│         ▼                                     ▼                    │
│  ┌──────────────┐                   ┌──────────────────┐          │
│  │  React SPA   │                   │  FastAPI App     │          │
│  │  (Frontend)  │◄───API Calls────►│  (Backend)       │          │
│  │              │    (JSON/HTTPS)   │                  │          │
│  └──────────────┘                   └────────┬─────────┘          │
│                                              │                     │
│                                              │ SQLAlchemy          │
│                                              ▼                     │
│                                     ┌──────────────────┐          │
│                                     │  PostgreSQL      │          │
│                                     │  (Azure Managed) │          │
│                                     └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Selected Technologies

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| **Frontend** | React | 18.2.0 | Component-based, virtual DOM, large ecosystem |
| | TypeScript | 5.3.3 | Type safety, IDE support, maintainability |
| | Tailwind CSS | 3.4.0 | Utility-first, small bundle, responsive |
| | Vite | 5.0.0 | Fast dev server, optimized builds |
| **Backend** | Python | 3.11.7 | Performance, async/await, type hints |
| | FastAPI | 0.109.0 | Async support, auto-docs, Pydantic integration |
| | SQLAlchemy | 2.0.25 | Mature ORM, async support |
| | Pydantic | 2.5.3 | Data validation, settings management |
| **Database** | PostgreSQL | 15.x | ACID compliance, JSONB, full-text search |
| | Alembic | 1.13.1 | Database migrations |
| **Auth** | JWT | PyJWT 2.8.0 | Stateless, scalable, industry standard |
| | Bcrypt | Passlib 1.7.4 | Secure password hashing |
| **Infrastructure** | Azure App Service | - | PaaS simplicity, auto-scaling |
| | Docker | 24.x | Containerization, consistency |
| | GitHub Actions | - | CI/CD automation |

### 2.2 Architecture Style: Modular Monolith

**Why not Microservices?**
- Small team size (2-4 developers)
- Single bounded context (user management)
- Simpler deployment and testing
- No distributed system complexity
- Cost-effective for initial scale

**Modular Structure:**
```
backend/
├── api/              # API routes (FastAPI)
├── services/         # Business logic
├── models/           # Database models (SQLAlchemy)
├── schemas/          # Pydantic models
├── core/             # Shared utilities
└── db/               # Database configuration
```

---

## 3. Data Architecture

### 3.1 Database Schema

```sql
-- Core Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Roles for RBAC
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    permissions JSONB DEFAULT '[]'
);

-- User-Role Many-to-Many
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Immutable Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);
```

### 3.2 Data Flow

**User Registration:**
```
Browser → React Form → POST /api/v1/auth/register
  → FastAPI Validation → Password Hash (bcrypt)
  → PostgreSQL INSERT → Audit Log Entry
  → Response (201 Created)
```

**Authentication:**
```
Browser → POST /api/v1/auth/login (email, password)
  → FastAPI → Verify Password → Generate JWT
  → Return {access_token, refresh_token, user}
```

---

## 4. Integration Architecture

### 4.1 API Design

**Base URL:** `https://api.example.com/api/v1`

**Authentication:** Bearer JWT in Authorization header

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | No | Create new account |
| `/auth/login` | POST | No | Authenticate, get tokens |
| `/auth/refresh` | POST | No | Refresh access token |
| `/auth/logout` | POST | Yes | Invalidate tokens |
| `/users` | GET | Yes | List users (paginated) |
| `/users/{id}` | GET | Yes | Get user details |
| `/users/{id}` | PUT | Yes | Update user |
| `/users/{id}` | DELETE | Admin | Delete user |
| `/users/me` | GET | Yes | Current user profile |

### 4.2 Authentication Flow

```
┌─────────┐     Login Request      ┌─────────┐
│  Client │───────────────────────►│ FastAPI │
│         │  (email, password)     │         │
│         │                        │         │
│         │◄───────────────────────│         │
│         │   {access_token,       │         │
│         │    refresh_token}      │         │
└────┬────┘                        └─────────┘
     │
     │ API Request + Authorization: Bearer {access_token}
     ▼
┌─────────┐     Validate JWT       ┌─────────┐
│ FastAPI │───────────────────────►│  Auth   │
│         │                        │ Middleware
│         │◄───────────────────────│         │
│         │   Token Data           │         │
│         │   (user_id, role)      │         │
└─────────┘                        └─────────┘
```

---

## 5. Deployment Architecture

### 5.1 Environment Strategy

| Environment | URL | Purpose | Azure Plan |
|-------------|-----|---------|------------|
| **Development** | localhost | Local development | Docker Compose |
| **Staging** | staging.ump.example.com | Pre-production testing | B1 |
| **Production** | app.ump.example.com | Live application | B1/B2 |

### 5.2 CI/CD Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │───►│    Test     │───►│    Build    │───►│   Deploy    │
│   to GitHub │    │   Pytest    │    │   Docker    │    │   Azure     │
│             │    │   Jest      │    │   Image     │    │  App Svc    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
   Trigger           Coverage > 80%      Push to ACR      Health Check
```

### 5.3 Docker Configuration

**Multi-stage Dockerfile:**
1. **Stage 1:** Build React frontend (Node.js)
2. **Stage 2:** Install Python dependencies
3. **Stage 3:** Production runtime (Python + Nginx static files)

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security                                   │
│  • HTTPS/TLS 1.3 only                                       │
│  • Azure WAF (Web Application Firewall)                     │
│  • Private database endpoints                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Application Security                               │
│  • JWT authentication with short expiry (15 min)            │
│  • Input validation with Pydantic                           │
│  • SQL injection prevention (SQLAlchemy ORM)                │
│  • XSS protection (React sanitization)                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Data Security                                      │
│  • Bcrypt password hashing (salt + pepper)                  │
│  • Database encryption at rest (Azure managed)              │
│  • Audit logging for all sensitive operations               │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 RBAC Permissions

| Role | Users | Roles | Audit Logs | Admin Panel |
|------|-------|-------|------------|-------------|
| **Admin** | CRUD | CRUD | Read | Full Access |
| **Manager** | CRU | Read | Read | Limited |
| **User** | Read Self | - | - | - |

---

## 7. Scalability Strategy

### 7.1 Current Scale (1K-10K users)
- Single Azure App Service (B1)
- Azure PostgreSQL Basic tier
- Optional Redis for sessions

### 7.2 Growth Path (10K-50K users)
- Vertical scaling: B1 → B2 → B3
- PostgreSQL General Purpose tier
- CDN for static assets
- Read replicas for reporting

### 7.3 Scale (50K+ users)
- Horizontal scaling with load balancer
- Database connection pooling (PgBouncer)
- Separate audit log service
- Consider microservices migration

---

## 8. Monitoring & Observability

### 8.1 Metrics

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| Response Time | App Insights | > 500ms p95 |
| Error Rate | App Insights | > 1% |
| CPU Usage | Azure Monitor | > 80% |
| Database Connections | PostgreSQL | > 80% |

### 8.2 Logging

- **Structured logging** with correlation IDs
- **Log levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Retention:** 30 days application logs, 1 year audit logs

---

## 9. Jira Tickets

Architecture work tracked in project **BHOGAR**:

| Ticket | Summary | Status |
|--------|---------|--------|
| BHOGAR-282 | System Overview and Container Design | Created |
| BHOGAR-283 | Technology Stack Selection | Created |
| BHOGAR-284 | Data Architecture and Database Design | Created |
| BHOGAR-285 | Integration and API Design | Created |
| BHOGAR-286 | Deployment and Infrastructure | Created |

---

## 10. References

- [System Overview](./01-system-overview.md) - C4 diagrams
- [Technology Stack](./02-technology-stack.md) - Detailed tech decisions
- [Data Architecture](./03-data-architecture.md) - Database design
- [Integration Architecture](./04-integration-architecture.md) - API specs
- [Deployment Architecture](./05-deployment-architecture.md) - Infrastructure

---

**Document Version:** 1.0  
**Last Updated:** 2024-01-25  
**Owner:** System Architect  
**Review Cycle:** Quarterly
