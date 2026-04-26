-- Migration: V2__Add_audit_logging.sql
-- Description: Add comprehensive audit logging tables
-- Created: 2026-04-26

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' NOT NULL,
    
    -- Actor information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Target resource
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    
    -- Action details
    action VARCHAR(50),
    description TEXT,
    old_values JSONB,
    new_values JSONB,
    changes JSONB,
    
    -- Request context
    request_id VARCHAR(255),
    correlation_id VARCHAR(255),
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,
    response_status INTEGER,
    
    -- Additional metadata
    metadata JSONB,
    error_message TEXT,
    stack_trace TEXT
);

-- Audit log indexes for common query patterns
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);
CREATE INDEX idx_audit_logs_correlation ON audit_logs(correlation_id);

-- Composite indexes for filtering
CREATE INDEX idx_audit_logs_timestamp_event ON audit_logs(timestamp DESC, event_type);
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp DESC);

-- Severity constraint
ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_severity 
    CHECK (severity IN ('info', 'warning', 'error', 'critical'));

-- Partitioning setup for high-volume audit logs (optional, for future scaling)
-- This creates a template for monthly partitioning
CREATE OR REPLACE FUNCTION create_audit_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_date := DATE_TRUNC('month', CURRENT_DATE);
    partition_name := 'audit_logs_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := partition_date;
    end_date := partition_date + INTERVAL '1 month';
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for security and compliance';
COMMENT ON COLUMN audit_logs.event_type IS 'Type of event: login_success, login_failure, user_created, etc.';
COMMENT ON COLUMN audit_logs.severity IS 'Event severity: info, warning, error, critical';
COMMENT ON COLUMN audit_logs.changes IS 'Computed diff between old_values and new_values';