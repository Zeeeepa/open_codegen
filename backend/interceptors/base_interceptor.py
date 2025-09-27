"""
Base Interceptor Class
Abstract base class for all API interceptors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class APIFormat(Enum):
    """Supported API formats for interception"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class InterceptedRequest:
    """Standardized request format after interception"""
    api_format: APIFormat
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    query_params: Dict[str, str]
    auth_info: Optional[Dict[str, Any]] = None
    original_url: str = ""
    client_ip: str = ""
    user_agent: str = ""


@dataclass
class InterceptedResponse:
    """Standardized response format before transformation back to original format"""
    status_code: int
    headers: Dict[str, str]
    body: Dict[str, Any]
    is_streaming: bool = False
    provider_used: Optional[str] = None
    processing_time: float = 0.0
    error: Optional[str] = None


class BaseInterceptor(ABC):
    """
    Abstract base class for API interceptors
    
    Each interceptor handles a specific API format (OpenAI, Anthropic, Gemini)
    and is responsible for:
    1. Validating incoming requests
    2. Extracting authentication information
    3. Parsing request parameters
    4. Converting to standardized format
    5. Transforming responses back to original format
    """
    
    def __init__(self, api_format: APIFormat):
        self.api_format = api_format
        self.logger = logging.getLogger(f"{__name__}.{api_format.value}")
    
    @abstractmethod
    def get_supported_endpoints(self) -> List[str]:
        """Return list of supported endpoint patterns"""
        pass
    
    @abstractmethod
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate incoming request
        Returns (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def extract_auth_info(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract authentication information from headers"""
        pass
    
    @abstractmethod
    def parse_request(self, endpoint: str, method: str, headers: Dict[str, str], 
                     body: Dict[str, Any], query_params: Dict[str, str]) -> InterceptedRequest:
        """Parse incoming request into standardized format"""
        pass
    
    @abstractmethod
    def format_response(self, intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Transform standardized response back to original API format"""
        pass
    
    @abstractmethod
    def format_error(self, error_message: str, error_code: str = "internal_error", 
                    status_code: int = 500) -> Dict[str, Any]:
        """Format error response in original API format"""
        pass
    
    def is_supported_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint is supported by this interceptor"""
        supported_endpoints = self.get_supported_endpoints()
        return any(endpoint.startswith(pattern) or endpoint.endswith(pattern) 
                  for pattern in supported_endpoints)
    
    def intercept_request(self, endpoint: str, method: str, headers: Dict[str, str],
                         body: Dict[str, Any], query_params: Dict[str, str],
                         client_ip: str = "", user_agent: str = "") -> InterceptedRequest:
        """
        Main interception method
        Validates, authenticates, and parses the request
        """
        try:
            # Validate request
            is_valid, error_msg = self.validate_request(body)
            if not is_valid:
                raise ValueError(f"Invalid request: {error_msg}")
            
            # Extract authentication
            auth_info = self.extract_auth_info(headers)
            if not auth_info:
                raise ValueError("Authentication required")
            
            # Parse request
            intercepted_request = self.parse_request(endpoint, method, headers, body, query_params)
            intercepted_request.auth_info = auth_info
            intercepted_request.client_ip = client_ip
            intercepted_request.user_agent = user_agent
            intercepted_request.original_url = endpoint
            
            self.logger.info(f"Successfully intercepted {self.api_format.value} request to {endpoint}")
            return intercepted_request
            
        except Exception as e:
            self.logger.error(f"Failed to intercept request: {str(e)}")
            raise
    
    def transform_response(self, intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """
        Transform provider response back to original API format
        """
        try:
            if intercepted_response.error:
                return self.format_error(intercepted_response.error)
            
            formatted_response = self.format_response(intercepted_response)
            self.logger.info(f"Successfully transformed response from provider {intercepted_response.provider_used}")
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Failed to transform response: {str(e)}")
            return self.format_error(f"Response transformation failed: {str(e)}")
