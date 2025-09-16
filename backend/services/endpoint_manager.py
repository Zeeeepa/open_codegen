"""
Endpoint management service with AI-assisted creation and testing
"""
import uuid
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re

from ..database import db_manager, EndpointConfig

logger = logging.getLogger(__name__)

class EndpointManager:
    """Manages custom API endpoints with AI assistance"""
    
    def __init__(self):
        self.driver = None
        self.session = None
        
    async def initialize(self):
        """Initialize the endpoint manager"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
            
    def _setup_headless_browser(self):
        """Setup headless Chrome browser"""
        if self.driver:
            return self.driver
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to setup headless browser: {e}")
            return None
    
    async def create_endpoint_from_description(self, description: str, user_id: str) -> Optional[EndpointConfig]:
        """Create an endpoint configuration from natural language description using AI"""
        try:
            # This would integrate with your AI service (OpenAI, Anthropic, etc.)
            # For now, we'll create a basic endpoint structure
            
            endpoint_id = str(uuid.uuid4())
            
            # Parse description for key information
            name = self._extract_name_from_description(description)
            url = self._extract_url_from_description(description)
            method = self._extract_method_from_description(description)
            
            endpoint = EndpointConfig(
                id=endpoint_id,
                name=name,
                url=url,
                method=method,
                user_id=user_id,
                variables=self._extract_variables_from_description(description)
            )
            
            # Save to database
            success = await db_manager.create_endpoint(endpoint)
            if success:
                logger.info(f"Created endpoint from description: {name}")
                return endpoint
            else:
                logger.error("Failed to save endpoint to database")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create endpoint from description: {e}")
            return None
    
    def _extract_name_from_description(self, description: str) -> str:
        """Extract endpoint name from description"""
        # Simple extraction - in production, use AI
        words = description.split()
        if "api" in description.lower():
            return f"Custom API - {' '.join(words[:3])}"
        return f"Endpoint - {' '.join(words[:3])}"
    
    def _extract_url_from_description(self, description: str) -> str:
        """Extract URL from description"""
        # Look for URLs in the description
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, description)
        return urls[0] if urls else "https://example.com/api"
    
    def _extract_method_from_description(self, description: str) -> str:
        """Extract HTTP method from description"""
        description_lower = description.lower()
        if "get" in description_lower:
            return "GET"
        elif "put" in description_lower:
            return "PUT"
        elif "delete" in description_lower:
            return "DELETE"
        return "POST"  # Default
    
    def _extract_variables_from_description(self, description: str) -> Dict[str, Any]:
        """Extract variables from description"""
        variables = {}
        
        # Look for common variable patterns
        if "api key" in description.lower() or "token" in description.lower():
            variables["api_key"] = {"type": "string", "required": True, "description": "API key for authentication"}
        
        if "model" in description.lower():
            variables["model"] = {"type": "string", "required": False, "default": "gpt-3.5-turbo", "description": "Model to use"}
        
        if "temperature" in description.lower():
            variables["temperature"] = {"type": "number", "required": False, "default": 0.7, "description": "Temperature for response generation"}
        
        return variables
    
    async def discover_website_endpoints(self, url: str) -> List[Dict[str, Any]]:
        """Discover API endpoints from a website"""
        try:
            driver = self._setup_headless_browser()
            if not driver:
                return []
            
            driver.get(url)
            await asyncio.sleep(2)  # Wait for page load
            
            # Look for API documentation patterns
            endpoints = []
            
            # Check for OpenAPI/Swagger documentation
            swagger_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'swagger') or contains(text(), 'openapi')]")
            if swagger_elements:
                endpoints.extend(await self._parse_swagger_docs(driver))
            
            # Look for API endpoint patterns in the page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find code blocks that might contain API endpoints
            code_blocks = soup.find_all(['code', 'pre'])
            for block in code_blocks:
                text = block.get_text()
                if self._looks_like_api_endpoint(text):
                    endpoint_info = self._parse_endpoint_from_text(text)
                    if endpoint_info:
                        endpoints.append(endpoint_info)
            
            return endpoints
            
        except Exception as e:
            logger.error(f"Failed to discover website endpoints: {e}")
            return []
    
    def _looks_like_api_endpoint(self, text: str) -> bool:
        """Check if text looks like an API endpoint"""
        api_patterns = [
            r'https?://[^\s]+/api/',
            r'POST|GET|PUT|DELETE\s+/',
            r'curl\s+-X',
            r'fetch\(',
            r'axios\.',
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _parse_endpoint_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse endpoint information from text"""
        try:
            # Extract URL
            url_match = re.search(r'https?://[^\s]+', text)
            if not url_match:
                return None
            
            url = url_match.group()
            
            # Extract method
            method_match = re.search(r'(POST|GET|PUT|DELETE)', text, re.IGNORECASE)
            method = method_match.group().upper() if method_match else "POST"
            
            return {
                "url": url,
                "method": method,
                "description": text[:200] + "..." if len(text) > 200 else text
            }
            
        except Exception as e:
            logger.error(f"Failed to parse endpoint from text: {e}")
            return None
    
    async def _parse_swagger_docs(self, driver) -> List[Dict[str, Any]]:
        """Parse Swagger/OpenAPI documentation"""
        endpoints = []
        try:
            # Look for Swagger UI elements
            swagger_elements = driver.find_elements(By.CLASS_NAME, "opblock")
            
            for element in swagger_elements:
                try:
                    method_element = element.find_element(By.CLASS_NAME, "opblock-summary-method")
                    path_element = element.find_element(By.CLASS_NAME, "opblock-summary-path")
                    
                    method = method_element.text.strip()
                    path = path_element.text.strip()
                    
                    endpoints.append({
                        "method": method,
                        "path": path,
                        "url": driver.current_url.split('/docs')[0] + path,
                        "source": "swagger"
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse swagger element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to parse swagger docs: {e}")
        
        return endpoints
    
    async def test_endpoint(self, endpoint: EndpointConfig, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test an endpoint configuration"""
        try:
            if not self.session:
                await self.initialize()
            
            # Prepare test data
            if test_data is None:
                test_data = {"message": "Hello, this is a test message"}
            
            # Prepare headers
            headers = endpoint.headers.copy()
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            
            # Make request
            start_time = datetime.utcnow()
            
            if endpoint.method.upper() == "GET":
                async with self.session.get(endpoint.url, headers=headers) as response:
                    response_data = await response.text()
                    status_code = response.status
            else:
                async with self.session.request(
                    endpoint.method.upper(),
                    endpoint.url,
                    headers=headers,
                    json=test_data
                ) as response:
                    response_data = await response.text()
                    status_code = response.status
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Try to parse as JSON
            try:
                response_json = json.loads(response_data)
            except:
                response_json = None
            
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "response_time": response_time,
                "response_data": response_data,
                "response_json": response_json,
                "error": None if 200 <= status_code < 300 else f"HTTP {status_code}"
            }
            
        except Exception as e:
            logger.error(f"Failed to test endpoint: {e}")
            return {
                "success": False,
                "status_code": 0,
                "response_time": 0,
                "response_data": None,
                "response_json": None,
                "error": str(e)
            }
    
    async def test_web_interface(self, endpoint: EndpointConfig, message: str) -> Dict[str, Any]:
        """Test web interface interaction using headless browser"""
        try:
            driver = self._setup_headless_browser()
            if not driver:
                return {"success": False, "error": "Failed to setup browser"}
            
            # Navigate to the URL
            driver.get(endpoint.url)
            await asyncio.sleep(3)  # Wait for page load
            
            # Find text input element
            text_input = None
            if endpoint.text_input_selector:
                try:
                    text_input = driver.find_element(By.CSS_SELECTOR, endpoint.text_input_selector)
                except:
                    pass
            
            # Fallback selectors for common input patterns
            if not text_input:
                selectors = [
                    'input[type="text"]',
                    'textarea',
                    'input[placeholder*="message"]',
                    'input[placeholder*="prompt"]',
                    '.input-field',
                    '#message-input',
                    '#prompt-input'
                ]
                
                for selector in selectors:
                    try:
                        text_input = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
            
            if not text_input:
                return {"success": False, "error": "Could not find text input element"}
            
            # Enter the message
            text_input.clear()
            text_input.send_keys(message)
            
            # Find and click send button
            send_button = None
            if endpoint.send_button_selector:
                try:
                    send_button = driver.find_element(By.CSS_SELECTOR, endpoint.send_button_selector)
                except:
                    pass
            
            # Fallback selectors for send buttons
            if not send_button:
                selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:contains("Send")',
                    'button:contains("Submit")',
                    '.send-button',
                    '#send-button'
                ]
                
                for selector in selectors:
                    try:
                        send_button = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
            
            if not send_button:
                return {"success": False, "error": "Could not find send button"}
            
            # Click send button
            send_button.click()
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Extract response
            response_text = ""
            if endpoint.response_selector:
                try:
                    response_element = driver.find_element(By.CSS_SELECTOR, endpoint.response_selector)
                    response_text = response_element.text
                except:
                    pass
            
            # Fallback response extraction
            if not response_text:
                # Look for common response patterns
                selectors = [
                    '.response',
                    '.message',
                    '.output',
                    '.result',
                    '[role="assistant"]',
                    '.assistant-message'
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            response_text = elements[-1].text  # Get the last (most recent) response
                            break
                    except:
                        continue
            
            return {
                "success": True,
                "response": response_text,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to test web interface: {e}")
            return {"success": False, "error": str(e)}
    
    async def convert_to_openai_format(self, response_data: str, endpoint: EndpointConfig) -> Dict[str, Any]:
        """Convert response to OpenAI-compatible format"""
        try:
            # Basic OpenAI format structure
            openai_response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(datetime.utcnow().timestamp()),
                "model": endpoint.model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_data
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            return openai_response
            
        except Exception as e:
            logger.error(f"Failed to convert to OpenAI format: {e}")
            return {
                "error": {
                    "message": f"Failed to convert response: {str(e)}",
                    "type": "conversion_error"
                }
            }

# Global endpoint manager instance
endpoint_manager = EndpointManager()
