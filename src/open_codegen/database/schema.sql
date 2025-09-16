-- Open Codegen Supabase Database Schema
-- Run this script in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable RLS (Row Level Security)
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- User sessions table for authentication
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- API provider configurations
CREATE TABLE IF NOT EXISTS api_provider_configs (
    provider_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    provider_name TEXT NOT NULL, -- 'openai', 'anthropic', 'gemini', 'codegen', 'z.ai', 'custom'
    provider_type TEXT NOT NULL, -- 'api', 'website'
    base_url TEXT,
    api_key TEXT, -- Encrypted
    model_mappings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider_name)
);

-- Endpoint configurations
CREATE TABLE IF NOT EXISTS endpoint_configs (
    endpoint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    endpoint_type TEXT NOT NULL, -- 'api', 'website'
    provider_id UUID REFERENCES api_provider_configs(provider_id) ON DELETE CASCADE,
    
    -- API endpoint fields
    url TEXT,
    method TEXT DEFAULT 'POST',
    headers JSONB DEFAULT '{}'::jsonb,
    
    -- Website endpoint fields
    website_url TEXT,
    input_selector TEXT, -- CSS/XPath selector for input field
    send_button_selector TEXT, -- CSS/XPath selector for send button
    response_selector TEXT, -- CSS/XPath selector for response
    wait_for_response_ms INTEGER DEFAULT 5000,
    
    -- Common fields
    variables JSONB DEFAULT '[]'::jsonb, -- Array of variable definitions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Endpoint variables (dynamic configuration)
CREATE TABLE IF NOT EXISTS endpoint_variables (
    variable_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint_id UUID NOT NULL REFERENCES endpoint_configs(endpoint_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    variable_type TEXT NOT NULL, -- 'string', 'number', 'boolean', 'json', 'secret'
    default_value TEXT,
    description TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    validation_rules JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(endpoint_id, name)
);

-- Website integration configurations
CREATE TABLE IF NOT EXISTS website_integrations (
    integration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    website_url TEXT NOT NULL,
    
    -- Selectors for different elements
    selectors JSONB NOT NULL DEFAULT '{
        "input": "",
        "send_button": "",
        "response": "",
        "error": "",
        "loading": ""
    }'::jsonb,
    
    -- Browser configuration
    browser_config JSONB DEFAULT '{
        "headless": true,
        "timeout": 30000,
        "wait_for_response": 5000,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }'::jsonb,
    
    -- Authentication if needed
    auth_config JSONB DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT TRUE,
    last_tested_at TIMESTAMPTZ,
    test_status TEXT, -- 'success', 'failed', 'pending'
    test_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI agent configurations
CREATE TABLE IF NOT EXISTS ai_agent_configs (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL, -- 'endpoint_creator', 'endpoint_tester', 'debugger'
    
    -- Agent configuration
    config JSONB NOT NULL DEFAULT '{
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": ""
    }'::jsonb,
    
    -- Capabilities
    capabilities JSONB DEFAULT '[]'::jsonb, -- Array of capability strings
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI agent conversations
CREATE TABLE IF NOT EXISTS ai_agent_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES ai_agent_configs(agent_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    title TEXT,
    
    -- Conversation state
    messages JSONB DEFAULT '[]'::jsonb, -- Array of message objects
    context JSONB DEFAULT '{}'::jsonb, -- Conversation context
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Endpoint test results
CREATE TABLE IF NOT EXISTS endpoint_test_results (
    test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint_id UUID NOT NULL REFERENCES endpoint_configs(endpoint_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    
    -- Test configuration
    test_input TEXT NOT NULL,
    test_variables JSONB DEFAULT '{}'::jsonb,
    
    -- Test results
    status TEXT NOT NULL, -- 'success', 'failed', 'timeout', 'error'
    response_data TEXT,
    response_time_ms INTEGER,
    error_message TEXT,
    
    -- Metadata
    tested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active, expires_at);

CREATE INDEX IF NOT EXISTS idx_api_provider_configs_user_id ON api_provider_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_provider_configs_active ON api_provider_configs(is_active);

CREATE INDEX IF NOT EXISTS idx_endpoint_configs_user_id ON endpoint_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_configs_active ON endpoint_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_endpoint_configs_type ON endpoint_configs(endpoint_type);

CREATE INDEX IF NOT EXISTS idx_endpoint_variables_endpoint_id ON endpoint_variables(endpoint_id);

CREATE INDEX IF NOT EXISTS idx_website_integrations_user_id ON website_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_website_integrations_active ON website_integrations(is_active);

CREATE INDEX IF NOT EXISTS idx_ai_agent_configs_user_id ON ai_agent_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_agent_configs_type ON ai_agent_configs(agent_type);

CREATE INDEX IF NOT EXISTS idx_ai_agent_conversations_agent_id ON ai_agent_conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_ai_agent_conversations_user_id ON ai_agent_conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_endpoint_test_results_endpoint_id ON endpoint_test_results(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_test_results_user_id ON endpoint_test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_test_results_tested_at ON endpoint_test_results(tested_at);

-- Enable Row Level Security
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE endpoint_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE endpoint_variables ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_agent_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE endpoint_test_results ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (users can only access their own data)
CREATE POLICY "Users can access their own sessions" ON user_sessions
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access their own provider configs" ON api_provider_configs
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access their own endpoints" ON endpoint_configs
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access variables for their endpoints" ON endpoint_variables
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM endpoint_configs 
            WHERE endpoint_configs.endpoint_id = endpoint_variables.endpoint_id 
            AND endpoint_configs.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can access their own website integrations" ON website_integrations
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access their own AI agents" ON ai_agent_configs
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access their own AI conversations" ON ai_agent_conversations
    FOR ALL USING (user_id = auth.uid()::text);

CREATE POLICY "Users can access their own test results" ON endpoint_test_results
    FOR ALL USING (user_id = auth.uid()::text);

-- Create functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_provider_configs_updated_at BEFORE UPDATE ON api_provider_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_endpoint_configs_updated_at BEFORE UPDATE ON endpoint_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_website_integrations_updated_at BEFORE UPDATE ON website_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_agent_configs_updated_at BEFORE UPDATE ON ai_agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_agent_conversations_updated_at BEFORE UPDATE ON ai_agent_conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
