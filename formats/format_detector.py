"""
Format Detector - Detects API format from request data and headers
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FormatDetector:
    """Detects the API format of incoming requests."""
    
    def detect_format(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> str:
        """
        Detect the API format from request data and headers.
        
        Returns:
            str: One of 'openai', 'anthropic', 'gemini'
        """
        
        # Check for Anthropic format
        if self._is_anthropic_format(request_data, headers):
            return "anthropic"
        
        # Check for Gemini format
        if self._is_gemini_format(request_data, headers):
            return "gemini"
        
        # Default to OpenAI format
        return "openai"
    
    def _is_anthropic_format(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Check if request is in Anthropic format."""
        
        # Check headers
        if "anthropic-version" in headers:
            return True
        
        # Check request structure
        if "max_tokens" in request_data and "model" in request_data:
            # Anthropic typically has max_tokens as a required field
            if request_data.get("model", "").startswith("claude"):
                return True
        
        return False
    
    def _is_gemini_format(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Check if request is in Gemini format."""
        
        # Check for Gemini-specific fields
        if "contents" in request_data:
            return True
        
        if "generationConfig" in request_data:
            return True
        
        # Check model name
        model = request_data.get("model", "")
        if "gemini" in model.lower():
            return True
        
        return False
