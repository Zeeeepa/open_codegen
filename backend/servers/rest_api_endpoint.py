"""
REST API Endpoint Server
Handles REST API endpoints (OpenAI, Gemini, DeepSeek, etc.)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import json
import aiohttp
import time
from urllib.parse import urljoin

from .base_endpoint import BaseEndpoint, EndpointStatus, EndpointHealth

logger = logging.getLogger(__name__)

class RestApiEndpoint(BaseEndpoint):
    """REST API endpoint for various AI services"""
    
    def __init__(self, name: str, config: Dict[str, Any], priority: int = 50):
        super().__init__(name, config, priority)
        
        # API specific configuration
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', self.url)
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.headers = config.get('headers', {})
        self.endpoint_path = config.get('endpoint_path', '/v1/chat/completions')
        
        # Request configuration
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.top_p = config.get('top_p', 1.0)
        self.frequency_penalty = config.get('frequency_penalty', 0.0)
        self.presence_penalty = config.get('presence_penalty', 0.0)
        
        # Rate limiting
        self.max_requests_per_minute = config.get('max_requests_per_minute', 60)
        self.request_timestamps = []
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Build headers
        self._build_headers()
        
    def _build_headers(self):
        """Build request headers based on configuration"""
        self.request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Universal-AI-Endpoint-Manager/1.0'
        }
        
        # Add API key if provided
        if self.api_key:
            # Different APIs use different header formats
            api_name = self.name.lower()
            
            if 'openai' in api_name:
                self.request_headers['Authorization'] = f'Bearer {self.api_key}'
            elif 'anthropic' in api_name or 'claude' in api_name:
                self.request_headers['x-api-key'] = self.api_key
                self.request_headers['anthropic-version'] = '2023-06-01'
            elif 'gemini' in api_name or 'google' in api_name:
                # Gemini uses API key in URL or header
                self.request_headers['Authorization'] = f'Bearer {self.api_key}'
            elif 'deepseek' in api_name:
                self.request_headers['Authorization'] = f'Bearer {self.api_key}'
            elif 'deepinfra' in api_name:
                self.request_headers['Authorization'] = f'Bearer {self.api_key}'
            else:
                # Generic bearer token
                self.request_headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Add custom headers
        self.request_headers.update(self.headers)
        
    async def start(self) -> bool:
        """Start the REST API endpoint"""
        try:
            self.update_status(EndpointStatus.STARTING)
            logger.info(f"Starting REST API endpoint: {self.name}")
            
            # Create aiohttp session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.request_headers
            )
            
            # Test the connection
            health_ok = await self.health_check()
            
            if health_ok:
                self._running = True
                self.update_status(EndpointStatus.RUNNING)
                self.update_health(EndpointHealth.HEALTHY)
                logger.info(f"REST API endpoint started successfully: {self.name}")
                return True
            else:
                await self._cleanup()
                self.update_status(EndpointStatus.ERROR)
                self.update_health(EndpointHealth.UNHEALTHY)
                logger.error(f"REST API endpoint health check failed: {self.name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start REST API endpoint {self.name}: {e}")
            self.update_status(EndpointStatus.ERROR)
            self.update_health(EndpointHealth.UNHEALTHY)
            await self._cleanup()
            return False
    
    async def stop(self) -> bool:
        """Stop the REST API endpoint"""
        try:
            self.update_status(EndpointStatus.STOPPING)
            logger.info(f"Stopping REST API endpoint: {self.name}")
            
            await self._cleanup()
            
            self._running = False
            self.update_status(EndpointStatus.STOPPED)
            self.update_health(EndpointHealth.UNKNOWN)
            
            logger.info(f"REST API endpoint stopped: {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop REST API endpoint {self.name}: {e}")
            self.update_status(EndpointStatus.ERROR)
            return False
    
    async def send_message(self, message: str, **kwargs) -> Optional[str]:
        """Send a message to the REST API endpoint"""
        if not self._running or not self.session:
            raise Exception("Endpoint not running")
        
        # Check rate limiting
        await self._check_rate_limit()
        
        try:
            # Build request payload
            payload = self._build_request_payload(message, **kwargs)
            
            # Make API request
            url = urljoin(self.base_url, self.endpoint_path)
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._extract_response_content(data)
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to send message to {self.name}: {e}")
            raise
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response from REST API"""
        if not self._running or not self.session:
            raise Exception("Endpoint not running")
        
        # Check rate limiting
        await self._check_rate_limit()
        
        try:
            # Build request payload with streaming enabled
            payload = self._build_request_payload(message, stream=True, **kwargs)
            
            # Make streaming API request
            url = urljoin(self.base_url, self.endpoint_path)
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                content = self._extract_stream_content(data)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
                else:
                    error_text = await response.text()
                    raise Exception(f"Streaming API request failed with status {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to stream message from {self.name}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Perform health check on the REST API endpoint"""
        try:
            if not self.session:
                return False
            
            # Try a simple request to check if the API is responsive
            test_payload = self._build_request_payload("Hello", max_tokens=1)
            url = urljoin(self.base_url, self.endpoint_path)
            
            async with self.session.post(url, json=test_payload) as response:
                return response.status in [200, 400, 401]  # 400/401 means API is responsive but request issue
                
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return False
    
    def _build_request_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Build request payload based on API type"""
        # Extract parameters
        model = kwargs.get('model', self.model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        stream = kwargs.get('stream', False)
        
        # Build messages array
        messages = [{"role": "user", "content": message}]
        
        # Base payload (OpenAI format)
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        # API-specific modifications
        api_name = self.name.lower()
        
        if 'anthropic' in api_name or 'claude' in api_name:
            # Anthropic Claude format
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
        elif 'gemini' in api_name or 'google' in api_name:
            # Google Gemini format
            payload = {
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
        elif 'deepseek' in api_name:
            # DeepSeek format (similar to OpenAI)
            payload.update({
                "top_p": kwargs.get('top_p', self.top_p),
                "frequency_penalty": kwargs.get('frequency_penalty', self.frequency_penalty),
                "presence_penalty": kwargs.get('presence_penalty', self.presence_penalty)
            })
        
        return payload
    
    def _extract_response_content(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract response content from API response"""
        try:
            api_name = self.name.lower()
            
            if 'anthropic' in api_name or 'claude' in api_name:
                # Anthropic Claude response format
                if 'content' in data and data['content']:
                    return data['content'][0].get('text', '')
            elif 'gemini' in api_name or 'google' in api_name:
                # Google Gemini response format
                if 'candidates' in data and data['candidates']:
                    content = data['candidates'][0].get('content', {})
                    if 'parts' in content and content['parts']:
                        return content['parts'][0].get('text', '')
            else:
                # OpenAI format (default)
                if 'choices' in data and data['choices']:
                    message = data['choices'][0].get('message', {})
                    return message.get('content', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract response content: {e}")
            return None
    
    def _extract_stream_content(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract content from streaming response chunk"""
        try:
            api_name = self.name.lower()
            
            if 'anthropic' in api_name or 'claude' in api_name:
                # Anthropic Claude streaming format
                if data.get('type') == 'content_block_delta':
                    return data.get('delta', {}).get('text', '')
            elif 'gemini' in api_name or 'google' in api_name:
                # Google Gemini streaming format
                if 'candidates' in data and data['candidates']:
                    content = data['candidates'][0].get('content', {})
                    if 'parts' in content and content['parts']:
                        return content['parts'][0].get('text', '')
            else:
                # OpenAI format (default)
                if 'choices' in data and data['choices']:
                    delta = data['choices'][0].get('delta', {})
                    return delta.get('content', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract stream content: {e}")
            return None
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if we're at the rate limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            # Calculate wait time
            oldest_request = min(self.request_timestamps)
            wait_time = 60 - (current_time - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached for {self.name}, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(current_time)
    
    async def _cleanup(self):
        """Clean up session resources"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
                
        except Exception as e:
            logger.error(f"Error during cleanup for {self.name}: {e}")
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API-specific information"""
        return {
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "model": self.model,
            "endpoint_path": self.endpoint_path,
            "rate_limit": self.max_requests_per_minute,
            "current_requests_in_window": len(self.request_timestamps)
        }
