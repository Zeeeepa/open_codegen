"""
Database models for Open Codegen using Pydantic v2.

All models mirror the database schema exactly for consistency.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class UserSession(BaseModel):
    """User session model."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID = Field(default_factory=uuid4)
    user_id: str
    email: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class APIProviderConfig(BaseModel):
    """API provider configuration model."""

    model_config = ConfigDict(from_attributes=True)

    provider_id: UUID = Field(default_factory=uuid4)
    user_id: str
    provider_name: str  # 'openai', 'anthropic', 'gemini', 'codegen', 'z.ai', 'custom'
    provider_type: str  # 'api', 'website'
    base_url: str | None = None
    api_key: str | None = None  # Will be encrypted
    model_mappings: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EndpointVariable(BaseModel):
    """Endpoint variable model."""

    model_config = ConfigDict(from_attributes=True)

    variable_id: UUID = Field(default_factory=uuid4)
    endpoint_id: UUID
    name: str
    variable_type: str  # 'string', 'number', 'boolean', 'json', 'secret'
    default_value: str | None = None
    description: str | None = None
    is_required: bool = False
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EndpointConfig(BaseModel):
    """Endpoint configuration model."""

    model_config = ConfigDict(from_attributes=True)

    endpoint_id: UUID = Field(default_factory=uuid4)
    user_id: str
    name: str
    description: str | None = None
    endpoint_type: str  # 'api', 'website'
    provider_id: UUID | None = None

    # API endpoint fields
    url: str | None = None
    method: str = "POST"
    headers: dict[str, Any] = Field(default_factory=dict)

    # Website endpoint fields
    website_url: str | None = None
    input_selector: str | None = None  # CSS/XPath selector for input field
    send_button_selector: str | None = None  # CSS/XPath selector for send button
    response_selector: str | None = None  # CSS/XPath selector for response
    wait_for_response_ms: int = 5000

    # Common fields
    variables: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebsiteIntegration(BaseModel):
    """Website integration configuration model."""

    model_config = ConfigDict(from_attributes=True)

    integration_id: UUID = Field(default_factory=uuid4)
    user_id: str
    name: str
    website_url: str

    # Selectors for different elements
    selectors: dict[str, str] = Field(default_factory=lambda: {
        "input": "",
        "send_button": "",
        "response": "",
        "error": "",
        "loading": ""
    })

    # Browser configuration
    browser_config: dict[str, Any] = Field(default_factory=lambda: {
        "headless": True,
        "timeout": 30000,
        "wait_for_response": 5000,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    # Authentication if needed
    auth_config: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True
    last_tested_at: datetime | None = None
    test_status: str | None = None  # 'success', 'failed', 'pending'
    test_error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIAgentConfig(BaseModel):
    """AI agent configuration model."""

    model_config = ConfigDict(from_attributes=True)

    agent_id: UUID = Field(default_factory=uuid4)
    user_id: str
    name: str
    agent_type: str  # 'endpoint_creator', 'endpoint_tester', 'debugger'

    # Agent configuration
    config: dict[str, Any] = Field(default_factory=lambda: {
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": ""
    })

    # Capabilities
    capabilities: list[str] = Field(default_factory=list)

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIAgentConversation(BaseModel):
    """AI agent conversation model."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    user_id: str
    title: str | None = None

    # Conversation state
    messages: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EndpointTestResult(BaseModel):
    """Endpoint test result model."""

    model_config = ConfigDict(from_attributes=True)

    test_id: UUID = Field(default_factory=uuid4)
    endpoint_id: UUID
    user_id: str

    # Test configuration
    test_input: str
    test_variables: dict[str, Any] = Field(default_factory=dict)

    # Test results
    status: str  # 'success', 'failed', 'timeout', 'error'
    response_data: str | None = None
    response_time_ms: int | None = None
    error_message: str | None = None

    # Metadata
    tested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Create/Update models (for API requests)
class UserSessionCreate(BaseModel):
    """Model for creating user sessions."""

    user_id: str
    email: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class APIProviderConfigCreate(BaseModel):
    """Model for creating API provider configurations."""

    provider_name: str
    provider_type: str
    base_url: str | None = None
    api_key: str | None = None
    model_mappings: dict[str, Any] = Field(default_factory=dict)


class EndpointConfigCreate(BaseModel):
    """Model for creating endpoint configurations."""

    name: str
    description: str | None = None
    endpoint_type: str
    provider_id: UUID | None = None

    # API endpoint fields
    url: str | None = None
    method: str = "POST"
    headers: dict[str, Any] = Field(default_factory=dict)

    # Website endpoint fields
    website_url: str | None = None
    input_selector: str | None = None
    send_button_selector: str | None = None
    response_selector: str | None = None
    wait_for_response_ms: int = 5000

    variables: list[dict[str, Any]] = Field(default_factory=list)


class WebsiteIntegrationCreate(BaseModel):
    """Model for creating website integrations."""

    name: str
    website_url: str
    selectors: dict[str, str]
    browser_config: dict[str, Any] = Field(default_factory=lambda: {
        "headless": True,
        "timeout": 30000,
        "wait_for_response": 5000,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    auth_config: dict[str, Any] = Field(default_factory=dict)


class AIAgentConfigCreate(BaseModel):
    """Model for creating AI agent configurations."""

    name: str
    agent_type: str
    config: dict[str, Any] = Field(default_factory=lambda: {
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": ""
    })
    capabilities: list[str] = Field(default_factory=list)
