-- OpenAI Codegen Adapter - Supabase Database Schema
-- This file contains the complete database schema for the enhanced adapter
-- Run this in your Supabase SQL Editor to create all required tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Website Configurations Table
-- Stores configuration for custom websites that can be interacted with via browser automation
CREATE TABLE IF NOT EXISTS codegen_adapter_website_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    authentication_required BOOLEAN DEFAULT FALSE,
    authentication_method TEXT, -- 'login_form', 'api_key', 'oauth', etc.
    authentication_config JSONB DEFAULT '{}', -- Stores auth-specific configuration
    headers JSONB DEFAULT '{}', -- Custom headers to send with requests
    cookies JSONB DEFAULT '{}', -- Cookies to set for the session
    user_agent TEXT,
    timeout INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    wait_for_load FLOAT DEFAULT 2.0,
    screenshot_on_error BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Endpoints Table
-- Main table for storing endpoint configurations (API endpoints and website chat interfaces)
CREATE TABLE IF NOT EXISTS codegen_adapter_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    endpoint_type TEXT NOT NULL CHECK (endpoint_type IN ('openai_api', 'anthropic_api', 'gemini_api', 'codegen_api', 'zai_webchat', 'custom_website')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error', 'testing')),
    
    -- API endpoint details
    url TEXT,
    model_name TEXT,
    api_key TEXT, -- Should be encrypted in production
    
    -- Website interaction details
    website_config_id UUID REFERENCES codegen_adapter_website_configs(id),
    text_input_selector TEXT, -- CSS selector for text input field
    send_button_selector TEXT, -- CSS selector for send button
    response_selector TEXT, -- CSS selector for response area
    
    -- Configuration
    request_template TEXT, -- Template for formatting requests
    response_parser TEXT, -- Configuration for parsing responses
    custom_headers JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    
    -- Metadata
    description TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_by TEXT,
    last_tested TIMESTAMP WITH TIME ZONE,
    test_results JSONB,
    usage_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Endpoint Variables Table
-- Stores variables that can be used with endpoints (API keys, parameters, etc.)
CREATE TABLE IF NOT EXISTS codegen_adapter_endpoint_variables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID NOT NULL REFERENCES codegen_adapter_endpoints(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    variable_type TEXT NOT NULL CHECK (variable_type IN ('string', 'integer', 'float', 'boolean', 'json', 'list')),
    value JSONB NOT NULL,
    default_value JSONB,
    description TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    is_sensitive BOOLEAN DEFAULT FALSE, -- For passwords, API keys, etc.
    validation_pattern TEXT, -- Regex pattern for validation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(endpoint_id, name)
);

-- Browser Interactions Table
-- Stores detailed browser interaction instructions for website automation
CREATE TABLE IF NOT EXISTS codegen_adapter_browser_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID NOT NULL REFERENCES codegen_adapter_endpoints(id) ON DELETE CASCADE,
    element_type TEXT NOT NULL CHECK (element_type IN ('text_input', 'textarea', 'send_button', 'response_container', 'login_form', 'chat_container')),
    selector TEXT NOT NULL, -- CSS selector for the element
    xpath TEXT, -- XPath selector as fallback
    element_text TEXT, -- Text content of the element
    attributes JSONB DEFAULT '{}', -- Element attributes
    interaction_method TEXT NOT NULL, -- 'click', 'type', 'wait', etc.
    wait_condition TEXT, -- Condition to wait for after interaction
    fallback_selectors TEXT[] DEFAULT ARRAY[]::TEXT[], -- Alternative selectors
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Sessions Table
-- Manages chat sessions and their state
CREATE TABLE IF NOT EXISTS codegen_adapter_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    session_name TEXT,
    endpoint_id UUID REFERENCES codegen_adapter_endpoints(id),
    provider TEXT, -- Current AI provider being used
    context JSONB DEFAULT '{}', -- Session context and variables
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}', -- Session-specific settings
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Messages Table
-- Stores individual chat messages
CREATE TABLE IF NOT EXISTS codegen_adapter_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES codegen_adapter_chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'tool_call', 'tool_result', 'image', 'file')),
    endpoint_id UUID REFERENCES codegen_adapter_endpoints(id),
    provider TEXT,
    model TEXT,
    tokens_used INTEGER,
    response_time FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Endpoint Tests Table
-- Stores results of endpoint testing
CREATE TABLE IF NOT EXISTS codegen_adapter_endpoint_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID NOT NULL REFERENCES codegen_adapter_endpoints(id) ON DELETE CASCADE,
    test_type TEXT NOT NULL CHECK (test_type IN ('connectivity', 'functionality', 'performance')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failure', 'warning')),
    request_data JSONB,
    response_data JSONB,
    response_time FLOAT,
    error_message TEXT,
    test_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_endpoints_type ON codegen_adapter_endpoints(endpoint_type);
CREATE INDEX IF NOT EXISTS idx_endpoints_status ON codegen_adapter_endpoints(status);
CREATE INDEX IF NOT EXISTS idx_endpoints_created_by ON codegen_adapter_endpoints(created_by);
CREATE INDEX IF NOT EXISTS idx_endpoints_last_tested ON codegen_adapter_endpoints(last_tested);

CREATE INDEX IF NOT EXISTS idx_endpoint_variables_endpoint_id ON codegen_adapter_endpoint_variables(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_variables_name ON codegen_adapter_endpoint_variables(name);
CREATE INDEX IF NOT EXISTS idx_endpoint_variables_type ON codegen_adapter_endpoint_variables(variable_type);

CREATE INDEX IF NOT EXISTS idx_browser_interactions_endpoint_id ON codegen_adapter_browser_interactions(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_browser_interactions_element_type ON codegen_adapter_browser_interactions(element_type);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON codegen_adapter_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_endpoint_id ON codegen_adapter_chat_sessions(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON codegen_adapter_chat_sessions(last_activity);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON codegen_adapter_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON codegen_adapter_chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON codegen_adapter_chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_endpoint_id ON codegen_adapter_chat_messages(endpoint_id);

CREATE INDEX IF NOT EXISTS idx_endpoint_tests_endpoint_id ON codegen_adapter_endpoint_tests(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_endpoint_tests_status ON codegen_adapter_endpoint_tests(status);
CREATE INDEX IF NOT EXISTS idx_endpoint_tests_created_at ON codegen_adapter_endpoint_tests(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at columns
CREATE TRIGGER update_website_configs_updated_at BEFORE UPDATE ON codegen_adapter_website_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoints_updated_at BEFORE UPDATE ON codegen_adapter_endpoints FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_variables_updated_at BEFORE UPDATE ON codegen_adapter_endpoint_variables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_browser_interactions_updated_at BEFORE UPDATE ON codegen_adapter_browser_interactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON codegen_adapter_chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
-- Uncomment the following lines if you want sample data

/*
-- Sample website configuration
INSERT INTO codegen_adapter_website_configs (name, url, description) VALUES 
('ChatGPT Web', 'https://chat.openai.com', 'OpenAI ChatGPT web interface');

-- Sample endpoints
INSERT INTO codegen_adapter_endpoints (name, endpoint_type, url, model_name, description) VALUES 
('OpenAI GPT-4', 'openai_api', 'https://api.openai.com/v1/chat/completions', 'gpt-4', 'OpenAI GPT-4 API endpoint'),
('Anthropic Claude', 'anthropic_api', 'https://api.anthropic.com/v1/messages', 'claude-3-sonnet-20240229', 'Anthropic Claude API endpoint'),
('Google Gemini', 'gemini_api', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent', 'gemini-pro', 'Google Gemini API endpoint');

-- Sample chat session
INSERT INTO codegen_adapter_chat_sessions (user_id, session_name, provider) VALUES 
('user123', 'Test Session', 'openai');
*/

-- Create RLS (Row Level Security) policies if needed
-- Uncomment and modify these if you need user-specific access control

/*
-- Enable RLS on tables
ALTER TABLE codegen_adapter_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE codegen_adapter_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE codegen_adapter_chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies (example - modify based on your auth requirements)
CREATE POLICY "Users can view their own endpoints" ON codegen_adapter_endpoints
    FOR SELECT USING (created_by = auth.uid()::text);

CREATE POLICY "Users can create endpoints" ON codegen_adapter_endpoints
    FOR INSERT WITH CHECK (created_by = auth.uid()::text);

CREATE POLICY "Users can update their own endpoints" ON codegen_adapter_endpoints
    FOR UPDATE USING (created_by = auth.uid()::text);

CREATE POLICY "Users can delete their own endpoints" ON codegen_adapter_endpoints
    FOR DELETE USING (created_by = auth.uid()::text);
*/
