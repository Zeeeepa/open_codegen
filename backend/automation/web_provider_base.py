"""
Web Provider Base Class
Base class for web automation providers with common functionality
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from abc import abstractmethod

from ..providers.base_provider import BaseProvider, ProviderType, ProviderStatus, ProviderResponse, ProviderContext
from .stealth_browser import StealthBrowser

logger = logging.getLogger(__name__)

class WebProviderBase(BaseProvider):
    """Base class for web automation providers"""
    
    def __init__(self, name: str, provider_type: ProviderType, config: Dict[str, Any] = None):
        super().__init__(name, provider_type, config)
        
        self.browser: Optional[StealthBrowser] = None
        self.base_url: str = config.get('base_url', '')
        self.login_required: bool = config.get('login_required', True)
        self.session_timeout: int = config.get('session_timeout', 3600)  # 1 hour
        self.last_activity: Optional[float] = None
        
        # UI selectors - to be defined by subclasses
        self.selectors = {
            'login_username': '',
            'login_password': '',
            'login_button': '',
            'chat_input': '',
            'send_button': '',
            'response_area': '',
            'new_chat_button': '',
            'send_button_disabled': '',
            'send_button_loading': ''
        }
        
        # Update selectors from config
        if 'selectors' in config:
            self.selectors.update(config['selectors'])
    
    async def initialize(self, context: ProviderContext) -> bool:
        """Initialize the web provider with authentication context"""
        try:
            if not self._validate_context(context):
                await self.set_status(ProviderStatus.ERROR, "Invalid context provided")
                return False
            
            self.context = context
            await self.set_status(ProviderStatus.INITIALIZING)
            
            # Create stealth browser
            browser_config = {
                'headless': self.config.get('headless', True),
                **self.config.get('browser_options', {})
            }
            
            self.browser = StealthBrowser(f"{self.name}_browser", **browser_config)
            await self.browser.initialize()
            
            # Navigate to base URL
            if self.base_url:
                success = await self.browser.navigate(self.base_url)
                if not success:
                    await self.set_status(ProviderStatus.ERROR, "Failed to navigate to base URL")
                    return False
            
            # Perform authentication if required
            if self.login_required:
                auth_success = await self._authenticate()
                if not auth_success:
                    await self.set_status(ProviderStatus.AUTHENTICATION_REQUIRED, "Authentication failed")
                    return False
            
            # Wait for chat interface to be ready
            await self._wait_for_chat_ready()
            
            self.last_activity = time.time()
            await self.set_status(ProviderStatus.ACTIVE)
            logger.info(f"Initialized web provider: {self.name}")
            return True
            
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, f"Initialization failed: {str(e)}")
            return False
    
    async def send_message(self, message: str, **kwargs) -> ProviderResponse:
        """Send a message through web interface"""
        if not self.browser:
            return ProviderResponse(
                content="",
                provider_name=self.name,
                success=False,
                error="Provider not initialized"
            )
        
        self._record_request()
        start_time = time.time()
        
        try:
            await self.set_status(ProviderStatus.BUSY)
            
            # Check if session is still valid
            if not await self._check_session_valid():
                # Try to refresh session
                if not await self._refresh_session():
                    return ProviderResponse(
                        content="",
                        provider_name=self.name,
                        success=False,
                        error="Session expired and refresh failed"
                    )
            
            # Clear any existing text and type new message
            if not await self.browser.type_text(self.selectors['chat_input'], message):
                return ProviderResponse(
                    content="",
                    provider_name=self.name,
                    success=False,
                    error="Failed to type message"
                )
            
            # Click send button
            if not await self.browser.click_element(self.selectors['send_button']):
                return ProviderResponse(
                    content="",
                    provider_name=self.name,
                    success=False,
                    error="Failed to click send button"
                )
            
            # Wait for response
            response_content = await self._wait_for_response()
            
            response_time = time.time() - start_time
            self.last_activity = time.time()
            
            await self.set_status(ProviderStatus.ACTIVE)
            
            return ProviderResponse(
                content=response_content,
                provider_name=self.name,
                success=True,
                response_time=response_time,
                metadata={
                    'method': 'web_automation',
                    'base_url': self.base_url
                }
            )
            
        except Exception as e:
            await self.set_status(ProviderStatus.ERROR, str(e))
            return ProviderResponse(
                content="",
                provider_name=self.name,
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def stream_message(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response (web providers typically don't support streaming)"""
        # Most web providers don't support true streaming
        # We'll simulate it by sending the full response in chunks
        response = await self.send_message(message, **kwargs)
        
        if response.success and response.content:
            # Split response into chunks and yield with delays
            words = response.content.split()
            chunk_size = 5  # words per chunk
            
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if i + chunk_size < len(words):
                    chunk += ' '
                yield chunk
                await asyncio.sleep(0.1)  # Small delay between chunks
        else:
            yield f"Error: {response.error or 'Unknown error'}"
    
    async def health_check(self) -> bool:
        """Check if the web provider is healthy"""
        try:
            if not self.browser:
                return False
            
            # Check if browser is healthy
            if not await self.browser.is_healthy():
                return False
            
            # Check if we can access the chat interface
            return await self._check_chat_interface_available()
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up web provider resources"""
        try:
            if self.browser:
                await self.browser.cleanup()
                self.browser = None
            
            await self.set_status(ProviderStatus.INACTIVE)
            logger.info(f"Cleaned up web provider: {self.name}")
            
        except Exception as e:
            logger.error(f"Error during web provider cleanup: {str(e)}")
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def _authenticate(self) -> bool:
        """Perform authentication specific to the provider"""
        pass
    
    @abstractmethod
    async def _wait_for_response(self) -> str:
        """Wait for and extract response from the web interface"""
        pass
    
    # Common helper methods
    
    async def _wait_for_chat_ready(self) -> bool:
        """Wait for chat interface to be ready"""
        try:
            # Wait for chat input to be available
            if not await self.browser.wait_for_element(self.selectors['chat_input'], timeout=15000):
                return False
            
            # Wait for send button to be available
            if not await self.browser.wait_for_element(self.selectors['send_button'], timeout=5000):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to wait for chat ready in {self.name}: {str(e)}")
            return False
    
    async def _check_session_valid(self) -> bool:
        """Check if the current session is still valid"""
        try:
            # Check session timeout
            if self.last_activity and time.time() - self.last_activity > self.session_timeout:
                return False
            
            # Check if chat interface is still available
            return await self._check_chat_interface_available()
            
        except Exception:
            return False
    
    async def _check_chat_interface_available(self) -> bool:
        """Check if chat interface elements are available"""
        try:
            if not self.browser:
                return False
            
            page = await self.browser.get_page()
            if not page:
                return False
            
            # Check if key elements exist
            chat_input = await page.query_selector(self.selectors['chat_input'])
            send_button = await page.query_selector(self.selectors['send_button'])
            
            return chat_input is not None and send_button is not None
            
        except Exception:
            return False
    
    async def _refresh_session(self) -> bool:
        """Attempt to refresh the session"""
        try:
            # Navigate back to base URL
            if not await self.browser.navigate(self.base_url):
                return False
            
            # Re-authenticate if required
            if self.login_required:
                if not await self._authenticate():
                    return False
            
            # Wait for chat interface
            if not await self._wait_for_chat_ready():
                return False
            
            self.last_activity = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh session for {self.name}: {str(e)}")
            return False
    
    async def _wait_for_send_button_ready(self, timeout: int = 30000) -> bool:
        """Wait for send button to be ready (not disabled/loading)"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout / 1000:
                page = await self.browser.get_page()
                if not page:
                    return False
                
                # Check if send button is not disabled
                if self.selectors.get('send_button_disabled'):
                    disabled_button = await page.query_selector(self.selectors['send_button_disabled'])
                    if disabled_button:
                        await asyncio.sleep(0.5)
                        continue
                
                # Check if send button is not in loading state
                if self.selectors.get('send_button_loading'):
                    loading_button = await page.query_selector(self.selectors['send_button_loading'])
                    if loading_button:
                        await asyncio.sleep(0.5)
                        continue
                
                # Send button should be ready
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for send button ready in {self.name}: {str(e)}")
            return False
    
    async def _start_new_chat(self) -> bool:
        """Start a new chat session"""
        try:
            if self.selectors.get('new_chat_button'):
                return await self.browser.click_element(self.selectors['new_chat_button'])
            return True  # No new chat button needed
            
        except Exception as e:
            logger.error(f"Failed to start new chat in {self.name}: {str(e)}")
            return False
    
    def _validate_context(self, context: ProviderContext) -> bool:
        """Validate web provider context"""
        if not super()._validate_context(context):
            return False
        
        # Check for required auth types
        if context.auth_type not in ["username_password", "cookies", "custom"]:
            return False
        
        # Validate based on auth type
        if context.auth_type == "username_password":
            return bool(context.credentials.get('username') and context.credentials.get('password'))
        elif context.auth_type == "cookies":
            return bool(context.credentials.get('cookies'))
        elif context.auth_type == "custom":
            return True  # Custom auth validation handled by subclasses
        
        return False
