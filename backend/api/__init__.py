"""
API routes module for OpenAI Codegen Adapter.
Contains FastAPI routes for Supabase integration and endpoint management.
"""

from .supabase_routes import router as supabase_router
from .websocket_routes import router as websocket_router

__all__ = ['supabase_router', 'websocket_router']
