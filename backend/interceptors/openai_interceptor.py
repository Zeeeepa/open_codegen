"""
OpenAI API Interceptor
Handles interception of OpenAI API calls
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from .base_interceptor import BaseInterceptor, APIFormat, InterceptedRequest, InterceptedResponse


class OpenAIInterceptor(BaseInterceptor):
    """
    OpenAI API Interceptor
    
    Handles OpenAI API endpoints:
    - /v1/chat/completions
    - /v1/completions  
    - /v1/embeddings
    - /v1/images/generations
    - /v1/images/edits
    - /v1/images/variations
    - /v1/audio/transcriptions
    - /v1/audio/translations
    - /v1/models
    """
    
    def __init__(self):
        super().__init__(APIFormat.OPENAI)
        
        # OpenAI endpoint patterns
        self.supported_endpoints = [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings", 
            "/v1/images/generations",
            "/v1/images/edits",
            "/v1/images/variations",
            "/v1/audio/transcriptions",
            "/v1/audio/translations",
            "/v1/models",
            "/v1/files",
            "/v1/fine-tuning/jobs"
        ]
        
        # Model name mappings for different providers
        self.model_mappings = {
            "gpt-4": "gpt-4",
            "gpt-4-turbo": "gpt-4-turbo", 
            "gpt-4-turbo-preview": "gpt-4-turbo-preview",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k": "gpt-3.5-turbo-16k",
            "text-embedding-ada-002": "text-embedding-ada-002",
            "dall-e-3": "dall-e-3",
            "dall-e-2": "dall-e-2",
            "whisper-1": "whisper-1"
        }
    
    def get_supported_endpoints(self) -> List[str]:
        """Return list of supported OpenAI endpoint patterns"""
        return self.supported_endpoints
    
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate OpenAI API request"""
        if not isinstance(request_data, dict):
            return False, "Request body must be JSON object"
        
        # Check for required fields based on endpoint type
        if "model" in request_data:
            model = request_data.get("model")
            if not model or not isinstance(model, str):
                return False, "Model field is required and must be a string"
        
        # Validate messages for chat completions
        if "messages" in request_data:
            messages = request_data.get("messages")
            if not isinstance(messages, list) or len(messages) == 0:
                return False, "Messages must be a non-empty array"
            
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    return False, "Each message must have 'role' and 'content' fields"
        
        # Validate prompt for completions
        if "prompt" in request_data:
            prompt = request_data.get("prompt")
            if not prompt or (not isinstance(prompt, str) and not isinstance(prompt, list)):
                return False, "Prompt must be a non-empty string or array"
        
        return True, None
    
    def extract_auth_info(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract OpenAI API key from Authorization header"""
        auth_header = headers.get("Authorization", "").strip()
        
        if not auth_header:
            return None
        
        # OpenAI uses "Bearer sk-..." format
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:].strip()
            if api_key.startswith("sk-") or api_key.startswith("org-"):
                return {
                    "type": "bearer",
                    "api_key": api_key,
                    "organization": headers.get("OpenAI-Organization"),
                    "project": headers.get("OpenAI-Project")
                }
        
        return None
    
    def parse_request(self, endpoint: str, method: str, headers: Dict[str, str], 
                     body: Dict[str, Any], query_params: Dict[str, str]) -> InterceptedRequest:
        """Parse OpenAI API request into standardized format"""
        
        # Create intercepted request
        intercepted_request = InterceptedRequest(
            api_format=self.api_format,
            endpoint=endpoint,
            method=method,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Extract and normalize model name
        if "model" in body:
            model = body["model"]
            intercepted_request.body["normalized_model"] = self.model_mappings.get(model, model)
        
        # Add OpenAI-specific metadata
        intercepted_request.body["_openai_metadata"] = {
            "original_endpoint": endpoint,
            "organization": headers.get("OpenAI-Organization"),
            "project": headers.get("OpenAI-Project"),
            "user": body.get("user"),
            "stream": body.get("stream", False)
        }
        
        return intercepted_request
    
    def format_response(self, intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Transform provider response back to OpenAI format"""
        
        response_body = intercepted_response.body
        
        # Handle different response types
        if "choices" in response_body:
            # Chat completions or completions response
            return self._format_completion_response(response_body, intercepted_response)
        elif "data" in response_body and isinstance(response_body["data"], list):
            # Embeddings or images response
            return self._format_data_response(response_body, intercepted_response)
        elif "text" in response_body:
            # Audio transcription response
            return self._format_audio_response(response_body, intercepted_response)
        else:
            # Generic response
            return response_body
    
    def _format_completion_response(self, response_body: Dict[str, Any], 
                                  intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Format chat/completion response in OpenAI format"""
        
        # Ensure OpenAI-compatible structure
        formatted_response = {
            "id": response_body.get("id", f"chatcmpl-{hash(str(response_body))}"[:29]),
            "object": response_body.get("object", "chat.completion"),
            "created": response_body.get("created", int(intercepted_response.processing_time)),
            "model": response_body.get("model", "gpt-3.5-turbo"),
            "choices": response_body.get("choices", []),
            "usage": response_body.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
        # Ensure choices have proper structure
        for i, choice in enumerate(formatted_response["choices"]):
            if "message" not in choice and "text" in choice:
                # Convert completion format to chat format
                formatted_response["choices"][i] = {
                    "index": choice.get("index", i),
                    "message": {
                        "role": "assistant",
                        "content": choice["text"]
                    },
                    "finish_reason": choice.get("finish_reason", "stop")
                }
        
        return formatted_response
    
    def _format_data_response(self, response_body: Dict[str, Any], 
                            intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Format data response (embeddings, images) in OpenAI format"""
        
        return {
            "object": response_body.get("object", "list"),
            "data": response_body.get("data", []),
            "model": response_body.get("model", "text-embedding-ada-002"),
            "usage": response_body.get("usage", {})
        }
    
    def _format_audio_response(self, response_body: Dict[str, Any], 
                             intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Format audio response in OpenAI format"""
        
        return {
            "text": response_body.get("text", "")
        }
    
    def format_error(self, error_message: str, error_code: str = "internal_error", 
                    status_code: int = 500) -> Dict[str, Any]:
        """Format error response in OpenAI format"""
        
        # Map common error codes to OpenAI format
        openai_error_codes = {
            "invalid_request": "invalid_request_error",
            "authentication_failed": "invalid_request_error", 
            "rate_limit": "rate_limit_exceeded",
            "model_not_found": "model_not_found",
            "internal_error": "api_error"
        }
        
        openai_error_code = openai_error_codes.get(error_code, "api_error")
        
        return {
            "error": {
                "message": error_message,
                "type": openai_error_code,
                "param": None,
                "code": error_code
            }
        }
