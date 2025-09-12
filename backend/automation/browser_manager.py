"""
Browser Manager
Manages browser instances and sessions for web automation providers
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from .stealth_browser import StealthBrowser

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser instances and contexts for web automation"""
    
    def __init__(self, max_browsers: int = 5, max_contexts_per_browser: int = 10):
        self.max_browsers = max_browsers
        self.max_contexts_per_browser = max_contexts_per_browser
        
        self.playwright = None
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.stealth_browsers: Dict[str, StealthBrowser] = {}
        
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the browser manager"""
        if self._initialized:
            return
        
        try:
            self.playwright = await async_playwright().start()
            self._initialized = True
            logger.info("Browser manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {str(e)}")
            raise
    
    async def create_browser(self, browser_id: str, browser_type: str = "chromium", **kwargs) -> Optional[Browser]:
        """Create a new browser instance"""
        async with self._lock:
            if not self._initialized:
                await self.initialize()
            
            if browser_id in self.browsers:
                logger.warning(f"Browser {browser_id} already exists")
                return self.browsers[browser_id]
            
            if len(self.browsers) >= self.max_browsers:
                logger.error(f"Maximum browsers ({self.max_browsers}) reached")
                return None
            
            try:
                # Default browser options for stealth
                default_options = {
                    'headless': kwargs.get('headless', True),
                    'args': [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                }
                
                # Merge with provided options
                options = {**default_options, **kwargs}
                
                # Create browser based on type
                if browser_type == "chromium":
                    browser = await self.playwright.chromium.launch(**options)
                elif browser_type == "firefox":
                    browser = await self.playwright.firefox.launch(**options)
                elif browser_type == "webkit":
                    browser = await self.playwright.webkit.launch(**options)
                else:
                    raise ValueError(f"Unsupported browser type: {browser_type}")
                
                self.browsers[browser_id] = browser
                logger.info(f"Created browser: {browser_id} ({browser_type})")
                return browser
                
            except Exception as e:
                logger.error(f"Failed to create browser {browser_id}: {str(e)}")
                return None
    
    async def create_stealth_browser(self, browser_id: str, **kwargs) -> Optional[StealthBrowser]:
        """Create a stealth browser with advanced evasion techniques"""
        async with self._lock:
            if browser_id in self.stealth_browsers:
                return self.stealth_browsers[browser_id]
            
            try:
                stealth_browser = StealthBrowser(browser_id, **kwargs)
                await stealth_browser.initialize()
                
                self.stealth_browsers[browser_id] = stealth_browser
                logger.info(f"Created stealth browser: {browser_id}")
                return stealth_browser
                
            except Exception as e:
                logger.error(f"Failed to create stealth browser {browser_id}: {str(e)}")
                return None
    
    async def create_context(self, context_id: str, browser_id: str, **kwargs) -> Optional[BrowserContext]:
        """Create a new browser context"""
        async with self._lock:
            if context_id in self.contexts:
                logger.warning(f"Context {context_id} already exists")
                return self.contexts[context_id]
            
            if browser_id not in self.browsers:
                logger.error(f"Browser {browser_id} not found")
                return None
            
            # Count contexts for this browser
            browser_contexts = [ctx for ctx_id, ctx in self.contexts.items() 
                             if ctx_id.startswith(f"{browser_id}_")]
            
            if len(browser_contexts) >= self.max_contexts_per_browser:
                logger.error(f"Maximum contexts per browser ({self.max_contexts_per_browser}) reached")
                return None
            
            try:
                browser = self.browsers[browser_id]
                
                # Default context options
                default_options = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                    'permissions': ['geolocation', 'notifications'],
                    'extra_http_headers': {
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                }
                
                # Merge with provided options
                options = {**default_options, **kwargs}
                
                context = await browser.new_context(**options)
                self.contexts[context_id] = context
                
                logger.info(f"Created context: {context_id} for browser: {browser_id}")
                return context
                
            except Exception as e:
                logger.error(f"Failed to create context {context_id}: {str(e)}")
                return None
    
    async def create_page(self, page_id: str, context_id: str) -> Optional[Page]:
        """Create a new page in a context"""
        async with self._lock:
            if page_id in self.pages:
                logger.warning(f"Page {page_id} already exists")
                return self.pages[page_id]
            
            if context_id not in self.contexts:
                logger.error(f"Context {context_id} not found")
                return None
            
            try:
                context = self.contexts[context_id]
                page = await context.new_page()
                
                # Add stealth scripts
                await self._add_stealth_scripts(page)
                
                self.pages[page_id] = page
                logger.info(f"Created page: {page_id} in context: {context_id}")
                return page
                
            except Exception as e:
                logger.error(f"Failed to create page {page_id}: {str(e)}")
                return None
    
    async def get_browser(self, browser_id: str) -> Optional[Browser]:
        """Get a browser by ID"""
        return self.browsers.get(browser_id)
    
    async def get_stealth_browser(self, browser_id: str) -> Optional[StealthBrowser]:
        """Get a stealth browser by ID"""
        return self.stealth_browsers.get(browser_id)
    
    async def get_context(self, context_id: str) -> Optional[BrowserContext]:
        """Get a context by ID"""
        return self.contexts.get(context_id)
    
    async def get_page(self, page_id: str) -> Optional[Page]:
        """Get a page by ID"""
        return self.pages.get(page_id)
    
    async def close_page(self, page_id: str) -> bool:
        """Close a page"""
        async with self._lock:
            if page_id not in self.pages:
                return False
            
            try:
                page = self.pages[page_id]
                await page.close()
                del self.pages[page_id]
                logger.info(f"Closed page: {page_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to close page {page_id}: {str(e)}")
                return False
    
    async def close_context(self, context_id: str) -> bool:
        """Close a context and all its pages"""
        async with self._lock:
            if context_id not in self.contexts:
                return False
            
            try:
                # Close all pages in this context
                pages_to_close = [page_id for page_id, page in self.pages.items() 
                                if page.context == self.contexts[context_id]]
                
                for page_id in pages_to_close:
                    await self.close_page(page_id)
                
                # Close context
                context = self.contexts[context_id]
                await context.close()
                del self.contexts[context_id]
                
                logger.info(f"Closed context: {context_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to close context {context_id}: {str(e)}")
                return False
    
    async def close_browser(self, browser_id: str) -> bool:
        """Close a browser and all its contexts"""
        async with self._lock:
            if browser_id not in self.browsers:
                return False
            
            try:
                # Close all contexts for this browser
                contexts_to_close = [ctx_id for ctx_id in self.contexts.keys() 
                                   if ctx_id.startswith(f"{browser_id}_")]
                
                for context_id in contexts_to_close:
                    await self.close_context(context_id)
                
                # Close browser
                browser = self.browsers[browser_id]
                await browser.close()
                del self.browsers[browser_id]
                
                logger.info(f"Closed browser: {browser_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to close browser {browser_id}: {str(e)}")
                return False
    
    async def close_stealth_browser(self, browser_id: str) -> bool:
        """Close a stealth browser"""
        async with self._lock:
            if browser_id not in self.stealth_browsers:
                return False
            
            try:
                stealth_browser = self.stealth_browsers[browser_id]
                await stealth_browser.cleanup()
                del self.stealth_browsers[browser_id]
                
                logger.info(f"Closed stealth browser: {browser_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to close stealth browser {browser_id}: {str(e)}")
                return False
    
    async def cleanup_all(self):
        """Close all browsers, contexts, and pages"""
        async with self._lock:
            try:
                # Close all stealth browsers
                for browser_id in list(self.stealth_browsers.keys()):
                    await self.close_stealth_browser(browser_id)
                
                # Close all regular browsers
                for browser_id in list(self.browsers.keys()):
                    await self.close_browser(browser_id)
                
                # Stop playwright
                if self.playwright:
                    await self.playwright.stop()
                    self.playwright = None
                
                self._initialized = False
                logger.info("Browser manager cleanup completed")
                
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get browser manager statistics"""
        return {
            'browsers': len(self.browsers),
            'stealth_browsers': len(self.stealth_browsers),
            'contexts': len(self.contexts),
            'pages': len(self.pages),
            'max_browsers': self.max_browsers,
            'max_contexts_per_browser': self.max_contexts_per_browser,
            'initialized': self._initialized
        }
    
    async def _add_stealth_scripts(self, page: Page):
        """Add stealth scripts to a page"""
        try:
            # Override navigator.webdriver
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Override plugins
            await page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # Override languages
            await page.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            # Override permissions
            await page.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
        except Exception as e:
            logger.warning(f"Failed to add stealth scripts: {str(e)}")
