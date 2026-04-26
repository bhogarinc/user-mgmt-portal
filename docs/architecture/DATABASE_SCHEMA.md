# Database Schema Documentation

## Overview

This document details the PostgreSQL database schema for the User Management Portal. The schema supports multi-tenancy, RBAC, audit logging, and soft deletes.

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   users     │◄──────┤ user_organizations│──────►│  organizations  │
├─────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)     │       │ id (PK)          │       │ id (PK)         │
│ email       │       │ user_id (FK)     │       │ name            │
│ username    │       │ org_id (FK)      │       │ slug            │
│ password    │       │ role             │       │ description     │
│ first_name  │       │ is_default       │       │ settings        │
│ last_name   │       │ joined_at        │       │ is_active       │
│ ...         │       └──────────────────┘       └─────────────────┘
└──────┬──────┘
       │
       │         ┌─────────────┐       ┌─────────────┐
       └────────►│ user_roles  │◄──────│    roles    │
                 ├─────────────┤       ├─────────────┤
                 │ id (PK)     │       │ id (PK)     │
                 │ user_id(FK) │       │ name        │
                 │ role_id(FK) │       │ description │
                 │ org_id(FK)  │       │ permissions │
                 │ granted_at  │       │ is_system   │
                 └─────────────┘       └─────────────┘
       │
       │         ┌─────────────┐
       └────────►│  sessions   │
                 ├─────────────┤
                 │ id (PK)     │
                 │ user_id(FK) │
                 │ token_hash  │
                 │ expires_at  │
                 └─────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         audit_logs                              │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)          │ timestamp      │ action       │ entity_type  │
│ entity_id        │ user_id (FK)   │ org_id (FK)  │ ip_address   │
│ user_agent       │ old_values     │ new_values   │ metadata     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table Definitions

### 1. users

Stores user account information with soft delete support.

```sql
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

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Constraints:**
- Email must be unique and valid format
- Username must be unique, alphanumeric with underscores
- Password is hashed using Argon2id
- Soft delete via `deleted_at` timestamp

---

### 2. organizations

Multi-tenant organization support.

```sql
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

-- Indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE is_active = TRUE;
```

**Constraints:**
- Slug must be URL-safe (lowercase, alphanumeric, hyphens)
- Settings stored as JSONB for flexibility

---

### 3. user_organizations

Junction table for user-organization membership.

```sql
CREATE TABLE user_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    is_default BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- Indexes
CREATE INDEX idx_user_orgs_user ON user_organizations(user_id);
CREATE INDEX idx_user_orgs_org ON user_organizations(organization_id);
CREATE INDEX idx_user_orgs_default ON user_organizations(user_id, is_default) WHERE is_default = TRUE;
```

**Constraints:**
- One default organization per user
- Role values: owner, admin, member

---

### 4. roles

Role definitions for RBAC.

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, organization_id)
);

-- Indexes
CREATE INDEX idx_roles_org ON roles(organization_id);
CREATE INDEX idx_roles_system ON roles(is_system_role) WHERE is_system_role = TRUE;
```

**Constraints:**
- System roles cannot be deleted
- Permissions stored as JSONB array of strings
- Role names unique within organization

---

### 5. user_roles

User-role assignments with optional organization context.

```sql
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

-- Indexes
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_roles_org ON user_roles(organization_id);
CREATE INDEX idx_user_roles_expires ON user_roles(expires_at) WHERE expires_at IS NOT NULL;
```

**Constraints:**
- Role expiration optional
- Audit trail via granted_by

---

### 6. sessions

Active user sessions for token management.

```sql
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

-- Indexes
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
```

**Constraints:**
- Token hashes stored, not tokens themselves
- Automatic cleanup of expired sessions via cron

---

### 7. audit_logs

Immutable audit trail with partitioning.

```sql
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

-- Create monthly partitions
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... auto-generate future partitions

-- Indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id, timestamp DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, timestamp DESC);
```

**Constraints:**
- Partitioned by month for performance
- Immutable - no updates allowed
- Retention policy: 2 years

---

## Data Types

### Custom Types

```sql
-- User status
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending');

-- Audit action types
CREATE TYPE audit_action AS ENUM (
    'create', 'update', 'delete', 'login', 'logout',
    'password_change', 'role_assign', 'role_revoke'
);

-- Organization role types
CREATE TYPE org_role AS ENUM ('owner', 'admin', 'member');
```

---

## Triggers and Functions

### Updated At Trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Audit Log Trigger

```sql
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        old_data = to_jsonb(OLD);
        new_data = null;
    ELSIF (TG_OP = 'INSERT') THEN
        old_data = null;
        new_data = to_jsonb(NEW);
    ELSIF (TG_OP = 'UPDATE') THEN
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);
    END IF;
    
    INSERT INTO audit_logs (
        action, entity_type, entity_id, old_values, new_values
    ) VALUES (
        TG_OP::audit_action,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        old_data,
        new_data
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply to audited tables
CREATE TRIGGER users_audit AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

---

## Row Level Security (RLS)

```sql
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see active users in their organizations
CREATE POLICY user_org_isolation ON users
    FOR SELECT
    USING (
        deleted_at IS NULL AND
        EXISTS (
            SELECT 1 FROM user_organizations uo
            WHERE uo.user_id = current_setting('app.current_user_id')::UUID
            AND uo.organization_id IN (
                SELECT organization_id FROM user_organizations 
                WHERE user_id = users.id
            )
        )
    );
```

---

## Migration Strategy

### Alembic Setup

```python
# alembic/env.py
from app.db.base import Base
from app.modules.users.models import User
from app.modules.organizations.models import Organization
# ... import all models

target_metadata = Base.metadata
```

### Migration Script Example

```python
"""create users table

Revision ID: abc123
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        # ...
    )
    op.create_index('idx_users_email', 'users', ['email'])


def downgrade():
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

---

## Performance Considerations

### Query Optimization

1. **Use filtered indexes** for soft-deleted records
2. **Partition audit_logs** by month for time-series queries
3. **Covering indexes** for common query patterns
4. **Connection pooling** with PgBouncer

### Maintenance

```sql
-- Vacuum and analyze regularly
VACUUM ANALYZE users;
VACUUM ANALYZE audit_logs;

-- Reindex monthly
REINDEX INDEX CONCURRENTLY idx_audit_logs_timestamp;
```

---

## Backup and Recovery

### Automated Backups

- **Azure**: Automated daily backups with 35-day retention
- **Point-in-time**: Restore to any moment in 35-day window
- **Geo-redundant**: Replicated to paired region

### Manual Backup Script

```bash
#!/bin/bash
# backup.sh
pg_dump -h $DB_HOST -U $DB_USER -Fc $DB_NAME > backup_$(date +%Y%m%d).dump
```

---

*Last Updated: January 2024*
*Owner: Database Architecture Team*
