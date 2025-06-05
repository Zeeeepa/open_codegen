"""
Enhanced error handling and custom exceptions for the OpenAI Codegen Adapter.
Provides consistent error responses across all API endpoints.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class CodegenAdapterError(Exception):
    """Base exception for Codegen Adapter errors."""
    
    def __init__(self, message: str, error_code: str = "ADAPTER_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class CodegenClientError(CodegenAdapterError):
    """Error communicating with Codegen API."""
    
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, "CODEGEN_CLIENT_ERROR", status_code)


class RequestValidationError(CodegenAdapterError):
    """Error validating incoming requests."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, "REQUEST_VALIDATION_ERROR", status_code)


class ResponseTransformationError(CodegenAdapterError):
    """Error transforming responses between API formats."""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, "RESPONSE_TRANSFORMATION_ERROR", status_code)


def create_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    api_format: str = "openai"
) -> Dict[str, Any]:
    """
    Create a standardized error response for different API formats.
    
    Args:
        error: The exception that occurred
        request_id: Optional request ID for tracking
        api_format: API format (openai, anthropic, gemini)
        
    Returns:
        Dict containing formatted error response
    """
    if isinstance(error, CodegenAdapterError):
        error_message = error.message
        error_code = error.error_code
        status_code = error.status_code
    else:
        error_message = str(error)
        error_code = "INTERNAL_ERROR"
        status_code = 500
    
    # Log the error
    logger.error(f"🚨 Error occurred: {error_code} - {error_message}")
    if status_code >= 500:
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
    
    # Format error response based on API type
    if api_format == "openai":
        return {
            "error": {
                "message": error_message,
                "type": error_code.lower(),
                "code": str(status_code)
            }
        }
    elif api_format == "anthropic":
        return {
            "type": "error",
            "error": {
                "type": error_code.lower(),
                "message": error_message
            }
        }
    elif api_format == "gemini":
        return {
            "error": {
                "code": status_code,
                "message": error_message,
                "status": error_code
            }
        }
    else:
        # Default format
        return {
            "error": {
                "message": error_message,
                "code": error_code,
                "status_code": status_code
            }
        }


def handle_codegen_client_error(error: Exception) -> CodegenClientError:
    """
    Handle errors from the Codegen client and convert to appropriate exception.
    
    Args:
        error: Original exception from Codegen client
        
    Returns:
        CodegenClientError with appropriate message and status code
    """
    error_message = str(error)
    
    # Check for common error patterns
    if "timeout" in error_message.lower():
        return CodegenClientError("Request to Codegen API timed out", 504)
    elif "connection" in error_message.lower():
        return CodegenClientError("Failed to connect to Codegen API", 502)
    elif "unauthorized" in error_message.lower() or "401" in error_message:
        return CodegenClientError("Invalid Codegen API credentials", 401)
    elif "rate limit" in error_message.lower() or "429" in error_message:
        return CodegenClientError("Codegen API rate limit exceeded", 429)
    else:
        return CodegenClientError(f"Codegen API error: {error_message}", 502)


def validate_request_size(content: str, max_size: int = 100000) -> None:
    """
    Validate that request content is not too large.
    
    Args:
        content: Request content to validate
        max_size: Maximum allowed size in characters
        
    Raises:
        RequestValidationError: If content exceeds max size
    """
    if len(content) > max_size:
        raise RequestValidationError(
            f"Request content too large: {len(content)} characters (max: {max_size})"
        )


def validate_model_name(model: str, supported_models: list) -> None:
    """
    Validate that the requested model is supported.
    
    Args:
        model: Model name to validate
        supported_models: List of supported model names
        
    Raises:
        RequestValidationError: If model is not supported
    """
    if model not in supported_models:
        raise RequestValidationError(
            f"Unsupported model: {model}. Supported models: {', '.join(supported_models)}"
        )


class ErrorHandler:
    """Centralized error handler for the adapter."""
    
    def __init__(self):
        self.error_counts = {}
    
    def handle_error(
        self,
        error: Exception,
        endpoint: str,
        request_id: Optional[str] = None,
        api_format: str = "openai"
    ) -> JSONResponse:
        """
        Handle an error and return appropriate JSON response.
        
        Args:
            error: The exception that occurred
            endpoint: The endpoint where the error occurred
            request_id: Optional request ID
            api_format: API format for error response
            
        Returns:
            JSONResponse with formatted error
        """
        # Track error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error with context
        logger.error(f"🚨 Error in {endpoint}: {error_type} - {str(error)}")
        if request_id:
            logger.error(f"   🆔 Request ID: {request_id}")
        
        # Create error response
        error_response = create_error_response(error, request_id, api_format)
        
        # Determine status code
        if isinstance(error, CodegenAdapterError):
            status_code = error.status_code
        elif isinstance(error, HTTPException):
            status_code = error.status_code
        else:
            status_code = 500
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self.error_counts.copy()


# Global error handler instance
error_handler = ErrorHandler()

