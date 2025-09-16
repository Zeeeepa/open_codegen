"""
Standardized response schemas for Universal AI Endpoint Manager

Defines the universal response format that all endpoints return,
regardless of their source type (web chat or REST API).
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class ResponseMetadata:
    """Metadata for AI responses"""
    provider: str = ""
    model: str = ""
    endpoint_id: str = ""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "endpoint_id": self.endpoint_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "response_time": self.response_time
        }

@dataclass
class ResponseUsage:
    """Usage statistics for AI responses"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost
        }

@dataclass
class ResponseContent:
    """Content of AI responses"""
    content: str = ""
    type: str = "text"
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "type": self.type,
            "additional_data": self.additional_data
        }

@dataclass
class SessionInfo:
    """Session information for persistent conversations"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    persistent: bool = True
    conversation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "persistent": self.persistent,
            "conversation_id": self.conversation_id
        }

@dataclass
class StandardResponse:
    """
    Universal response format for all AI endpoints
    
    This standardized format ensures consistency across all providers,
    whether they're REST APIs or web chat interfaces.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    response: ResponseContent = field(default_factory=ResponseContent)
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
    usage: Optional[ResponseUsage] = None
    session: Optional[SessionInfo] = None
    error: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "response": self.response.to_dict(),
            "metadata": self.metadata.to_dict(),
            "success": self.success
        }
        
        if self.usage:
            result["usage"] = self.usage.to_dict()
        
        if self.session:
            result["session"] = self.session.to_dict()
        
        if self.error:
            result["error"] = self.error
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardResponse':
        """Create StandardResponse from dictionary"""
        response_content = ResponseContent(**data.get("response", {}))
        metadata = ResponseMetadata(**data.get("metadata", {}))
        
        usage = None
        if data.get("usage"):
            usage = ResponseUsage(**data["usage"])
        
        session = None
        if data.get("session"):
            session = SessionInfo(**data["session"])
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            response=response_content,
            metadata=metadata,
            usage=usage,
            session=session,
            error=data.get("error"),
            success=data.get("success", True)
        )
    
    @classmethod
    def create_error_response(cls, error_message: str, endpoint_id: str = "", provider: str = "") -> 'StandardResponse':
        """Create an error response"""
        metadata = ResponseMetadata(
            provider=provider,
            endpoint_id=endpoint_id
        )
        
        return cls(
            response=ResponseContent(content="", type="error"),
            metadata=metadata,
            error=error_message,
            success=False
        )
    
    @classmethod
    def create_success_response(
        cls, 
        content: str, 
        provider: str, 
        model: str, 
        endpoint_id: str,
        response_time: float = 0.0,
        usage: Optional[ResponseUsage] = None,
        session: Optional[SessionInfo] = None
    ) -> 'StandardResponse':
        """Create a successful response"""
        response_content = ResponseContent(content=content, type="text")
        metadata = ResponseMetadata(
            provider=provider,
            model=model,
            endpoint_id=endpoint_id,
            response_time=response_time
        )
        
        return cls(
            response=response_content,
            metadata=metadata,
            usage=usage,
            session=session,
            success=True
        )
