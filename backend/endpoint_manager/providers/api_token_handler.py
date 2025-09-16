"""
API Token handler for token-based authentication systems.
Handles token refresh, custom authentication flows, and API interactions.
"""
import logging
from typing import Dict, Any, Optional
import aiohttp
import json

from .base_handler import BaseProviderHandler

logger = logging.getLogger(__name__)


class ApiTokenHandler(BaseProviderHandler):
    """
    Handler for API token-based endpoints with custom authentication.
    
    Supports token refresh, custom headers, and flexible authentication flows
    for providers that don't fit standard REST API patterns.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._current_token: Optional[str] = None
    
    async def start(self) -> None:
        """Initialize session and authenticate."""
        # Validate required configuration
        required_keys = ["api_base_url", "auth_type"]
        self.validate_required_config(required_keys)
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=self.get_config_value("timeout", 30))
        self._session = aiohttp.ClientSession(timeout=timeout)
        
        # Perform initial authentication
        await self._authenticate()
        
        self._is_started = True
        logger.info(f"API token handler started for {self.endpoint_id}")
    
    async def stop(self) -> None:
        """Close session and cleanup."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._current_token = None
        self._is_started = False
        logger.info(f"API token handler stopped for {self.endpoint_id}")
    
    async def send_message(self, message: str) -> str:
        """
        Send message using token-based authentication.
        
        Args:
            message: Message to send
            
        Returns:
            Response from the API
        """
        if not self._is_started or not self._session:
            raise RuntimeError("Handler not started")
        
        # Ensure we have a valid token
        if not self._current_token:
            await self._authenticate()
        
        # Prepare request
        url = self._get_endpoint_url()
        headers = self._get_request_headers()
        payload = self._prepare_payload(message)
        
        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                if response.status == 401:  # Token expired
                    logger.info("Token expired, refreshing...")
                    await self._refresh_token()
                    headers = self._get_request_headers()  # Get new headers
                    
                    # Retry with new token
                    async with self._session.post(url, json=payload, headers=headers) as retry_response:
                        if retry_response.status == 200:
                            response_data = await retry_response.json()
                            return self._extract_response(response_data)
                        else:
                            error_text = await retry_response.text()
                            raise Exception(f"Request failed: {error_text}")
                
                elif response.status == 200:
                    response_data = await response.json()
                    return self._extract_response(response_data)
                
                else:
                    error_text = await response.text()
                    raise Exception(f"Request failed with status {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
    
    async def health_check(self) -> bool:
        """Check if the API token endpoint is accessible."""
        try:
            if not self._is_started or not self._session:
                return False
            
            # Simple health check - try to send a basic message
            await self.send_message("ping")
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for {self.endpoint_id}: {e}")
            return False
    
    async def _authenticate(self) -> None:
        """Perform initial authentication to get token."""
        auth_type = self.get_config_value("auth_type")
        
        if auth_type == "bearer_token":
            # Direct token usage
            self._current_token = self.get_config_value("bearer_token")
            if not self._current_token:
                raise ValueError("Bearer token is required")
        
        elif auth_type == "oauth":
            # OAuth flow (simplified)
            await self._oauth_authenticate()
        
        elif auth_type == "custom":
            # Custom authentication flow
            await self._custom_authenticate()
        
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")
    
    async def _refresh_token(self) -> None:
        """Refresh the authentication token."""
        refresh_url = self.get_config_value("token_refresh_url")
        
        if not refresh_url:
            # If no refresh URL, try re-authenticating
            await self._authenticate()
            return
        
        # TODO: Implement token refresh logic
        # This would depend on the specific provider's refresh mechanism
        logger.warning("Token refresh not implemented, re-authenticating...")
        await self._authenticate()
    
    async def _oauth_authenticate(self) -> None:
        """Perform OAuth authentication flow."""
        # TODO: Implement OAuth flow
        # This is a simplified placeholder
        client_id = self.get_config_value("client_id")
        client_secret = self.get_config_value("client_secret")
        
        if not client_id or not client_secret:
            raise ValueError("OAuth requires client_id and client_secret")
        
        # Placeholder token
        self._current_token = "oauth_token_placeholder"
        logger.warning("OAuth authentication is placeholder implementation")
    
    async def _custom_authenticate(self) -> None:
        """Perform custom authentication flow."""
        # TODO: Implement custom authentication
        # This would be provider-specific
        custom_token = self.get_config_value("custom_token")
        
        if custom_token:
            self._current_token = custom_token
        else:
            raise ValueError("Custom authentication requires custom_token")
    
    def _get_endpoint_url(self) -> str:
        """Get the API endpoint URL."""
        base_url = self.get_config_value("api_base_url").rstrip("/")
        endpoint_path = self.get_config_value("endpoint_path", "/chat")
        return f"{base_url}{endpoint_path}"
    
    def _get_request_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"open-codegen-endpoint/{self.endpoint_id}"
        }
        
        # Add authentication header
        if self._current_token:
            auth_header_format = self.get_config_value("auth_header_format", "Bearer {token}")
            headers["Authorization"] = auth_header_format.format(token=self._current_token)
        
        # Add custom headers
        custom_headers = self.get_config_value("custom_headers", {})
        headers.update(custom_headers)
        
        return headers
    
    def _prepare_payload(self, message: str) -> Dict[str, Any]:
        """Prepare request payload."""
        # Default payload structure
        payload = {
            "message": message,
            "model": self.config.model_name
        }
        
        # Add any custom payload fields
        custom_payload = self.get_config_value("custom_payload", {})
        payload.update(custom_payload)
        
        return payload
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract response content from API response."""
        # Try common response field names
        response_fields = ["response", "content", "text", "message", "answer"]
        
        for field in response_fields:
            if field in response_data:
                content = response_data[field]
                if isinstance(content, str):
                    return content
                elif isinstance(content, list) and content:
                    return str(content[0])
                elif isinstance(content, dict):
                    return json.dumps(content)
        
        # If no standard field found, return the entire response as JSON
        return json.dumps(response_data)
