#!/usr/bin/env python3
"""
Health Check Utility for OpenAI Codegen Adapter
Provides comprehensive health monitoring and diagnostics
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from config import load_config, setup_logging

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: float
    details: Dict[str, Any]
    error: str = None

class HealthChecker:
    """Comprehensive health checker for the adapter"""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logging(config)
        self.base_url = f"http://{config.server.host}:{config.server.port}"
    
    async def check_server_health(self) -> HealthCheckResult:
        """Check if the adapter server is running and responsive"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheckResult(
                            service="adapter_server",
                            status="healthy",
                            response_time_ms=response_time,
                            details=data
                        )
                    else:
                        return HealthCheckResult(
                            service="adapter_server",
                            status="unhealthy",
                            response_time_ms=response_time,
                            details={"status_code": response.status},
                            error=f"HTTP {response.status}"
                        )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="adapter_server",
                status="unhealthy",
                response_time_ms=response_time,
                details={},
                error=str(e)
            )
    
    async def check_openai_endpoint(self) -> HealthCheckResult:
        """Check OpenAI-compatible endpoint"""
        start_time = time.time()
        
        try:
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "Health check"}],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=10
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheckResult(
                            service="openai_endpoint",
                            status="healthy",
                            response_time_ms=response_time,
                            details={
                                "model": data.get("model"),
                                "choices_count": len(data.get("choices", []))
                            }
                        )
                    else:
                        error_text = await response.text()
                        return HealthCheckResult(
                            service="openai_endpoint",
                            status="unhealthy",
                            response_time_ms=response_time,
                            details={"status_code": response.status},
                            error=error_text
                        )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="openai_endpoint",
                status="unhealthy",
                response_time_ms=response_time,
                details={},
                error=str(e)
            )
    
    async def check_anthropic_endpoint(self) -> HealthCheckResult:
        """Check Anthropic-compatible endpoint"""
        start_time = time.time()
        
        try:
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Health check"}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    timeout=10
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheckResult(
                            service="anthropic_endpoint",
                            status="healthy",
                            response_time_ms=response_time,
                            details={
                                "model": data.get("model"),
                                "content_count": len(data.get("content", []))
                            }
                        )
                    else:
                        error_text = await response.text()
                        return HealthCheckResult(
                            service="anthropic_endpoint",
                            status="unhealthy",
                            response_time_ms=response_time,
                            details={"status_code": response.status},
                            error=error_text
                        )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="anthropic_endpoint",
                status="unhealthy",
                response_time_ms=response_time,
                details={},
                error=str(e)
            )
    
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        self.logger.info("Starting comprehensive health check...")
        
        checks = [
            self.check_server_health(),
            self.check_openai_endpoint(),
            self.check_anthropic_endpoint()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(HealthCheckResult(
                    service=f"check_{i}",
                    status="unknown",
                    response_time_ms=0,
                    details={},
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def print_results(self, results: List[HealthCheckResult]):
        """Print health check results in a formatted way"""
        print("\n" + "="*60)
        print("🏥 HEALTH CHECK RESULTS")
        print("="*60)
        
        overall_healthy = True
        
        for result in results:
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "❌", 
                "unknown": "❓"
            }.get(result.status, "❓")
            
            print(f"\n{status_emoji} {result.service.upper()}")
            print(f"   Status: {result.status}")
            print(f"   Response Time: {result.response_time_ms:.1f}ms")
            
            if result.details:
                print(f"   Details: {json.dumps(result.details, indent=6)}")
            
            if result.error:
                print(f"   Error: {result.error}")
                overall_healthy = False
            
            if result.status != "healthy":
                overall_healthy = False
        
        print("\n" + "="*60)
        if overall_healthy:
            print("🎉 ALL SYSTEMS HEALTHY!")
        else:
            print("⚠️  SOME ISSUES DETECTED - CHECK LOGS ABOVE")
        print("="*60)
        
        return overall_healthy

async def main():
    """Main health check function"""
    try:
        config = load_config()
        checker = HealthChecker(config)
        
        results = await checker.run_all_checks()
        healthy = checker.print_results(results)
        
        # Exit with appropriate code
        exit(0 if healthy else 1)
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())

