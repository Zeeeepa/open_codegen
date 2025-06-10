#!/usr/bin/env python3
"""
Web UI Dashboard Server
======================

A FastAPI server that provides a web dashboard for the OpenAI Codegen Adapter.
Features:
- Service provider configuration
- Real-time message history
- Test buttons for each service
- Session statistics
- Live status monitoring
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.service_providers import get_all_service_providers


class TestRequest(BaseModel):
    """Request model for running tests."""
    service: str
    endpoint: str


class TestResponse(BaseModel):
    """Response model for test results."""
    success: bool
    service: str
    prompt: str
    response: str
    error: Optional[str] = None
    timestamp: str


class DashboardServer:
    """Web dashboard server for the OpenAI Codegen Adapter."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="OpenAI Codegen Adapter Dashboard",
            description="Web dashboard for managing and testing AI service providers",
            version="1.0.0"
        )
        
        # Setup templates and static files
        self.templates_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
        
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Mount static files if directory exists and has content
        if self.static_dir.exists() and any(self.static_dir.iterdir()):
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all routes for the dashboard."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Serve the main dashboard page."""
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/providers")
        async def get_providers():
            """Get all available service providers."""
            providers = get_all_service_providers()
            return {
                name: {
                    "name": config.name,
                    "base_url": config.base_url,
                    "api_version": config.api_version,
                    "supports_streaming": config.supports_streaming,
                    "supports_multimodal": config.supports_multimodal
                }
                for name, config in providers.items()
            }
        
        @self.app.post("/api/test")
        async def run_test(test_request: TestRequest):
            """Run a test for a specific service."""
            try:
                result = await self.execute_test(test_request.service, test_request.endpoint)
                return result
            except Exception as e:
                return TestResponse(
                    success=False,
                    service=test_request.service,
                    prompt="Test request",
                    response="",
                    error=str(e),
                    timestamp=datetime.now().isoformat()
                )
        
        @self.app.get("/api/status/{service}")
        async def check_service_status(service: str):
            """Check the status of a specific service."""
            try:
                # This would check if the service is reachable
                # For now, we'll return a simple status
                return {"service": service, "status": "online", "timestamp": datetime.now().isoformat()}
            except Exception as e:
                return {"service": service, "status": "offline", "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def execute_test(self, service: str, endpoint: str) -> TestResponse:
        """Execute a test for the specified service."""
        timestamp = datetime.now().isoformat()
        
        try:
            if service.lower() == "openai":
                return await self.test_openai(endpoint, timestamp)
            elif service.lower() == "anthropic":
                return await self.test_anthropic(endpoint, timestamp)
            elif service.lower() == "google":
                return await self.test_google(endpoint, timestamp)
            else:
                raise ValueError(f"Unknown service: {service}")
                
        except Exception as e:
            return TestResponse(
                success=False,
                service=service,
                prompt="Test request",
                response="",
                error=str(e),
                timestamp=timestamp
            )
    
    async def test_openai(self, endpoint: str, timestamp: str) -> TestResponse:
        """Test OpenAI service."""
        prompt = "Explain quantum computing in simple terms."
        
        try:
            # Run the enhanced test script
            result = await self.run_test_script("test_openai_enhanced.py", endpoint)
            
            if result["success"]:
                return TestResponse(
                    success=True,
                    service="OPENAI",
                    prompt=prompt,
                    response=result["response"],
                    timestamp=timestamp
                )
            else:
                return TestResponse(
                    success=False,
                    service="OPENAI",
                    prompt=prompt,
                    response="",
                    error=result["error"],
                    timestamp=timestamp
                )
                
        except Exception as e:
            return TestResponse(
                success=False,
                service="OPENAI",
                prompt=prompt,
                response="",
                error=str(e),
                timestamp=timestamp
            )
    
    async def test_anthropic(self, endpoint: str, timestamp: str) -> TestResponse:
        """Test Anthropic service."""
        prompt = "What are three interesting facts about space exploration?"
        
        try:
            # Run the enhanced test script
            result = await self.run_test_script("test_anthropic_enhanced.py", endpoint)
            
            if result["success"]:
                return TestResponse(
                    success=True,
                    service="ANTHROPIC",
                    prompt=prompt,
                    response=result["response"],
                    timestamp=timestamp
                )
            else:
                return TestResponse(
                    success=False,
                    service="ANTHROPIC",
                    prompt=prompt,
                    response="",
                    error=result["error"],
                    timestamp=timestamp
                )
                
        except Exception as e:
            return TestResponse(
                success=False,
                service="ANTHROPIC",
                prompt=prompt,
                response="",
                error=str(e),
                timestamp=timestamp
            )
    
    async def test_google(self, endpoint: str, timestamp: str) -> TestResponse:
        """Test Google service."""
        prompt = "What are three interesting facts about space exploration?"
        
        try:
            # Run the enhanced test script
            result = await self.run_test_script("test_google_enhanced.py", endpoint)
            
            if result["success"]:
                return TestResponse(
                    success=True,
                    service="GEMINI",
                    prompt=prompt,
                    response=result["response"],
                    timestamp=timestamp
                )
            else:
                return TestResponse(
                    success=False,
                    service="GEMINI",
                    prompt=prompt,
                    response="",
                    error=result["error"],
                    timestamp=timestamp
                )
                
        except Exception as e:
            return TestResponse(
                success=False,
                service="GEMINI",
                prompt=prompt,
                response="",
                error=str(e),
                timestamp=timestamp
            )
    
    async def run_test_script(self, script_name: str, endpoint: str) -> Dict[str, Any]:
        """Run a test script and return the result."""
        try:
            # Change to the root directory
            root_dir = Path(__file__).parent.parent
            script_path = root_dir / script_name
            
            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"Test script {script_name} not found"
                }
            
            # Set environment variable for the endpoint
            env = os.environ.copy()
            if "openai" in script_name.lower():
                env["OPENAI_BASE_URL"] = endpoint
            elif "anthropic" in script_name.lower():
                env["ANTHROPIC_BASE_URL"] = endpoint
            elif "google" in script_name.lower():
                env["GOOGLE_BASE_URL"] = endpoint
            
            # Run the script
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                cwd=str(root_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Try to parse the output as JSON
                try:
                    output = stdout.decode().strip()
                    result = json.loads(output)
                    return result
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "response": stdout.decode().strip()
                    }
            else:
                return {
                    "success": False,
                    "error": stderr.decode().strip() or stdout.decode().strip()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def run(self):
        """Run the dashboard server."""
        print(f"🌐 Starting OpenAI Codegen Adapter Dashboard")
        print(f"📊 Dashboard URL: http://{self.host}:{self.port}")
        print(f"🔧 Configure service providers and run tests")
        print(f"�� View real-time message history")
        print()
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


def main():
    """Main entry point for the dashboard server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Codegen Adapter Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8888, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = DashboardServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()
