"""
Universal adapter system for the AI Endpoint Management System
"""

from .base_adapter import BaseAdapter, AdapterResponse, AdapterError
from .rest_api_adapter import RestApiAdapter
from .web_chat_adapter import WebChatAdapter

__all__ = [
    'BaseAdapter',
    'AdapterResponse', 
    'AdapterError',
    'RestApiAdapter',
    'WebChatAdapter'
]
