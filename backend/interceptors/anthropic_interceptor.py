"""
Anthropic API Interceptor
Handles interception of Anthropic Claude API calls
"""

from typing import Dict, Any, Optional, List, Tuple
from .base_interceptor import BaseInterceptor, APIFormat, InterceptedRequest, InterceptedResponse


class AnthropicInterceptor(BaseInterceptor):
    """
    Anthropic API Interceptor
    
    Handles Anthropic Claude API endpoints:
    - /v1/messages
    - /v1/complete (legacy)
    - /v1/models
    """
    
    def __init__(self):
        super().__init__(APIFormat.ANTHROPIC)
        
        # Anthropic endpoint patterns
        self.supported_endpoints = [
            "/v1/messages",
            "/v1/complete",
            "/v1/models"
        ]
        
        # Model name mappings
        self.model_mappings = {
            "claude-3-opus-20240229": "claude-3-opus",
            "claude-3-sonnet-20240229": "claude-3-sonnet", 
            "claude-3-haiku-20240307": "claude-3-haiku",
            "claude-2.1": "claude-2.1",
            "claude-2.0": "claude-2.0",
            "claude-instant-1.2": "claude-instant"
        }
    
    def get_supported_endpoints(self) -> List[str]:
        """Return list of supported Anthropic endpoint patterns"""
        return self.supported_endpoints
    
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate Anthropic API request"""
        if not isinstance(request_data, dict):
            return False, "Request body must be JSON object"
        
        # Check for required fields
        if "model" in request_data:
            model = request_data.get("model")
            if not model or not isinstance(model, str):
                return False, "Model field is required and must be a string"
        
        # Validate messages for new API format
        if "messages" in request_data:
            messages = request_data.get("messages")
            if not isinstance(messages, list) or len(messages) == 0:
                return False, "Messages must be a non-empty array"
            
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    return False, "Each message must have 'role' and 'content' fields"
                
                role = msg.get("role")
                if role not in ["user", "assistant"]:
                    return False, "Message role must be 'user' or 'assistant'"
        
        # Validate prompt for legacy API
        if "prompt" in request_data:
            prompt = request_data.get("prompt")
            if not prompt or not isinstance(prompt, str):
                return False, "Prompt must be a non-empty string"
        
        # Validate max_tokens
        max_tokens = request_data.get("max_tokens")
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                return False, "max_tokens must be a positive integer"
        
        return True, None
    
    def extract_auth_info(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract Anthropic API key from x-api-key header"""
        
        # Anthropic uses x-api-key header
        api_key = headers.get("x-api-key", "").strip()
        
        if not api_key:
            # Also check Authorization header as fallback
            auth_header = headers.get("Authorization", "").strip()
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:].strip()
        
        if api_key:
            return {
                "type": "api_key",
                "api_key": api_key,
                "anthropic_version": headers.get("anthropic-version", "2023-06-01")
            }
        
        return None
    
    def parse_request(self, endpoint: str, method: str, headers: Dict[str, str], 
                     body: Dict[str, Any], query_params: Dict[str, str]) -> InterceptedRequest:
        """Parse Anthropic API request into standardized format"""
        
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
        
        # Convert Anthropic messages format to standardized format if needed
        if "messages" in body:
            # Anthropic messages format is already close to standard
            intercepted_request.body["standardized_messages"] = body["messages"]
        elif "prompt" in body:
            # Convert legacy prompt format to messages format
            intercepted_request.body["standardized_messages"] = [
                {
                    "role": "user",
                    "content": body["prompt"]
                }
            ]
        
        # Add Anthropic-specific metadata
        intercepted_request.body["_anthropic_metadata"] = {
            "original_endpoint": endpoint,
            "anthropic_version": headers.get("anthropic-version", "2023-06-01"),
            "system": body.get("system"),
            "max_tokens": body.get("max_tokens", 1024),
            "temperature": body.get("temperature", 1.0),
            "top_p": body.get("top_p", 1.0),
            "top_k": body.get("top_k"),
            "stop_sequences": body.get("stop_sequences", []),
            "stream": body.get("stream", False)
        }
        
        return intercepted_request
    
    def format_response(self, intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Transform provider response back to Anthropic format"""
        
        response_body = intercepted_response.body
        
        # Handle different response types
        if "content" in response_body or "message" in response_body:
            # Messages API response
            return self._format_messages_response(response_body, intercepted_response)
        elif "completion" in response_body:
            # Legacy completion response
            return self._format_completion_response(response_body, intercepted_response)
        elif "choices" in response_body:
            # Convert OpenAI-style response to Anthropic format
            return self._convert_openai_to_anthropic(response_body, intercepted_response)
        else:
            # Generic response
            return response_body
    
    def _format_messages_response(self, response_body: Dict[str, Any], 
                                intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Format messages response in Anthropic format"""
        
        # Extract content from various possible formats
        content = response_body.get("content", "")
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                content = content[0]["text"]
            else:
                content = str(content[0])
        elif isinstance(content, dict) and "text" in content:
            content = content["text"]
        
        formatted_response = {
            "id": response_body.get("id", f"msg_{hash(str(response_body))}"[:29]),
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": str(content)
                }
            ],
            "model": response_body.get("model", "claude-3-sonnet"),
            "stop_reason": response_body.get("stop_reason", "end_turn"),
            "stop_sequence": response_body.get("stop_sequence"),
            "usage": {
                "input_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response_body.get("usage", {}).get("output_tokens", 0)
            }
        }
        
        return formatted_response
    
    def _format_completion_response(self, response_body: Dict[str, Any], 
                                  intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Format legacy completion response in Anthropic format"""
        
        return {
            "completion": response_body.get("completion", ""),
            "stop_reason": response_body.get("stop_reason", "stop_sequence"),
            "model": response_body.get("model", "claude-2"),
            "truncated": response_body.get("truncated", False),
            "stop": response_body.get("stop"),
            "log_id": response_body.get("log_id", f"log_{hash(str(response_body))}"[:29])
        }
    
    def _convert_openai_to_anthropic(self, response_body: Dict[str, Any], 
                                   intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Convert OpenAI-style response to Anthropic format"""
        
        choices = response_body.get("choices", [])
        if not choices:
            return self.format_error("No choices in response")
        
        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        return {
            "id": response_body.get("id", f"msg_{hash(str(response_body))}"[:29]),
            "type": "message", 
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ],
            "model": response_body.get("model", "claude-3-sonnet"),
            "stop_reason": "end_turn" if choice.get("finish_reason") == "stop" else "max_tokens",
            "stop_sequence": None,
            "usage": {
                "input_tokens": response_body.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": response_body.get("usage", {}).get("completion_tokens", 0)
            }
        }
    
    def format_error(self, error_message: str, error_code: str = "internal_error", 
                    status_code: int = 500) -> Dict[str, Any]:
        """Format error response in Anthropic format"""
        
        # Map common error codes to Anthropic format
        anthropic_error_types = {
            "invalid_request": "invalid_request_error",
            "authentication_failed": "authentication_error",
            "rate_limit": "rate_limit_error", 
            "model_not_found": "not_found_error",
            "internal_error": "api_error"
        }
        
        anthropic_error_type = anthropic_error_types.get(error_code, "api_error")
        
        return {
            "type": "error",
            "error": {
                "type": anthropic_error_type,
                "message": error_message
            }
        }
