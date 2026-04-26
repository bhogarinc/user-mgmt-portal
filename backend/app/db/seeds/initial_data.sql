-- Seed Data: initial_data.sql
-- Description: Initial seed data for User Management Portal
-- Created: 2026-04-26

-- ============================================
-- PERMISSIONS
-- ============================================

-- User management permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('users:create', 'users', 'create', 'Create new users'),
    ('users:read', 'users', 'read', 'View user details'),
    ('users:read:self', 'users', 'read:self', 'View own profile'),
    ('users:update', 'users', 'update', 'Update any user'),
    ('users:update:self', 'users', 'update:self', 'Update own profile'),
    ('users:delete', 'users', 'delete', 'Delete users'),
    ('users:activate', 'users', 'activate', 'Activate/deactivate users'),
    ('users:manage_roles', 'users', 'manage_roles', 'Assign/remove user roles')
ON CONFLICT (name) DO NOTHING;

-- Role management permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('roles:create', 'roles', 'create', 'Create new roles'),
    ('roles:read', 'roles', 'read', 'View roles'),
    ('roles:update', 'roles', 'update', 'Update roles'),
    ('roles:delete', 'roles', 'delete', 'Delete roles'),
    ('roles:manage_permissions', 'roles', 'manage_permissions', 'Assign role permissions')
ON CONFLICT (name) DO NOTHING;

-- Audit permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('audit:read', 'audit', 'read', 'View audit logs'),
    ('audit:export', 'audit', 'export', 'Export audit logs'),
    ('audit:configure', 'audit', 'configure', 'Configure audit settings')
ON CONFLICT (name) DO NOTHING;

-- System permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('system:configure', 'system', 'configure', 'System configuration'),
    ('system:manage_security', 'system', 'manage_security', 'Manage security settings'),
    ('system:view_metrics', 'system', 'view_metrics', 'View system metrics')
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- ROLES
-- ============================================

-- Admin role (system role)
INSERT INTO roles (name, description, is_system_role) VALUES
    ('admin', 'Full system access with all permissions', TRUE)
ON CONFLICT (name) DO NOTHING;

-- User role (system role)
INSERT INTO roles (name, description, is_system_role) VALUES
    ('user', 'Standard user with basic permissions', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Manager role (system role)
INSERT INTO roles (name, description, is_system_role) VALUES
    ('manager', 'Can manage users and view reports', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Auditor role (system role)
INSERT INTO roles (name, description, is_system_role) VALUES
    ('auditor', 'Read-only access to audit logs and user data', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- ROLE PERMISSIONS
-- ============================================

-- Admin gets all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- User role permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('users:read:self', 'users:update:self')
WHERE r.name = 'user'
ON CONFLICT DO NOTHING;

-- Manager role permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN (
    'users:read', 'users:update', 'users:activate',
    'roles:read', 'audit:read'
)
WHERE r.name = 'manager'
ON CONFLICT DO NOTHING;

-- Auditor role permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('audit:read', 'audit:export', 'users:read')
WHERE r.name = 'auditor'
ON CONFLICT DO NOTHING;

-- ============================================
-- DEFAULT ADMIN USER
-- ============================================

-- Note: This creates a default admin user.
-- In production, change the password immediately after first login!
-- Password: Admin123! (bcrypt hashed)

INSERT INTO users (
    id,
    email,
    username,
    hashed_password,
    first_name,
    last_name,
    is_active,
    is_verified,
    is_superuser,
    email_verified_at
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@example.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IzK', -- Admin123!
    'System',
    'Administrator',
    TRUE,
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;

-- Assign admin role to default admin user
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT 
    '00000000-0000-0000-0000-000000000001',
    r.id,
    CURRENT_TIMESTAMP
FROM roles r
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Create security settings for admin
INSERT INTO security_settings (user_id, notify_on_login, notify_on_password_change)
VALUES ('00000000-0000-0000-0000-000000000001', TRUE, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================
-- COMPLETION
-- ============================================

-- Verify seed data
SELECT 'Permissions count: ' || COUNT(*) FROM permissions;
SELECT 'Roles count: ' || COUNT(*) FROM roles;
SELECT 'Role permissions count: ' || COUNT(*) FROM role_permissions;
SELECT 'Default admin created: ' || CASE WHEN EXISTS (
    SELECT 1 FROM users WHERE email = 'admin@example.com'
) THEN 'YES' ELSE 'NO' END;