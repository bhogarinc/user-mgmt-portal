# TaskFlow Database Schema

## Overview

TaskFlow uses PostgreSQL 15 with a **schema-per-tenant** multi-tenancy approach. This document defines the complete database schema including tables, relationships, indexes, and constraints.

---

## Multi-Tenancy Strategy

### Schema Organization

```
public                          tenant_{uuid} schemas
├── tenants  ─────────────────▶  ├── workspaces
├── users                      │  ├── projects
├── roles                      │  ├── boards
├── permissions                │  ├── sprints
└── audit_log                  │  ├── tasks
                               │  ├── comments
                               │  ├── attachments
                               │  ├── labels
                               │  ├── custom_fields
                               │  └── team_members
```

### Tenant Isolation

Each tenant has a dedicated schema with complete data isolation:

```sql
-- Create tenant schema
CREATE SCHEMA IF NOT EXISTS tenant_a1b2c3d4;

-- Set search path for tenant
SET search_path TO tenant_a1b2c3d4, public;

-- Enable Row Level Security as additional protection
ALTER TABLE tenant_a1b2c3d4.tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON tenant_a1b2c3d4.tasks
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

---

## Public Schema (Shared Tables)

### 1. Tenants Table

```sql
CREATE TABLE public.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'suspended', 'cancelled')),
    plan VARCHAR(20) NOT NULL DEFAULT 'free'
        CHECK (plan IN ('free', 'starter', 'professional', 'enterprise')),
    settings JSONB DEFAULT '{}',
    billing_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_tenants_slug ON public.tenants(slug);
CREATE INDEX idx_tenants_status ON public.tenants(status);
```

### 2. Users Table

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en-US',
    auth_provider VARCHAR(20) DEFAULT 'local'
        CHECK (auth_provider IN ('local', 'azure_ad', 'google', 'github')),
    auth_provider_id VARCHAR(255),
    last_login_at TIMESTAMPTZ,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_auth_provider ON public.users(auth_provider, auth_provider_id);
CREATE INDEX idx_users_status ON public.users(status) WHERE deleted_at IS NULL;
```

### 3. User Tenants (Membership)

```sql
CREATE TABLE public.user_tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES public.roles(id),
    invited_by UUID REFERENCES public.users(id),
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('pending', 'active', 'inactive')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, tenant_id)
);

CREATE INDEX idx_user_tenants_user ON public.user_tenants(user_id);
CREATE INDEX idx_user_tenants_tenant ON public.user_tenants(tenant_id);
CREATE INDEX idx_user_tenants_status ON public.user_tenants(status);
```

### 4. Roles Table

```sql
CREATE TABLE public.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- System roles
INSERT INTO public.roles (id, name, description, permissions, is_system) VALUES
('role-admin', 'Admin', 'Full access to all features', '["*"]', TRUE),
('role-manager', 'Manager', 'Can manage projects and teams', '["projects:*", "tasks:*", "teams:*", "reports:*"]', TRUE),
('role-member', 'Member', 'Can create and manage own tasks', '["tasks:create", "tasks:read", "tasks:update:own", "projects:read"]', TRUE),
('role-viewer', 'Viewer', 'Read-only access', '["projects:read", "tasks:read"]', TRUE);
```

### 5. Audit Log

```sql
CREATE TABLE public.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id),
    user_id UUID REFERENCES public.users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_tenant ON public.audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_log_user ON public.audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_entity ON public.audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_action ON public.audit_log(action, created_at DESC);
```

---

## Tenant Schema Tables

### 1. Workspaces

```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50),
    settings JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_workspaces_tenant ON workspaces(tenant_id);
CREATE INDEX idx_workspaces_archived ON workspaces(archived_at) WHERE archived_at IS NULL;
```

### 2. Projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    key VARCHAR(10) NOT NULL, -- e.g., "PROJ", "DEV"
    status VARCHAR(20) DEFAULT 'active' 
        CHECK (status IN ('active', 'archived', 'deleted')),
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    color VARCHAR(7) DEFAULT '#10B981',
    settings JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(tenant_id, key)
);

CREATE INDEX idx_projects_workspace ON projects(workspace_id);
CREATE INDEX idx_projects_status ON projects(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_dates ON projects(start_date, target_end_date);
```

### 3. Teams

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#8B5CF6',
    created_by UUID NOT NULL REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_teams_workspace ON teams(workspace_id);
CREATE INDEX idx_teams_archived ON teams(archived_at) WHERE archived_at IS NULL;
```

### 4. Team Members

```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id),
    role VARCHAR(20) DEFAULT 'member'
        CHECK (role IN ('lead', 'member')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
```

### 5. Sprints

```sql
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    goal TEXT,
    number INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'planning'
        CHECK (status IN ('planning', 'active', 'completed', 'cancelled')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    completed_at TIMESTAMPTZ,
    total_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0,
    created_by UUID NOT NULL REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, number)
);

CREATE INDEX idx_sprints_project ON sprints(project_id);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_dates ON sprints(start_date, end_date);
```

### 6. Boards

```sql
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) DEFAULT 'kanban'
        CHECK (type IN ('kanban', 'scrum', 'custom')),
    settings JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_boards_project ON boards(project_id);
CREATE INDEX idx_boards_sprint ON boards(sprint_id);
```

### 7. Board Columns (Status Columns)

```sql
CREATE TABLE board_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#6B7280',
    position INTEGER NOT NULL,
    wip_limit INTEGER,
    definition_of_done TEXT,
    is_done_column BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(board_id, position)
);

CREATE INDEX idx_board_columns_board ON board_columns(board_id);
CREATE INDEX idx_board_columns_position ON board_columns(board_id, position);
```

### 8. Tasks

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    sprint_id UUID REFERENCES sprints(id),
    board_id UUID REFERENCES boards(id),
    column_id UUID REFERENCES board_columns(id),
    
    -- Identification
    task_number INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Categorization
    type VARCHAR(20) DEFAULT 'task'
        CHECK (type IN ('epic', 'story', 'task', 'bug', 'subtask')),
    priority VARCHAR(10) DEFAULT 'medium'
        CHECK (priority IN ('lowest', 'low', 'medium', 'high', 'highest')),
    status VARCHAR(20) DEFAULT 'todo'
        CHECK (status IN ('backlog', 'todo', 'in_progress', 'in_review', 'done', 'cancelled')),
    
    -- Estimation
    story_points INTEGER CHECK (story_points >= 0 AND story_points <= 100),
    time_estimate INTEGER, -- in minutes
    time_spent INTEGER DEFAULT 0, -- in minutes
    
    -- Assignment
    reporter_id UUID NOT NULL REFERENCES public.users(id),
    assignee_id UUID REFERENCES public.users(id),
    
    -- Hierarchy
    parent_id UUID REFERENCES tasks(id),
    epic_id UUID REFERENCES tasks(id) WHERE type = 'epic',
    
    -- Positioning (for drag-and-drop)
    position DECIMAL(10,2) NOT NULL DEFAULT 0,
    
    -- Dates
    due_date TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    UNIQUE(project_id, task_number)
);

-- Primary indexes
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_sprint ON tasks(sprint_id);
CREATE INDEX idx_tasks_board ON tasks(board_id);
CREATE INDEX idx_tasks_column ON tasks(column_id);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_status ON tasks(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_type ON tasks(type);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_position ON tasks(board_id, column_id, position);
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_deleted ON tasks(deleted_at) WHERE deleted_at IS NULL;

-- Full-text search
CREATE INDEX idx_tasks_search ON tasks 
    USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
```

### 9. Task Labels

```sql
CREATE TABLE labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) DEFAULT '#6B7280',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE TABLE task_labels (
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    label_id UUID NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (task_id, label_id)
);

CREATE INDEX idx_task_labels_task ON task_labels(task_id);
CREATE INDEX idx_task_labels_label ON task_labels(label_id);
```

### 10. Task Comments

```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.users(id),
    content TEXT NOT NULL,
    parent_id UUID REFERENCES comments(id), -- For threaded comments
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_comments_task ON comments(task_id, created_at DESC);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_parent ON comments(parent_id) WHERE parent_id IS NOT NULL;
```

### 11. Attachments

```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES public.users(id),
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_attachments_task ON attachments(task_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_attachments_uploader ON attachments(uploaded_by);
```

### 12. Custom Fields

```sql
CREATE TABLE custom_field_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    field_type VARCHAR(20) NOT NULL
        CHECK (field_type IN ('text', 'number', 'date', 'select', 'multi_select', 'checkbox', 'user')),
    options JSONB, -- For select/multi_select types
    is_required BOOLEAN DEFAULT FALSE,
    default_value JSONB,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE TABLE task_custom_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    field_definition_id UUID NOT NULL REFERENCES custom_field_definitions(id),
    value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, field_definition_id)
);

CREATE INDEX idx_task_custom_fields_task ON task_custom_fields(task_id);
CREATE INDEX idx_task_custom_fields_definition ON task_custom_fields(field_definition_id);
```

### 13. Task History / Activity Log

```sql
CREATE TABLE task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id),
    action VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_task_history_task ON task_history(task_id, created_at DESC);
CREATE INDEX idx_task_history_user ON task_history(user_id);
CREATE INDEX idx_task_history_action ON task_history(action);
```

### 14. Notifications

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    action_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
```

---

## Indexes Summary

### Performance-Critical Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| tasks | `idx_tasks_position` | Drag-and-drop ordering |
| tasks | `idx_tasks_search` | Full-text search |
| tasks | `idx_tasks_status` | Board filtering |
| comments | `idx_comments_task` | Task activity feed |
| task_history | `idx_task_history_task` | Task audit trail |
| notifications | `idx_notifications_unread` | Real-time badge count |

### Foreign Key Indexes

All foreign keys are automatically indexed by PostgreSQL. Additional composite indexes are created for frequently joined queries.

---

## Constraints & Validation

### Data Integrity

```sql
-- Ensure task position is unique within column
CREATE UNIQUE INDEX idx_unique_task_position 
    ON tasks(board_id, column_id, position) 
    WHERE deleted_at IS NULL;

-- Prevent circular dependencies in task hierarchy
CREATE OR REPLACE FUNCTION check_task_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NOT NULL THEN
        IF NEW.parent_id = NEW.id OR EXISTS (
            WITH RECURSIVE hierarchy AS (
                SELECT id, parent_id FROM tasks WHERE id = NEW.parent_id
                UNION ALL
                SELECT t.id, t.parent_id 
                FROM tasks t 
                INNER JOIN hierarchy h ON t.id = h.parent_id
                WHERE t.id = NEW.id
            )
            SELECT 1 FROM hierarchy WHERE id = NEW.id
        ) THEN
            RAISE EXCEPTION 'Circular dependency detected in task hierarchy';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_task_hierarchy
    BEFORE INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION check_task_hierarchy();
```

---

## Migration Strategy

### Alembic Migration Structure

```
migrations/
├── versions/
│   ├── 001_create_tenants.py
│   ├── 002_create_users.py
│   ├── 003_create_roles.py
│   ├── 004_create_tenant_schema_template.py
│   └── 005_add_audit_log.py
├── env.py
├── alembic.ini
└── script.py.mako
```

### Zero-Downtime Migrations

1. **Add new columns as nullable** → Backfill data → Add constraints
2. **Create new tables** → Dual-write → Migrate reads → Deprecate old
3. **Index creation** → Use `CONCURRENTLY` to avoid locks

---

## Backup & Recovery

### Automated Backups

```sql
-- Continuous archiving to Azure Blob Storage
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'azcopy copy %p https://taskflowbackups.blob.core.windows.net/wal/%f';

-- Daily full backups via pg_dump
-- Point-in-time recovery enabled
```

### Retention Policy

- **WAL Archives**: 7 days
- **Daily Backups**: 30 days
- **Weekly Backups**: 12 weeks
- **Monthly Backups**: 1 year

---

*Schema Version: 1.0*
*Last Updated: 2024*
*Owner: Database Architecture Team*
