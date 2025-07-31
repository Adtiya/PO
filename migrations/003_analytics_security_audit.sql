-- Migration 003: Analytics, Security, and Audit Domains
-- Description: Creates analytics, security, and audit tables
-- Author: Manus AI
-- Date: 2025-01-30

-- ============================================================================
-- ANALYTICS DOMAIN
-- ============================================================================

-- Usage sessions for tracking user activity
CREATE TABLE usage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Session identification
    session_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    
    -- Geographic information
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Session metrics
    page_views INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    llm_interactions INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    
    -- Session duration
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

-- API usage logs for performance monitoring
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request identification
    request_id VARCHAR(255) UNIQUE,
    session_id UUID REFERENCES usage_sessions(id),
    user_id UUID REFERENCES users(id),
    
    -- API details
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    
    -- Performance metrics
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    
    -- Error tracking
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Metadata
    request_headers JSONB,
    request_params JSONB,
    response_headers JSONB,
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analytics reports configuration
CREATE TABLE analytics_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Report identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL, -- 'usage', 'performance', 'cost', 'user_behavior'
    
    -- Report configuration
    data_sources JSONB NOT NULL, -- Configuration for data collection
    filters JSONB DEFAULT '{}',
    aggregations JSONB DEFAULT '{}',
    
    -- Scheduling
    schedule_type VARCHAR(20), -- 'manual', 'daily', 'weekly', 'monthly'
    schedule_config JSONB DEFAULT '{}',
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Access control
    created_by UUID NOT NULL REFERENCES users(id),
    shared_with UUID[], -- User IDs with access
    is_public BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_generated_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Report execution tracking
CREATE TABLE report_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES analytics_reports(id) ON DELETE CASCADE,
    
    -- Execution details
    execution_type VARCHAR(20) NOT NULL, -- 'manual', 'scheduled'
    triggered_by UUID REFERENCES users(id),
    
    -- Status and results
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    result_data JSONB,
    result_file_path TEXT,
    error_message TEXT,
    
    -- Performance
    execution_time_ms INTEGER,
    rows_processed INTEGER,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Cost centers for budget management
CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cost center identification
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    code VARCHAR(50) UNIQUE,
    
    -- Hierarchy
    parent_cost_center_id UUID REFERENCES cost_centers(id),
    
    -- Budget management
    monthly_budget DECIMAL(12, 2),
    annual_budget DECIMAL(12, 2),
    
    -- Responsible parties
    manager_id UUID REFERENCES users(id),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cost allocations for detailed cost tracking
CREATE TABLE cost_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cost tracking
    user_id UUID REFERENCES users(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    
    -- Service and resource
    service_type VARCHAR(50) NOT NULL, -- 'llm', 'storage', 'compute', 'api'
    resource_id VARCHAR(255),
    
    -- Cost details
    cost_amount DECIMAL(12, 6) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_period DATE, -- YYYY-MM-01 format
    
    -- Usage metrics
    usage_quantity DECIMAL(15, 6),
    usage_unit VARCHAR(50), -- 'tokens', 'requests', 'gb_hours', 'minutes'
    
    -- Metadata
    cost_breakdown JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    
    -- Timestamps
    incurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECURITY DOMAIN
-- ============================================================================

-- Data classifications for security and compliance
CREATE TABLE data_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Classification details
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    sensitivity_level INTEGER NOT NULL, -- 1 (public) to 5 (top secret)
    
    -- Regulatory compliance
    compliance_frameworks TEXT[], -- 'GDPR', 'HIPAA', 'SOX', 'PCI-DSS'
    retention_period_days INTEGER,
    
    -- Handling requirements
    encryption_required BOOLEAN DEFAULT false,
    masking_required BOOLEAN DEFAULT false,
    access_logging_required BOOLEAN DEFAULT true,
    
    -- Default masking rules
    default_masking_rules JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data elements for PII detection and masking
CREATE TABLE data_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Element identification
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    element_type VARCHAR(100), -- 'email', 'phone', 'ssn', 'credit_card', 'name'
    
    -- Classification
    classification_id UUID NOT NULL REFERENCES data_classifications(id),
    
    -- Detection rules
    detection_patterns JSONB DEFAULT '[]', -- Regex patterns for auto-detection
    validation_rules JSONB DEFAULT '{}',
    
    -- Masking configuration
    masking_method VARCHAR(50), -- 'hash', 'encrypt', 'tokenize', 'redact', 'partial'
    masking_parameters JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    auto_detected BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(table_name, column_name)
);

-- Masking policies for dynamic data protection
CREATE TABLE masking_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Policy identification
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    
    -- Policy scope
    applies_to_tables TEXT[], -- Table names or patterns
    applies_to_columns TEXT[], -- Column names or patterns
    applies_to_users UUID[], -- Specific users (empty = all users)
    applies_to_roles UUID[], -- Specific roles (empty = all roles)
    
    -- Masking rules
    masking_rules JSONB NOT NULL, -- Detailed masking configuration
    
    -- Conditions
    condition_expression TEXT, -- SQL-like condition for when to apply
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100, -- Higher priority = applied first
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Encryption keys management
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Key identification
    key_name VARCHAR(255) UNIQUE NOT NULL,
    key_type VARCHAR(50) NOT NULL, -- 'aes256', 'rsa2048', 'rsa4096'
    key_purpose VARCHAR(100) NOT NULL, -- 'data_encryption', 'token_signing', 'file_encryption'
    
    -- Key material (encrypted with master key)
    encrypted_key_material TEXT NOT NULL,
    key_checksum VARCHAR(64),
    
    -- Key lifecycle
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'rotating', 'deprecated', 'revoked'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    rotated_at TIMESTAMP WITH TIME ZONE,
    
    -- Key hierarchy
    parent_key_id UUID REFERENCES encryption_keys(id),
    
    -- Usage tracking
    usage_count BIGINT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Access control
    allowed_services TEXT[],
    created_by UUID NOT NULL REFERENCES users(id)
);

-- Encrypted data registry for tracking encrypted fields
CREATE TABLE encrypted_data_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Data location
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    
    -- Encryption details
    encryption_key_id UUID NOT NULL REFERENCES encryption_keys(id),
    encryption_algorithm VARCHAR(50) NOT NULL,
    initialization_vector VARCHAR(255),
    
    -- Metadata
    encrypted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    encrypted_by UUID REFERENCES users(id),
    
    UNIQUE(table_name, column_name, record_id)
);

-- Compliance frameworks
CREATE TABLE compliance_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Framework identification
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20),
    description TEXT,
    
    -- Framework details
    jurisdiction VARCHAR(100), -- 'EU', 'US', 'Global'
    framework_type VARCHAR(50), -- 'privacy', 'security', 'financial', 'industry'
    
    -- Requirements
    requirements JSONB NOT NULL, -- Detailed compliance requirements
    controls JSONB DEFAULT '{}', -- Required controls and procedures
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    effective_date DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compliance assessments
CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Assessment details
    framework_id UUID NOT NULL REFERENCES compliance_frameworks(id),
    assessment_name VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(50), -- 'self_assessment', 'external_audit', 'continuous_monitoring'
    
    -- Scope
    scope_description TEXT,
    systems_in_scope TEXT[],
    data_types_in_scope TEXT[],
    
    -- Assessment results
    overall_status VARCHAR(20), -- 'compliant', 'non_compliant', 'partially_compliant', 'in_progress'
    compliance_score DECIMAL(5, 2), -- 0.00 to 100.00
    findings JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    
    -- Timeline
    assessment_period_start DATE,
    assessment_period_end DATE,
    
    -- Responsible parties
    conducted_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'in_review', 'approved', 'archived'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- AUDIT DOMAIN
-- ============================================================================

-- Comprehensive audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event identification
    event_type VARCHAR(100) NOT NULL, -- 'create', 'update', 'delete', 'access', 'login', 'permission_change'
    event_category VARCHAR(50) NOT NULL, -- 'authentication', 'authorization', 'data_access', 'system'
    
    -- Actor information
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES usage_sessions(id),
    ip_address INET,
    user_agent TEXT,
    
    -- Target information
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Context
    action_description TEXT,
    business_context TEXT,
    risk_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    
    -- Technical details
    application_name VARCHAR(100),
    service_name VARCHAR(100),
    api_endpoint VARCHAR(255),
    request_id VARCHAR(255),
    
    -- Compliance
    compliance_relevant BOOLEAN DEFAULT false,
    retention_period_days INTEGER DEFAULT 2555, -- 7 years default
    
    -- Metadata
    additional_data JSONB DEFAULT '{}',
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Change tracking for critical data
CREATE TABLE change_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Change identification
    change_set_id UUID NOT NULL, -- Groups related changes
    sequence_number INTEGER NOT NULL, -- Order within change set
    
    -- Target information
    table_name VARCHAR(255) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    
    -- Change details
    column_name VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    data_type VARCHAR(50),
    
    -- Change context
    changed_by UUID REFERENCES users(id),
    change_reason TEXT,
    business_justification TEXT,
    
    -- Approval workflow
    requires_approval BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    change_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security events and incident tracking
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event classification
    event_type VARCHAR(100) NOT NULL, -- 'failed_login', 'privilege_escalation', 'data_breach', 'suspicious_activity'
    severity VARCHAR(20) NOT NULL, -- 'info', 'low', 'medium', 'high', 'critical'
    
    -- Event details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Actor and target
    source_user_id UUID REFERENCES users(id),
    target_user_id UUID REFERENCES users(id),
    source_ip INET,
    target_resource VARCHAR(255),
    
    -- Detection
    detection_method VARCHAR(100), -- 'automated_rule', 'manual_review', 'external_alert'
    detection_rule_id VARCHAR(255),
    
    -- Impact assessment
    potential_impact TEXT,
    affected_systems TEXT[],
    affected_data_types TEXT[],
    
    -- Response
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'false_positive'
    assigned_to UUID REFERENCES users(id),
    resolution_notes TEXT,
    
    -- Compliance
    regulatory_notification_required BOOLEAN DEFAULT false,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    event_data JSONB DEFAULT '{}',
    
    -- Timestamps
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- MICROSERVICES SUPPORT
-- ============================================================================

-- Service registry for microservices discovery
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Service identification
    service_name VARCHAR(100) UNIQUE NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- 'api', 'worker', 'scheduler', 'gateway'
    version VARCHAR(20) NOT NULL,
    
    -- Network configuration
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    protocol VARCHAR(10) DEFAULT 'http', -- 'http', 'https', 'grpc'
    base_path VARCHAR(255) DEFAULT '/',
    
    -- Health monitoring
    health_check_url TEXT,
    health_status VARCHAR(20) DEFAULT 'unknown', -- 'healthy', 'degraded', 'unhealthy', 'unknown'
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Service metadata
    description TEXT,
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Configuration management
CREATE TABLE configuration_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Configuration identification
    service_name VARCHAR(100), -- NULL for global settings
    environment VARCHAR(50) NOT NULL, -- 'development', 'staging', 'production'
    config_key VARCHAR(255) NOT NULL,
    
    -- Configuration value
    config_value TEXT,
    value_type VARCHAR(20) DEFAULT 'string', -- 'string', 'number', 'boolean', 'json'
    is_encrypted BOOLEAN DEFAULT false,
    
    -- Metadata
    description TEXT,
    default_value TEXT,
    validation_rules JSONB DEFAULT '{}',
    
    -- Change tracking
    version INTEGER DEFAULT 1,
    changed_by UUID REFERENCES users(id),
    change_reason TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(service_name, environment, config_key)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Usage sessions indexes
CREATE INDEX idx_usage_sessions_user ON usage_sessions(user_id);
CREATE INDEX idx_usage_sessions_started ON usage_sessions(started_at);
CREATE INDEX idx_usage_sessions_ip ON usage_sessions(ip_address);

-- API usage logs indexes (partitioned by month)
CREATE INDEX idx_api_logs_timestamp ON api_usage_logs(timestamp);
CREATE INDEX idx_api_logs_endpoint ON api_usage_logs(endpoint);
CREATE INDEX idx_api_logs_user ON api_usage_logs(user_id);
CREATE INDEX idx_api_logs_status ON api_usage_logs(status_code);

-- Analytics reports indexes
CREATE INDEX idx_analytics_reports_type ON analytics_reports(report_type);
CREATE INDEX idx_analytics_reports_creator ON analytics_reports(created_by);
CREATE INDEX idx_analytics_reports_schedule ON analytics_reports(next_run_at);

-- Report executions indexes
CREATE INDEX idx_report_executions_report ON report_executions(report_id);
CREATE INDEX idx_report_executions_status ON report_executions(status);
CREATE INDEX idx_report_executions_started ON report_executions(started_at);

-- Cost centers indexes
CREATE INDEX idx_cost_centers_parent ON cost_centers(parent_cost_center_id);
CREATE INDEX idx_cost_centers_manager ON cost_centers(manager_id);

-- Cost allocations indexes (partitioned by billing_period)
CREATE INDEX idx_cost_allocations_user ON cost_allocations(user_id);
CREATE INDEX idx_cost_allocations_cost_center ON cost_allocations(cost_center_id);
CREATE INDEX idx_cost_allocations_period ON cost_allocations(billing_period);
CREATE INDEX idx_cost_allocations_service ON cost_allocations(service_type);

-- Data elements indexes
CREATE INDEX idx_data_elements_table ON data_elements(table_name);
CREATE INDEX idx_data_elements_classification ON data_elements(classification_id);
CREATE INDEX idx_data_elements_type ON data_elements(element_type);

-- Masking policies indexes
CREATE INDEX idx_masking_policies_active ON masking_policies(is_active);
CREATE INDEX idx_masking_policies_priority ON masking_policies(priority);

-- Encryption keys indexes
CREATE INDEX idx_encryption_keys_status ON encryption_keys(status);
CREATE INDEX idx_encryption_keys_purpose ON encryption_keys(key_purpose);
CREATE INDEX idx_encryption_keys_expires ON encryption_keys(expires_at);

-- Encrypted data registry indexes
CREATE INDEX idx_encrypted_data_table ON encrypted_data_registry(table_name, column_name);
CREATE INDEX idx_encrypted_data_key ON encrypted_data_registry(encryption_key_id);

-- Compliance assessments indexes
CREATE INDEX idx_compliance_assessments_framework ON compliance_assessments(framework_id);
CREATE INDEX idx_compliance_assessments_status ON compliance_assessments(status);
CREATE INDEX idx_compliance_assessments_period ON compliance_assessments(assessment_period_start, assessment_period_end);

-- Audit logs indexes (partitioned by month)
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_risk ON audit_logs(risk_level);
CREATE INDEX idx_audit_logs_compliance ON audit_logs(compliance_relevant);

-- Change tracking indexes
CREATE INDEX idx_change_tracking_changeset ON change_tracking(change_set_id);
CREATE INDEX idx_change_tracking_table_record ON change_tracking(table_name, record_id);
CREATE INDEX idx_change_tracking_changed_by ON change_tracking(changed_by);
CREATE INDEX idx_change_tracking_timestamp ON change_tracking(changed_at);

-- Security events indexes
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_status ON security_events(status);
CREATE INDEX idx_security_events_occurred ON security_events(occurred_at);
CREATE INDEX idx_security_events_source_user ON security_events(source_user_id);

-- Services indexes
CREATE INDEX idx_services_name ON services(service_name);
CREATE INDEX idx_services_type ON services(service_type);
CREATE INDEX idx_services_health ON services(health_status);
CREATE INDEX idx_services_active ON services(is_active);

-- Configuration settings indexes
CREATE INDEX idx_config_service_env ON configuration_settings(service_name, environment);
CREATE INDEX idx_config_key ON configuration_settings(config_key);
CREATE INDEX idx_config_active ON configuration_settings(is_active);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Apply triggers to new tables with updated_at columns
CREATE TRIGGER update_analytics_reports_updated_at BEFORE UPDATE ON analytics_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cost_centers_updated_at BEFORE UPDATE ON cost_centers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_classifications_updated_at BEFORE UPDATE ON data_classifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_elements_updated_at BEFORE UPDATE ON data_elements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_masking_policies_updated_at BEFORE UPDATE ON masking_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_frameworks_updated_at BEFORE UPDATE ON compliance_frameworks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_assessments_updated_at BEFORE UPDATE ON compliance_assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuration_settings_updated_at BEFORE UPDATE ON configuration_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

