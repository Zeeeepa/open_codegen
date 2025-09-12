"""
Codegen API Provider
Integrates with existing enhanced_server.py functionality to route to OpenAI/Anthropic/Gemini
"""

import aiohttp
import asyncio
import time
import json
import os
from typing import Dict, Any, AsyncGenerator
import logging

from .base_provider import BaseProvider, ProviderType, ProviderStatus, ProviderResponse, ProviderContext
from .provider_factory import register_provider

logger = logging.getLogger(__name__)

@register_provider("codegen_api")
class CodegenAPIProvider(BaseProvider):
    """Provider that uses Codegen API to route to OpenAI/Anthropic/Gemini"""
    
    def __init__(self, name: str, provider_type: ProviderType, config: Dict[str, Any] = None):
        super().__init__(name, provider_type, config)
        
        # Default configuration
        self.base_url = config.get('base_url', os.getenv('CODEGEN_BASE_URL', 'https://codegen-sh--rest-api.modal.run'))
        self.org_id = config.get('org_id', os.getenv('CODEGEN_ORG_ID', '323'))
        self.timeout = config.get('timeout', int(os.getenv('CODEGEN_TIMEOUT', '300')))
        self.max_retries = config.get('max_retries', int(os.getenv('CODEGEN_MAX_RETRIES', '20')))
        self.base_delay = config.get('base_delay', int(os.getenv('CODEGEN_BASE_DELAY', '2')))
        
        # Model mapping for different providers
        self.model_mapping = {
            # OpenAI models
            'gpt-3.5-turbo': 'codegen-standard',
            'gpt-4': 'codegen-advanced',
            'gpt-3.5-turbo-instruct': 'codegen-standard',
            'gpt-4-turbo': 'codegen-advanced',
            'gpt-4o': 'codegen-advanced',
            
            # Anthropic models
            'claude-3-sonnet-20240229': 'codegen-advanced',
            'claude-3-haiku-20240307': 'codegen-standard',
            'claude-3-opus-20240229': 'codegen-premium',
            'claude-3-5-sonnet-20241022': 'codegen-advanced',
            
            # Gemini models
            'gemini-1.5-pro': 'codegen-advanced',
            'gemini-1.5-flash': 'codegen-standard',
            'gemini-pro': 'codegen-standard',
            
            # Default fallback
            'default': config.get('default_model', os.getenv('CODEGEN_DEFAULT_MODEL', 'codegen-standard'))
        }
        
        # Update with custom mapping if provided
        custom_mapping = config.get('model_mapping', {})
        if custom_mapping:
            self.model_mapping.update(custom_mapping)
        
        self.session: aiohttp.ClientSession = None
        self.token: str = None
    
    async def initialize(self, context: ProviderContext) -> bool:
        """Initialize the provider with authentication context"""
        try:
            if not self._validate_context(context):
                await self.set_status(ProviderStatus.ERROR, "Invalid context provided")
                return False
            
            self.context = context
            
            # Extract token from credentials
            if context.auth_type == "token":
                self.token = context.credentials.get('token')
            elif context.auth_type == "env":
                self.token = os.getenv('CODEGEN_TOKEN')
            else:
                await self.set_status(ProviderStatus.ERROR, f"Unsupported auth type: {context.auth_type}")
                return False
            
            if not self.token:
                await self.set_status(ProviderStatus.AUTHENTICATION_REQUIRED, "No token provided")
                return False
            
            # Create HTTP session
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'OpenCodegen-MultiAI/1.0'
                }
            )
            
            await self.set_status(ProviderStatus.ACTIVE)
            logger.info(f"Initialized Codegen API provider: {self.name}")
            return True
            
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, f"Initialization failed: {str(e)}")
            return False
    
    async def send_message(self, message: str, **kwargs) -> ProviderResponse:
        """Send a message to Codegen API"""
        if not self.session:
            return ProviderResponse(
                content="",
                provider_name=self.name,
                success=False,
                error="Provider not initialized"
            )
        
        self._record_request()
        start_time = time.time()
        
        try:
            await self.set_status(ProviderStatus.BUSY)
            
            # Extract parameters
            model = kwargs.get('model', 'codegen-standard')
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2000)
            
            # Map model if needed
            if model in self.model_mapping:
                codegen_model = self.model_mapping[model]
            else:
                codegen_model = self.model_mapping['default']
            
            # Prepare request payload
            payload = {
                'model': codegen_model,
                'messages': [{'role': 'user', 'content': message}],
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': False
            }
            
            # Add organization ID
            if self.org_id:
                payload['organization'] = self.org_id
            
            # Make request with retries
            response_data = await self._make_request_with_retry('/v1/chat/completions', payload)
            
            # Extract response content
            content = ""
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract usage information
            usage = response_data.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            
            await self.set_status(ProviderStatus.ACTIVE)
            
            return ProviderResponse(
                content=content,
                provider_name=self.name,
                model_name=codegen_model,
                success=True,
                response_time=response_time,
                tokens_used=tokens_used,
                metadata={
                    'original_model': model,
                    'mapped_model': codegen_model,
                    'usage': usage
                }
            )
            
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, str(e))
            return ProviderResponse(
                content="",
                provider_name=self.name,
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a message response from Codegen API"""
        if not self.session:
            yield f"Error: Provider not initialized"
            return
        
        self._record_request()
        
        try:
            await self.set_status(ProviderStatus.BUSY)
            
            # Extract parameters
            model = kwargs.get('model', 'codegen-standard')
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2000)
            
            # Map model if needed
            if model in self.model_mapping:
                codegen_model = self.model_mapping[model]
            else:
                codegen_model = self.model_mapping['default']
            
            # Prepare request payload
            payload = {
                'model': codegen_model,
                'messages': [{'role': 'user', 'content': message}],
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': True
            }
            
            # Add organization ID
            if self.org_id:
                payload['organization'] = self.org_id
            
            # Make streaming request
            async with self.session.post(f"{self.base_url}/v1/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    yield f"Error: HTTP {response.status} - {error_text}"
                    return
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data)
                            if 'choices' in chunk_data and chunk_data['choices']:
                                choice = chunk_data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
            
            await self.set_status(ProviderStatus.ACTIVE)
            
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, str(e))
            yield f"Error: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check if the Codegen API is healthy"""
        if not self.session:
            return False
        
        try:
            # Simple health check with minimal request
            payload = {
                'model': 'codegen-standard',
                'messages': [{'role': 'user', 'content': 'ping'}],
                'max_tokens': 5
            }
            
            if self.org_id:
                payload['organization'] = self.org_id
            
            async with self.session.post(f"{self.base_url}/v1/chat/completions", json=payload) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        await self.set_status(ProviderStatus.INACTIVE)
        logger.info(f"Cleaned up Codegen API provider: {self.name}")
    
    async def _make_request_with_retry(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        await self.set_status(ProviderStatus.RATE_LIMITED)
                        retry_after = int(response.headers.get('Retry-After', self.base_delay * (2 ** attempt)))
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                last_exception = Exception(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                    
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        # All retries exhausted
        raise last_exception or Exception("Max retries exceeded")
    
    def _validate_context(self, context: ProviderContext) -> bool:
        """Validate Codegen API context"""
        if not super()._validate_context(context):
            return False
        
        # Check for required auth types
        if context.auth_type not in ["token", "env"]:
            return False
        
        # If token auth, must have token in credentials
        if context.auth_type == "token" and not context.credentials.get('token'):
            return False
        
        return True
