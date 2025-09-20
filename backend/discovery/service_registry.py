"""
Service Registry - Automatic detection and configuration for popular AI services
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
from playwright.async_api import async_playwright
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    Automatically discovers and configures popular AI services
    """
    
    def __init__(self):
        self.known_services = {
            # Bolt.new
            "bolt.new": {
                "name": "bolt-web",
                "type": "web_chat",
                "priority": 65,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input, #message-input",
                    "send_button": "button[type='submit'], .send-button, button:contains('Send')",
                    "response": ".response, .ai-response, .message-content",
                    "new_chat": ".new-chat, button:contains('New')"
                },
                "login_required": False
            },
            
            # Google AI Studio
            "aistudio.google.com": {
                "name": "google-ai-studio",
                "type": "web_chat", 
                "priority": 75,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input",
                    "send_button": "button[aria-label*='Send'], button:contains('Send')",
                    "response": ".model-response, .ai-message",
                    "new_chat": "button:contains('New chat')"
                },
                "login_required": True
            },
            
            # Gemini
            "gemini.google.com": {
                "name": "gemini-web",
                "type": "web_chat",
                "priority": 75,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input",
                    "send_button": "button[aria-label*='Send'], button:contains('Send')",
                    "response": ".model-response, .response-content",
                    "new_chat": "button:contains('New chat')"
                },
                "login_required": True
            },
            
            # Mistral Chat
            "chat.mistral.ai": {
                "name": "mistral-web",
                "type": "web_chat",
                "priority": 70,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input",
                    "send_button": "button[type='submit'], .send-button",
                    "response": ".message-content, .ai-response",
                    "new_chat": "button:contains('New conversation')"
                },
                "login_required": True
            },
            
            # DeepSeek Chat
            "chat.deepseek.com": {
                "name": "deepseek-web",
                "type": "web_chat",
                "priority": 80,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], #chat-input",
                    "send_button": "button[type='submit'], .send-button",
                    "response": ".message-content, .ai-response",
                    "new_chat": ".new-chat-button"
                },
                "login_required": True
            },
            
            # Z.ai
            "z.ai": {
                "name": "zai-web",
                "type": "web_chat",
                "priority": 100,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input",
                    "send_button": "button[type='submit'], button:contains('Send')",
                    "response": ".message.assistant, .ai-message",
                    "new_chat": "button:contains('New Chat')"
                },
                "login_required": True
            },
            
            # Claude
            "claude.ai": {
                "name": "claude-web",
                "type": "web_chat",
                "priority": 85,
                "selectors": {
                    "chat_input": "textarea[placeholder*='message'], .chat-input",
                    "send_button": "button[aria-label*='Send'], button:contains('Send')",
                    "response": ".message-content, .claude-response",
                    "new_chat": "button:contains('New conversation')"
                },
                "login_required": True
            }
        }
    
    async def discover_service(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Automatically discover and configure a service from URL
        """
        try:
            domain = self._extract_domain(url)
            
            # Check if it's a known service
            if domain in self.known_services:
                return await self._create_config_from_template(url, domain)
            
            # Try to analyze unknown service
            return await self._analyze_unknown_service(url)
            
        except Exception as e:
            logger.error(f"Error discovering service from {url}: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url.lower()
    
    async def _create_config_from_template(self, url: str, domain: str) -> Dict[str, Any]:
        """
        Create configuration from known service template
        """
        template = self.known_services[domain]
        
        config = {
            "name": template["name"],
            "provider_type": template["type"],
            "base_url": url,
            "priority": template["priority"],
            "auto_discovered": True,
            "description": f"Auto-discovered {template['name']} service",
            "config": {
                "chat_input_selector": template["selectors"]["chat_input"],
                "send_button_selector": template["selectors"]["send_button"],
                "response_selector": template["selectors"]["response"],
                "new_chat_selector": template["selectors"]["new_chat"],
                "login_required": template.get("login_required", False),
                "browser_config": {
                    "headless": True,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "viewport": {"width": 1920, "height": 1080},
                    "timeout": 30000
                }
            }
        }
        
        # Add login URL if login is required
        if template.get("login_required", False):
            config["config"]["login_url"] = self._guess_login_url(url)
        
        return config
    
    async def _analyze_unknown_service(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Analyze unknown service using browser automation
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the page
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Analyze the page structure
                analysis = await self._analyze_page_structure(page)
                
                await browser.close()
                
                if analysis:
                    return self._create_config_from_analysis(url, analysis)
                
        except Exception as e:
            logger.error(f"Error analyzing unknown service {url}: {e}")
        
        return None
    
    async def _analyze_page_structure(self, page) -> Optional[Dict[str, Any]]:
        """
        Analyze page structure to identify chat interface elements
        """
        try:
            # Look for common chat interface patterns
            selectors = {
                "chat_input": [
                    "textarea[placeholder*='message']",
                    "textarea[placeholder*='Message']", 
                    "input[placeholder*='message']",
                    "textarea[placeholder*='type']",
                    ".chat-input",
                    "#chat-input",
                    "#message-input",
                    "textarea[name*='message']"
                ],
                "send_button": [
                    "button[type='submit']",
                    "button:has-text('Send')",
                    "button[aria-label*='Send']",
                    ".send-button",
                    "button:has-text('Submit')",
                    "button[data-testid*='send']"
                ],
                "response": [
                    ".message-content",
                    ".ai-response", 
                    ".response",
                    ".assistant-message",
                    ".bot-message",
                    "[data-role='assistant']",
                    ".ai-message"
                ],
                "new_chat": [
                    "button:has-text('New')",
                    "button:has-text('Clear')",
                    ".new-chat",
                    ".new-conversation",
                    "button[aria-label*='New']"
                ]
            }
            
            found_selectors = {}
            
            # Test each selector type
            for selector_type, candidates in selectors.items():
                for selector in candidates:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            found_selectors[selector_type] = selector
                            break
                    except:
                        continue
            
            # Must have at least input and send button to be considered a chat interface
            if "chat_input" in found_selectors and "send_button" in found_selectors:
                return {
                    "selectors": found_selectors,
                    "is_chat_interface": True,
                    "title": await page.title(),
                    "url": page.url
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
            return None
    
    def _create_config_from_analysis(self, url: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create endpoint configuration from page analysis
        """
        domain = self._extract_domain(url)
        selectors = analysis.get("selectors", {})
        
        # Generate endpoint name
        endpoint_name = f"{domain.split('.')[0]}-web"
        
        config = {
            "name": endpoint_name,
            "provider_type": "web_chat",
            "base_url": url,
            "priority": 50,  # Default priority for unknown services
            "auto_discovered": True,
            "description": f"Auto-discovered web chat interface: {analysis.get('title', domain)}",
            "config": {
                "chat_input_selector": selectors.get("chat_input", "textarea"),
                "send_button_selector": selectors.get("send_button", "button[type='submit']"),
                "response_selector": selectors.get("response", ".message-content"),
                "new_chat_selector": selectors.get("new_chat", "button:contains('New')"),
                "login_required": self._requires_login(url),
                "browser_config": {
                    "headless": True,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "viewport": {"width": 1920, "height": 1080},
                    "timeout": 30000
                }
            }
        }
        
        # Add login URL if needed
        if config["config"]["login_required"]:
            config["config"]["login_url"] = self._guess_login_url(url)
        
        return config
    
    def _requires_login(self, url: str) -> bool:
        """
        Guess if service requires login based on URL patterns
        """
        login_indicators = [
            "chat.openai.com",
            "claude.ai", 
            "chat.deepseek.com",
            "aistudio.google.com",
            "gemini.google.com",
            "chat.mistral.ai",
            "z.ai"
        ]
        
        return any(indicator in url.lower() for indicator in login_indicators)
    
    def _guess_login_url(self, url: str) -> str:
        """
        Guess login URL based on base URL
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Common login URL patterns
            login_paths = ["/login", "/auth/login", "/signin", "/auth"]
            
            # Try to guess based on known patterns
            domain = parsed.netloc.lower()
            if "openai.com" in domain:
                return f"{base_url}/auth/login"
            elif "claude.ai" in domain:
                return f"{base_url}/login"
            elif "deepseek.com" in domain:
                return f"{base_url}/login"
            elif "google.com" in domain:
                return f"{base_url}/login"
            elif "mistral.ai" in domain:
                return f"{base_url}/login"
            elif "z.ai" in domain:
                return f"{base_url}/login"
            else:
                return f"{base_url}/login"
                
        except:
            return f"{url}/login"
    
    def get_all_known_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all known service templates
        """
        return self.known_services.copy()
    
    def add_service_template(
        self, 
        domain: str, 
        name: str, 
        service_type: str,
        priority: int,
        selectors: Dict[str, str],
        login_required: bool = False
    ):
        """
        Add a new service template
        """
        self.known_services[domain] = {
            "name": name,
            "type": service_type,
            "priority": priority,
            "selectors": selectors,
            "login_required": login_required
        }
        
        logger.info(f"Added service template for {domain}: {name}")
    
    async def validate_service_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate that a service configuration works
        """
        try:
            # Basic validation - check required fields
            required_fields = ["name", "provider_type", "base_url", "config"]
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # For web chat, validate selectors
            if config["provider_type"] == "web_chat":
                required_selectors = ["chat_input_selector", "send_button_selector"]
                config_data = config.get("config", {})
                for selector in required_selectors:
                    if not config_data.get(selector):
                        logger.error(f"Missing required selector: {selector}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating service config: {e}")
            return False
