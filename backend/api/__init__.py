"""
API routes for the Universal AI Endpoint Management System
"""

from .endpoints import router as endpoints_router
from .chat import router as chat_router

__all__ = ['endpoints_router', 'chat_router']
