"""
REST API handler for standard HTTP-based AI endpoints.
Handles authentication, request formatting, and response parsing.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
import json

from .base_handler import BaseProviderHandler
from backend.database.models import RestApiConfig

logger = logging.getLogger(__name__)


class RestApiHandler(BaseProviderHandler):
    """
    Handler for REST API-based AI endpoints.
    
    Supports various authentication methods (API key, bearer token, basic auth)
    and handles HTTP requests with proper error handling and retries.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_config: Optional[RestApiConfig] = None
    
    async def start(self) -> None:
        """Initialize HTTP session and validate configuration."""
        # Validate required configuration
        required_keys = ["api_base_url", "auth_type"]
        self.validate_required_config(required_keys)
        
        # Parse configuration into RestApiConfig
        self._api_config = RestApiConfig(**self.config_data)
        
        # Validate authentication configuration
        self._validate_auth_config()
        
        # Create HTTP session with timeout
        timeout = aiohttp.ClientTimeout(total=self._api_config.timeout)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self._get_default_headers()
        )
        
        # Test connection
        await self._test_connection()
        
        self._is_started = True
        logger.info(f"REST API handler started for {self.endpoint_id}")
    
    async def stop(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._is_started = False
        logger.info(f"REST API handler stopped for {self.endpoint_id}")
    
    async def send_message(self, message: str) -> str:
        """
        Send message to REST API endpoint.
        
        Args:
            message: Message to send
            
        Returns:
            Response from the API
            
        Raises:
            Exception: If request fails after retries
        """
        if not self._is_started or not self._session:
            raise RuntimeError("Handler not started")
        
        # Prepare request payload
        payload = self._prepare_request_payload(message)
        
        # Send request with retries
        for attempt in range(self._api_config.max_retries):
            try:
                async with self._session.post(
                    self._get_endpoint_url(),
                    json=payload,
                    headers=self._get_auth_headers()
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        return self._extract_response_content(response_data)
                    
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            f"Rate limited, waiting {wait_time}s before retry"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}: {error_text}"
                        )
            
            except aiohttp.ClientError as e:
                if attempt == self._api_config.max_retries - 1:
                    raise Exception(f"Request failed after {attempt + 1} attempts: {e}")
                
                wait_time = 2 ** attempt
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        
        raise Exception("Max retries exceeded")
    
    async def health_check(self) -> bool:
        """Perform health check by sending a simple request."""
        try:
            if not self._is_started or not self._session:
                return False
            
            # Send a simple health check message
            await self.send_message("Hello")
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for {self.endpoint_id}: {e}")
            return False
    
    def _validate_auth_config(self) -> None:
        """Validate authentication configuration based on auth type."""
        auth_type = self._api_config.auth_type
        
        if auth_type == "api_key":
            if not self._api_config.api_key:
                raise ValueError("API key is required for api_key auth type")
        
        elif auth_type == "bearer_token":
            if not self._api_config.bearer_token:
                raise ValueError("Bearer token is required for bearer_token auth type")
        
        elif auth_type == "basic_auth":
            if not self._api_config.username or not self._api_config.password:
                raise ValueError(
                    "Username and password are required for basic_auth auth type"
                )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"open-codegen-endpoint/{self.endpoint_id}"
        }
        
        # Add custom headers from configuration
        if self._api_config and self._api_config.headers:
            headers.update(self._api_config.headers)
        
        return headers
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth type."""
        headers = {}
        
        if self._api_config.auth_type == "api_key":
            headers["Authorization"] = f"Bearer {self._api_config.api_key}"
        
        elif self._api_config.auth_type == "bearer_token":
            headers["Authorization"] = f"Bearer {self._api_config.bearer_token}"
        
        elif self._api_config.auth_type == "basic_auth":
            import base64
            credentials = f"{self._api_config.username}:{self._api_config.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        return headers
    
    def _get_endpoint_url(self) -> str:
        """Get the full endpoint URL."""
        base_url = self._api_config.api_base_url.rstrip("/")
        
        # Common endpoint patterns for different providers
        if "openai" in base_url.lower():
            return f"{base_url}/v1/chat/completions"
        elif "anthropic" in base_url.lower():
            return f"{base_url}/v1/messages"
        elif "google" in base_url.lower() or "gemini" in base_url.lower():
            return f"{base_url}/v1/models/gemini-pro:generateContent"
        else:
            # Generic endpoint - assume it's ready to receive requests
            return base_url
    
    def _prepare_request_payload(self, message: str) -> Dict[str, Any]:
        """Prepare request payload based on provider type."""
        base_url = self._api_config.api_base_url.lower()
        
        if "openai" in base_url:
            return {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
        
        elif "anthropic" in base_url:
            return {
                "model": self.config.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": message}]
            }
        
        elif "google" in base_url or "gemini" in base_url:
            return {
                "contents": [{
                    "parts": [{"text": message}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 1000,
                    "temperature": 0.7
                }
            }
        
        else:
            # Generic payload
            return {
                "message": message,
                "model": self.config.model_name
            }
    
    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract content from API response based on provider format."""
        try:
            # OpenAI format
            if "choices" in response_data:
                return response_data["choices"][0]["message"]["content"]
            
            # Anthropic format
            elif "content" in response_data:
                if isinstance(response_data["content"], list):
                    return response_data["content"][0]["text"]
                return response_data["content"]
            
            # Google/Gemini format
            elif "candidates" in response_data:
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Generic format - look for common response fields
            elif "response" in response_data:
                return response_data["response"]
            elif "text" in response_data:
                return response_data["text"]
            elif "message" in response_data:
                return response_data["message"]
            
            else:
                # Return the entire response as JSON string if format is unknown
                return json.dumps(response_data)
        
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract response content: {e}")
            return json.dumps(response_data)
    
    async def _test_connection(self) -> None:
        """Test the connection to the API endpoint."""
        try:
            # Simple GET request to test connectivity
            async with self._session.get(
                self._api_config.api_base_url,
                headers=self._get_auth_headers()
            ) as response:
                # Accept any response that's not a connection error
                pass
        
        except aiohttp.ClientConnectorError as e:
            raise Exception(f"Failed to connect to API endpoint: {e}")
        except Exception:
            # Other errors are acceptable for connection test
            # (e.g., 404, 401 - means we can reach the server)
            pass
