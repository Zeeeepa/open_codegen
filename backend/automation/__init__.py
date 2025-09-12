"""
Web Automation Framework for Open Codegen
Provides browser automation capabilities with stealth techniques
"""

from .browser_manager import BrowserManager
from .stealth_browser import StealthBrowser
from .web_provider_base import WebProviderBase

__all__ = [
    'BrowserManager',
    'StealthBrowser', 
    'WebProviderBase'
]
