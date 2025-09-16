"""
REST API adapter for the Universal AI Endpoint Management System
Handles OpenAI-compatible APIs, Codegen API, and other REST endpoints
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from .base_adapter import BaseAdapter, AdapterResponse, AdapterError

logger = logging.getLogger(__name__)

class RestApiAdapter(BaseAdapter):
    """Adapter for REST API providers (OpenAI, Codegen, Gemini, etc.)"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.session = None
        self.base_url = provider_config.get('base_url', '')
        self.api_key = provider_config.get('api_key', '')
        self.timeout = provider_config.get('timeout_seconds', 30)
        
    async def initialize(self) -> bool:
        """Initialize HTTP session and validate connection"""
        try:
            # Create aiohttp session with timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Validate connection with health check
            health_status = await self.health_check()
            self.is_initialized = health_status.get('status') == 'healthy'
            
            logger.info(f"REST API adapter initialized for {self.provider_name}: {self.is_initialized}")
            return self.is_initialized
            
        except Exception as e:
            logger.error(f"Failed to initialize REST API adapter for {self.provider_name}: {e}")
            self.is_initialized = False
            return False
    
    async def send_message(self, message: str, **kwargs) -> AdapterResponse:
        """Send message to REST API endpoint"""
        if not self.is_initialized:
            raise AdapterError("Adapter not initialized", "NOT_INITIALIZED")
        
        self.validate_request(message, **kwargs)
        
        # Get session info
        session_id = kwargs.get('session_id')
        if session_id:
            self.update_session_activity(session_id)
            self.add_to_conversation_history(session_id, 'user', message)
        
        # Map model name
        requested_model = kwargs.get('model', 'gpt-3.5-turbo')
        mapped_model = self.get_model_mapping(requested_model)
        
        try:
            # Prepare request based on provider type
            if self.provider_name == "Codegen REST API":
                response = await self._send_codegen_request(message, mapped_model, **kwargs)
            else:
                response = await self._send_openai_compatible_request(message, mapped_model, **kwargs)
            
            # Add to conversation history
            if session_id:
                self.add_to_conversation_history(session_id, 'assistant', response.content)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending message to {self.provider_name}: {e}")
            raise AdapterError(f"Request failed: {str(e)}", "REQUEST_FAILED", {'original_error': str(e)})
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response from REST API"""
        if not self.is_initialized:
            raise AdapterError("Adapter not initialized", "NOT_INITIALIZED")
        
        self.validate_request(message, **kwargs)
        
        session_id = kwargs.get('session_id')
        if session_id:
            self.update_session_activity(session_id)
            self.add_to_conversation_history(session_id, 'user', message)
        
        requested_model = kwargs.get('model', 'gpt-3.5-turbo')
        mapped_model = self.get_model_mapping(requested_model)
        
        try:
            full_response = ""
            
            if self.provider_name == "Codegen REST API":
                async for chunk in self._stream_codegen_request(message, mapped_model, **kwargs):
                    full_response += chunk
                    yield chunk
            else:
                async for chunk in self._stream_openai_compatible_request(message, mapped_model, **kwargs):
                    full_response += chunk
                    yield chunk
            
            # Add complete response to conversation history
            if session_id:
                self.add_to_conversation_history(session_id, 'assistant', full_response)
                
        except Exception as e:
            logger.error(f"Error streaming message from {self.provider_name}: {e}")
            raise AdapterError(f"Streaming failed: {str(e)}", "STREAM_FAILED", {'original_error': str(e)})
    
    async def _send_codegen_request(self, message: str, model: str, **kwargs) -> AdapterResponse:
        """Send request to Codegen API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Get conversation history for context
        session_id = kwargs.get('session_id')
        messages = []
        
        if session_id:
            history = self.get_conversation_history(session_id)
            messages = [{'role': msg['role'], 'content': msg['content']} for msg in history[-10:]]  # Last 10 messages
        
        messages.append({'role': 'user', 'content': message})
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048),
            'stream': False
        }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise AdapterError(f"API request failed: {error_text}", "API_ERROR")
            
            data = await response.json()
            content = data['choices'][0]['message']['content']
            
            return self.create_response(
                content=content,
                model=model,
                session_id=session_id,
                usage=data.get('usage', {}),
                metadata={'provider_response': data}
            )
    
    async def _send_openai_compatible_request(self, message: str, model: str, **kwargs) -> AdapterResponse:
        """Send request to OpenAI-compatible API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        session_id = kwargs.get('session_id')
        messages = []
        
        if session_id:
            history = self.get_conversation_history(session_id)
            messages = [{'role': msg['role'], 'content': msg['content']} for msg in history[-10:]]
        
        messages.append({'role': 'user', 'content': message})
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048),
            'stream': False
        }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise AdapterError(f"API request failed: {error_text}", "API_ERROR")
            
            data = await response.json()
            content = data['choices'][0]['message']['content']
            
            return self.create_response(
                content=content,
                model=model,
                session_id=session_id,
                usage=data.get('usage', {}),
                metadata={'provider_response': data}
            )
    
    async def _stream_codegen_request(self, message: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream request to Codegen API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        session_id = kwargs.get('session_id')
        messages = []
        
        if session_id:
            history = self.get_conversation_history(session_id)
            messages = [{'role': msg['role'], 'content': msg['content']} for msg in history[-10:]]
        
        messages.append({'role': 'user', 'content': message})
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048),
            'stream': True
        }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise AdapterError(f"API request failed: {error_text}", "API_ERROR")
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
    
    async def _stream_openai_compatible_request(self, message: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream request to OpenAI-compatible API"""
        # Similar implementation to _stream_codegen_request
        # This would be customized based on the specific API's streaming format
        async for chunk in self._stream_codegen_request(message, model, **kwargs):
            yield chunk
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health and availability"""
        try:
            if not self.session:
                return {'status': 'unhealthy', 'error': 'No session available'}
            
            # Try a simple request to check connectivity
            url = f"{self.base_url}/v1/models" if "/v1" not in self.base_url else f"{self.base_url}/models"
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return {
                        'status': 'healthy',
                        'response_time': response.headers.get('X-Response-Time', 'unknown'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status}',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
        logger.info(f"REST API adapter cleaned up for {self.provider_name}")
