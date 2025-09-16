"""
Error handling utilities for Open Codegen.

Provides safe error parsing and custom exception classes following KISS principles.
"""

from typing import Any


def safe_parse_error(err: Any, default_message: str = "Unknown error") -> Exception:
    """
    Safely parse an error message.

    Args:
        err: The error to parse
        default_message: The default message to return if the error is not an instance of Error

    Returns:
        The error message or the default message
    """
    if isinstance(err, Exception):
        return err

    return Exception(default_message)


class OpenCodegenError(Exception):
    """Base exception for Open Codegen errors."""
    pass


class DatabaseError(OpenCodegenError):
    """Database-related errors."""
    pass


class SupabaseConnectionError(DatabaseError):
    """Supabase connection errors."""
    pass


class EndpointError(OpenCodegenError):
    """Endpoint management errors."""
    pass


class EndpointValidationError(EndpointError):
    """Endpoint validation errors."""
    pass


class AIAgentError(OpenCodegenError):
    """AI agent operation errors."""
    pass


class WebsiteIntegrationError(OpenCodegenError):
    """Website integration errors."""
    pass


class BrowserAutomationError(WebsiteIntegrationError):
    """Browser automation errors."""
    pass


class VariableError(OpenCodegenError):
    """Variable management errors."""
    pass


class ConfigurationError(OpenCodegenError):
    """Configuration-related errors."""
    pass
