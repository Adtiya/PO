# Enterprise AI System - Database Schema Design

## Overview

This document outlines the comprehensive database schema design for the Enterprise AI System, implementing dynamic Role-Based Access Control (RBAC) and supporting all microservices components including Profile/Identity (PI), Object-Based Reasoning (OBR), Data Analytics (DA), Business Abstraction (BA), and Platform Services (PS) layers.

The schema is designed for PostgreSQL and follows enterprise-grade patterns for scalability, security, and maintainability. It supports dynamic permission management, resource-based access control, audit logging, SSO integration, data masking, and comprehensive analytics.

## Core Design Principles

### 1. Dynamic RBAC Foundation
The schema implements a flexible permission system that supports:
- Resource-based permissions with granular control
- Permission inheritance through role hierarchies
- Context-aware access control based on conditions
- Temporal permissions with expiration dates
- Delegation and proxy permissions

### 2. Microservices Architecture Support
Each service domain has dedicated schemas while maintaining referential integrity:
- **Identity Domain**: User management, authentication, and profiles
- **Authorization Domain**: Dynamic RBAC with advanced features
- **LLM Domain**: AI integration, conversations, and analytics
- **Analytics Domain**: Business intelligence and reporting
- **Security Domain**: Audit logging, data masking, and compliance

### 3. Enterprise Security Features
- Comprehensive audit trails for all operations
- Data classification and masking capabilities
- Encryption key management
- Compliance tracking and reporting
- Multi-tenant isolation support

### 4. Performance and Scalability
- Optimized indexing strategies
- Partitioning for large tables
- Caching-friendly design
- Read replica support
- Connection pooling optimization

## Schema Domains



## 1. Identity Domain

The Identity domain manages user accounts, profiles, authentication, and SSO integration. It serves as the foundation for all user-related operations across the system.

### 1.1 Users Table

The central user entity with comprehensive profile information and security features.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL for SSO-only users
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    phone_number VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en-US',
    
    -- Account status and verification
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    phone_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Security tracking
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    
    -- Multi-factor authentication
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret VARCHAR(255),
    backup_codes TEXT[], -- Encrypted backup codes
    
    -- Metadata and timestamps
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete support
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login_at);
```

### 1.2 User Profiles Table

Extended profile information for enhanced user management and personalization.

```sql
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Personal information
    date_of_birth DATE,
    gender VARCHAR(20),
    bio TEXT,
    website_url TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    
    -- Professional information
    job_title VARCHAR(200),
    company VARCHAR(200),
    department VARCHAR(100),
    manager_id UUID REFERENCES users(id),
    
    -- Preferences
    notification_preferences JSONB DEFAULT '{}',
    privacy_settings JSONB DEFAULT '{}',
    ui_preferences JSONB DEFAULT '{}',
    
    -- Location information
    country VARCHAR(100),
    state_province VARCHAR(100),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    address_line1 TEXT,
    address_line2 TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_manager ON user_profiles(manager_id);
CREATE INDEX idx_user_profiles_company ON user_profiles(company);
```

### 1.3 SSO Providers and Integrations

Support for multiple SSO providers and external identity systems.

```sql
CREATE TABLE sso_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL, -- 'oauth2', 'saml', 'oidc'
    
    -- Configuration
    client_id VARCHAR(255),
    client_secret VARCHAR(255), -- Encrypted
    discovery_url TEXT,
    authorization_url TEXT,
    token_url TEXT,
    userinfo_url TEXT,
    jwks_url TEXT,
    
    -- SAML specific
    saml_metadata_url TEXT,
    saml_certificate TEXT,
    
    -- Provider settings
    scopes TEXT[],
    attribute_mapping JSONB DEFAULT '{}',
    auto_create_users BOOLEAN DEFAULT false,
    auto_assign_roles UUID[], -- Default roles for new users
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sso_providers_type ON sso_providers(provider_type);
CREATE INDEX idx_sso_providers_active ON sso_providers(is_active);
```

```sql
CREATE TABLE user_sso_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES sso_providers(id) ON DELETE CASCADE,
    
    -- External account information
    external_id VARCHAR(255) NOT NULL,
    external_username VARCHAR(255),
    external_email VARCHAR(255),
    
    -- Token management
    access_token TEXT, -- Encrypted
    refresh_token TEXT, -- Encrypted
    token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Account linking
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    external_data JSONB DEFAULT '{}',
    
    UNIQUE(provider_id, external_id)
);

CREATE INDEX idx_user_sso_accounts_user ON user_sso_accounts(user_id);
CREATE INDEX idx_user_sso_accounts_provider ON user_sso_accounts(provider_id);
CREATE INDEX idx_user_sso_accounts_external ON user_sso_accounts(external_id);
```

## 2. Authorization Domain

The Authorization domain implements the dynamic RBAC system with advanced features including resource-based permissions, role hierarchies, and context-aware access control.

### 2.1 Resources and Resource Types

Define the resources that can be protected by the permission system.

```sql
CREATE TABLE resource_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Resource hierarchy support
    parent_type_id UUID REFERENCES resource_types(id),
    
    -- Available actions for this resource type
    available_actions TEXT[] NOT NULL DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Built-in resource types
INSERT INTO resource_types (name, description, available_actions) VALUES
('system', 'System-wide resources', ARRAY['manage', 'configure', 'monitor']),
('user', 'User accounts and profiles', ARRAY['create', 'read', 'update', 'delete', 'impersonate']),
('role', 'Roles and permissions', ARRAY['create', 'read', 'update', 'delete', 'assign']),
('conversation', 'LLM conversations', ARRAY['create', 'read', 'update', 'delete', 'share']),
('document', 'Documents and files', ARRAY['create', 'read', 'update', 'delete', 'download']),
('analytics', 'Analytics and reports', ARRAY['create', 'read', 'update', 'delete', 'export']),
('api', 'API endpoints', ARRAY['access', 'rate_limit_exempt']);
```

```sql
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type_id UUID NOT NULL REFERENCES resource_types(id),
    
    -- Resource identification
    resource_id VARCHAR(255) NOT NULL, -- External resource identifier
    name VARCHAR(255),
    description TEXT,
    
    -- Hierarchy support
    parent_resource_id UUID REFERENCES resources(id),
    
    -- Ownership
    owner_id UUID REFERENCES users(id),
    
    -- Resource attributes for condition evaluation
    attributes JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(resource_type_id, resource_id)
);

CREATE INDEX idx_resources_type ON resources(resource_type_id);
CREATE INDEX idx_resources_owner ON resources(owner_id);
CREATE INDEX idx_resources_parent ON resources(parent_resource_id);
CREATE INDEX idx_resources_active ON resources(is_active);
```

### 2.2 Dynamic Roles and Role Hierarchies

Enhanced role system supporting hierarchies, inheritance, and dynamic creation.

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    
    -- Role hierarchy
    parent_role_id UUID REFERENCES roles(id),
    role_level INTEGER DEFAULT 0, -- For hierarchy depth
    
    -- Role properties
    is_system_role BOOLEAN DEFAULT false, -- Cannot be deleted
    is_assignable BOOLEAN DEFAULT true,
    max_assignments INTEGER, -- Limit number of users
    
    -- Temporal properties
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Auto-assignment rules
    auto_assign_conditions JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_roles_parent ON roles(parent_role_id);
CREATE INDEX idx_roles_level ON roles(role_level);
CREATE INDEX idx_roles_assignable ON roles(is_assignable);
CREATE INDEX idx_roles_valid ON roles(valid_from, valid_until);
```

### 2.3 Permissions and Permission Policies

Granular permission system with condition-based access control.

```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Permission identification
    name VARCHAR(200) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- Resource and action
    resource_type_id UUID NOT NULL REFERENCES resource_types(id),
    action VARCHAR(100) NOT NULL,
    
    -- Condition-based access control
    conditions JSONB DEFAULT '{}', -- JSON conditions for evaluation
    
    -- Permission properties
    is_system_permission BOOLEAN DEFAULT false,
    requires_approval BOOLEAN DEFAULT false,
    approval_workflow_id UUID, -- Reference to workflow system
    
    -- Temporal properties
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_permissions_resource_action ON permissions(resource_type_id, action);
CREATE INDEX idx_permissions_valid ON permissions(valid_from, valid_until);
```

```sql
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    
    -- Permission grant properties
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Temporal override
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Conditions override
    additional_conditions JSONB DEFAULT '{}',
    
    UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);
CREATE INDEX idx_role_permissions_valid ON role_permissions(valid_from, valid_until);
```

### 2.4 User Role Assignments

Dynamic user-role assignments with advanced features.

```sql
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    
    -- Assignment properties
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assignment_reason TEXT,
    
    -- Temporal assignment
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Context-specific assignment
    context_conditions JSONB DEFAULT '{}',
    resource_scope UUID REFERENCES resources(id), -- Limit to specific resource
    
    -- Delegation support
    is_delegated BOOLEAN DEFAULT false,
    delegated_by UUID REFERENCES users(id),
    delegation_depth INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES users(id),
    revocation_reason TEXT,
    
    UNIQUE(user_id, role_id, resource_scope)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_roles_active ON user_roles(is_active);
CREATE INDEX idx_user_roles_valid ON user_roles(valid_from, valid_until);
CREATE INDEX idx_user_roles_delegated ON user_roles(is_delegated, delegated_by);
```

### 2.5 Direct User Permissions

Support for direct permission grants bypassing roles.

```sql
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    
    -- Resource-specific permission
    resource_id UUID REFERENCES resources(id),
    
    -- Grant properties
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    grant_reason TEXT,
    
    -- Temporal permission
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Conditions override
    additional_conditions JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES users(id),
    revocation_reason TEXT,
    
    UNIQUE(user_id, permission_id, resource_id)
);

CREATE INDEX idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission ON user_permissions(permission_id);
CREATE INDEX idx_user_permissions_resource ON user_permissions(resource_id);
CREATE INDEX idx_user_permissions_active ON user_permissions(is_active);
CREATE INDEX idx_user_permissions_valid ON user_permissions(valid_from, valid_until);
```


## 3. LLM Domain

The LLM domain manages AI interactions, conversations, document processing, and usage analytics with enhanced tracking and cost management capabilities.

### 3.1 LLM Providers and Models

Support for multiple LLM providers and model configurations.

```sql
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL, -- 'openai', 'anthropic', 'azure', 'local'
    
    -- API configuration
    api_base_url TEXT,
    api_key_encrypted TEXT, -- Encrypted API key
    api_version VARCHAR(20),
    
    -- Provider settings
    default_model VARCHAR(100),
    supported_models JSONB DEFAULT '[]',
    rate_limits JSONB DEFAULT '{}',
    pricing_config JSONB DEFAULT '{}',
    
    -- Status and health
    is_active BOOLEAN DEFAULT true,
    health_status VARCHAR(20) DEFAULT 'unknown', -- 'healthy', 'degraded', 'down'
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX idx_llm_providers_health ON llm_providers(health_status);
```

```sql
CREATE TABLE llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    
    -- Model identification
    model_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    
    -- Model capabilities
    max_tokens INTEGER,
    supports_functions BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    supports_streaming BOOLEAN DEFAULT true,
    
    -- Pricing
    input_token_cost DECIMAL(10, 8), -- Cost per 1K input tokens
    output_token_cost DECIMAL(10, 8), -- Cost per 1K output tokens
    
    -- Performance characteristics
    average_latency_ms INTEGER,
    quality_score DECIMAL(3, 2), -- 0.00 to 5.00
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(provider_id, model_name)
);

CREATE INDEX idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX idx_llm_models_active ON llm_models(is_active);
```

### 3.2 Enhanced Conversations and Messages

Advanced conversation management with context tracking and analytics.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Conversation properties
    title VARCHAR(255),
    description TEXT,
    conversation_type VARCHAR(50) DEFAULT 'chat', -- 'chat', 'analysis', 'generation'
    
    -- Context and state
    context JSONB DEFAULT '{}',
    system_prompt TEXT,
    conversation_state VARCHAR(20) DEFAULT 'active', -- 'active', 'archived', 'deleted'
    
    -- Model configuration
    default_model_id UUID REFERENCES llm_models(id),
    model_parameters JSONB DEFAULT '{}', -- temperature, max_tokens, etc.
    
    -- Sharing and collaboration
    is_shared BOOLEAN DEFAULT false,
    share_token VARCHAR(255) UNIQUE,
    shared_until TIMESTAMP WITH TIME ZONE,
    
    -- Analytics
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_state ON conversations(conversation_state);
CREATE INDEX idx_conversations_shared ON conversations(is_shared, share_token);
CREATE INDEX idx_conversations_updated ON conversations(updated_at);
```

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message properties
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system', 'function'
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- 'text', 'image', 'file', 'function_call'
    
    -- Model and processing
    model_id UUID REFERENCES llm_models(id),
    model_parameters JSONB DEFAULT '{}',
    
    -- Token usage and cost
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0,
    
    -- Performance metrics
    response_time_ms INTEGER,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Message relationships
    parent_message_id UUID REFERENCES messages(id),
    thread_id UUID, -- For branching conversations
    
    -- Content analysis
    sentiment_score DECIMAL(3, 2), -- -1.00 to 1.00
    content_categories TEXT[],
    safety_flags JSONB DEFAULT '{}',
    
    -- Metadata and attachments
    metadata JSONB DEFAULT '{}',
    attachments JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);
CREATE INDEX idx_messages_thread ON messages(thread_id);
```

### 3.3 Document Processing and Knowledge Management

Enhanced document processing with versioning and knowledge extraction.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Document properties
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64), -- SHA-256 hash for deduplication
    
    -- Storage information
    storage_provider VARCHAR(50), -- 's3', 'gcs', 'azure', 'local'
    storage_path TEXT,
    storage_metadata JSONB DEFAULT '{}',
    
    -- Document classification
    document_type VARCHAR(50), -- 'pdf', 'docx', 'txt', 'image', 'spreadsheet'
    content_type VARCHAR(50), -- 'contract', 'report', 'presentation', 'code'
    language VARCHAR(10),
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    extraction_status VARCHAR(20) DEFAULT 'pending',
    
    -- Content extraction
    extracted_text TEXT,
    extracted_metadata JSONB DEFAULT '{}',
    page_count INTEGER,
    word_count INTEGER,
    
    -- Security and access
    access_level VARCHAR(20) DEFAULT 'private', -- 'private', 'shared', 'public'
    encryption_key_id UUID,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_hash ON documents(file_hash);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_created ON documents(created_at);
```

```sql
CREATE TABLE document_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Job configuration
    processing_type VARCHAR(50) NOT NULL, -- 'extract', 'summarize', 'analyze', 'translate'
    job_parameters JSONB DEFAULT '{}',
    
    -- Processing details
    model_id UUID REFERENCES llm_models(id),
    status VARCHAR(20) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    
    -- Results
    output_data JSONB,
    error_message TEXT,
    
    -- Performance metrics
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_document_jobs_document ON document_processing_jobs(document_id);
CREATE INDEX idx_document_jobs_user ON document_processing_jobs(user_id);
CREATE INDEX idx_document_jobs_status ON document_processing_jobs(status);
CREATE INDEX idx_document_jobs_type ON document_processing_jobs(processing_type);
```

### 3.4 Prompt Templates and Management

Advanced prompt template system with versioning and analytics.

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    tags TEXT[],
    
    -- Template content
    template_content TEXT NOT NULL,
    template_version INTEGER DEFAULT 1,
    
    -- Variables and validation
    required_variables JSONB DEFAULT '[]',
    optional_variables JSONB DEFAULT '[]',
    variable_schemas JSONB DEFAULT '{}', -- JSON Schema for validation
    
    -- Model configuration
    recommended_models UUID[],
    default_parameters JSONB DEFAULT '{}',
    
    -- Usage and performance
    usage_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3, 2),
    performance_metrics JSONB DEFAULT '{}',
    
    -- Access control
    visibility VARCHAR(20) DEFAULT 'private', -- 'private', 'shared', 'public'
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(name, template_version)
);

CREATE INDEX idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_creator ON prompt_templates(created_by);
CREATE INDEX idx_prompt_templates_visibility ON prompt_templates(visibility);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);
```

## 4. Analytics Domain

The Analytics domain provides comprehensive business intelligence, usage tracking, and performance monitoring capabilities.

### 4.1 Usage Analytics and Metrics

Detailed tracking of system usage and performance metrics.

```sql
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

CREATE INDEX idx_usage_sessions_user ON usage_sessions(user_id);
CREATE INDEX idx_usage_sessions_started ON usage_sessions(started_at);
CREATE INDEX idx_usage_sessions_ip ON usage_sessions(ip_address);
```

```sql
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

-- Partition by month for performance
CREATE INDEX idx_api_logs_timestamp ON api_usage_logs(timestamp);
CREATE INDEX idx_api_logs_endpoint ON api_usage_logs(endpoint);
CREATE INDEX idx_api_logs_user ON api_usage_logs(user_id);
CREATE INDEX idx_api_logs_status ON api_usage_logs(status_code);
```

### 4.2 Business Analytics and Reporting

Advanced analytics for business intelligence and decision making.

```sql
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

CREATE INDEX idx_analytics_reports_type ON analytics_reports(report_type);
CREATE INDEX idx_analytics_reports_creator ON analytics_reports(created_by);
CREATE INDEX idx_analytics_reports_schedule ON analytics_reports(next_run_at);
```

```sql
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

CREATE INDEX idx_report_executions_report ON report_executions(report_id);
CREATE INDEX idx_report_executions_status ON report_executions(status);
CREATE INDEX idx_report_executions_started ON report_executions(started_at);
```

### 4.3 Cost Tracking and Billing

Comprehensive cost management and billing analytics.

```sql
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

CREATE INDEX idx_cost_centers_parent ON cost_centers(parent_cost_center_id);
CREATE INDEX idx_cost_centers_manager ON cost_centers(manager_id);
```

```sql
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

-- Partition by billing_period for performance
CREATE INDEX idx_cost_allocations_user ON cost_allocations(user_id);
CREATE INDEX idx_cost_allocations_cost_center ON cost_allocations(cost_center_id);
CREATE INDEX idx_cost_allocations_period ON cost_allocations(billing_period);
CREATE INDEX idx_cost_allocations_service ON cost_allocations(service_type);
```


## 5. Security Domain

The Security domain manages data classification, masking, encryption, and compliance features essential for enterprise security.

### 5.1 Data Classification and Masking

Comprehensive data classification system with automated PII detection and masking capabilities.

```sql
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

-- Built-in classifications
INSERT INTO data_classifications (name, description, sensitivity_level, compliance_frameworks, encryption_required, masking_required) VALUES
('public', 'Publicly available information', 1, '{}', false, false),
('internal', 'Internal business information', 2, '{}', false, false),
('confidential', 'Confidential business information', 3, '{}', true, false),
('restricted', 'Restricted access information', 4, ARRAY['GDPR'], true, true),
('top_secret', 'Highly classified information', 5, ARRAY['GDPR', 'HIPAA'], true, true);
```

```sql
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

CREATE INDEX idx_data_elements_table ON data_elements(table_name);
CREATE INDEX idx_data_elements_classification ON data_elements(classification_id);
CREATE INDEX idx_data_elements_type ON data_elements(element_type);
```

```sql
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

CREATE INDEX idx_masking_policies_active ON masking_policies(is_active);
CREATE INDEX idx_masking_policies_priority ON masking_policies(priority);
```

### 5.2 Encryption and Key Management

Enterprise-grade encryption key management system.

```sql
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

CREATE INDEX idx_encryption_keys_status ON encryption_keys(status);
CREATE INDEX idx_encryption_keys_purpose ON encryption_keys(key_purpose);
CREATE INDEX idx_encryption_keys_expires ON encryption_keys(expires_at);
```

```sql
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

CREATE INDEX idx_encrypted_data_table ON encrypted_data_registry(table_name, column_name);
CREATE INDEX idx_encrypted_data_key ON encrypted_data_registry(encryption_key_id);
```

### 5.3 Compliance and Governance

Comprehensive compliance tracking and governance framework.

```sql
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

-- Built-in compliance frameworks
INSERT INTO compliance_frameworks (name, version, description, jurisdiction, framework_type, effective_date) VALUES
('GDPR', '2018', 'General Data Protection Regulation', 'EU', 'privacy', '2018-05-25'),
('CCPA', '2020', 'California Consumer Privacy Act', 'US-CA', 'privacy', '2020-01-01'),
('HIPAA', '1996', 'Health Insurance Portability and Accountability Act', 'US', 'privacy', '1996-08-21'),
('SOX', '2002', 'Sarbanes-Oxley Act', 'US', 'financial', '2002-07-30'),
('PCI-DSS', '4.0', 'Payment Card Industry Data Security Standard', 'Global', 'security', '2022-03-31');
```

```sql
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

CREATE INDEX idx_compliance_assessments_framework ON compliance_assessments(framework_id);
CREATE INDEX idx_compliance_assessments_status ON compliance_assessments(status);
CREATE INDEX idx_compliance_assessments_period ON compliance_assessments(assessment_period_start, assessment_period_end);
```

## 6. Audit Domain

The Audit domain provides comprehensive audit logging, change tracking, and forensic capabilities.

### 6.1 Comprehensive Audit Logging

Enterprise-grade audit logging with detailed change tracking and forensic capabilities.

```sql
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

-- Partition by month for performance
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_risk ON audit_logs(risk_level);
CREATE INDEX idx_audit_logs_compliance ON audit_logs(compliance_relevant);
```

### 6.2 Change Tracking and Versioning

Detailed change tracking for critical data with versioning support.

```sql
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

CREATE INDEX idx_change_tracking_changeset ON change_tracking(change_set_id);
CREATE INDEX idx_change_tracking_table_record ON change_tracking(table_name, record_id);
CREATE INDEX idx_change_tracking_changed_by ON change_tracking(changed_by);
CREATE INDEX idx_change_tracking_timestamp ON change_tracking(changed_at);
```

### 6.3 Security Events and Incident Tracking

Advanced security event monitoring and incident response tracking.

```sql
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

CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_status ON security_events(status);
CREATE INDEX idx_security_events_occurred ON security_events(occurred_at);
CREATE INDEX idx_security_events_source_user ON security_events(source_user_id);
```

## 7. Microservices Support Tables

Additional tables to support the microservices architecture and inter-service communication.

### 7.1 Service Registry and Discovery

Service registry for microservices discovery and health monitoring.

```sql
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

CREATE INDEX idx_services_name ON services(service_name);
CREATE INDEX idx_services_type ON services(service_type);
CREATE INDEX idx_services_health ON services(health_status);
CREATE INDEX idx_services_active ON services(is_active);
```

### 7.2 Configuration Management

Centralized configuration management for all services.

```sql
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

CREATE INDEX idx_config_service_env ON configuration_settings(service_name, environment);
CREATE INDEX idx_config_key ON configuration_settings(config_key);
CREATE INDEX idx_config_active ON configuration_settings(is_active);
```

## 8. Performance Optimization

### 8.1 Indexing Strategy

The schema includes comprehensive indexing for optimal query performance:

- **Primary Keys**: All tables use UUID primary keys for global uniqueness
- **Foreign Keys**: All foreign key relationships are indexed
- **Query Patterns**: Indexes optimized for common query patterns
- **Composite Indexes**: Multi-column indexes for complex queries
- **Partial Indexes**: Conditional indexes for filtered queries

### 8.2 Partitioning Strategy

Large tables are designed for partitioning:

- **Time-based Partitioning**: Audit logs, usage logs, and analytics data
- **Hash Partitioning**: User data and conversations for horizontal scaling
- **Range Partitioning**: Cost allocations and billing data by period

### 8.3 Caching Considerations

Tables designed for effective caching:

- **Permission Cache**: Role and permission data optimized for Redis caching
- **Session Cache**: User session data with TTL support
- **Configuration Cache**: Service configuration with change notifications

## 9. Migration and Deployment

### 9.1 Migration Scripts

The schema will be deployed using versioned migration scripts:

1. **Initial Schema**: Core tables and relationships
2. **Data Seeding**: Default roles, permissions, and configurations
3. **Indexes and Constraints**: Performance optimizations
4. **Partitioning Setup**: Large table partitioning
5. **Security Setup**: Encryption keys and audit triggers

### 9.2 Backup and Recovery

Comprehensive backup strategy:

- **Point-in-time Recovery**: Transaction log backups
- **Cross-region Replication**: Disaster recovery setup
- **Encrypted Backups**: All backups encrypted at rest
- **Compliance Retention**: Long-term retention for audit data

This comprehensive database schema provides the foundation for a robust, scalable, and secure enterprise AI system with dynamic RBAC capabilities, comprehensive audit logging, and advanced analytics features.

