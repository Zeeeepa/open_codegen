"""
Z.ai SDK adapter for the Universal AI Endpoint Management System
Uses the Z.ai Python SDK for direct API communication instead of browser automation
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, List
from datetime import datetime

from .base_adapter import BaseAdapter, AdapterResponse, AdapterError
from ..zai_sdk.client import ZAIClient
from ..zai_sdk.core.exceptions import ZAIError
from ..zai_sdk.models import ChatCompletionResponse

logger = logging.getLogger(__name__)

class ZaiSdkAdapter(BaseAdapter):
    """Adapter for Z.ai using the Python SDK"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.client = None
        self.base_url = provider_config.get('base_url', 'https://chat.z.ai')
        self.timeout = provider_config.get('timeout_seconds', 180)
        self.auto_auth = provider_config.get('auto_auth', True)
        self.verbose = provider_config.get('verbose', False)
        
    async def initialize(self) -> bool:
        """Initialize the Z.ai SDK client"""
        try:
            # Initialize Z.ai client with automatic guest token authentication
            self.client = ZAIClient(
                base_url=self.base_url,
                timeout=self.timeout,
                auto_auth=self.auto_auth,
                verbose=self.verbose
            )
            
            # Check if we have a valid token (basic connectivity test)
            if not self.client.token:
                logger.error("No authentication token available")
                return False
            
            self.is_initialized = True
            logger.info(f"Z.ai SDK adapter initialized for {self.provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Z.ai SDK adapter for {self.provider_name}: {e}")
            self.client = None
            return False
    
    async def send_message(self, message: str, **kwargs) -> AdapterResponse:
        """Send message using Z.ai SDK"""
        if not self.is_initialized or not self.client:
            raise AdapterError("Adapter not initialized", "NOT_INITIALIZED")
        
        self.validate_request(message, **kwargs)
        
        session_id = kwargs.get('session_id')
        if session_id:
            self.update_session_activity(session_id)
            self.add_to_conversation_history(session_id, 'user', message)
        
        try:
            # Extract parameters
            model = kwargs.get('model', 'glm-4.5v')  # Default to GLM-4.5V
            enable_thinking = kwargs.get('enable_thinking', True)
            temperature = kwargs.get('temperature')
            top_p = kwargs.get('top_p')
            max_tokens = kwargs.get('max_tokens')
            
            # Map model names to Z.ai model IDs if needed
            model_mapping = {
                'gpt-3.5-turbo': 'glm-4.5v',
                'gpt-4': '0727-360B-API',
                'gpt-4-turbo': '0727-360B-API',
                'claude-3-sonnet': '0727-360B-API',
                'claude-3-haiku': 'glm-4.5v'
            }
            zai_model = model_mapping.get(model, model)
            
            # Send message using the SDK
            response: ChatCompletionResponse = await asyncio.to_thread(
                self.client.simple_chat,
                message=message,
                model=zai_model,
                enable_thinking=enable_thinking,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            # Add to conversation history
            if session_id:
                self.add_to_conversation_history(session_id, 'assistant', response.content)
            
            # Get the actual model used (from the mapping or original)
            actual_model = self.get_model_mapping(model)
            
            return self.create_response(
                content=response.content,
                model=actual_model,
                session_id=session_id,
                metadata={
                    'method': 'zai_sdk',
                    'zai_model': zai_model,
                    'thinking': response.thinking if hasattr(response, 'thinking') else None,
                    'usage': response.usage if hasattr(response, 'usage') else None,
                    'message_id': response.message_id if hasattr(response, 'message_id') else None
                }
            )
            
        except ZAIError as e:
            logger.error(f"Z.ai API error: {e}")
            raise AdapterError(f"Z.ai API failed: {str(e)}", "ZAI_API_ERROR")
        except Exception as e:
            logger.error(f"Error sending message through Z.ai SDK: {e}")
            raise AdapterError(f"Z.ai SDK failed: {str(e)}", "ZAI_SDK_FAILED")
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response using Z.ai SDK"""
        if not self.is_initialized or not self.client:
            raise AdapterError("Adapter not initialized", "NOT_INITIALIZED")
        
        self.validate_request(message, **kwargs)
        
        session_id = kwargs.get('session_id')
        if session_id:
            self.update_session_activity(session_id)
            self.add_to_conversation_history(session_id, 'user', message)
        
        try:
            # Create a chat for streaming
            model = kwargs.get('model', 'glm-4.5v')
            enable_thinking = kwargs.get('enable_thinking', True)
            
            # Map model names
            model_mapping = {
                'gpt-3.5-turbo': 'glm-4.5v',
                'gpt-4': '0727-360B-API',
                'gpt-4-turbo': '0727-360B-API',
                'claude-3-sonnet': '0727-360B-API',
                'claude-3-haiku': 'glm-4.5v'
            }
            zai_model = model_mapping.get(model, model)
            
            # Create a chat session
            chat_response = await asyncio.to_thread(
                self.client.create_chat,
                title="Streaming Chat",
                models=[zai_model],
                enable_thinking=enable_thinking
            )
            
            chat_id = chat_response.id
            
            # Stream the completion
            messages = [{"role": "user", "content": message}]
            
            full_content = ""
            async def stream_wrapper():
                nonlocal full_content
                for chunk in self.client.stream_completion(
                    chat_id=chat_id,
                    messages=messages,
                    model=zai_model,
                    enable_thinking=enable_thinking
                ):
                    if chunk.phase == "answer" and chunk.delta_content:
                        full_content += chunk.delta_content
                        yield chunk.delta_content
            
            # Stream the response
            async for chunk in stream_wrapper():
                yield chunk
            
            # Add final response to conversation history
            if session_id and full_content:
                self.add_to_conversation_history(session_id, 'assistant', full_content)
            
        except ZAIError as e:
            logger.error(f"Z.ai streaming error: {e}")
            raise AdapterError(f"Z.ai streaming failed: {str(e)}", "ZAI_STREAMING_ERROR")
        except Exception as e:
            logger.error(f"Error streaming message through Z.ai SDK: {e}")
            raise AdapterError(f"Z.ai SDK streaming failed: {str(e)}", "ZAI_SDK_STREAMING_FAILED")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Z.ai SDK adapter health"""
        try:
            if not self.client:
                return {'status': 'unhealthy', 'error': 'No client available'}
            
            # Basic health check - verify we have authentication
            return {
                'status': 'healthy' if self.client.token else 'unhealthy',
                'auth_data': self.client.auth_data is not None,
                'token': bool(self.client.token),
                'base_url': self.base_url,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from Z.ai SDK"""
        if not self.client:
            return []
        
        # Return hardcoded models since API requires special permissions
        # These are the models available in Z.ai according to the SDK
        return [
            {
                'id': 'glm-4.5v',
                'name': 'GLM-4.5V',
                'owned_by': 'zhipuai',
                'description': 'Advanced visual understanding and analysis model',
                'capabilities': {
                    'vision': True,
                    'citations': False,
                    'web_search': False,
                    'mcp': False
                },
                'params': {
                    'temperature': 0.8,
                    'top_p': 0.6,
                    'max_tokens': 80000
                }
            },
            {
                'id': '0727-360B-API',
                'name': 'GLM-4.5',
                'owned_by': 'zhipuai',
                'description': 'Most advanced model, proficient in coding and tool use',
                'capabilities': {
                    'vision': False,
                    'citations': False,
                    'web_search': False,
                    'mcp': True
                },
                'params': {
                    'temperature': 0.6,
                    'top_p': 0.95,
                    'max_tokens': 80000
                }
            }
        ]
    
    async def cleanup(self) -> None:
        """Clean up SDK resources"""
        try:
            if self.client:
                # Close any sessions if needed
                # The SDK handles its own cleanup
                self.client = None
            
            self.is_initialized = False
            logger.info(f"Z.ai SDK adapter cleaned up for {self.provider_name}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")