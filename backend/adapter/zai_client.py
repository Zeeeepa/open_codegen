"""
Z.ai API client for handling requests to Z.ai service.
Follows KISS principle with simple, focused functionality.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import aiohttp
from aiohttp import ClientTimeout, ClientSession

from .zai_exceptions import (
    ZaiError, ZaiAuthenticationError, ZaiRateLimitError,
    ZaiConnectionError, ZaiTimeoutError, ZaiStreamingError
)
from .models import ZaiChatRequest, ZaiChatResponse, ZaiStreamResponse

logger = logging.getLogger(__name__)


class ZaiClient:
    """Client for Z.ai API interactions."""
    
    def __init__(self, base_url: str = "https://z.ai/api/v1", timeout: int = 60):
        """
        Initialize Z.ai client.
        
        Args:
            base_url: Z.ai API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _handle_error_response(self, status: int, response_data: Dict[str, Any]):
        """Handle error responses from Z.ai API."""
        error_message = response_data.get('error', {}).get('message', 'Unknown error')
        
        if status == 401:
            raise ZaiAuthenticationError(error_message)
        elif status == 429:
            raise ZaiRateLimitError(error_message)
        elif status >= 500:
            raise ZaiConnectionError(f"Server error: {error_message}")
        else:
            raise ZaiError(error_message, status_code=status)
    
    async def chat_completion(self, request: ZaiChatRequest) -> ZaiChatResponse:
        """
        Send chat completion request to Z.ai.
        
        Args:
            request: Z.ai chat request
            
        Returns:
            Z.ai chat response
            
        Raises:
            ZaiError: On API errors
        """
        session = await self._get_session()
        url = f"{self.base_url}/chat/completions"
        
        try:
            async with session.post(
                url,
                json=request.dict(exclude_none=True),
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    self._handle_error_response(response.status, response_data)
                
                return ZaiChatResponse(**response_data)
                
        except asyncio.TimeoutError:
            raise ZaiTimeoutError()
        except aiohttp.ClientError as e:
            raise ZaiConnectionError(f"Connection error: {str(e)}")
        except json.JSONDecodeError:
            raise ZaiError("Invalid JSON response from Z.ai API")
    
    async def chat_completion_stream(
        self, 
        request: ZaiChatRequest
    ) -> AsyncGenerator[ZaiStreamResponse, None]:
        """
        Send streaming chat completion request to Z.ai.
        
        Args:
            request: Z.ai chat request with stream=True
            
        Yields:
            Z.ai streaming responses
            
        Raises:
            ZaiStreamingError: On streaming errors
        """
        session = await self._get_session()
        url = f"{self.base_url}/chat/completions"
        
        # Ensure streaming is enabled
        request_data = request.dict(exclude_none=True)
        request_data['stream'] = True
        
        try:
            async with session.post(
                url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_data = await response.json()
                    self._handle_error_response(response.status, error_data)
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line or not line.startswith('data: '):
                        continue
                    
                    if line == 'data: [DONE]':
                        break
                    
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        yield ZaiStreamResponse(**data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming data: {line}")
                        continue
                        
        except asyncio.TimeoutError:
            raise ZaiTimeoutError("Streaming request timed out")
        except aiohttp.ClientError as e:
            raise ZaiStreamingError(f"Streaming connection error: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
