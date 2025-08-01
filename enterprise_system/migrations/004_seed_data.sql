-- Migration 004: Seed Data
-- Description: Inserts default data for resource types, roles, permissions, and configurations
-- Author: Manus AI
-- Date: 2025-01-30

-- ============================================================================
-- SEED RESOURCE TYPES
-- ============================================================================

INSERT INTO resource_types (name, description, available_actions) VALUES
('system', 'System-wide resources and configuration', ARRAY['manage', 'configure', 'monitor', 'backup', 'restore']),
('user', 'User accounts and profiles', ARRAY['create', 'read', 'update', 'delete', 'impersonate', 'reset_password']),
('role', 'Roles and permissions management', ARRAY['create', 'read', 'update', 'delete', 'assign', 'revoke']),
('permission', 'Permission management', ARRAY['create', 'read', 'update', 'delete', 'grant', 'revoke']),
('conversation', 'LLM conversations and chat history', ARRAY['create', 'read', 'update', 'delete', 'share', 'export']),
('message', 'Individual chat messages', ARRAY['create', 'read', 'update', 'delete', 'flag']),
('document', 'Documents and file management', ARRAY['create', 'read', 'update', 'delete', 'download', 'process']),
('prompt_template', 'Prompt templates and management', ARRAY['create', 'read', 'update', 'delete', 'use', 'share']),
('analytics', 'Analytics and reporting', ARRAY['create', 'read', 'update', 'delete', 'export', 'schedule']),
('audit', 'Audit logs and compliance', ARRAY['read', 'export', 'archive']),
('api', 'API endpoints and services', ARRAY['access', 'rate_limit_exempt', 'admin_access']),
('cost_center', 'Cost centers and budget management', ARRAY['create', 'read', 'update', 'delete', 'manage_budget']),
('encryption_key', 'Encryption key management', ARRAY['create', 'read', 'update', 'delete', 'rotate', 'use']),
('compliance', 'Compliance frameworks and assessments', ARRAY['create', 'read', 'update', 'delete', 'assess', 'report']);

-- ============================================================================
-- SEED DATA CLASSIFICATIONS
-- ============================================================================

INSERT INTO data_classifications (name, description, sensitivity_level, compliance_frameworks, encryption_required, masking_required) VALUES
('public', 'Publicly available information', 1, '{}', false, false),
('internal', 'Internal business information', 2, '{}', false, false),
('confidential', 'Confidential business information', 3, '{}', true, false),
('restricted', 'Restricted access information with PII', 4, ARRAY['GDPR'], true, true),
('top_secret', 'Highly classified information', 5, ARRAY['GDPR', 'HIPAA'], true, true);

-- ============================================================================
-- SEED COMPLIANCE FRAMEWORKS
-- ============================================================================

INSERT INTO compliance_frameworks (name, version, description, jurisdiction, framework_type, effective_date, requirements) VALUES
('GDPR', '2018', 'General Data Protection Regulation', 'EU', 'privacy', '2018-05-25', 
 '{"data_protection": true, "consent_management": true, "right_to_erasure": true, "data_portability": true, "breach_notification": true}'::jsonb),
('CCPA', '2020', 'California Consumer Privacy Act', 'US-CA', 'privacy', '2020-01-01',
 '{"consumer_rights": true, "data_disclosure": true, "opt_out_rights": true, "non_discrimination": true}'::jsonb),
('HIPAA', '1996', 'Health Insurance Portability and Accountability Act', 'US', 'privacy', '1996-08-21',
 '{"phi_protection": true, "access_controls": true, "audit_logs": true, "encryption": true}'::jsonb),
('SOX', '2002', 'Sarbanes-Oxley Act', 'US', 'financial', '2002-07-30',
 '{"financial_reporting": true, "internal_controls": true, "audit_requirements": true}'::jsonb),
('PCI-DSS', '4.0', 'Payment Card Industry Data Security Standard', 'Global', 'security', '2022-03-31',
 '{"network_security": true, "data_protection": true, "vulnerability_management": true, "access_control": true}'::jsonb);

-- ============================================================================
-- SEED DEFAULT ROLES
-- ============================================================================

INSERT INTO roles (name, display_name, description, is_system_role, is_assignable, role_level) VALUES
('super_admin', 'Super Administrator', 'Full system access with all permissions', true, true, 0),
('admin', 'Administrator', 'Administrative access to most system functions', true, true, 1),
('manager', 'Manager', 'Management access with team oversight capabilities', true, true, 2),
('analyst', 'Data Analyst', 'Analytics and reporting access', true, true, 3),
('user', 'Standard User', 'Basic user access to core features', true, true, 4),
('viewer', 'Viewer', 'Read-only access to permitted resources', true, true, 5),
('api_user', 'API User', 'Programmatic access for integrations', true, true, 4),
('compliance_officer', 'Compliance Officer', 'Compliance monitoring and reporting access', true, true, 2),
('security_admin', 'Security Administrator', 'Security configuration and monitoring access', true, true, 1),
('cost_manager', 'Cost Manager', 'Cost center and budget management access', true, true, 3);

-- ============================================================================
-- SEED PERMISSIONS
-- ============================================================================

-- System permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('system.manage', 'System Management', 'Full system management access', 
 (SELECT id FROM resource_types WHERE name = 'system'), 'manage', true),
('system.configure', 'System Configuration', 'System configuration access', 
 (SELECT id FROM resource_types WHERE name = 'system'), 'configure', true),
('system.monitor', 'System Monitoring', 'System monitoring and health checks', 
 (SELECT id FROM resource_types WHERE name = 'system'), 'monitor', true);

-- User management permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('user.create', 'Create Users', 'Create new user accounts', 
 (SELECT id FROM resource_types WHERE name = 'user'), 'create', true),
('user.read', 'Read Users', 'View user information', 
 (SELECT id FROM resource_types WHERE name = 'user'), 'read', true),
('user.update', 'Update Users', 'Modify user information', 
 (SELECT id FROM resource_types WHERE name = 'user'), 'update', true),
('user.delete', 'Delete Users', 'Delete user accounts', 
 (SELECT id FROM resource_types WHERE name = 'user'), 'delete', true),
('user.impersonate', 'Impersonate Users', 'Login as another user', 
 (SELECT id FROM resource_types WHERE name = 'user'), 'impersonate', true);

-- Role management permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('role.create', 'Create Roles', 'Create new roles', 
 (SELECT id FROM resource_types WHERE name = 'role'), 'create', true),
('role.read', 'Read Roles', 'View role information', 
 (SELECT id FROM resource_types WHERE name = 'role'), 'read', true),
('role.update', 'Update Roles', 'Modify role information', 
 (SELECT id FROM resource_types WHERE name = 'role'), 'update', true),
('role.delete', 'Delete Roles', 'Delete roles', 
 (SELECT id FROM resource_types WHERE name = 'role'), 'delete', true),
('role.assign', 'Assign Roles', 'Assign roles to users', 
 (SELECT id FROM resource_types WHERE name = 'role'), 'assign', true);

-- Conversation permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('conversation.create', 'Create Conversations', 'Start new conversations', 
 (SELECT id FROM resource_types WHERE name = 'conversation'), 'create', true),
('conversation.read', 'Read Conversations', 'View conversations', 
 (SELECT id FROM resource_types WHERE name = 'conversation'), 'read', true),
('conversation.update', 'Update Conversations', 'Modify conversations', 
 (SELECT id FROM resource_types WHERE name = 'conversation'), 'update', true),
('conversation.delete', 'Delete Conversations', 'Delete conversations', 
 (SELECT id FROM resource_types WHERE name = 'conversation'), 'delete', true),
('conversation.share', 'Share Conversations', 'Share conversations with others', 
 (SELECT id FROM resource_types WHERE name = 'conversation'), 'share', true);

-- Document permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('document.create', 'Upload Documents', 'Upload new documents', 
 (SELECT id FROM resource_types WHERE name = 'document'), 'create', true),
('document.read', 'Read Documents', 'View documents', 
 (SELECT id FROM resource_types WHERE name = 'document'), 'read', true),
('document.update', 'Update Documents', 'Modify documents', 
 (SELECT id FROM resource_types WHERE name = 'document'), 'update', true),
('document.delete', 'Delete Documents', 'Delete documents', 
 (SELECT id FROM resource_types WHERE name = 'document'), 'delete', true),
('document.process', 'Process Documents', 'Process documents with AI', 
 (SELECT id FROM resource_types WHERE name = 'document'), 'process', true);

-- Analytics permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('analytics.create', 'Create Reports', 'Create analytics reports', 
 (SELECT id FROM resource_types WHERE name = 'analytics'), 'create', true),
('analytics.read', 'View Analytics', 'View analytics and reports', 
 (SELECT id FROM resource_types WHERE name = 'analytics'), 'read', true),
('analytics.export', 'Export Analytics', 'Export analytics data', 
 (SELECT id FROM resource_types WHERE name = 'analytics'), 'export', true);

-- Audit permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('audit.read', 'View Audit Logs', 'View audit logs and compliance data', 
 (SELECT id FROM resource_types WHERE name = 'audit'), 'read', true),
('audit.export', 'Export Audit Data', 'Export audit logs and compliance reports', 
 (SELECT id FROM resource_types WHERE name = 'audit'), 'export', true);

-- API permissions
INSERT INTO permissions (name, display_name, description, resource_type_id, action, is_system_permission) VALUES
('api.access', 'API Access', 'Basic API access', 
 (SELECT id FROM resource_types WHERE name = 'api'), 'access', true),
('api.admin_access', 'Admin API Access', 'Administrative API access', 
 (SELECT id FROM resource_types WHERE name = 'api'), 'admin_access', true);

-- ============================================================================
-- ASSIGN PERMISSIONS TO ROLES
-- ============================================================================

-- Super Admin - All permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'super_admin';

-- Admin - Most permissions except super admin functions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin'
AND p.name NOT IN ('user.impersonate', 'system.manage');

-- Manager - User and team management
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'manager'
AND p.name IN (
    'user.read', 'user.update', 'role.read', 'role.assign',
    'conversation.read', 'document.read', 'analytics.read',
    'api.access'
);

-- Analyst - Analytics and reporting focus
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'analyst'
AND p.name IN (
    'user.read', 'conversation.read', 'document.read', 'document.process',
    'analytics.create', 'analytics.read', 'analytics.export',
    'audit.read', 'api.access'
);

-- Standard User - Basic functionality
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'user'
AND p.name IN (
    'conversation.create', 'conversation.read', 'conversation.update', 'conversation.delete',
    'document.create', 'document.read', 'document.update', 'document.delete', 'document.process',
    'api.access'
);

-- Viewer - Read-only access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'viewer'
AND p.name IN (
    'user.read', 'conversation.read', 'document.read', 'analytics.read'
);

-- API User - Programmatic access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'api_user'
AND p.name IN (
    'conversation.create', 'conversation.read', 'conversation.update',
    'document.create', 'document.read', 'document.process',
    'api.access'
);

-- Compliance Officer - Compliance and audit access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'compliance_officer'
AND p.name IN (
    'user.read', 'audit.read', 'audit.export', 'analytics.read', 'analytics.export'
);

-- Security Admin - Security management
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'security_admin'
AND p.name IN (
    'system.configure', 'system.monitor', 'user.read', 'user.update',
    'role.read', 'audit.read', 'audit.export', 'api.admin_access'
);

-- ============================================================================
-- SEED LLM PROVIDERS AND MODELS
-- ============================================================================

-- OpenAI Provider
INSERT INTO llm_providers (name, provider_type, api_base_url, default_model, supported_models, pricing_config) VALUES
('openai', 'openai', 'https://api.openai.com/v1', 'gpt-4o-mini',
 '["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]'::jsonb,
 '{"currency": "USD", "billing_unit": "tokens"}'::jsonb);

-- Get OpenAI provider ID for model insertion
DO $$
DECLARE
    openai_provider_id UUID;
BEGIN
    SELECT id INTO openai_provider_id FROM llm_providers WHERE name = 'openai';
    
    -- Insert OpenAI models
    INSERT INTO llm_models (provider_id, model_name, display_name, description, max_tokens, supports_functions, supports_vision, input_token_cost, output_token_cost) VALUES
    (openai_provider_id, 'gpt-4o', 'GPT-4o', 'Most advanced GPT-4 model with vision capabilities', 128000, true, true, 0.0025, 0.01),
    (openai_provider_id, 'gpt-4o-mini', 'GPT-4o Mini', 'Faster and more affordable GPT-4 model', 128000, true, true, 0.00015, 0.0006),
    (openai_provider_id, 'gpt-4-turbo', 'GPT-4 Turbo', 'High-performance GPT-4 model', 128000, true, true, 0.01, 0.03),
    (openai_provider_id, 'gpt-3.5-turbo', 'GPT-3.5 Turbo', 'Fast and efficient model for most tasks', 16385, true, false, 0.0005, 0.0015);
END $$;

-- ============================================================================
-- SEED CONFIGURATION SETTINGS
-- ============================================================================

-- Global system settings
INSERT INTO configuration_settings (service_name, environment, config_key, config_value, value_type, description) VALUES
(NULL, 'production', 'system.name', 'Enterprise AI System', 'string', 'System display name'),
(NULL, 'production', 'system.version', '1.0.0', 'string', 'Current system version'),
(NULL, 'production', 'security.session_timeout', '1800', 'number', 'Session timeout in seconds'),
(NULL, 'production', 'security.max_login_attempts', '5', 'number', 'Maximum failed login attempts'),
(NULL, 'production', 'security.password_min_length', '8', 'number', 'Minimum password length'),
(NULL, 'production', 'llm.default_model', 'gpt-4o-mini', 'string', 'Default LLM model'),
(NULL, 'production', 'llm.max_tokens_per_request', '4000', 'number', 'Maximum tokens per LLM request'),
(NULL, 'production', 'analytics.retention_days', '365', 'number', 'Analytics data retention period'),
(NULL, 'production', 'audit.retention_days', '2555', 'number', 'Audit log retention period (7 years)'),
(NULL, 'production', 'files.max_upload_size', '104857600', 'number', 'Maximum file upload size in bytes (100MB)');

-- Service-specific settings
INSERT INTO configuration_settings (service_name, environment, config_key, config_value, value_type, description) VALUES
('user_service', 'production', 'jwt.access_token_expires', '1800', 'number', 'JWT access token expiration in seconds'),
('user_service', 'production', 'jwt.refresh_token_expires', '604800', 'number', 'JWT refresh token expiration in seconds'),
('llm_service', 'production', 'rate_limit.requests_per_minute', '60', 'number', 'Rate limit for LLM requests per minute'),
('llm_service', 'production', 'rate_limit.tokens_per_hour', '100000', 'number', 'Rate limit for tokens per hour'),
('analytics_service', 'production', 'reports.max_concurrent_executions', '5', 'number', 'Maximum concurrent report executions');

-- ============================================================================
-- SEED COST CENTERS
-- ============================================================================

INSERT INTO cost_centers (name, description, code, monthly_budget, annual_budget) VALUES
('Engineering', 'Engineering and development team', 'ENG', 10000.00, 120000.00),
('Marketing', 'Marketing and growth team', 'MKT', 5000.00, 60000.00),
('Sales', 'Sales and business development', 'SALES', 3000.00, 36000.00),
('Operations', 'Operations and infrastructure', 'OPS', 8000.00, 96000.00),
('Research', 'Research and development', 'R&D', 15000.00, 180000.00),
('General', 'General administrative costs', 'GEN', 2000.00, 24000.00);

-- ============================================================================
-- SEED PROMPT TEMPLATES
-- ============================================================================

-- Get the first user ID for template creation (will be updated when real users exist)
DO $$
DECLARE
    system_user_id UUID := gen_random_uuid();
BEGIN
    -- Insert system user for template ownership
    INSERT INTO users (id, email, username, first_name, last_name, is_active, is_verified) 
    VALUES (system_user_id, 'system@enterprise.ai', 'system', 'System', 'User', true, true);
    
    -- Insert default prompt templates
    INSERT INTO prompt_templates (name, display_name, description, category, template_content, required_variables, created_by) VALUES
    ('document_summary', 'Document Summary', 'Summarize uploaded documents', 'document_processing',
     'Please provide a comprehensive summary of the following document:\n\n{document_content}\n\nSummary should include:\n- Main topics and themes\n- Key findings or conclusions\n- Important details and data points\n- Actionable insights',
     '["document_content"]'::jsonb, system_user_id),
    
    ('code_review', 'Code Review', 'Review code for best practices and issues', 'development',
     'Please review the following code for:\n- Best practices\n- Potential bugs or issues\n- Performance improvements\n- Security concerns\n\nCode:\n```{language}\n{code}\n```\n\nProvide specific feedback and suggestions.',
     '["code", "language"]'::jsonb, system_user_id),
    
    ('data_analysis', 'Data Analysis', 'Analyze data and provide insights', 'analytics',
     'Analyze the following data and provide insights:\n\n{data}\n\nPlease include:\n- Key patterns and trends\n- Statistical observations\n- Recommendations based on the data\n- Potential areas for further investigation',
     '["data"]'::jsonb, system_user_id),
    
    ('meeting_notes', 'Meeting Notes Summary', 'Summarize meeting notes and extract action items', 'productivity',
     'Please summarize the following meeting notes and extract action items:\n\n{meeting_notes}\n\nProvide:\n- Meeting summary\n- Key decisions made\n- Action items with owners (if mentioned)\n- Follow-up items',
     '["meeting_notes"]'::jsonb, system_user_id),
    
    ('email_draft', 'Professional Email Draft', 'Draft professional emails', 'communication',
     'Draft a professional email with the following details:\n\nTo: {recipient}\nSubject: {subject}\nPurpose: {purpose}\nKey points to include: {key_points}\nTone: {tone}\n\nPlease write a clear, professional email that addresses all the key points.',
     '["recipient", "subject", "purpose", "key_points", "tone"]'::jsonb, system_user_id);
END $$;

-- ============================================================================
-- CREATE SYSTEM RESOURCES
-- ============================================================================

-- Create system-level resources
INSERT INTO resources (resource_type_id, resource_id, name, description) VALUES
((SELECT id FROM resource_types WHERE name = 'system'), 'global', 'Global System', 'Global system configuration and management'),
((SELECT id FROM resource_types WHERE name = 'api'), 'public_api', 'Public API', 'Public API endpoints'),
((SELECT id FROM resource_types WHERE name = 'api'), 'admin_api', 'Admin API', 'Administrative API endpoints'),
((SELECT id FROM resource_types WHERE name = 'analytics'), 'system_analytics', 'System Analytics', 'System-wide analytics and reporting');

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

-- Log the completion of seed data migration
DO $$
BEGIN
    RAISE NOTICE 'Seed data migration completed successfully';
    RAISE NOTICE 'Created % resource types', (SELECT COUNT(*) FROM resource_types);
    RAISE NOTICE 'Created % roles', (SELECT COUNT(*) FROM roles);
    RAISE NOTICE 'Created % permissions', (SELECT COUNT(*) FROM permissions);
    RAISE NOTICE 'Created % role-permission assignments', (SELECT COUNT(*) FROM role_permissions);
    RAISE NOTICE 'Created % LLM models', (SELECT COUNT(*) FROM llm_models);
    RAISE NOTICE 'Created % configuration settings', (SELECT COUNT(*) FROM configuration_settings);
    RAISE NOTICE 'Created % prompt templates', (SELECT COUNT(*) FROM prompt_templates);
END $$;

