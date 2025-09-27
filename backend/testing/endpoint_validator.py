#!/usr/bin/env python3
"""
Comprehensive Endpoint Validator
Tests all 13 AI providers with real queries and validates coherent responses
"""

import asyncio
import json
import time
import httpx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class TestResult:
    provider_id: str
    provider_name: str
    endpoint: str
    status: TestStatus
    response_time: float
    response_content: str
    error_message: Optional[str] = None
    coherence_score: float = 0.0
    model_used: Optional[str] = None


class EndpointValidator:
    """Comprehensive validator for all AI provider endpoints"""
    
    def __init__(self):
        self.providers = self._load_provider_configs()
        self.test_queries = self._load_test_queries()
        self.results: List[TestResult] = []
        
    def _load_provider_configs(self) -> List[Dict[str, Any]]:
        """Load provider configurations"""
        return [
            {
                "id": "qwen-api",
                "name": "Qwen API",
                "endpoint": "http://localhost:8000",
                "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
                "auth_header": "Bearer qwen-test-key"
            },
            {
                "id": "qwenchat2api", 
                "name": "QwenChat2API",
                "endpoint": "http://localhost:8001",
                "models": ["qwen-chat-turbo", "qwen-chat-plus"],
                "auth_header": "Bearer qwenchat-test-key"
            },
            {
                "id": "k2think2api",
                "name": "K2Think API",
                "endpoint": "http://localhost:8002", 
                "models": ["k2-think-v1", "k2-think-reasoning"],
                "auth_header": "Bearer k2think-test-key"
            },
            {
                "id": "k2think2api2",
                "name": "K2Think API v2",
                "endpoint": "http://localhost:8003",
                "models": ["k2-think-v2", "k2-think-advanced"],
                "auth_header": "Bearer k2think2-test-key"
            },
            {
                "id": "k2think2api3",
                "name": "K2Think API v3", 
                "endpoint": "http://localhost:8004",
                "models": ["k2-think-v3", "k2-think-pro"],
                "auth_header": "Bearer k2think3-test-key"
            },
            {
                "id": "grok2api",
                "name": "Grok API",
                "endpoint": "http://localhost:8005",
                "models": ["grok-1", "grok-1.5", "grok-2"],
                "auth_header": "Bearer grok-test-key"
            },
            {
                "id": "ztoapi",
                "name": "Z.ai API (Go)",
                "endpoint": "http://localhost:8006",
                "models": ["z-ai-turbo", "z-ai-plus"],
                "auth_header": "Bearer zai-go-test-key"
            },
            {
                "id": "z-ai2api-python",
                "name": "Z.ai API (Python)",
                "endpoint": "http://localhost:8007",
                "models": ["z-ai-python", "z-ai-advanced"],
                "auth_header": "Bearer zai-python-test-key"
            },
            {
                "id": "ztoapits",
                "name": "Z.ai API (TypeScript)",
                "endpoint": "http://localhost:8008",
                "models": ["z-ai-ts", "z-ai-node"],
                "auth_header": "Bearer zai-ts-test-key"
            },
            {
                "id": "openai-proxy-z",
                "name": "OpenAI Proxy for Z",
                "endpoint": "http://localhost:8009",
                "models": ["z-ai-proxy", "z-ai-compat"],
                "auth_header": "Bearer openai-proxy-test-key"
            },
            {
                "id": "zai-python-sdk",
                "name": "Z.ai Python SDK",
                "endpoint": "http://localhost:8010",
                "models": ["z-ai-sdk", "z-ai-client"],
                "auth_header": "Bearer zai-sdk-test-key"
            },
            {
                "id": "codegen-api",
                "name": "Codegen API",
                "endpoint": "http://localhost:8011",
                "models": ["codegen-base", "codegen-instruct"],
                "auth_header": "Bearer codegen-test-key"
            },
            {
                "id": "talkai",
                "name": "TalkAI",
                "endpoint": "http://localhost:8012",
                "models": ["MBZUAI-IFM/K2-Think", "MBZUAI-IFM/K2-Think-Reasoning"],
                "auth_header": "Bearer sk-talkai-test-key"
            }
        ]
    
    def _load_test_queries(self) -> List[Dict[str, Any]]:
        """Load test queries for validation"""
        return [
            {
                "name": "Simple Greeting",
                "query": "Hello! How are you today?",
                "expected_keywords": ["hello", "hi", "good", "fine", "well", "today"],
                "min_length": 10,
                "coherence_checks": ["greeting_response", "polite_tone"]
            },
            {
                "name": "Math Problem",
                "query": "What is 15 + 27? Please show your work.",
                "expected_keywords": ["42", "fifteen", "twenty-seven", "add", "sum"],
                "min_length": 15,
                "coherence_checks": ["math_accuracy", "explanation_provided"]
            },
            {
                "name": "Creative Writing",
                "query": "Write a short story about a robot learning to paint.",
                "expected_keywords": ["robot", "paint", "learn", "art", "story"],
                "min_length": 100,
                "coherence_checks": ["narrative_structure", "creative_content"]
            },
            {
                "name": "Technical Question",
                "query": "Explain the difference between REST and GraphQL APIs.",
                "expected_keywords": ["REST", "GraphQL", "API", "difference", "endpoint"],
                "min_length": 50,
                "coherence_checks": ["technical_accuracy", "clear_explanation"]
            },
            {
                "name": "Reasoning Task",
                "query": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
                "expected_keywords": ["logic", "reasoning", "conclude", "roses", "flowers", "red"],
                "min_length": 30,
                "coherence_checks": ["logical_reasoning", "clear_conclusion"]
            }
        ]
    
    async def validate_all_endpoints(self) -> Dict[str, Any]:
        """Validate all provider endpoints with comprehensive testing"""
        logger.info("🚀 Starting comprehensive endpoint validation for 13 providers...")
        
        start_time = time.time()
        
        # Test each provider with each query
        tasks = []
        for provider in self.providers:
            for query in self.test_queries:
                task = self._test_provider_endpoint(provider, query)
                tasks.append(task)
        
        # Run all tests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, TestResult):
                self.results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Test failed with exception: {result}")
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        report = self._generate_validation_report(total_time)
        
        logger.info(f"✅ Validation completed in {total_time:.2f} seconds")
        return report
    
    async def _test_provider_endpoint(self, provider: Dict[str, Any], query: Dict[str, Any]) -> TestResult:
        """Test a specific provider endpoint with a specific query"""
        
        result = TestResult(
            provider_id=provider["id"],
            provider_name=provider["name"],
            endpoint=provider["endpoint"],
            status=TestStatus.PENDING,
            response_time=0.0,
            response_content="",
            model_used=provider["models"][0] if provider["models"] else None
        )
        
        try:
            result.status = TestStatus.RUNNING
            logger.info(f"🧪 Testing {provider['name']} with query: {query['name']}")
            
            start_time = time.time()
            
            # Prepare request
            request_data = {
                "model": provider["models"][0] if provider["models"] else "default",
                "messages": [
                    {"role": "user", "content": query["query"]}
                ],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": provider["auth_header"]
            }
            
            # Make request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{provider['endpoint']}/v1/chat/completions",
                    json=request_data,
                    headers=headers
                )
                
                response_time = time.time() - start_time
                result.response_time = response_time
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Extract response content
                    if "choices" in response_data and response_data["choices"]:
                        content = response_data["choices"][0].get("message", {}).get("content", "")
                        result.response_content = content
                        
                        # Validate response coherence
                        coherence_score = self._validate_response_coherence(content, query)
                        result.coherence_score = coherence_score
                        
                        if coherence_score >= 0.6:  # 60% coherence threshold
                            result.status = TestStatus.SUCCESS
                            logger.info(f"✅ {provider['name']} - {query['name']}: SUCCESS (coherence: {coherence_score:.2f})")
                        else:
                            result.status = TestStatus.FAILED
                            result.error_message = f"Low coherence score: {coherence_score:.2f}"
                            logger.warning(f"⚠️ {provider['name']} - {query['name']}: LOW COHERENCE ({coherence_score:.2f})")
                    else:
                        result.status = TestStatus.FAILED
                        result.error_message = "No content in response"
                        logger.error(f"❌ {provider['name']} - {query['name']}: NO CONTENT")
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ {provider['name']} - {query['name']}: HTTP {response.status_code}")
                    
        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.error_message = "Request timeout"
            logger.error(f"⏰ {provider['name']} - {query['name']}: TIMEOUT")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            logger.error(f"💥 {provider['name']} - {query['name']}: ERROR - {str(e)}")
        
        return result
    
    def _validate_response_coherence(self, content: str, query: Dict[str, Any]) -> float:
        """Validate response coherence and relevance"""
        if not content or len(content.strip()) < query.get("min_length", 10):
            return 0.0
        
        score = 0.0
        max_score = 1.0
        
        # Check for expected keywords (40% of score)
        keyword_score = 0.0
        expected_keywords = query.get("expected_keywords", [])
        if expected_keywords:
            found_keywords = sum(1 for keyword in expected_keywords 
                               if keyword.lower() in content.lower())
            keyword_score = found_keywords / len(expected_keywords)
        
        score += keyword_score * 0.4
        
        # Check minimum length requirement (20% of score)
        min_length = query.get("min_length", 10)
        length_score = min(1.0, len(content.strip()) / min_length)
        score += length_score * 0.2
        
        # Check for coherence indicators (40% of score)
        coherence_score = 0.0
        
        # Basic coherence checks
        if len(content.split()) >= 3:  # At least 3 words
            coherence_score += 0.2
        
        if any(char in content for char in '.!?'):  # Has punctuation
            coherence_score += 0.2
        
        if not any(word in content.lower() for word in ['error', 'failed', 'cannot', 'unable']):
            coherence_score += 0.3
        
        if len(content.split('\n')) <= 10:  # Not excessively long
            coherence_score += 0.1
        
        if content.strip() and not content.startswith('Error'):
            coherence_score += 0.2
        
        score += coherence_score * 0.4
        
        return min(1.0, score)
    
    def _generate_validation_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        # Group results by provider
        provider_results = {}
        for result in self.results:
            if result.provider_id not in provider_results:
                provider_results[result.provider_id] = {
                    "name": result.provider_name,
                    "endpoint": result.endpoint,
                    "tests": [],
                    "success_count": 0,
                    "total_tests": 0,
                    "avg_response_time": 0.0,
                    "avg_coherence": 0.0
                }
            
            provider_results[result.provider_id]["tests"].append({
                "status": result.status.value,
                "response_time": result.response_time,
                "coherence_score": result.coherence_score,
                "error_message": result.error_message,
                "response_preview": result.response_content[:100] + "..." if len(result.response_content) > 100 else result.response_content
            })
            
            provider_results[result.provider_id]["total_tests"] += 1
            if result.status == TestStatus.SUCCESS:
                provider_results[result.provider_id]["success_count"] += 1
        
        # Calculate statistics
        for provider_id, data in provider_results.items():
            if data["total_tests"] > 0:
                data["success_rate"] = data["success_count"] / data["total_tests"]
                
                successful_tests = [t for t in data["tests"] if t["status"] == "success"]
                if successful_tests:
                    data["avg_response_time"] = sum(t["response_time"] for t in successful_tests) / len(successful_tests)
                    data["avg_coherence"] = sum(t["coherence_score"] for t in successful_tests) / len(successful_tests)
        
        # Overall statistics
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.status == TestStatus.SUCCESS])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR])
        
        overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Working providers
        working_providers = []
        for provider_id, data in provider_results.items():
            if data.get("success_rate", 0) > 0:
                working_providers.append({
                    "id": provider_id,
                    "name": data["name"],
                    "success_rate": data["success_rate"],
                    "avg_response_time": data["avg_response_time"],
                    "avg_coherence": data["avg_coherence"]
                })
        
        working_providers.sort(key=lambda x: x["success_rate"], reverse=True)
        
        report = {
            "validation_summary": {
                "total_providers": len(self.providers),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "overall_success_rate": overall_success_rate,
                "total_time": total_time,
                "working_providers_count": len(working_providers)
            },
            "working_providers": working_providers,
            "provider_details": provider_results,
            "test_queries": [q["name"] for q in self.test_queries],
            "timestamp": time.time()
        }
        
        return report
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print a formatted summary report"""
        
        print("\n" + "="*80)
        print("🎯 UNIFIED AI PROVIDER VALIDATION REPORT")
        print("="*80)
        
        summary = report["validation_summary"]
        print(f"📊 OVERALL STATISTICS:")
        print(f"   • Total Providers Tested: {summary['total_providers']}")
        print(f"   • Total Tests Executed: {summary['total_tests']}")
        print(f"   • Successful Tests: {summary['successful_tests']} ✅")
        print(f"   • Failed Tests: {summary['failed_tests']} ❌")
        print(f"   • Error Tests: {summary['error_tests']} 💥")
        print(f"   • Overall Success Rate: {summary['overall_success_rate']:.1%}")
        print(f"   • Working Providers: {summary['working_providers_count']}/{summary['total_providers']}")
        print(f"   • Total Validation Time: {summary['total_time']:.2f}s")
        
        print(f"\n🏆 WORKING PROVIDERS (Ranked by Success Rate):")
        if report["working_providers"]:
            for i, provider in enumerate(report["working_providers"], 1):
                print(f"   {i}. {provider['name']}")
                print(f"      Success Rate: {provider['success_rate']:.1%}")
                print(f"      Avg Response Time: {provider['avg_response_time']:.0f}ms")
                print(f"      Avg Coherence: {provider['avg_coherence']:.2f}")
                print()
        else:
            print("   ❌ No providers are currently working!")
        
        print(f"🧪 TEST QUERIES USED:")
        for i, query in enumerate(report["test_queries"], 1):
            print(f"   {i}. {query}")
        
        print("\n" + "="*80)
        
        if summary['working_providers_count'] > 0:
            print(f"🎉 SUCCESS: {summary['working_providers_count']} providers are working and returning coherent responses!")
        else:
            print("⚠️  WARNING: No providers are currently working. Check configurations and endpoints.")
        
        print("="*80)


async def main():
    """Main validation function"""
    validator = EndpointValidator()
    
    print("🚀 Starting comprehensive validation of 13 AI providers...")
    print("This will test each provider with 5 different queries to validate coherent responses.\n")
    
    # Run validation
    report = await validator.validate_all_endpoints()
    
    # Print summary
    validator.print_summary_report(report)
    
    # Save detailed report
    with open("validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: validation_report.json")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
