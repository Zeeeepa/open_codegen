"""
AI Endpoint Orchestrator
A comprehensive system for managing AI endpoints with trading bot-style controls.

Converts web chat interfaces and REST APIs into standardized, manageable endpoints
with persistent sessions, auto-scaling, and AI-assisted configuration.
"""

__version__ = "1.0.0"
__author__ = "Zeeeepa"
__description__ = "Universal AI Endpoint Management System"

from .core.endpoint_status import EndpointStatus, HealthStatus
from .config_manager.yaml_schema import EndpointConfig, YAMLConfigManager

# Only import what exists for now
try:
    from .core.endpoint_registry import EndpointRegistry
    _has_registry = True
except ImportError:
    _has_registry = False

__all__ = [
    "EndpointStatus", 
    "HealthStatus",
    "EndpointConfig",
    "YAMLConfigManager"
]

if _has_registry:
    __all__.append("EndpointRegistry")
