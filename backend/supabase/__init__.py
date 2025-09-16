"""
Supabase integration module for OpenAI Codegen Adapter.
Provides database backend for endpoint management, chat history, and website configurations.
"""

from .client import SupabaseManager
from .models import (
    EndpointContext,
    WebsiteConfig,
    ChatSession,
    EndpointVariable,
    BrowserInteraction
)

__all__ = [
    'SupabaseManager',
    'EndpointContext',
    'WebsiteConfig', 
    'ChatSession',
    'EndpointVariable',
    'BrowserInteraction'
]
