"""
Core components for the AI Endpoint Orchestrator.

This module contains the fundamental components for endpoint management,
including the registry, status tracking, health monitoring, and load balancing.
"""

from .endpoint_status import EndpointStatus, HealthStatus

# Only import what exists for now
try:
    from .endpoint_registry import EndpointRegistry
    _has_registry = True
except ImportError:
    _has_registry = False

__all__ = [
    "EndpointStatus",
    "HealthStatus"
]

if _has_registry:
    __all__.append("EndpointRegistry")
