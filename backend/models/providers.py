"""
Provider models for the Universal AI Endpoint Management System
"""

import enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Enum, Integer, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel

class ProviderType(enum.Enum):
    """Types of AI providers supported"""
    REST_API = "rest_api"
    WEB_CHAT = "web_chat"
    API_TOKEN = "api_token"  # Updated from hybrid as requested
    ZAI_SDK = "zai_sdk"  # Z.ai Python SDK integration

class EndpointProvider(BaseModel):
    """Provider configuration for different AI services"""
    __tablename__ = 'endpoint_providers'
    
    name = Column(String(200), nullable=False, unique=True)
    provider_type = Column(Enum(ProviderType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration for different provider types
    base_url = Column(String(500), nullable=True)
    api_key = Column(String(1000), nullable=True)  # Encrypted in production
    
    # Web chat specific fields
    login_url = Column(String(500), nullable=True)
    username = Column(String(200), nullable=True)
    password = Column(String(500), nullable=True)  # Encrypted in production
    
    # Browser automation settings
    browser_config = Column(JSON, default=dict, nullable=True)
    
    # Rate limiting and performance settings
    max_requests_per_minute = Column(Integer, default=60, nullable=False)
    max_concurrent_requests = Column(Integer, default=5, nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    
    # Health monitoring
    is_healthy = Column(Boolean, default=True, nullable=False)
    last_health_check = Column(String(50), nullable=True)
    health_check_interval = Column(Integer, default=300, nullable=False)  # 5 minutes
    
    # Model mapping for this provider
    model_mapping = Column(JSON, default=dict, nullable=True)
    
    # Default settings
    is_default = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    
    # Relationships
    instances = relationship("EndpointInstance", back_populates="provider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EndpointProvider(name='{self.name}', type='{self.provider_type.value}')>"

class EndpointInstance(BaseModel):
    """Individual server instances for each provider"""
    __tablename__ = 'endpoint_instances'
    
    provider_id = Column(UUID(as_uuid=True), ForeignKey('endpoint_providers.id'), nullable=False)
    instance_name = Column(String(200), nullable=False)  # e.g., webdeepseek1, webdeepseek8
    
    # Instance status
    status = Column(String(50), default='stopped', nullable=False)  # stopped, starting, running, error
    port = Column(Integer, nullable=True)
    process_id = Column(Integer, nullable=True)
    
    # Session management
    session_data = Column(JSON, default=dict, nullable=True)
    cookies = Column(JSON, default=dict, nullable=True)
    fingerprint = Column(JSON, default=dict, nullable=True)
    
    # Performance metrics
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    average_response_time = Column(Integer, default=0, nullable=False)  # milliseconds
    
    # Resource usage
    cpu_usage = Column(Integer, default=0, nullable=False)  # percentage
    memory_usage = Column(Integer, default=0, nullable=False)  # MB
    
    # Configuration overrides for this instance
    config_overrides = Column(JSON, default=dict, nullable=True)
    
    # Relationships
    provider = relationship("EndpointProvider", back_populates="instances")
    
    def __repr__(self):
        return f"<EndpointInstance(name='{self.instance_name}', status='{self.status}')>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def is_running(self) -> bool:
        """Check if instance is currently running"""
        return self.status == 'running'
