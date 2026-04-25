# Data Architecture

## User Management Portal — Data Flow & Schema Design

---

## 1. Data Flow Diagrams

### 1.1 User Registration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER REGISTRATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
    │  Client  │         │  FastAPI │         │  Service │         │   DB     │
    └────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
         │                    │                    │                    │
         │ 1. POST /register  │                    │                    │
         │───────────────────►│                    │                    │
         │ {email, password,  │                    │                    │
         │  full_name}        │                    │                    │
         │                    │                    │                    │
         │                    │ 2. Validate input  │                    │
         │                    │ (Pydantic schema)  │                    │
         │                    │                    │                    │
         │                    │ 3. Check email     │                    │
         │                    │    uniqueness      │                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 4. Query users     │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│ (exists?)          │
         │                    │                    │                    │
         │                    │ 5. Hash password   │                    │
         │                    │ (bcrypt/Argon2)    │                    │
         │                    │                    │                    │
         │                    │ 6. Create user     │                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 7. INSERT user     │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│ (user created)     │
         │                    │                    │                    │
         │                    │ 8. Create audit log│                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 9. INSERT audit    │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│                    │
         │                    │                    │                    │
         │ 10. Return user   │                    │                    │
         │     (no password) │                    │                    │
         │◄───────────────────│                    │                    │
         │                    │                    │                    │
```

### 1.2 Authentication Flow (JWT)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JWT AUTHENTICATION FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
    │  Client  │         │  FastAPI │         │  Auth    │         │   DB     │
    │          │         │          │         │ Service  │         │          │
    └────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
         │                    │                    │                    │
         │ 1. POST /login     │                    │                    │
         │ {email, password}  │                    │                    │
         │───────────────────►│                    │                    │
         │                    │                    │                    │
         │                    │ 2. Authenticate    │                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 3. Fetch user      │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │◄───────────────────│
         │                    │                    │ 4. Verify password │
         │                    │                    │    (bcrypt check)  │
         │                    │                    │                    │
         │                    │                    │ 5. Generate tokens │
         │                    │                    │    • Access (15min)│
         │                    │                    │    • Refresh (7d)  │
         │                    │◄───────────────────│                    │
         │                    │                    │                    │
         │                    │ 6. Store refresh   │                    │
         │                    │    token (Redis)   │                    │
         │                    │───────────────────►                    │
         │                    │                    │                    │
         │ 7. Return tokens  │                    │                    │
         │ {access, refresh} │                    │                    │
         │◄───────────────────│                    │                    │
         │                    │                    │                    │
         │                    │                    │                    │
         │ ═══════════════════════════════════════════════════════════ │
         │                    SUBSEQUENT REQUESTS (with access token)   │
         │ ═══════════════════════════════════════════════════════════ │
         │                    │                    │                    │
         │ 8. GET /users      │                    │                    │
         │ Authorization:     │                    │                    │
         │ Bearer <token>     │                    │                    │
         │───────────────────►│                    │                    │
         │                    │                    │                    │
         │                    │ 9. Validate JWT    │                    │
         │                    │ (signature, exp)   │                    │
         │                    │                    │                    │
         │                    │ 10. Extract claims │                    │
         │                    │ {sub, role, iat}   │                    │
         │                    │                    │                    │
         │                    │ 11. Check RBAC     │                    │
         │                    │ (role permissions) │                    │
         │                    │                    │                    │
         │                    │ 12. Fetch users    │                    │
         │                    │───────────────────►                    │
         │                    │                    │ 13. Query DB       │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│                    │
         │                    │                    │                    │
         │ 14. Return data   │                    │                    │
         │◄───────────────────│                    │                    │
         │                    │                    │                    │
```

### 1.3 User Update Flow (with Audit Trail)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER UPDATE WITH AUDIT                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
    │  Client  │         │  FastAPI │         │  Service │         │   DB     │
    └────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
         │                    │                    │                    │
         │ 1. PUT /users/:id  │                    │                    │
         │ {full_name, role}  │                    │                    │
         │ Authorization:     │                    │                    │
         │ Bearer <token>     │                    │                    │
         │───────────────────►│                    │                    │
         │                    │                    │                    │
         │                    │ 2. Validate JWT    │                    │
         │                    │ 3. Check RBAC      │                    │
         │                    │ (can edit users?)  │                    │
         │                    │                    │                    │
         │                    │ 4. Fetch current   │                    │
         │                    │    user state      │                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 5. SELECT user     │
         │                    │                    │───────────────────►│
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│                    │
         │                    │                    │                    │
         │                    │ 6. Update user     │                    │
         │                    │───────────────────►│                    │
         │                    │                    │ 7. BEGIN TX        │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │ 8. UPDATE user     │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │ 9. INSERT audit    │
         │                    │                    │    {               │
         │                    │                    │      action: UPDATE│
         │                    │                    │      entity: user  │
         │                    │                    │      entity_id: id │
         │                    │                    │      old_values: {}│
         │                    │                    │      new_values: {}│
         │                    │                    │      performed_by  │
         │                    │                    │    }               │
         │                    │                    │───────────────────►│
         │                    │                    │                    │
         │                    │                    │ 10. COMMIT TX      │
         │                    │                    │───────────────────►│
         │                    │                    │◄───────────────────│
         │                    │◄───────────────────│                    │
         │                    │                    │                    │
         │ 11. Return updated│                    │                    │
         │     user          │                    │                    │
         │◄───────────────────│                    │                    │
         │                    │                    │                    │
```

---

## 2. Database Schema Design

### 2.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTITY RELATIONSHIP DIAGRAM                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   users     │         │ audit_logs  │         │   sessions  │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ PK id       │◄────────┤ PK id       │         │ PK id       │
│    UUID     │    ┌────┤ FK user_id  │         │ FK user_id  │─┐
│    email    │    │    │    action   │         │    token    │ │
│    password │    │    │    entity   │         │    expires  │ │
│    full_name│    │    │    entity_id│         │    created  │ │
│    role     │    │    │    old_val  │         └─────────────┘ │
│    is_active│    │    │    new_val  │                         │
│    metadata │    │    │    performed│◄────────────────────────┘
│    created_at    │    │    created  │
│    updated_at    │    └─────────────┘
└─────────────┘    │
      ▲            │
      │            │
      │            │    ┌─────────────┐
      │            │    │refresh_token│
      │            │    ├─────────────┤
      │            └───►│ PK id       │
      │                 │ FK user_id  │
      │                 │    token    │
      │                 │    expires  │
      │                 │    created  │
      │                 └─────────────┘
      │
      │         ┌─────────────┐
      │         │password_reset│
      │         ├─────────────┤
      └────────►│ PK id       │
                │ FK user_id  │
                │    token    │
                │    expires  │
                │    used     │
                └─────────────┘
```

### 2.2 Table Definitions

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'manager', 'user', 'viewer'))
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created ON users(created_at);
CREATE INDEX idx_users_search ON users 
    USING gin(to_tsvector('english', coalesce(full_name, '') || ' ' || coalesce(email, '')));
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    performed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_performed_by ON audit_logs(performed_by);
CREATE INDEX idx_audit_performed_at ON audit_logs(performed_at);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

#### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    replaced_by UUID REFERENCES refresh_tokens(id)
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

#### password_resets
```sql
CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_resets_user ON password_resets(user_id);
CREATE INDEX idx_password_resets_token ON password_resets(token_hash);
```

### 2.3 SQLAlchemy Models

```python
# models/user.py
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Boolean, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", 
        back_populates="user",
        lazy="dynamic"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('ix_users_search', 
              func.to_tsvector('english', 
                  func.coalesce(full_name, '') + ' ' + 
                  func.coalesce(email, '')),
              postgresql_using='gin'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    performed_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    replaced_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id"),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
```

---

## 3. Caching Strategy

### 3.1 Cache Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CACHING ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  Browser Cache  │  • Static assets (JS, CSS, images)
│  (CDN/Local)    │  • Cache-Control: public, max-age=31536000
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Response  │  • ETags for conditional requests
│   Caching       │  • 304 Not Modified responses
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Application    │  • User sessions (Redis)
│  Cache (Redis)  │  • Rate limiting counters
│                 │  • Frequently accessed data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database       │  • Query result cache (PostgreSQL)
│  Cache          │  • Connection pooling
└─────────────────┘
```

### 3.2 Redis Configuration

```python
# core/cache.py
import redis.asyncio as redis
from functools import wraps
import json
import hashlib
from typing import Optional, Callable, Any

from app.core.config import settings

# Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)


def cache_result(expire: int = 300):
    """Decorator to cache function results in Redis."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"cache:{func.__name__}:{hashlib.md5(
                json.dumps({'args': args, 'kwargs': kwargs}, default=str).encode()
            ).hexdigest()}"
            
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator


class CacheKeys:
    """Cache key patterns."""
    
    @staticmethod
    def user(user_id: str) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def user_by_email(email: str) -> str:
        return f"user:email:{email.lower()}"
    
    @staticmethod
    def refresh_token(token_hash: str) -> str:
        return f"refresh_token:{token_hash}"
    
    @staticmethod
    def rate_limit_ip(ip: str) -> str:
        return f"rate_limit:ip:{ip}"
    
    @staticmethod
    def rate_limit_user(user_id: str) -> str:
        return f"rate_limit:user:{user_id}"
```

### 3.3 Cache Invalidation Strategy

| Data Type | Cache TTL | Invalidation Trigger |
|-----------|-----------|---------------------|
| User profile | 5 minutes | User update, password change |
| User list (paginated) | 1 minute | Any user CRUD operation |
| Session/Refresh token | 7 days | Logout, token refresh, password change |
| Rate limit counters | 1 hour | Automatic expiration |
| Static assets | 1 year | Build/deployment |

---

## 4. Data Migration Approach

### 4.1 Migration Strategy with Alembic

```
migrations/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_audit_logs.py
│   ├── 003_add_refresh_tokens.py
│   └── 004_add_password_resets.py
├── env.py
├── script.py.mako
└── alembic.ini
```

### 4.2 Sample Migration

```python
# migrations/versions/002_add_audit_logs.py
"""Add audit_logs table

Revision ID: 002
Revises: 001
Create Date: 2024-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_performed_by', 'audit_logs', ['performed_by'])
    op.create_index('ix_audit_logs_performed_at', 'audit_logs', ['performed_at'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])


def downgrade():
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_performed_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_performed_by', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_table('audit_logs')
```

### 4.3 Migration Runbook

```bash
# Development - auto-generate migration from model changes
cd backend
alembic revision --autogenerate -m "Add new feature"

# Review generated migration before applying!

# Apply migrations
cd backend
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001

# View current version
alembic current

# View history
alembic history --verbose
```

---

## 5. Backup and Recovery

### 5.1 Azure PostgreSQL Backup Strategy

| Backup Type | Frequency | Retention | Method |
|-------------|-----------|-----------|--------|
| Automated | Daily | 7-35 days | Azure managed |
| Point-in-time | Continuous | 7 days | Azure managed |
| Geo-redundant | Daily | Configurable | Azure paired region |
| Manual exports | Weekly | 90 days | `pg_dump` to blob storage |

### 5.2 Disaster Recovery Procedure

```bash
# 1. Identify recovery point
# 2. Restore from Azure portal or CLI

# Azure CLI restore example
az postgres flexible-server restore \
    --name user-mgmt-portal-prod-restored \
    --resource-group user-mgmt-rg \
    --restore-point-in-time "2024-01-25T10:00:00Z" \
    --source-server user-mgmt-portal-prod

# 3. Update application connection string
# 4. Verify data integrity
# 5. Update DNS/connection routing
```

---

## 6. Data Retention Policies

| Data Type | Retention Period | Action After Retention |
|-----------|-----------------|----------------------|
| Active user data | Indefinite | Archive after 2 years inactive |
| Deleted users | 90 days | Permanent deletion |
| Audit logs | 7 years | Archive to cold storage |
| Session tokens | 7 days | Automatic cleanup |
| Password reset tokens | 24 hours | Automatic cleanup |
| Application logs | 30 days | Archive to blob storage |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-25  
**Owner**: System Architect
