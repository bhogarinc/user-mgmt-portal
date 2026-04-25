# User Management Portal — Architecture Documentation

## Overview

This directory contains comprehensive architecture documentation for the User Management Portal, a full-stack web application for user management with JWT authentication.

## Architecture Documents

| Document | Description | Key Topics |
|----------|-------------|------------|
| [01-system-overview.md](./01-system-overview.md) | System context and container diagrams | C4 architecture, system boundaries, modular monolith justification |
| [02-technology-stack.md](./02-technology-stack.md) | Complete technology stack selection | Frontend (React/TypeScript), Backend (FastAPI), Infrastructure (Azure) |
| [03-data-architecture.md](./03-data-architecture.md) | Data flow and database design | ERD, data flows, caching strategy, migrations |
| [04-integration-architecture.md](./04-integration-architecture.md) | API gateway and authentication | JWT flow, rate limiting, security headers, external integrations |
| [05-deployment-architecture.md](./05-deployment-architecture.md) | Infrastructure and deployment | Azure resources, CI/CD pipeline, monitoring, scaling |

## Quick Reference

### Project Identifiers
- **JIRA_PROJECT_KEY**: UMP
- **GITHUB_REPO**: user-mgmt-portal
- **CONFLUENCE_SPACE**: UMP

### Architecture Tickets (Jira)

The following architecture tasks should be created in Jira project **UMP**:

| Ticket | Title | Priority |
|--------|-------|----------|
| ARCH-001 | Design System Architecture Overview | Highest |
| ARCH-002 | Define Technology Stack Selection | Highest |
| ARCH-003 | Design Data Architecture | High |
| ARCH-004 | Design Integration Architecture | High |
| ARCH-005 | Design Deployment Architecture | High |

### Technology Stack Summary

```
Frontend:        React 18 + TypeScript 5 + Tailwind CSS + Vite
Backend:         FastAPI + Python 3.11 + SQLAlchemy 2.0 + Alembic
Database:        PostgreSQL 15 + Redis (caching)
Authentication:  JWT (access + refresh tokens) + bcrypt/Argon2
Infrastructure:  Azure App Service + Azure PostgreSQL + Azure Monitor
CI/CD:           GitHub Actions + Azure Container Registry
Testing:         pytest + React Testing Library + Playwright
```

## Architecture Principles

1. **Security First**: JWT authentication, HTTPS-only, security headers, input validation
2. **Simplicity**: Modular monolith architecture for faster development and easier maintenance
3. **Scalability**: Horizontal scaling path from B1 to multiple instances
4. **Observability**: Comprehensive logging, metrics, and distributed tracing
5. **DevOps**: Infrastructure as code, automated CI/CD, environment parity

## Diagram Key

Architecture diagrams use ASCII art for version control compatibility. For visual diagrams, use:
- [C4 Model](https://c4model.com/) for system architecture
- [dbdiagram.io](https://dbdiagram.io) for database schemas
- [Mermaid](https://mermaid.js.org/) for flow diagrams

---

**Document Owner**: System Architect  
**Last Updated**: 2024-01-25  
**Review Cycle**: Quarterly
