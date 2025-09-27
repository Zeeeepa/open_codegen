"""
Gemini API Interceptor
Handles interception of Google Gemini API calls
"""

from typing import Dict, Any, Optional, List, Tuple
from .base_interceptor import BaseInterceptor, APIFormat, InterceptedRequest, InterceptedResponse


class GeminiInterceptor(BaseInterceptor):
    """
    Gemini API Interceptor
    
    Handles Google Gemini API endpoints:
    - /v1/models/{model}:generateContent
    - /v1/models/{model}:streamGenerateContent
    - /v1/models/{model}:embedContent
    - /v1/models
    """
    
    def __init__(self):
        super().__init__(APIFormat.GEMINI)
        
        # Gemini endpoint patterns
        self.supported_endpoints = [
            "/v1/models/",
            "/v1beta/models/",
            ":generateContent",
            ":streamGenerateContent", 
            ":embedContent",
            "/v1/models",
            "/v1beta/models"
        ]
        
        # Model name mappings
        self.model_mappings = {
            "gemini-pro": "gemini-1.0-pro",
            "gemini-pro-vision": "gemini-1.0-pro-vision",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "text-embedding-004": "text-embedding-004"
        }
    
    def get_supported_endpoints(self) -> List[str]:
        """Return list of supported Gemini endpoint patterns"""
        return self.supported_endpoints
    
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate Gemini API request"""
        if not isinstance(request_data, dict):
            return False, "Request body must be JSON object"
        
        # Validate contents for generateContent
        if "contents" in request_data:
            contents = request_data.get("contents")
            if not isinstance(contents, list) or len(contents) == 0:
                return False, "Contents must be a non-empty array"
            
            for content in contents:
                if not isinstance(content, dict):
                    return False, "Each content must be an object"
                
                if "parts" not in content:
                    return False, "Each content must have 'parts' field"
                
                parts = content.get("parts")
                if not isinstance(parts, list) or len(parts) == 0:
                    return False, "Parts must be a non-empty array"
        
        # Validate text for embedContent
        if "content" in request_data and "parts" in request_data["content"]:
            content = request_data["content"]
            if not isinstance(content, dict):
                return False, "Content must be an object"
        
        # Validate generation config
        generation_config = request_data.get("generationConfig")
        if generation_config is not None:
            if not isinstance(generation_config, dict):
                return False, "generationConfig must be an object"
        
        return True, None
    
    def extract_auth_info(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract Gemini API key from query params or headers"""
        
        # Gemini typically uses API key in query params, but also check headers
        api_key = None
        
        # Check Authorization header
        auth_header = headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:].strip()
        
        # Check x-goog-api-key header
        if not api_key:
            api_key = headers.get("x-goog-api-key", "").strip()
        
        if api_key:
            return {
                "type": "api_key",
                "api_key": api_key,
                "project_id": headers.get("x-goog-user-project")
            }
        
        return None
    
    def parse_request(self, endpoint: str, method: str, headers: Dict[str, str], 
                     body: Dict[str, Any], query_params: Dict[str, str]) -> InterceptedRequest:
        """Parse Gemini API request into standardized format"""
        
        # Create intercepted request
        intercepted_request = InterceptedRequest(
            api_format=self.api_format,
            endpoint=endpoint,
            method=method,
            headers=headers,
            body=body,
            query_params=query_params
        )
        
        # Extract model name from endpoint
        model_name = self._extract_model_from_endpoint(endpoint)
        if model_name:
            intercepted_request.body["model"] = model_name
            intercepted_request.body["normalized_model"] = self.model_mappings.get(model_name, model_name)
        
        # Convert Gemini contents format to standardized messages format
        if "contents" in body:
            standardized_messages = self._convert_contents_to_messages(body["contents"])
            intercepted_request.body["standardized_messages"] = standardized_messages
        
        # Add Gemini-specific metadata
        intercepted_request.body["_gemini_metadata"] = {
            "original_endpoint": endpoint,
            "generation_config": body.get("generationConfig", {}),
            "safety_settings": body.get("safetySettings", []),
            "tools": body.get("tools", []),
            "tool_config": body.get("toolConfig", {}),
            "system_instruction": body.get("systemInstruction"),
            "project_id": headers.get("x-goog-user-project")
        }
        
        return intercepted_request
    
    def _extract_model_from_endpoint(self, endpoint: str) -> Optional[str]:
        """Extract model name from Gemini endpoint"""
        
        # Pattern: /v1/models/{model}:generateContent
        if "/models/" in endpoint:
            parts = endpoint.split("/models/")
            if len(parts) > 1:
                model_part = parts[1].split(":")[0]
                return model_part
        
        return None
    
    def _convert_contents_to_messages(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Gemini contents format to standardized messages format"""
        
        messages = []
        
        for content in contents:
            role = content.get("role", "user")
            parts = content.get("parts", [])
            
            # Convert Gemini role to standard role
            if role == "model":
                role = "assistant"
            
            # Combine all text parts into a single message
            text_content = ""
            for part in parts:
                if "text" in part:
                    text_content += part["text"]
                elif "inlineData" in part:
                    # Handle inline data (images, etc.)
                    text_content += f"[Image: {part['inlineData'].get('mimeType', 'unknown')}]"
                elif "fileData" in part:
                    # Handle file data
                    text_content += f"[File: {part['fileData'].get('mimeType', 'unknown')}]"
            
            if text_content:
                messages.append({
                    "role": role,
                    "content": text_content
                })
        
        return messages
    
    def format_response(self, intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Transform provider response back to Gemini format"""
        
        response_body = intercepted_response.body
        
        # Handle different response types
        if "candidates" in response_body:
            # Already in Gemini format
            return response_body
        elif "choices" in response_body:
            # Convert OpenAI-style response to Gemini format
            return self._convert_openai_to_gemini(response_body, intercepted_response)
        elif "content" in response_body or "message" in response_body:
            # Convert Anthropic-style response to Gemini format
            return self._convert_anthropic_to_gemini(response_body, intercepted_response)
        else:
            # Try to create a basic Gemini response
            return self._create_basic_gemini_response(response_body, intercepted_response)
    
    def _convert_openai_to_gemini(self, response_body: Dict[str, Any], 
                                intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Convert OpenAI-style response to Gemini format"""
        
        choices = response_body.get("choices", [])
        if not choices:
            return self.format_error("No choices in response")
        
        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": content
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": self._map_finish_reason(choice.get("finish_reason", "STOP")),
                    "index": choice.get("index", 0),
                    "safetyRatings": []
                }
            ],
            "usageMetadata": {
                "promptTokenCount": response_body.get("usage", {}).get("prompt_tokens", 0),
                "candidatesTokenCount": response_body.get("usage", {}).get("completion_tokens", 0),
                "totalTokenCount": response_body.get("usage", {}).get("total_tokens", 0)
            }
        }
    
    def _convert_anthropic_to_gemini(self, response_body: Dict[str, Any], 
                                   intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Convert Anthropic-style response to Gemini format"""
        
        content = response_body.get("content", [])
        text_content = ""
        
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                text_content = content[0]["text"]
            else:
                text_content = str(content[0])
        elif isinstance(content, str):
            text_content = content
        
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": text_content
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": self._map_anthropic_stop_reason(response_body.get("stop_reason", "end_turn")),
                    "index": 0,
                    "safetyRatings": []
                }
            ],
            "usageMetadata": {
                "promptTokenCount": response_body.get("usage", {}).get("input_tokens", 0),
                "candidatesTokenCount": response_body.get("usage", {}).get("output_tokens", 0),
                "totalTokenCount": response_body.get("usage", {}).get("input_tokens", 0) + response_body.get("usage", {}).get("output_tokens", 0)
            }
        }
    
    def _create_basic_gemini_response(self, response_body: Dict[str, Any], 
                                    intercepted_response: InterceptedResponse) -> Dict[str, Any]:
        """Create a basic Gemini response from generic response"""
        
        # Try to extract text content from various possible fields
        text_content = ""
        if "text" in response_body:
            text_content = response_body["text"]
        elif "completion" in response_body:
            text_content = response_body["completion"]
        elif "response" in response_body:
            text_content = str(response_body["response"])
        else:
            text_content = str(response_body)
        
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": text_content
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0,
                    "safetyRatings": []
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 0,
                "candidatesTokenCount": 0,
                "totalTokenCount": 0
            }
        }
    
    def _map_finish_reason(self, openai_finish_reason: str) -> str:
        """Map OpenAI finish reason to Gemini finish reason"""
        
        mapping = {
            "stop": "STOP",
            "length": "MAX_TOKENS",
            "content_filter": "SAFETY",
            "function_call": "STOP",
            "tool_calls": "STOP"
        }
        
        return mapping.get(openai_finish_reason.lower(), "STOP")
    
    def _map_anthropic_stop_reason(self, anthropic_stop_reason: str) -> str:
        """Map Anthropic stop reason to Gemini finish reason"""
        
        mapping = {
            "end_turn": "STOP",
            "max_tokens": "MAX_TOKENS",
            "stop_sequence": "STOP"
        }
        
        return mapping.get(anthropic_stop_reason, "STOP")
    
    def format_error(self, error_message: str, error_code: str = "internal_error", 
                    status_code: int = 500) -> Dict[str, Any]:
        """Format error response in Gemini format"""
        
        # Map common error codes to Gemini format
        gemini_error_codes = {
            "invalid_request": "INVALID_ARGUMENT",
            "authentication_failed": "UNAUTHENTICATED",
            "rate_limit": "RESOURCE_EXHAUSTED",
            "model_not_found": "NOT_FOUND",
            "internal_error": "INTERNAL"
        }
        
        gemini_error_code = gemini_error_codes.get(error_code, "INTERNAL")
        
        return {
            "error": {
                "code": status_code,
                "message": error_message,
                "status": gemini_error_code
            }
        }
