-- Migration: V4__Add_password_history.sql
-- Description: Add password policy and security settings tables
-- Created: 2026-04-26

-- Password policies table (for configurable policies per tenant/role)
CREATE TABLE password_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Length requirements
    min_length INTEGER DEFAULT 8,
    max_length INTEGER DEFAULT 128,
    
    -- Character requirements
    require_uppercase BOOLEAN DEFAULT TRUE,
    require_lowercase BOOLEAN DEFAULT TRUE,
    require_digits BOOLEAN DEFAULT TRUE,
    require_special_chars BOOLEAN DEFAULT TRUE,
    special_chars VARCHAR(50) DEFAULT '!@#$%^&*()_+-=[]{}|;:,.<>?',
    
    -- Advanced requirements
    min_unique_chars INTEGER DEFAULT 5,
    prevent_common_passwords BOOLEAN DEFAULT TRUE,
    prevent_username_in_password BOOLEAN DEFAULT TRUE,
    prevent_reuse_count INTEGER DEFAULT 5,
    
    -- Expiration
    max_age_days INTEGER DEFAULT 90,
    expire_warning_days INTEGER DEFAULT 7,
    
    -- Lockout policy
    max_failed_attempts INTEGER DEFAULT 5,
    lockout_duration_minutes INTEGER DEFAULT 30,
    reset_lockout_after_minutes INTEGER DEFAULT 30,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policy constraints
ALTER TABLE password_policies ADD CONSTRAINT chk_password_min_length 
    CHECK (min_length >= 4 AND min_length <= max_length);
ALTER TABLE password_policies ADD CONSTRAINT chk_password_max_length 
    CHECK (max_length <= 256);
ALTER TABLE password_policies ADD CONSTRAINT chk_prevent_reuse 
    CHECK (prevent_reuse_count >= 1 AND prevent_reuse_count <= 24);
ALTER TABLE password_policies ADD CONSTRAINT chk_max_age 
    CHECK (max_age_days >= 0 AND max_age_days <= 365);
ALTER TABLE password_policies ADD CONSTRAINT chk_max_failed_attempts 
    CHECK (max_failed_attempts >= 1 AND max_failed_attempts <= 10);

-- User password policy assignments
CREATE TABLE user_password_policies (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES password_policies(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Security settings table (global and per-user)
CREATE TABLE security_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Two-factor authentication
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_method VARCHAR(20) CHECK (mfa_method IN ('app', 'sms', 'email')),
    mfa_secret_encrypted TEXT,
    mfa_backup_codes TEXT[],
    mfa_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Login notifications
    notify_on_login BOOLEAN DEFAULT TRUE,
    notify_on_password_change BOOLEAN DEFAULT TRUE,
    notify_email VARCHAR(255),
    
    -- Session settings
    session_timeout_minutes INTEGER DEFAULT 30,
    concurrent_sessions_allowed INTEGER DEFAULT 5,
    require_reauth_for_sensitive_actions BOOLEAN DEFAULT TRUE,
    
    -- IP restrictions
    allowed_ips INET[],
    blocked_ips INET[],
    geo_restriction_enabled BOOLEAN DEFAULT FALSE,
    allowed_countries VARCHAR(2)[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_security_settings_user ON security_settings(user_id);
CREATE INDEX idx_security_settings_mfa ON security_settings(mfa_enabled) WHERE mfa_enabled = TRUE;

-- Insert default password policy
INSERT INTO password_policies (
    name,
    description,
    is_default,
    min_length,
    max_length,
    require_uppercase,
    require_lowercase,
    require_digits,
    require_special_chars,
    prevent_reuse_count,
    max_age_days,
    max_failed_attempts,
    lockout_duration_minutes
) VALUES (
    'Default Policy',
    'Standard password policy for all users',
    TRUE,
    8,
    128,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    5,
    90,
    5,
    30
);

-- Insert strict password policy for admins
INSERT INTO password_policies (
    name,
    description,
    is_default,
    min_length,
    require_uppercase,
    require_lowercase,
    require_digits,
    require_special_chars,
    prevent_reuse_count,
    max_age_days,
    max_failed_attempts
) VALUES (
    'Admin Policy',
    'Strict policy for administrator accounts',
    FALSE,
    12,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    10,
    60,
    3
);

-- Trigger for updated_at
CREATE TRIGGER update_password_policies_updated_at 
    BEFORE UPDATE ON password_policies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_settings_updated_at 
    BEFORE UPDATE ON security_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE password_policies IS 'Configurable password policies for different user types';
COMMENT ON TABLE user_password_policies IS 'Assigns password policies to users';
COMMENT ON TABLE security_settings IS 'User-specific security and MFA settings';