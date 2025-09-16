"""
Web Chat adapter for the Universal AI Endpoint Management System
Handles browser automation for web-based AI chat interfaces like Z.ai, DeepSeek, etc.
"""

import asyncio
import json
import logging
import random
import string
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .base_adapter import BaseAdapter, AdapterResponse, AdapterError

logger = logging.getLogger(__name__)

class WebChatAdapter(BaseAdapter):
    """Adapter for web-based chat interfaces using browser automation"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_config = provider_config.get('browser_config', {})
        self.login_url = provider_config.get('login_url')
        self.username = provider_config.get('username')
        self.password = provider_config.get('password')
        self.is_authenticated = False
        
    async def initialize(self) -> bool:
        """Initialize browser and authenticate if needed"""
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with configuration
            browser_args = self._get_browser_args()
            self.browser = await self.playwright.chromium.launch(**browser_args)
            
            # Create context with fingerprinting
            context_options = self._get_context_options()
            self.context = await self.browser.new_context(**context_options)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set up anti-detection measures
            await self._setup_anti_detection()
            
            # Authenticate if credentials provided
            if self.username and self.password:
                await self._authenticate()
            
            # Navigate to base URL
            await self.page.goto(self.provider_config.get('base_url', 'about:blank'))
            
            # Wait for chat interface to load
            await self._wait_for_chat_interface()
            
            self.is_initialized = True
            logger.info(f"Web chat adapter initialized for {self.provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize web chat adapter for {self.provider_name}: {e}")
            await self.cleanup()
            return False
    
    def _get_browser_args(self) -> Dict[str, Any]:
        """Get browser launch arguments"""
        args = {
            'headless': self.browser_config.get('headless', True),
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
                '--disable-javascript-harmony-shipping',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-ipc-flooding-protection',
                '--enable-features=NetworkService,NetworkServiceLogging',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--use-mock-keychain',
            ]
        }
        
        # Add proxy if configured
        proxy_config = self.browser_config.get('proxy')
        if proxy_config:
            args['proxy'] = proxy_config
            
        return args
    
    def _get_context_options(self) -> Dict[str, Any]:
        """Get browser context options with fingerprinting"""
        viewport = self.browser_config.get('viewport', {'width': 1920, 'height': 1080})
        user_agent = self.browser_config.get('user_agent', self._generate_user_agent())
        
        options = {
            'viewport': viewport,
            'user_agent': user_agent,
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation'],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        return options
    
    def _generate_user_agent(self) -> str:
        """Generate realistic user agent"""
        chrome_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0']
        chrome_version = random.choice(chrome_versions)
        
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    async def _setup_anti_detection(self):
        """Set up anti-detection measures"""
        # Override webdriver property
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # Override plugins
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        # Override languages
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        # Override permissions
        await self.page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    async def _authenticate(self) -> bool:
        """Authenticate with the web service"""
        try:
            if not self.login_url:
                logger.warning(f"No login URL provided for {self.provider_name}")
                return False
            
            # Navigate to login page
            await self.page.goto(self.login_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Provider-specific authentication
            if "z.ai" in self.login_url.lower():
                success = await self._authenticate_zai()
            else:
                success = await self._authenticate_generic()
            
            self.is_authenticated = success
            return success
            
        except Exception as e:
            logger.error(f"Authentication failed for {self.provider_name}: {e}")
            return False
    
    async def _authenticate_zai(self) -> bool:
        """Authenticate with Z.ai"""
        try:
            # Wait for login form
            await self.page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            
            # Fill email
            email_input = await self.page.query_selector('input[type="email"], input[name="email"]')
            if email_input:
                await email_input.fill(self.username)
            
            # Fill password
            password_input = await self.page.query_selector('input[type="password"], input[name="password"]')
            if password_input:
                await password_input.fill(self.password)
            
            # Click login button
            login_button = await self.page.query_selector('button[type="submit"], button:has-text("登录"), button:has-text("Login")')
            if login_button:
                await login_button.click()
            
            # Wait for redirect or success indicator
            await self.page.wait_for_load_state('networkidle')
            
            # Check if login was successful
            current_url = self.page.url
            if 'login' not in current_url.lower() or 'dashboard' in current_url.lower():
                logger.info("Z.ai authentication successful")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Z.ai authentication error: {e}")
            return False
    
    async def _authenticate_generic(self) -> bool:
        """Generic authentication for unknown providers"""
        try:
            # Try to find common login elements
            selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]'
            ]
            
            username_input = None
            for selector in selectors:
                username_input = await self.page.query_selector(selector)
                if username_input:
                    break
            
            if username_input:
                await username_input.fill(self.username)
            
            # Find password input
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(self.password)
            
            # Find and click submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("登录")'
            ]
            
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button:
                    await submit_button.click()
                    break
            
            await self.page.wait_for_load_state('networkidle')
            return True
            
        except Exception as e:
            logger.error(f"Generic authentication error: {e}")
            return False
    
    async def _wait_for_chat_interface(self):
        """Wait for chat interface to be ready"""
        try:
            # Common chat interface selectors
            chat_selectors = [
                '.chat-input',
                'textarea[placeholder*="message" i]',
                'input[placeholder*="message" i]',
                '[contenteditable="true"]',
                'textarea',
                '.message-input'
            ]
            
            for selector in chat_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Chat interface ready with selector: {selector}")
                    return
                except:
                    continue
            
            logger.warning("No chat interface found, proceeding anyway")
            
        except Exception as e:
            logger.error(f"Error waiting for chat interface: {e}")
    
    async def send_message(self, message: str, **kwargs) -> AdapterResponse:
        """Send message through web chat interface"""
        if not self.is_initialized:
            raise AdapterError("Adapter not initialized", "NOT_INITIALIZED")
        
        self.validate_request(message, **kwargs)
        
        session_id = kwargs.get('session_id')
        if session_id:
            self.update_session_activity(session_id)
            self.add_to_conversation_history(session_id, 'user', message)
        
        try:
            # Send message
            await self._send_message_to_interface(message)
            
            # Wait for and capture response
            response_content = await self._wait_for_response()
            
            # Add to conversation history
            if session_id:
                self.add_to_conversation_history(session_id, 'assistant', response_content)
            
            model = self.get_model_mapping(kwargs.get('model', 'default'))
            
            return self.create_response(
                content=response_content,
                model=model,
                session_id=session_id,
                metadata={'method': 'web_chat', 'url': self.page.url}
            )
            
        except Exception as e:
            logger.error(f"Error sending message through web chat: {e}")
            raise AdapterError(f"Web chat failed: {str(e)}", "WEB_CHAT_FAILED")
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response (simulated for web chat)"""
        # For web chat, we'll simulate streaming by yielding the complete response
        response = await self.send_message(message, **kwargs)
        
        # Simulate streaming by yielding chunks
        content = response.content
        chunk_size = 10
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.1)  # Simulate streaming delay
    
    async def _send_message_to_interface(self, message: str):
        """Send message to the web chat interface"""
        # Try different input methods
        input_selectors = [
            '.chat-input',
            'textarea[placeholder*="message" i]',
            'input[placeholder*="message" i]',
            '[contenteditable="true"]',
            'textarea:not([readonly])',
            '.message-input'
        ]
        
        input_element = None
        for selector in input_selectors:
            input_element = await self.page.query_selector(selector)
            if input_element:
                break
        
        if not input_element:
            raise AdapterError("No input element found", "NO_INPUT_ELEMENT")
        
        # Clear existing content and type message
        await input_element.click()
        await input_element.fill('')
        await input_element.type(message, delay=50)  # Human-like typing
        
        # Find and click send button
        send_selectors = [
            'button[type="submit"]',
            'button:has-text("Send")',
            'button:has-text("发送")',
            '.send-button',
            '[aria-label*="send" i]'
        ]
        
        send_button = None
        for selector in send_selectors:
            send_button = await self.page.query_selector(selector)
            if send_button:
                break
        
        if send_button:
            await send_button.click()
        else:
            # Try pressing Enter
            await input_element.press('Enter')
        
        # Wait a moment for message to be sent
        await asyncio.sleep(1)
    
    async def _wait_for_response(self, timeout: int = 30) -> str:
        """Wait for and capture the AI response"""
        start_time = asyncio.get_event_loop().time()
        
        # Common response selectors
        response_selectors = [
            '.message:last-child',
            '.chat-message:last-child',
            '.response:last-child',
            '.ai-message:last-child',
            '[data-role="assistant"]:last-child'
        ]
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Get the last message
                        last_element = elements[-1]
                        text_content = await last_element.text_content()
                        
                        if text_content and text_content.strip():
                            return text_content.strip()
                except:
                    continue
            
            await asyncio.sleep(0.5)
        
        # Fallback: try to get any new text content
        try:
            # Get all text content and try to extract the response
            page_content = await self.page.text_content('body')
            # This is a simplified approach - in practice, you'd need more sophisticated parsing
            return "Response captured from web interface"
        except:
            raise AdapterError("No response received within timeout", "RESPONSE_TIMEOUT")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check web chat adapter health"""
        try:
            if not self.page:
                return {'status': 'unhealthy', 'error': 'No page available'}
            
            # Check if page is responsive
            await self.page.evaluate('() => document.title')
            
            return {
                'status': 'healthy',
                'url': self.page.url,
                'authenticated': self.is_authenticated,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.is_initialized = False
            logger.info(f"Web chat adapter cleaned up for {self.provider_name}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
