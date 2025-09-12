"""
Stealth Browser
Advanced browser automation with stealth techniques inspired by thermoptic project
"""

import asyncio
import random
import logging
from typing import Dict, Optional, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class StealthBrowser:
    """Advanced stealth browser with evasion techniques"""
    
    def __init__(self, browser_id: str, **kwargs):
        self.browser_id = browser_id
        self.config = kwargs
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Stealth configuration
        self.stealth_config = {
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ],
            'viewports': [
                {'width': 1920, 'height': 1080},
                {'width': 1366, 'height': 768},
                {'width': 1440, 'height': 900},
                {'width': 1536, 'height': 864}
            ],
            'timezones': [
                'America/New_York',
                'America/Los_Angeles', 
                'Europe/London',
                'Europe/Berlin'
            ],
            'locales': [
                'en-US',
                'en-GB',
                'de-DE',
                'fr-FR'
            ]
        }
    
    async def initialize(self):
        """Initialize the stealth browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Random stealth configuration
            user_agent = random.choice(self.stealth_config['user_agents'])
            viewport = random.choice(self.stealth_config['viewports'])
            timezone = random.choice(self.stealth_config['timezones'])
            locale = random.choice(self.stealth_config['locales'])
            
            # Advanced browser arguments for stealth
            browser_args = [
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
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Optional: for faster loading
                '--disable-javascript',  # Will be re-enabled selectively
                '--disable-default-apps',
                '--disable-sync',
                '--disable-background-networking',
                '--disable-component-update',
                '--disable-client-side-phishing-detection',
                '--disable-hang-monitor',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-domain-reliability',
                '--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer',
                '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                '--disable-features=AudioServiceOutOfProcess',
                '--disable-features=VizServiceDisplayCompositor',
                '--disable-logging',
                '--disable-login-animations',
                '--disable-notifications',
                '--disable-permissions-api',
                '--disable-presentation-api',
                '--disable-print-preview',
                '--disable-speech-api',
                '--disable-file-system',
                '--disable-sensors',
                '--disable-device-discovery-notifications',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-back-forward-cache',
                '--disable-ipc-flooding-protection',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--no-crash-upload',
                '--no-default-browser-check',
                '--no-pings',
                '--password-store=basic',
                '--use-mock-keychain',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--mute-audio',
                '--no-service-autorun',
                '--disable-background-mode',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-features=TranslateUI',
                '--disable-gpu',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--disable-hang-monitor',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-domain-reliability',
                '--disable-features=VizDisplayCompositor',
                '--disable-features=VizHitTestSurfaceLayer',
                '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                '--disable-features=AudioServiceOutOfProcess',
                '--disable-features=VizServiceDisplayCompositor',
                '--disable-logging',
                '--disable-login-animations',
                '--disable-notifications',
                '--disable-permissions-api',
                '--disable-presentation-api',
                '--disable-print-preview',
                '--disable-speech-api',
                '--disable-file-system',
                '--disable-sensors',
                '--disable-device-discovery-notifications',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-back-forward-cache',
                '--disable-ipc-flooding-protection'
            ]
            
            # Launch browser with stealth options
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=browser_args,
                ignore_default_args=['--enable-automation'],
                channel=self.config.get('channel', None)
            )
            
            # Create context with stealth settings
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale=locale,
                timezone_id=timezone,
                permissions=['geolocation', 'notifications'],
                extra_http_headers={
                    'Accept-Language': f'{locale.lower()},{locale[:2].lower()};q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Apply advanced stealth techniques
            await self._apply_stealth_techniques()
            
            logger.info(f"Initialized stealth browser: {self.browser_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize stealth browser {self.browser_id}: {str(e)}")
            raise
    
    async def _apply_stealth_techniques(self):
        """Apply advanced stealth techniques to the page"""
        if not self.page:
            return
        
        try:
            # Override webdriver detection
            await self.page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override the `plugins` property to use a custom getter.
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override the `languages` property to use a custom getter.
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Override the `permissions` property to use a custom getter.
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock chrome runtime
                window.chrome = {
                    runtime: {},
                };
                
                // Override toString methods
                const getParameter = WebGLRenderingContext.getParameter;
                const getExtension = WebGLRenderingContext.getExtension;
                
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    
                    return getParameter(parameter);
                };
                
                WebGLRenderingContext.prototype.getExtension = function(name) {
                    return getExtension(name);
                };
                
                // Override screen properties
                Object.defineProperty(screen, 'availTop', { get: () => 0 });
                Object.defineProperty(screen, 'availLeft', { get: () => 0 });
                Object.defineProperty(screen, 'availWidth', { get: () => screen.width });
                Object.defineProperty(screen, 'availHeight', { get: () => screen.height - 40 });
                Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
                Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
                
                // Mock battery API
                Object.defineProperty(navigator, 'getBattery', {
                    get: () => () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    })
                });
                
                // Mock connection API
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        downlink: 10,
                        effectiveType: '4g',
                        rtt: 50,
                        saveData: false
                    })
                });
                
                // Mock media devices
                Object.defineProperty(navigator, 'mediaDevices', {
                    get: () => ({
                        enumerateDevices: () => Promise.resolve([
                            { deviceId: 'default', kind: 'audioinput', label: 'Default - Microphone' },
                            { deviceId: 'default', kind: 'audiooutput', label: 'Default - Speaker' },
                            { deviceId: 'default', kind: 'videoinput', label: 'Default - Camera' }
                        ])
                    })
                });
                
                // Override Date.prototype.getTimezoneOffset
                const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                Date.prototype.getTimezoneOffset = function() {
                    return originalGetTimezoneOffset.call(this);
                };
                
                // Mock hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4
                });
                
                // Mock device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Override toString methods to hide automation
                const originalToString = Function.prototype.toString;
                Function.prototype.toString = function() {
                    if (this === navigator.webdriver) {
                        return 'function webdriver() { [native code] }';
                    }
                    return originalToString.call(this);
                };
                
                // Mock notification permission
                Object.defineProperty(Notification, 'permission', {
                    get: () => 'default'
                });
            """)
            
            # Add mouse movement simulation
            await self.page.add_init_script("""
                // Simulate human-like mouse movements
                let mouseX = 0;
                let mouseY = 0;
                
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });
                
                // Random mouse movements
                setInterval(() => {
                    if (Math.random() < 0.1) {
                        const event = new MouseEvent('mousemove', {
                            clientX: mouseX + (Math.random() - 0.5) * 10,
                            clientY: mouseY + (Math.random() - 0.5) * 10
                        });
                        document.dispatchEvent(event);
                    }
                }, 1000);
            """)
            
        except Exception as e:
            logger.warning(f"Failed to apply stealth techniques: {str(e)}")
    
    async def navigate(self, url: str, wait_until: str = 'networkidle') -> bool:
        """Navigate to a URL with stealth techniques"""
        if not self.page:
            return False
        
        try:
            # Add random delay before navigation
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Navigate with stealth
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            
            # Random delay after navigation
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed for {self.browser_id}: {str(e)}")
            return False
    
    async def type_text(self, selector: str, text: str, delay: Optional[float] = None) -> bool:
        """Type text with human-like delays"""
        if not self.page:
            return False
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=10000)
            if not element:
                return False
            
            # Clear existing text
            await element.click()
            await self.page.keyboard.press('Control+a')
            await self.page.keyboard.press('Delete')
            
            # Type with human-like delays
            if delay is None:
                delay = random.uniform(0.05, 0.15)
            
            for char in text:
                await self.page.keyboard.type(char)
                await asyncio.sleep(delay + random.uniform(-0.02, 0.02))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to type text in {self.browser_id}: {str(e)}")
            return False
    
    async def click_element(self, selector: str, delay: Optional[float] = None) -> bool:
        """Click element with human-like behavior"""
        if not self.page:
            return False
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=10000)
            if not element:
                return False
            
            # Move mouse to element first
            await element.hover()
            
            # Random delay before click
            if delay is None:
                delay = random.uniform(0.1, 0.5)
            await asyncio.sleep(delay)
            
            # Click with slight randomization
            await element.click()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to click element in {self.browser_id}: {str(e)}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for element to appear"""
        if not self.page:
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element not found in {self.browser_id}: {str(e)}")
            return False
    
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content from element"""
        if not self.page:
            return None
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                return await element.text_content()
            return None
        except Exception as e:
            logger.error(f"Failed to get text in {self.browser_id}: {str(e)}")
            return None
    
    async def get_page(self) -> Optional[Page]:
        """Get the current page"""
        return self.page
    
    async def get_context(self) -> Optional[BrowserContext]:
        """Get the browser context"""
        return self.context
    
    async def get_browser(self) -> Optional[Browser]:
        """Get the browser instance"""
        return self.browser
    
    async def screenshot(self, path: Optional[str] = None) -> Optional[bytes]:
        """Take a screenshot"""
        if not self.page:
            return None
        
        try:
            if path:
                await self.page.screenshot(path=path)
                return None
            else:
                return await self.page.screenshot()
        except Exception as e:
            logger.error(f"Failed to take screenshot in {self.browser_id}: {str(e)}")
            return None
    
    async def cleanup(self):
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
            
            logger.info(f"Cleaned up stealth browser: {self.browser_id}")
            
        except Exception as e:
            logger.error(f"Error during stealth browser cleanup: {str(e)}")
    
    async def is_healthy(self) -> bool:
        """Check if browser is healthy"""
        try:
            if not self.page:
                return False
            
            # Simple health check
            await self.page.evaluate('() => document.readyState')
            return True
            
        except Exception:
            return False
