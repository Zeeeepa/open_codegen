"""
Pydantic models for Supabase database entities.
Defines data structures for endpoint contexts, website configurations, and chat sessions.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class EndpointType(str, Enum):
    """Types of endpoints supported by the system."""
    OPENAI_API = "openai_api"
    ANTHROPIC_API = "anthropic_api"
    GEMINI_API = "gemini_api"
    CODEGEN_API = "codegen_api"
    ZAI_WEBCHAT = "zai_webchat"
    CUSTOM_WEBSITE = "custom_website"


class InteractionElementType(str, Enum):
    """Types of interaction elements on websites."""
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea"
    SEND_BUTTON = "send_button"
    RESPONSE_CONTAINER = "response_container"
    LOGIN_FORM = "login_form"
    CHAT_CONTAINER = "chat_container"


class VariableType(str, Enum):
    """Types of variables that can be stored."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"


class EndpointStatus(str, Enum):
    """Status of endpoints."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class BrowserInteraction(BaseModel):
    """Model for browser interaction context."""
    id: Optional[str] = None
    endpoint_id: str
    element_type: InteractionElementType
    selector: str = Field(..., description="CSS selector for the element")
    xpath: Optional[str] = Field(None, description="XPath selector as fallback")
    element_text: Optional[str] = Field(None, description="Text content of the element")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Element attributes")
    interaction_method: str = Field(..., description="Method to interact (click, type, etc.)")
    wait_condition: Optional[str] = Field(None, description="Condition to wait for after interaction")
    fallback_selectors: List[str] = Field(default_factory=list, description="Alternative selectors")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EndpointVariable(BaseModel):
    """Model for endpoint variables."""
    id: Optional[str] = None
    endpoint_id: str
    name: str = Field(..., description="Variable name")
    variable_type: VariableType
    value: Union[str, int, float, bool, Dict, List] = Field(..., description="Variable value")
    default_value: Optional[Union[str, int, float, bool, Dict, List]] = None
    description: Optional[str] = None
    is_required: bool = False
    is_sensitive: bool = False  # For passwords, API keys, etc.
    validation_pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('value', 'default_value')
    def validate_value_type(cls, v, values):
        """Validate that value matches the specified type."""
        if v is None:
            return v
        
        var_type = values.get('variable_type')
        if var_type == VariableType.STRING and not isinstance(v, str):
            raise ValueError("Value must be a string")
        elif var_type == VariableType.INTEGER and not isinstance(v, int):
            raise ValueError("Value must be an integer")
        elif var_type == VariableType.FLOAT and not isinstance(v, (int, float)):
            raise ValueError("Value must be a float")
        elif var_type == VariableType.BOOLEAN and not isinstance(v, bool):
            raise ValueError("Value must be a boolean")
        elif var_type == VariableType.JSON and not isinstance(v, dict):
            raise ValueError("Value must be a JSON object")
        elif var_type == VariableType.LIST and not isinstance(v, list):
            raise ValueError("Value must be a list")
        
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebsiteConfig(BaseModel):
    """Model for website configuration."""
    id: Optional[str] = None
    name: str = Field(..., description="Human-readable name for the website")
    url: str = Field(..., description="Base URL of the website")
    description: Optional[str] = None
    authentication_required: bool = False
    authentication_method: Optional[str] = Field(None, description="login_form, api_key, oauth, etc.")
    authentication_config: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers to send")
    cookies: Dict[str, str] = Field(default_factory=dict, description="Cookies to set")
    user_agent: Optional[str] = None
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    wait_for_load: float = Field(2.0, description="Seconds to wait for page load")
    screenshot_on_error: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EndpointContext(BaseModel):
    """Model for endpoint context storage."""
    id: Optional[str] = None
    name: str = Field(..., description="Human-readable name for the endpoint")
    endpoint_type: EndpointType
    status: EndpointStatus = EndpointStatus.ACTIVE
    
    # API endpoint details
    url: Optional[str] = Field(None, description="API endpoint URL")
    model_name: Optional[str] = Field(None, description="Model name to use")
    api_key: Optional[str] = Field(None, description="API key (encrypted)")
    
    # Website interaction details
    website_config_id: Optional[str] = Field(None, description="Reference to WebsiteConfig")
    text_input_selector: Optional[str] = Field(None, description="CSS selector for text input")
    send_button_selector: Optional[str] = Field(None, description="CSS selector for send button")
    response_selector: Optional[str] = Field(None, description="CSS selector for response area")
    
    # Configuration
    request_template: Optional[str] = Field(None, description="Template for request formatting")
    response_parser: Optional[str] = Field(None, description="Parser configuration for responses")
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    last_tested: Optional[datetime] = None
    test_results: Optional[Dict[str, Any]] = None
    usage_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """Model for chat session management."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    endpoint_id: Optional[str] = Field(None, description="Current active endpoint")
    provider: Optional[str] = Field(None, description="Current AI provider")
    
    # Session state
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context and variables")
    message_count: int = 0
    total_tokens: int = 0
    
    # Configuration
    settings: Dict[str, Any] = Field(default_factory=dict, description="Session-specific settings")
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatMessage(BaseModel):
    """Model for individual chat messages."""
    id: Optional[str] = None
    session_id: str
    role: str = Field(..., description="user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    message_type: str = Field("text", description="text, tool_call, tool_result, etc.")
    
    # Metadata
    endpoint_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EndpointTest(BaseModel):
    """Model for endpoint testing results."""
    id: Optional[str] = None
    endpoint_id: str
    test_type: str = Field(..., description="connectivity, functionality, performance")
    status: str = Field(..., description="success, failure, warning")
    
    # Test details
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Test configuration
    test_config: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response models for API endpoints

class CreateEndpointRequest(BaseModel):
    """Request model for creating endpoints."""
    name: str
    endpoint_type: EndpointType
    url: Optional[str] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    website_config: Optional[WebsiteConfig] = None
    variables: List[EndpointVariable] = Field(default_factory=list)
    browser_interactions: List[BrowserInteraction] = Field(default_factory=list)


class UpdateEndpointRequest(BaseModel):
    """Request model for updating endpoints."""
    name: Optional[str] = None
    status: Optional[EndpointStatus] = None
    url: Optional[str] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class TestEndpointRequest(BaseModel):
    """Request model for testing endpoints."""
    test_message: str = "Hello, this is a test message."
    test_type: str = "functionality"
    timeout: int = 30


class SupabaseConnectionConfig(BaseModel):
    """Model for Supabase connection configuration."""
    url: str = Field(..., description="Supabase project URL")
    key: str = Field(..., description="Supabase anon/service key")
    table_prefix: str = Field("codegen_adapter", description="Prefix for table names")
    auto_create_tables: bool = Field(True, description="Automatically create tables if they don't exist")
    
    class Config:
        # Don't include sensitive fields in serialization by default
        fields = {
            'key': {'write_only': True}
        }


class SupabaseConnectionTest(BaseModel):
    """Model for Supabase connection test results."""
    success: bool
    message: str
    connection_time: Optional[float] = None
    tables_found: List[str] = Field(default_factory=list)
    tables_created: List[str] = Field(default_factory=list)
    error_details: Optional[str] = None
