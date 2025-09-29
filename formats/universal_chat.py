"""
Universal Chat Format - Common format for all providers
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class UniversalChatFormat:
    """Universal chat format for internal processing."""
    
    @staticmethod
    def create_simple_request(message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a simple WebChat request."""
        return {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "format": "webchat"
        }
    
    @staticmethod
    def create_response(content: str, provider: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a WebChat response."""
        return {
            "success": True,
            "content": content,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "streaming": False
        }
    
    @staticmethod
    def create_error_response(error: str, provider: str) -> Dict[str, Any]:
        """Create a WebChat error response."""
        return {
            "success": False,
            "error": error,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "content": f"Error: {error}",
            "metadata": {"error_type": "processing_error"}
        }
