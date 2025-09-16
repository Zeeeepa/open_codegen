"""
Z.ai specific exceptions for error handling.
Following KISS principle with clear, specific exception types.
"""

from typing import Optional, Dict, Any


class ZaiError(Exception):
    """Base exception for Z.ai related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ZaiAuthenticationError(ZaiError):
    """Raised when Z.ai authentication fails."""
    
    def __init__(self, message: str = "Z.ai authentication failed"):
        super().__init__(message, status_code=401)


class ZaiRateLimitError(ZaiError):
    """Raised when Z.ai rate limit is exceeded."""
    
    def __init__(self, message: str = "Z.ai rate limit exceeded"):
        super().__init__(message, status_code=429)


class ZaiModelNotFoundError(ZaiError):
    """Raised when requested Z.ai model is not available."""
    
    def __init__(self, model: str):
        message = f"Z.ai model '{model}' not found or not available"
        super().__init__(message, status_code=404)


class ZaiValidationError(ZaiError):
    """Raised when request validation fails for Z.ai API."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        super().__init__(message, status_code=400)


class ZaiConnectionError(ZaiError):
    """Raised when connection to Z.ai API fails."""
    
    def __init__(self, message: str = "Failed to connect to Z.ai API"):
        super().__init__(message, status_code=503)


class ZaiTimeoutError(ZaiError):
    """Raised when Z.ai API request times out."""
    
    def __init__(self, message: str = "Z.ai API request timed out"):
        super().__init__(message, status_code=504)


class ZaiStreamingError(ZaiError):
    """Raised when Z.ai streaming response fails."""
    
    def __init__(self, message: str = "Z.ai streaming response failed"):
        super().__init__(message, status_code=500)
