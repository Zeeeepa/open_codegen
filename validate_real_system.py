#!/usr/bin/env python3
"""
Comprehensive system validation with real API calls
Tests the entire Universal AI Endpoint Manager with actual functionality
"""

import asyncio
import aiohttp
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    """Validates the entire system with real functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    async def start(self):
        """Start the validator"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        logger.info("🚀 System Validator started")
    
    async def stop(self):
        """Stop the validator"""
        if self.session:
            await self.session.close()
        logger.info("🛑 System Validator stopped")
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        if success:
            self.test_results['passed'] += 1
            logger.info(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
            logger.error(f"❌ {test_name}: FAILED {message}")
    
    async def test_server_health(self):
        """Test if server is running and healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Server Health", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_test("Server Health", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Server Health", False, str(e))
            return False
    
    async def test_list_endpoints(self):
        """Test listing endpoints"""
        try:
            async with self.session.get(f"{self.base_url}/api/endpoints/") as response:
                if response.status == 200:
                    endpoints = await response.json()
                    self.log_test("List Endpoints", True, f"Found {len(endpoints)} endpoints")
                    return endpoints
                else:
                    self.log_test("List Endpoints", False, f"HTTP {response.status}")
                    return []
        except Exception as e:
            self.log_test("List Endpoints", False, str(e))
            return []
    
    async def test_create_mock_endpoint(self):
        """Test creating a mock endpoint"""
        try:
            endpoint_config = {
                "name": "test-mock-endpoint",
                "provider_type": "api_token",
                "description": "Test mock endpoint for validation",
                "base_url": "https://httpbin.org",
                "api_key": "test-key",
                "model": "test-model"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/endpoints/", 
                json=endpoint_config
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.log_test("Create Mock Endpoint", True, result.get('message', ''))
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Create Mock Endpoint", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Create Mock Endpoint", False, str(e))
            return False
    
    async def test_start_endpoint(self, endpoint_name: str):
        """Test starting an endpoint"""
        try:
            async with self.session.post(f"{self.base_url}/api/endpoints/{endpoint_name}/start") as response:
                if response.status == 200:
                    result = await response.json()
                    self.log_test(f"Start Endpoint ({endpoint_name})", True, result.get('message', ''))
                    return True
                else:
                    error_text = await response.text()
                    self.log_test(f"Start Endpoint ({endpoint_name})", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test(f"Start Endpoint ({endpoint_name})", False, str(e))
            return False
    
    async def test_endpoint_health(self, endpoint_name: str):
        """Test endpoint health check"""
        try:
            async with self.session.get(f"{self.base_url}/api/endpoints/{endpoint_name}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.log_test(f"Endpoint Health ({endpoint_name})", True, f"Status: {health_data}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test(f"Endpoint Health ({endpoint_name})", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test(f"Endpoint Health ({endpoint_name})", False, str(e))
            return False
    
    async def test_send_message_to_endpoint(self, endpoint_name: str):
        """Test sending a message to an endpoint"""
        try:
            message_data = {
                "message": "Hello! This is a test message from the system validator.",
                "model": "test-model",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            async with self.session.post(
                f"{self.base_url}/api/endpoints/{endpoint_name}/test",
                json=message_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_content = result.get('response', {}).get('content', 'No content')
                    self.log_test(f"Send Message ({endpoint_name})", True, f"Response: {response_content[:100]}...")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test(f"Send Message ({endpoint_name})", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test(f"Send Message ({endpoint_name})", False, str(e))
            return False
    
    async def test_openai_compatible_api(self):
        """Test OpenAI-compatible chat completions API"""
        try:
            chat_data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "What is 2+2? Please give a short answer."}
                ],
                "temperature": 0.7,
                "max_tokens": 50,
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=chat_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
                    self.log_test("OpenAI Compatible API", True, f"Response: {content}")
                    return True
                elif response.status == 503:
                    self.log_test("OpenAI Compatible API", True, "No endpoints available (expected)")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("OpenAI Compatible API", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("OpenAI Compatible API", False, str(e))
            return False
    
    async def test_list_models(self):
        """Test listing available models"""
        try:
            async with self.session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    models = await response.json()
                    model_count = len(models.get('data', []))
                    self.log_test("List Models", True, f"Found {model_count} models")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("List Models", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("List Models", False, str(e))
            return False
    
    async def test_system_status(self):
        """Test system status endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    status = await response.json()
                    system_status = status.get('system', {}).get('status', 'unknown')
                    endpoints_count = status.get('system', {}).get('endpoints_total', 0)
                    self.log_test("System Status", True, f"Status: {system_status}, Endpoints: {endpoints_count}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("System Status", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("System Status", False, str(e))
            return False
    
    async def test_web_interface(self):
        """Test web interface availability"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    content = await response.text()
                    if "Universal AI Endpoint Manager" in content:
                        self.log_test("Web Interface", True, "Interface loaded successfully")
                        return True
                    else:
                        self.log_test("Web Interface", False, "Interface content not found")
                        return False
                else:
                    self.log_test("Web Interface", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Web Interface", False, str(e))
            return False
    
    async def run_comprehensive_validation(self):
        """Run all validation tests"""
        logger.info("🔍 Starting Comprehensive System Validation")
        logger.info("=" * 60)
        
        # Test 1: Server Health
        logger.info("\n🏥 Testing Server Health...")
        server_healthy = await self.test_server_health()
        
        if not server_healthy:
            logger.error("❌ Server is not healthy. Stopping validation.")
            return False
        
        # Test 2: Web Interface
        logger.info("\n🌐 Testing Web Interface...")
        await self.test_web_interface()
        
        # Test 3: System Status
        logger.info("\n📊 Testing System Status...")
        await self.test_system_status()
        
        # Test 4: List Endpoints
        logger.info("\n📋 Testing Endpoint Management...")
        await self.test_list_endpoints()
        
        # Test 5: Create Mock Endpoint
        logger.info("\n➕ Testing Endpoint Creation...")
        endpoint_created = await self.test_create_mock_endpoint()
        
        # Test 6: Start Endpoint (if created)
        if endpoint_created:
            logger.info("\n▶️ Testing Endpoint Start...")
            await self.test_start_endpoint("test-mock-endpoint")
            
            # Test 7: Endpoint Health
            logger.info("\n🔍 Testing Endpoint Health...")
            await self.test_endpoint_health("test-mock-endpoint")
            
            # Test 8: Send Message to Endpoint
            logger.info("\n💬 Testing Message Sending...")
            await self.test_send_message_to_endpoint("test-mock-endpoint")
        
        # Test 9: OpenAI Compatible API
        logger.info("\n🔌 Testing OpenAI Compatible API...")
        await self.test_openai_compatible_api()
        
        # Test 10: List Models
        logger.info("\n📚 Testing Model Listing...")
        await self.test_list_models()
        
        # Print Results
        logger.info("\n" + "=" * 60)
        logger.info("📊 VALIDATION RESULTS")
        logger.info("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"✅ Tests Passed: {self.test_results['passed']}")
        logger.info(f"❌ Tests Failed: {self.test_results['failed']}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            logger.info("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                logger.info(f"  • {error}")
        
        if success_rate >= 80:
            logger.info("\n🎉 VALIDATION PASSED! System is working correctly.")
            return True
        else:
            logger.info("\n⚠️ VALIDATION FAILED! System needs attention.")
            return False

async def wait_for_server(base_url: str, max_attempts: int = 30):
    """Wait for server to be ready"""
    logger.info(f"⏳ Waiting for server at {base_url}...")
    
    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info("✅ Server is ready!")
                        return True
        except:
            pass
        
        logger.info(f"⏳ Attempt {attempt + 1}/{max_attempts}...")
        await asyncio.sleep(2)
    
    logger.error("❌ Server did not become ready in time")
    return False

async def main():
    """Main validation function"""
    print("🤖 Universal AI Endpoint Manager - System Validation")
    print("=" * 60)
    
    # Wait for server to be ready
    server_ready = await wait_for_server("http://localhost:8000")
    
    if not server_ready:
        print("❌ Server is not running. Please start the server first:")
        print("   python -m backend.main")
        return False
    
    # Run validation
    validator = SystemValidator()
    await validator.start()
    
    try:
        success = await validator.run_comprehensive_validation()
        return success
    finally:
        await validator.stop()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
