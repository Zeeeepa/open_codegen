"""
Endpoint models for the Universal AI Endpoint Management System
"""

import enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Enum, Integer, ForeignKey, Text, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel

class EndpointStatus(enum.Enum):
    """Status of an endpoint"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class Endpoint(BaseModel):
    """Main endpoint configuration"""
    __tablename__ = 'endpoints'
    
    name = Column(String(200), nullable=False, unique=True)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Provider reference
    provider_id = Column(UUID(as_uuid=True), ForeignKey('endpoint_providers.id'), nullable=False)
    
    # Endpoint configuration
    endpoint_url = Column(String(500), nullable=False)
    model_name = Column(String(200), nullable=False)  # e.g., webdeepseek1, gpt-4, etc.
    
    # Status and health
    status = Column(Enum(EndpointStatus), default=EndpointStatus.INACTIVE, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Performance settings
    priority = Column(Integer, default=100, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)  # For load balancing
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_hour = Column(Integer, default=1000, nullable=False)
    
    # Cost tracking
    cost_per_request = Column(Float, default=0.0, nullable=False)
    cost_per_token = Column(Float, default=0.0, nullable=False)
    
    # Configuration
    configuration = relationship("EndpointConfiguration", back_populates="endpoint", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("EndpointSession", back_populates="endpoint", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Endpoint(name='{self.name}', model='{self.model_name}', status='{self.status.value}')>"

class EndpointConfiguration(BaseModel):
    """Detailed configuration for an endpoint"""
    __tablename__ = 'endpoint_configurations'
    
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey('endpoints.id'), nullable=False, unique=True)
    
    # Model parameters
    max_tokens = Column(Integer, default=2048, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=1.0, nullable=False)
    frequency_penalty = Column(Float, default=0.0, nullable=False)
    presence_penalty = Column(Float, default=0.0, nullable=False)
    
    # System prompts and templates
    system_prompt = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=True)
    response_template = Column(Text, nullable=True)
    
    # Web chat specific configuration
    web_chat_config = Column(JSON, default=dict, nullable=True)
    
    # Custom headers and parameters
    custom_headers = Column(JSON, default=dict, nullable=True)
    custom_parameters = Column(JSON, default=dict, nullable=True)
    
    # Timeout and retry settings
    request_timeout = Column(Integer, default=30, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=1, nullable=False)
    
    # Response processing
    response_filters = Column(JSON, default=list, nullable=True)
    response_transformers = Column(JSON, default=list, nullable=True)
    
    # Validation rules
    input_validation = Column(JSON, default=dict, nullable=True)
    output_validation = Column(JSON, default=dict, nullable=True)
    
    # Relationships
    endpoint = relationship("Endpoint", back_populates="configuration")
    
    def __repr__(self):
        return f"<EndpointConfiguration(endpoint_id='{self.endpoint_id}')>"

class EndpointSession(BaseModel):
    """Session management for endpoints"""
    __tablename__ = 'endpoint_sessions'
    
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey('endpoints.id'), nullable=False)
    session_id = Column(String(200), nullable=False)
    
    # Session data
    session_data = Column(JSON, default=dict, nullable=True)
    conversation_history = Column(JSON, default=list, nullable=True)
    
    # Browser session data (for web chat endpoints)
    cookies = Column(JSON, default=dict, nullable=True)
    local_storage = Column(JSON, default=dict, nullable=True)
    session_storage = Column(JSON, default=dict, nullable=True)
    
    # Authentication data
    auth_tokens = Column(JSON, default=dict, nullable=True)
    csrf_tokens = Column(JSON, default=dict, nullable=True)
    
    # Session metadata
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    fingerprint = Column(JSON, default=dict, nullable=True)
    
    # Session state
    is_authenticated = Column(Boolean, default=False, nullable=False)
    last_activity = Column(String(50), nullable=True)
    expires_at = Column(String(50), nullable=True)
    
    # Performance tracking
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    
    # Relationships
    endpoint = relationship("Endpoint", back_populates="sessions")
    
    def __repr__(self):
        return f"<EndpointSession(session_id='{self.session_id}', endpoint_id='{self.endpoint_id}')>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
