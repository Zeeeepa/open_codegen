"""
Endpoint Manager for OpenAI Codegen Adapter

This module manages dynamic API endpoints, allowing users to create, test,
and manage custom endpoints that can route to any AI provider.
"""

import json
import uuid
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EndpointManager:
    """Manages dynamic API endpoints with AI-assisted generation"""
    
    def __init__(self, storage_path: str = "data/endpoints.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.endpoints = {}
        self._load_endpoints()
    
    def _load_endpoints(self):
        """Load endpoints from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    self.endpoints = json.load(f)
                logger.info(f"Loaded {len(self.endpoints)} endpoints from storage")
            else:
                self.endpoints = {}
        except Exception as e:
            logger.error(f"Failed to load endpoints: {e}")
            self.endpoints = {}
    
    def _save_endpoints(self):
        """Save endpoints to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.endpoints, f, indent=2, default=str)
            logger.info(f"Saved {len(self.endpoints)} endpoints to storage")
        except Exception as e:
            logger.error(f"Failed to save endpoints: {e}")
    
    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get all endpoints"""
        return list(self.endpoints.values())
    
    async def create_endpoint(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new endpoint"""
        try:
            endpoint_id = str(uuid.uuid4())
            endpoint = {
                "id": endpoint_id,
                "name": endpoint_data.get("name", ""),
                "description": endpoint_data.get("description", ""),
                "method": endpoint_data.get("method", "GET"),
                "url": endpoint_data.get("url", ""),
                "headers": endpoint_data.get("headers", {}),
                "body": endpoint_data.get("body", ""),
                "provider": endpoint_data.get("provider", "openai"),
                "variables": endpoint_data.get("variables", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "test_results": None,
            }
            
            self.endpoints[endpoint_id] = endpoint
            self._save_endpoints()
            
            logger.info(f"Created endpoint: {endpoint['name']} ({endpoint_id})")
            return endpoint
        except Exception as e:
            logger.error(f"Failed to create endpoint: {e}")
            raise
    
    async def update_endpoint(self, endpoint_id: str, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing endpoint"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints[endpoint_id]
            endpoint.update({
                "name": endpoint_data.get("name", endpoint["name"]),
                "description": endpoint_data.get("description", endpoint["description"]),
                "method": endpoint_data.get("method", endpoint["method"]),
                "url": endpoint_data.get("url", endpoint["url"]),
                "headers": endpoint_data.get("headers", endpoint["headers"]),
                "body": endpoint_data.get("body", endpoint["body"]),
                "provider": endpoint_data.get("provider", endpoint["provider"]),
                "variables": endpoint_data.get("variables", endpoint["variables"]),
                "updated_at": datetime.now().isoformat(),
            })
            
            self._save_endpoints()
            
            logger.info(f"Updated endpoint: {endpoint['name']} ({endpoint_id})")
            return endpoint
        except Exception as e:
            logger.error(f"Failed to update endpoint: {e}")
            raise
    
    async def delete_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """Delete an endpoint"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints.pop(endpoint_id)
            self._save_endpoints()
            
            logger.info(f"Deleted endpoint: {endpoint['name']} ({endpoint_id})")
            return {"status": "success", "message": "Endpoint deleted"}
        except Exception as e:
            logger.error(f"Failed to delete endpoint: {e}")
            raise
    
    async def test_endpoint(self, endpoint_id: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test an endpoint"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints[endpoint_id]
            
            # Prepare request
            url = endpoint["url"]
            method = endpoint["method"].upper()
            headers = endpoint.get("headers", {})
            body = endpoint.get("body", "")
            
            # Replace variables if provided
            if test_data:
                for key, value in test_data.items():
                    url = url.replace(f"{{{key}}}", str(value))
                    body = body.replace(f"{{{key}}}", str(value))
            
            # Parse body if it's JSON
            request_body = None
            if body:
                try:
                    request_body = json.loads(body)
                except json.JSONDecodeError:
                    request_body = body
            
            # Make request
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if isinstance(request_body, str) else None,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds() * 1000
                    
                    response_text = await response.text()
                    
                    # Try to parse as JSON
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        response_data = response_text
                    
                    test_result = {
                        "status_code": response.status,
                        "response_time_ms": response_time,
                        "headers": dict(response.headers),
                        "data": response_data,
                        "success": 200 <= response.status < 300,
                        "tested_at": start_time.isoformat(),
                    }
                    
                    # Save test result
                    endpoint["test_results"] = test_result
                    self._save_endpoints()
                    
                    logger.info(f"Tested endpoint {endpoint['name']}: {response.status} in {response_time:.2f}ms")
                    return test_result
                    
        except Exception as e:
            logger.error(f"Failed to test endpoint: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "tested_at": datetime.now().isoformat(),
            }
            
            # Save error result
            if endpoint_id in self.endpoints:
                self.endpoints[endpoint_id]["test_results"] = error_result
                self._save_endpoints()
            
            return error_result
    
    async def generate_endpoint_with_ai(self, prompt: str) -> Dict[str, Any]:
        """Generate an endpoint using AI based on natural language prompt"""
        try:
            # This is a simplified AI generation - in a real implementation,
            # you would use the Codegen client or another AI service
            
            # Parse common patterns from the prompt
            endpoint_data = self._parse_endpoint_from_prompt(prompt)
            
            logger.info(f"Generated endpoint from prompt: {prompt[:100]}...")
            return endpoint_data
        except Exception as e:
            logger.error(f"Failed to generate endpoint with AI: {e}")
            raise
    
    def _parse_endpoint_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse endpoint details from natural language prompt"""
        prompt_lower = prompt.lower()
        
        # Detect HTTP method
        method = "GET"
        if "post" in prompt_lower or "create" in prompt_lower or "send" in prompt_lower:
            method = "POST"
        elif "put" in prompt_lower or "update" in prompt_lower:
            method = "PUT"
        elif "delete" in prompt_lower or "remove" in prompt_lower:
            method = "DELETE"
        
        # Detect provider
        provider = "openai"
        if "anthropic" in prompt_lower or "claude" in prompt_lower:
            provider = "anthropic"
        elif "gemini" in prompt_lower or "google" in prompt_lower:
            provider = "gemini"
        elif "z.ai" in prompt_lower or "zai" in prompt_lower or "glm" in prompt_lower:
            provider = "zai"
        elif "codegen" in prompt_lower:
            provider = "codegen"
        
        # Generate basic endpoint structure
        endpoint_data = {
            "name": f"AI Generated Endpoint - {method}",
            "description": f"Generated from prompt: {prompt[:100]}...",
            "method": method,
            "url": self._generate_url_from_prompt(prompt, provider),
            "headers": self._generate_headers_from_prompt(prompt, provider),
            "body": self._generate_body_from_prompt(prompt, method, provider),
            "provider": provider,
            "variables": self._extract_variables_from_prompt(prompt),
        }
        
        return endpoint_data
    
    def _generate_url_from_prompt(self, prompt: str, provider: str) -> str:
        """Generate URL based on prompt and provider"""
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1",
            "zai": "https://open.zai.chat/v1",
            "codegen": "https://api.codegen.com/v1",
        }
        
        base_url = base_urls.get(provider, "https://api.example.com")
        
        # Detect endpoint type
        if "chat" in prompt.lower() or "message" in prompt.lower():
            return f"{base_url}/chat/completions"
        elif "completion" in prompt.lower():
            return f"{base_url}/completions"
        elif "embedding" in prompt.lower():
            return f"{base_url}/embeddings"
        else:
            return f"{base_url}/custom-endpoint"
    
    def _generate_headers_from_prompt(self, prompt: str, provider: str) -> Dict[str, str]:
        """Generate headers based on prompt and provider"""
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add provider-specific headers
        if provider == "openai":
            headers["Authorization"] = "Bearer {api_key}"
        elif provider == "anthropic":
            headers["x-api-key"] = "{api_key}"
            headers["anthropic-version"] = "2023-06-01"
        elif provider == "gemini":
            headers["Authorization"] = "Bearer {api_key}"
        elif provider == "zai":
            headers["Authorization"] = "Bearer {api_key}"
        
        return headers
    
    def _generate_body_from_prompt(self, prompt: str, method: str, provider: str) -> str:
        """Generate request body based on prompt, method, and provider"""
        if method == "GET":
            return ""
        
        # Generate basic chat completion body
        if "chat" in prompt.lower() or "message" in prompt.lower():
            body = {
                "model": self._get_default_model(provider),
                "messages": [
                    {"role": "user", "content": "{message}"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            if provider == "anthropic":
                body = {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "user", "content": "{message}"}
                    ]
                }
            
            return json.dumps(body, indent=2)
        
        return json.dumps({"data": "{input}"}, indent=2)
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        models = {
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229",
            "gemini": "gemini-pro",
            "zai": "glm-4.5",
            "codegen": "codegen-standard",
        }
        return models.get(provider, "default-model")
    
    def _extract_variables_from_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract variables from prompt"""
        variables = []
        
        # Common variables
        if "api" in prompt.lower() and "key" in prompt.lower():
            variables.append({
                "name": "api_key",
                "type": "string",
                "description": "API key for authentication",
                "required": True
            })
        
        if "message" in prompt.lower() or "text" in prompt.lower():
            variables.append({
                "name": "message",
                "type": "string",
                "description": "The message or text to process",
                "required": True
            })
        
        return variables


# Export main class
__all__ = ['EndpointManager']

