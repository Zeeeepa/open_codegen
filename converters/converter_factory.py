"""Converter Factory - Creates format converters"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseConverter:
    def to_webchat(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API format to WebChat format."""
        message = ""
        if "messages" in request_data:
            # OpenAI/Anthropic format
            messages = request_data["messages"]
            if messages and isinstance(messages, list):
                message = messages[-1].get("content", "")
        elif "contents" in request_data:
            # Gemini format
            contents = request_data["contents"]
            if contents and isinstance(contents, list):
                parts = contents[0].get("parts", [])
                if parts:
                    message = parts[0].get("text", "")
        
        return {
            "message": message,
            "metadata": {"original_format": "unknown", "model": request_data.get("model", "")},
            "format": "webchat"
        }
    
    def from_webchat(self, webchat_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert WebChat format back to API format."""
        return {
            "choices": [{
                "message": {"role": "assistant", "content": webchat_response.get("content", "")},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    
    def stream_chunk_from_webchat(self, chunk: str, api_format: str) -> str:
        return f"data: {chunk}\n\n"
    
    def create_error_chunk(self, error: str, api_format: str) -> str:
        return f"data: [ERROR] {error}\n\n"

class ConverterFactory:
    def __init__(self):
        self.converter = BaseConverter()
    
    def get_converter(self, api_format: str):
        return self.converter
