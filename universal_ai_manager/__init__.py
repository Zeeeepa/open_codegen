"""
Universal AI Endpoint Manager

A comprehensive system for managing AI endpoints with trading bot-style architecture.
Converts web chat interfaces and REST APIs into standardized endpoints with
individual server control, persistent sessions, and AI-assisted discovery.

Based on the cryptocurrency bot architecture pattern but adapted for AI endpoint management.
"""

__version__ = "1.0.0"
__author__ = "Universal AI Manager Team"
__description__ = "Trading bot-style AI endpoint management system"

from .core.endpoint_manager import EndpointManager
from .core.registry import EndpointRegistry
from .models.endpoint import EndpointConfig, EndpointStatus
from .schemas.response import StandardResponse

__all__ = [
    "EndpointManager",
    "EndpointRegistry", 
    "EndpointConfig",
    "EndpointStatus",
    "StandardResponse"
]
