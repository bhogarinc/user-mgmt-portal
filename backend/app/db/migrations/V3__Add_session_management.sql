-- Migration: V3__Add_session_management.sql
-- Description: Add user session tracking and security tables
-- Created: 2026-04-26

-- User sessions table for active session tracking
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash VARCHAR(255) NOT NULL UNIQUE,
    
    -- Session metadata
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    location_city VARCHAR(100),
    location_country VARCHAR(2),
    
    -- Session timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    terminated_at TIMESTAMP WITH TIME ZONE,
    
    -- Session state
    is_active BOOLEAN DEFAULT TRUE,
    termination_reason VARCHAR(50),
    
    CONSTRAINT chk_session_termination_reason 
        CHECK (termination_reason IN ('logout', 'expired', 'revoked', 'security', 'concurrent_limit'))
);

-- Session indexes
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_created ON user_sessions(created_at DESC);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token_hash);

-- Password history table for security
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(50) DEFAULT 'user_initiated',
    
    CONSTRAINT chk_password_change_reason 
        CHECK (change_reason IN ('user_initiated', 'reset', 'expiration', 'admin_reset', 'security_breach'))
);

-- Password history indexes
CREATE INDEX idx_password_history_user ON password_history(user_id);
CREATE INDEX idx_password_history_created ON password_history(created_at DESC);

-- Login attempts tracking for brute force protection
CREATE TABLE login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    
    -- Geolocation (if available)
    country_code VARCHAR(2),
    city VARCHAR(100),
    
    -- Device info
    device_fingerprint VARCHAR(255)
);

-- Login attempts indexes
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_time ON login_attempts(attempted_at DESC);
CREATE INDEX idx_login_attempts_email_time ON login_attempts(email, attempted_at DESC);
CREATE INDEX idx_login_attempts_ip_time ON login_attempts(ip_address, attempted_at DESC);

-- Cleanup old login attempts (keep 90 days)
CREATE INDEX idx_login_attempts_cleanup ON login_attempts(attempted_at) 
    WHERE attempted_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Concurrent session limit enforcement
CREATE OR REPLACE FUNCTION enforce_session_limit()
RETURNS TRIGGER AS $$
BEGIN
    -- Deactivate oldest sessions if user has more than 5 active sessions
    UPDATE user_sessions
    SET is_active = FALSE,
        terminated_at = CURRENT_TIMESTAMP,
        termination_reason = 'concurrent_limit'
    WHERE id IN (
        SELECT id FROM user_sessions
        WHERE user_id = NEW.user_id
          AND is_active = TRUE
        ORDER BY created_at ASC
        OFFSET 4
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_enforce_session_limit
    AFTER INSERT ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION enforce_session_limit();

-- Comments
COMMENT ON TABLE user_sessions IS 'Active user sessions for security monitoring';
COMMENT ON TABLE password_history IS 'Historical passwords to prevent reuse';
COMMENT ON TABLE login_attempts IS 'Failed and successful login attempts for security analysis';