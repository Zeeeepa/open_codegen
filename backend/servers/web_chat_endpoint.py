"""
Web Chat Endpoint Server
Handles web-based chat interfaces using browser automation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import json
import time
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from .base_endpoint import BaseEndpoint, EndpointStatus, EndpointHealth

logger = logging.getLogger(__name__)

class WebChatEndpoint(BaseEndpoint):
    """Web chat endpoint using browser automation"""
    
    def __init__(self, name: str, config: Dict[str, Any], priority: int = 50):
        super().__init__(name, config, priority)
        
        # Web chat specific configuration
        self.login_url = config.get('login_url', self.url)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.chat_input_selector = config.get('chat_input_selector', 'textarea, input[type="text"]')
        self.send_button_selector = config.get('send_button_selector', 'button[type="submit"], button:contains("Send")')
        self.response_selector = config.get('response_selector', '.message, .response, .chat-message')
        self.new_chat_selector = config.get('new_chat_selector', 'button:contains("New"), button:contains("Clear")')
        
        # Browser configuration
        self.browser_config = config.get('browser_config', {})
        self.headless = self.browser_config.get('headless', True)
        self.user_agent = self.browser_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.viewport = self.browser_config.get('viewport', {'width': 1920, 'height': 1080})
        
        # Session management
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # State tracking
        self.is_logged_in = False
        self.last_response_count = 0
        
    async def start(self) -> bool:
        """Start the web chat endpoint"""
        try:
            self.update_status(EndpointStatus.STARTING)
            logger.info(f"Starting web chat endpoint: {self.name}")
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Create browser context with fingerprinting
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set up page event handlers
            self.page.on('console', self._handle_console_message)
            self.page.on('pageerror', self._handle_page_error)
            
            # Navigate to login URL and attempt login
            await self._navigate_and_login()
            
            self._running = True
            self.update_status(EndpointStatus.RUNNING)
            self.update_health(EndpointHealth.HEALTHY)
            
            logger.info(f"Web chat endpoint started successfully: {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start web chat endpoint {self.name}: {e}")
            self.update_status(EndpointStatus.ERROR)
            self.update_health(EndpointHealth.UNHEALTHY)
            await self._cleanup()
            return False
    
    async def stop(self) -> bool:
        """Stop the web chat endpoint"""
        try:
            self.update_status(EndpointStatus.STOPPING)
            logger.info(f"Stopping web chat endpoint: {self.name}")
            
            await self._cleanup()
            
            self._running = False
            self.is_logged_in = False
            self.update_status(EndpointStatus.STOPPED)
            self.update_health(EndpointHealth.UNKNOWN)
            
            logger.info(f"Web chat endpoint stopped: {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop web chat endpoint {self.name}: {e}")
            self.update_status(EndpointStatus.ERROR)
            return False
    
    async def send_message(self, message: str, **kwargs) -> Optional[str]:
        """Send a message to the web chat interface"""
        if not self._running or not self.page:
            raise Exception("Endpoint not running")
        
        try:
            # Ensure we're logged in
            if not self.is_logged_in:
                await self._navigate_and_login()
            
            # Find and fill the chat input
            await self.page.wait_for_selector(self.chat_input_selector, timeout=10000)
            chat_input = self.page.locator(self.chat_input_selector).first
            
            # Clear existing text and type new message
            await chat_input.clear()
            await chat_input.fill(message)
            
            # Get current response count before sending
            current_responses = await self._count_responses()
            
            # Send the message
            send_button = self.page.locator(self.send_button_selector).first
            await send_button.click()
            
            # Wait for new response
            response = await self._wait_for_response(current_responses)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send message to {self.name}: {e}")
            # Try to recover by refreshing the page
            await self._recover_session()
            raise
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response from web chat"""
        if not self._running or not self.page:
            raise Exception("Endpoint not running")
        
        try:
            # Send message and get initial response
            response = await self.send_message(message, **kwargs)
            
            if response:
                # Simulate streaming by yielding words with delays
                words = response.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield word
                    else:
                        yield f" {word}"
                    await asyncio.sleep(0.05)  # Slightly longer delay for web chat
                    
        except Exception as e:
            logger.error(f"Failed to stream message from {self.name}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Perform health check on the web chat endpoint"""
        try:
            if not self._running or not self.page:
                return False
            
            # Check if page is responsive
            await self.page.evaluate('document.title')
            
            # Check if we can find the chat input
            chat_input = self.page.locator(self.chat_input_selector).first
            is_visible = await chat_input.is_visible()
            
            return is_visible
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return False
    
    async def _navigate_and_login(self):
        """Navigate to the chat interface and login if needed"""
        try:
            logger.info(f"Navigating to {self.login_url}")
            await self.page.goto(self.login_url, wait_until='networkidle')
            
            # Wait a moment for the page to fully load
            await asyncio.sleep(2)
            
            # Check if login is required
            if self.username and self.password:
                await self._perform_login()
            
            # Wait for chat interface to be ready
            await self.page.wait_for_selector(self.chat_input_selector, timeout=15000)
            
            self.is_logged_in = True
            logger.info(f"Successfully navigated and logged in to {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to navigate and login to {self.name}: {e}")
            raise
    
    async def _perform_login(self):
        """Perform login if credentials are provided"""
        try:
            # Common login selectors
            username_selectors = [
                'input[type="email"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]'
            ]
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]'
            ]
            
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'input[type="submit"]'
            ]
            
            # Find and fill username
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = self.page.locator(selector).first
                    if await username_input.is_visible():
                        break
                except:
                    continue
            
            if username_input:
                await username_input.fill(self.username)
                logger.info(f"Filled username for {self.name}")
            
            # Find and fill password
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.page.locator(selector).first
                    if await password_input.is_visible():
                        break
                except:
                    continue
            
            if password_input:
                await password_input.fill(self.password)
                logger.info(f"Filled password for {self.name}")
            
            # Find and click login button
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.page.locator(selector).first
                    if await login_button.is_visible():
                        break
                except:
                    continue
            
            if login_button:
                await login_button.click()
                logger.info(f"Clicked login button for {self.name}")
                
                # Wait for navigation or chat interface
                await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Login failed for {self.name}: {e}")
            raise
    
    async def _count_responses(self) -> int:
        """Count current number of responses on the page"""
        try:
            responses = self.page.locator(self.response_selector)
            count = await responses.count()
            return count
        except:
            return 0
    
    async def _wait_for_response(self, previous_count: int, timeout: int = 30) -> Optional[str]:
        """Wait for a new response to appear"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_count = await self._count_responses()
                
                if current_count > previous_count:
                    # Get the latest response
                    responses = self.page.locator(self.response_selector)
                    latest_response = responses.nth(current_count - 1)
                    
                    # Wait for the response to be fully loaded
                    await asyncio.sleep(1)
                    
                    response_text = await latest_response.inner_text()
                    return response_text.strip()
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error waiting for response: {e}")
                await asyncio.sleep(1)
        
        logger.warning(f"Timeout waiting for response from {self.name}")
        return None
    
    async def _recover_session(self):
        """Attempt to recover the session by refreshing the page"""
        try:
            logger.info(f"Attempting to recover session for {self.name}")
            
            if self.page:
                await self.page.reload(wait_until='networkidle')
                await asyncio.sleep(2)
                
                # Check if we need to login again
                if self.username and self.password:
                    try:
                        await self.page.wait_for_selector(self.chat_input_selector, timeout=5000)
                        self.is_logged_in = True
                    except:
                        await self._perform_login()
                
                logger.info(f"Session recovered for {self.name}")
                
        except Exception as e:
            logger.error(f"Failed to recover session for {self.name}: {e}")
            self.is_logged_in = False
    
    async def _cleanup(self):
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
                
        except Exception as e:
            logger.error(f"Error during cleanup for {self.name}: {e}")
    
    def _handle_console_message(self, msg):
        """Handle browser console messages"""
        if msg.type == 'error':
            logger.warning(f"Browser console error in {self.name}: {msg.text}")
    
    def _handle_page_error(self, error):
        """Handle page errors"""
        logger.error(f"Page error in {self.name}: {error}")
    
    async def new_chat(self):
        """Start a new chat session"""
        try:
            if not self._running or not self.page:
                return False
            
            # Try to find and click new chat button
            try:
                new_chat_button = self.page.locator(self.new_chat_selector).first
                if await new_chat_button.is_visible():
                    await new_chat_button.click()
                    await asyncio.sleep(1)
                    return True
            except:
                pass
            
            # Fallback: refresh the page
            await self.page.reload(wait_until='networkidle')
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start new chat for {self.name}: {e}")
            return False
