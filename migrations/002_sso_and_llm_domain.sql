-- Migration 002: SSO and LLM Domain
-- Description: Creates SSO integration and LLM domain tables
-- Author: Manus AI
-- Date: 2025-01-30

-- ============================================================================
-- SSO INTEGRATION TABLES
-- ============================================================================

-- SSO providers configuration
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

-- User SSO account linkages
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

-- ============================================================================
-- LLM DOMAIN TABLES
-- ============================================================================

-- LLM providers and their configurations
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

-- LLM models and their capabilities
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

-- Enhanced conversations with context tracking
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

-- Enhanced messages with detailed tracking
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

-- Document management and processing
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

-- Document processing jobs
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

-- Prompt templates with versioning
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

-- LLM usage logging for analytics and cost tracking
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    
    -- Usage details
    model_id UUID REFERENCES llm_models(id),
    operation_type VARCHAR(50) NOT NULL, -- 'chat', 'completion', 'summarize', etc.
    
    -- Token usage
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Cost and performance
    cost DECIMAL(10, 6) DEFAULT 0,
    response_time_ms INTEGER,
    
    -- Metadata
    request_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR SSO AND LLM DOMAIN
-- ============================================================================

-- SSO providers indexes
CREATE INDEX idx_sso_providers_type ON sso_providers(provider_type);
CREATE INDEX idx_sso_providers_active ON sso_providers(is_active);

-- User SSO accounts indexes
CREATE INDEX idx_user_sso_accounts_user ON user_sso_accounts(user_id);
CREATE INDEX idx_user_sso_accounts_provider ON user_sso_accounts(provider_id);
CREATE INDEX idx_user_sso_accounts_external ON user_sso_accounts(external_id);

-- LLM providers indexes
CREATE INDEX idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX idx_llm_providers_health ON llm_providers(health_status);

-- LLM models indexes
CREATE INDEX idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX idx_llm_models_active ON llm_models(is_active);

-- Conversations indexes
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_state ON conversations(conversation_state);
CREATE INDEX idx_conversations_shared ON conversations(is_shared, share_token);
CREATE INDEX idx_conversations_updated ON conversations(updated_at);

-- Messages indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);
CREATE INDEX idx_messages_thread ON messages(thread_id);

-- Documents indexes
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_hash ON documents(file_hash);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_created ON documents(created_at);

-- Document processing jobs indexes
CREATE INDEX idx_document_jobs_document ON document_processing_jobs(document_id);
CREATE INDEX idx_document_jobs_user ON document_processing_jobs(user_id);
CREATE INDEX idx_document_jobs_status ON document_processing_jobs(status);
CREATE INDEX idx_document_jobs_type ON document_processing_jobs(processing_type);

-- Prompt templates indexes
CREATE INDEX idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_creator ON prompt_templates(created_by);
CREATE INDEX idx_prompt_templates_visibility ON prompt_templates(visibility);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);

-- LLM usage logs indexes (partitioned by month for performance)
CREATE INDEX idx_llm_usage_logs_user ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_usage_logs_conversation ON llm_usage_logs(conversation_id);
CREATE INDEX idx_llm_usage_logs_model ON llm_usage_logs(model_id);
CREATE INDEX idx_llm_usage_logs_created ON llm_usage_logs(created_at);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Apply triggers to new tables with updated_at columns
CREATE TRIGGER update_sso_providers_updated_at BEFORE UPDATE ON sso_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_providers_updated_at BEFORE UPDATE ON llm_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

