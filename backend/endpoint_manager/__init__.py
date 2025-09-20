"""
Universal AI Endpoint Manager - Enhanced Integration

Trading bot-style endpoint management system integrated into open_codegen.
Manages AI endpoints with individual server control, persistent sessions, and AI-assisted discovery.
"""

from .core.manager import UniversalEndpointManager
from .core.registry import EndpointRegistry
from .models.endpoint import EndpointConfig, EndpointStatus, EndpointType
from .models.session import SessionState, SessionManager
from .schemas.response import StandardResponse, ResponseMetadata

__all__ = [
    "UniversalEndpointManager",
    "EndpointRegistry",
    "EndpointConfig", 
    "EndpointStatus",
    "EndpointType",
    "SessionState",
    "SessionManager",
    "StandardResponse",
    "ResponseMetadata"
]
