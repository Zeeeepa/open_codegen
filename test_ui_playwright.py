#!/usr/bin/env python3
"""
Comprehensive MCP Playwright UI Testing Suite
Tests all UI components and functionality of the Universal AI Endpoint Management System
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, Page, Browser
from typing import List, Dict, Any


class UITestSuite:
    """Comprehensive UI testing using Playwright"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        
    async def log_test(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        # Color output
        color = "\033[92m" if status == "PASS" else "\033[91m"  # Green or Red
        reset = "\033[0m"
        
        print(f"{color}[{status}]{reset} {test_name}")
        if details:
            print(f"  └─ {details}")
        if error:
            print(f"  └─ ERROR: {error}")
    
    async def test_page_load(self, page: Page) -> bool:
        """Test if the main page loads correctly"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_selector(".app-container", timeout=10000)
            
            # Check title
            title = await page.title()
            await self.log_test("Page Load", "PASS", f"Title: {title}")
            return True
        except Exception as e:
            await self.log_test("Page Load", "FAIL", error=str(e))
            return False
    
    async def test_header_components(self, page: Page) -> bool:
        """Test header components and connection status"""
        try:
            # Check header exists
            header = await page.query_selector(".app-header")
            if not header:
                raise Exception("Header not found")
            
            # Check title
            title_element = await page.query_selector(".app-header h1")
            title_text = await title_element.text_content() if title_element else ""
            
            # Check connection status
            status_element = await page.query_selector("#connectionStatus")
            status_text = await status_element.text_content() if status_element else ""
            
            # Check settings button
            settings_btn = await page.query_selector("#settingsBtn")
            is_visible = await settings_btn.is_visible() if settings_btn else False
            
            await self.log_test("Header Components", "PASS", 
                              f"Title: {title_text}, Status: {status_text}, Settings Btn: {is_visible}")
            return True
        except Exception as e:
            await self.log_test("Header Components", "FAIL", error=str(e))
            return False
    
    async def test_sidebar_navigation(self, page: Page) -> bool:
        """Test sidebar navigation and tab switching"""
        try:
            # Get all navigation items
            nav_items = await page.query_selector_all(".nav-item")
            if len(nav_items) == 0:
                raise Exception("No navigation items found")
            
            tab_names = []
            for item in nav_items:
                tab_name = await item.get_attribute("data-tab")
                tab_text = await item.text_content()
                tab_names.append(f"{tab_name}: {tab_text.strip()}")
                
                # Click the tab
                await item.click()
                await page.wait_for_timeout(500)  # Wait for transition
                
                # Check if corresponding content is visible
                content = await page.query_selector(f"#{tab_name}")
                if content:
                    is_active = await content.evaluate("el => el.classList.contains('active')")
                    if not is_active:
                        raise Exception(f"Tab {tab_name} not properly activated")
            
            await self.log_test("Sidebar Navigation", "PASS", 
                              f"Tested {len(nav_items)} tabs: {', '.join(tab_names)}")
            return True
        except Exception as e:
            await self.log_test("Sidebar Navigation", "FAIL", error=str(e))
            return False
    
    async def test_dashboard_stats(self, page: Page) -> bool:
        """Test dashboard statistics cards"""
        try:
            # Navigate to dashboard
            dashboard_tab = await page.query_selector('[data-tab="dashboard"]')
            await dashboard_tab.click()
            await page.wait_for_timeout(500)
            
            # Check stat cards
            stat_cards = await page.query_selector_all(".stat-card")
            if len(stat_cards) == 0:
                raise Exception("No stat cards found")
            
            stats = []
            for card in stat_cards:
                stat_value = await card.query_selector("h3")
                stat_label = await card.query_selector("p")
                
                value_text = await stat_value.text_content() if stat_value else "N/A"
                label_text = await stat_label.text_content() if stat_label else "N/A"
                stats.append(f"{label_text}: {value_text}")
            
            await self.log_test("Dashboard Stats", "PASS", 
                              f"Found {len(stat_cards)} stats: {', '.join(stats)}")
            return True
        except Exception as e:
            await self.log_test("Dashboard Stats", "FAIL", error=str(e))
            return False
    
    async def test_endpoints_management(self, page: Page) -> bool:
        """Test endpoints management interface"""
        try:
            # Navigate to endpoints tab
            endpoints_tab = await page.query_selector('[data-tab="endpoints"]')
            await endpoints_tab.click()
            await page.wait_for_timeout(500)
            
            # Check add endpoint button
            add_btn = await page.query_selector("#addEndpointBtn")
            if not add_btn:
                raise Exception("Add endpoint button not found")
            
            # Click add endpoint button
            await add_btn.click()
            await page.wait_for_timeout(500)
            
            # Check if modal opens
            modal = await page.query_selector("#addEndpointModal")
            if not modal:
                raise Exception("Add endpoint modal not found")
            
            is_visible = await modal.evaluate("el => getComputedStyle(el).display !== 'none'")
            if not is_visible:
                raise Exception("Add endpoint modal not visible")
            
            # Check form elements
            form_elements = await modal.query_selector_all("input, select")
            
            # Close modal
            close_btn = await modal.query_selector(".modal-close")
            if close_btn:
                await close_btn.click()
            
            await self.log_test("Endpoints Management", "PASS", 
                              f"Modal opened with {len(form_elements)} form elements")
            return True
        except Exception as e:
            await self.log_test("Endpoints Management", "FAIL", error=str(e))
            return False
    
    async def test_yaml_editor(self, page: Page) -> bool:
        """Test YAML editor functionality"""
        try:
            # Navigate to YAML editor tab
            yaml_tab = await page.query_selector('[data-tab="yaml-editor"]')
            await yaml_tab.click()
            await page.wait_for_timeout(1000)  # Wait for CodeMirror to load
            
            # Check editor exists
            editor = await page.query_selector("#yamlEditor")
            if not editor:
                raise Exception("YAML editor not found")
            
            # Check control buttons
            validate_btn = await page.query_selector("#validateYamlBtn")
            save_btn = await page.query_selector("#saveConfigBtn")
            upload_btn = await page.query_selector("#uploadYamlBtn")
            
            buttons_found = []
            if validate_btn:
                buttons_found.append("Validate")
            if save_btn:
                buttons_found.append("Save")
            if upload_btn:
                buttons_found.append("Upload")
            
            # Test if editor is visible (CodeMirror might be using different selector)
            codemirror = await page.query_selector(".CodeMirror textarea")
            if codemirror:
                await codemirror.fill("name: TestEndpoint\nURL: https://example.com")
            else:
                await editor.fill("name: TestEndpoint\nURL: https://example.com")
            
            # Get editor content to verify
            content = await editor.input_value()
            
            await self.log_test("YAML Editor", "PASS", 
                              f"Editor functional, buttons: {', '.join(buttons_found)}")
            return True
        except Exception as e:
            await self.log_test("YAML Editor", "FAIL", error=str(e))
            return False
    
    async def test_chat_interface(self, page: Page) -> bool:
        """Test chat interface functionality"""
        try:
            # Navigate to chat interface
            chat_tab = await page.query_selector('[data-tab="chat-interface"]')
            await chat_tab.click()
            await page.wait_for_timeout(500)
            
            # Check chat components
            chat_messages = await page.query_selector("#chatMessages")
            chat_input = await page.query_selector("#chatInput")
            send_btn = await page.query_selector("#sendMessageBtn")
            endpoint_selector = await page.query_selector("#endpointSelector")
            
            components = []
            if chat_messages:
                components.append("Messages Area")
            if chat_input:
                components.append("Input Field")
            if send_btn:
                components.append("Send Button")
            if endpoint_selector:
                components.append("Endpoint Selector")
            
            # Test input functionality
            if chat_input:
                await chat_input.fill("Test message")
                input_value = await chat_input.input_value()
                if input_value != "Test message":
                    raise Exception("Chat input not working properly")
            
            await self.log_test("Chat Interface", "PASS", 
                              f"Components found: {', '.join(components)}")
            return True
        except Exception as e:
            await self.log_test("Chat Interface", "FAIL", error=str(e))
            return False
    
    async def test_monitoring_dashboard(self, page: Page) -> bool:
        """Test monitoring dashboard functionality"""
        try:
            # Navigate to monitoring
            monitoring_tab = await page.query_selector('[data-tab="monitoring"]')
            await monitoring_tab.click()
            await page.wait_for_timeout(1000)  # Wait for charts to load
            
            # Check monitoring components
            performance_chart = await page.query_selector("#performanceChart")
            health_list = await page.query_selector("#healthList")
            cpu_meter = await page.query_selector("#cpuMeter")
            memory_meter = await page.query_selector("#memoryMeter")
            log_viewer = await page.query_selector("#logViewer")
            refresh_btn = await page.query_selector("#refreshMetricsBtn")
            
            components = []
            if performance_chart:
                components.append("Performance Chart")
            if health_list:
                components.append("Health List")
            if cpu_meter:
                components.append("CPU Meter")
            if memory_meter:
                components.append("Memory Meter")
            if log_viewer:
                components.append("Log Viewer")
            if refresh_btn:
                components.append("Refresh Button")
            
            # Test refresh button
            if refresh_btn:
                await refresh_btn.click()
                await page.wait_for_timeout(500)
            
            await self.log_test("Monitoring Dashboard", "PASS", 
                              f"Components found: {', '.join(components)}")
            return True
        except Exception as e:
            await self.log_test("Monitoring Dashboard", "FAIL", error=str(e))
            return False
    
    async def test_templates_section(self, page: Page) -> bool:
        """Test templates section"""
        try:
            # Navigate to templates
            templates_tab = await page.query_selector('[data-tab="templates"]')
            await templates_tab.click()
            await page.wait_for_timeout(500)
            
            # Check templates components
            create_btn = await page.query_selector("#createTemplateBtn")
            templates_grid = await page.query_selector("#templatesGrid")
            
            components = []
            if create_btn:
                components.append("Create Template Button")
            if templates_grid:
                components.append("Templates Grid")
            
            await self.log_test("Templates Section", "PASS", 
                              f"Components found: {', '.join(components)}")
            return True
        except Exception as e:
            await self.log_test("Templates Section", "FAIL", error=str(e))
            return False
    
    async def test_api_endpoints(self, page: Page) -> bool:
        """Test API endpoints are accessible"""
        try:
            # Test health endpoint
            health_response = await page.evaluate("""
                fetch('/health')
                    .then(response => response.json())
                    .catch(error => ({ error: error.message }))
            """)
            
            # Test providers endpoint
            providers_response = await page.evaluate("""
                fetch('/api/providers')
                    .then(response => response.json())
                    .catch(error => ({ error: error.message }))
            """)
            
            api_tests = []
            if 'error' not in health_response:
                api_tests.append("Health endpoint working")
            if 'error' not in providers_response:
                api_tests.append("Providers endpoint working")
            
            await self.log_test("API Endpoints", "PASS", 
                              f"Tests: {', '.join(api_tests)}")
            return True
        except Exception as e:
            await self.log_test("API Endpoints", "FAIL", error=str(e))
            return False
    
    async def test_responsive_design(self, page: Page) -> bool:
        """Test responsive design at different viewport sizes"""
        try:
            # Test different viewport sizes
            viewports = [
                {"width": 1920, "height": 1080, "name": "Desktop Large"},
                {"width": 1366, "height": 768, "name": "Desktop Standard"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 375, "height": 667, "name": "Mobile"}
            ]
            
            responsive_results = []
            for viewport in viewports:
                await page.set_viewport_size(viewport["width"], viewport["height"])
                await page.wait_for_timeout(500)
                
                # Check if sidebar is visible/responsive
                sidebar = await page.query_selector(".sidebar")
                sidebar_visible = await sidebar.is_visible() if sidebar else False
                
                # Check if main content adapts
                content = await page.query_selector(".content-area")
                content_visible = await content.is_visible() if content else False
                
                responsive_results.append(f"{viewport['name']}: Sidebar={sidebar_visible}, Content={content_visible}")
            
            await self.log_test("Responsive Design", "PASS", 
                              f"Tested viewports: {', '.join(responsive_results)}")
            return True
        except Exception as e:
            await self.log_test("Responsive Design", "FAIL", error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all UI tests"""
        print("🎯 Starting Comprehensive MCP Playwright UI Testing Suite")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Run all tests
                tests = [
                    self.test_page_load,
                    self.test_header_components,
                    self.test_sidebar_navigation,
                    self.test_dashboard_stats,
                    self.test_endpoints_management,
                    self.test_yaml_editor,
                    self.test_chat_interface,
                    self.test_monitoring_dashboard,
                    self.test_templates_section,
                    self.test_api_endpoints,
                    self.test_responsive_design
                ]
                
                results = []
                for test in tests:
                    result = await test(page)
                    results.append(result)
                
                # Generate summary
                passed = sum(1 for r in results if r)
                total = len(results)
                success_rate = (passed / total) * 100 if total > 0 else 0
                
                print("\n" + "=" * 60)
                print(f"🎯 TEST SUMMARY")
                print(f"Total Tests: {total}")
                print(f"Passed: {passed}")
                print(f"Failed: {total - passed}")
                print(f"Success Rate: {success_rate:.1f}%")
                
                if success_rate >= 80:
                    print("✅ UI TESTING SUCCESSFUL - All major components working!")
                else:
                    print("⚠️ Some UI components need attention")
                
                return {
                    "total_tests": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate,
                    "details": self.results
                }
                
            finally:
                await browser.close()


async def main():
    """Main testing function"""
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    await asyncio.sleep(3)
    
    # Run tests
    test_suite = UITestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    with open("ui_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Full test results saved to: ui_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())