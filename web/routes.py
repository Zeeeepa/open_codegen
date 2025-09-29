"""
Web routes for the Universal AI API Gateway
"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

def setup_routes(app: FastAPI, templates: Jinja2Templates, api_gateway, config_manager):
    """Setup all web routes."""
    
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Main dashboard page."""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/chat", response_class=HTMLResponse)
    async def chat_interface(request: Request):
        """Chat interface page."""
        return templates.TemplateResponse("chat.html", {"request": request})
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_panel(request: Request):
        """Admin panel page."""
        return templates.TemplateResponse("admin.html", {"request": request})
    
    # API Routes
    @app.get("/api/health")
    async def health_check():
        """System health check."""
        try:
            health_status = await api_gateway.health_check()
            return health_status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Health check failed", "details": str(e)}
            )
    
    @app.get("/api/providers")
    async def get_providers():
        """Get all providers and their status."""
        try:
            providers = await api_gateway.get_available_providers()
            return providers
        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to get providers", "details": str(e)}
            )
    
    @app.post("/api/providers/{provider_name}/toggle")
    async def toggle_provider(provider_name: str, request: Request):
        """Toggle provider enabled/disabled status."""
        try:
            data = await request.json()
            enabled = data.get("enabled", False)
            
            # Update provider configuration
            provider_config = config_manager.get_provider_config(provider_name)
            if not provider_config:
                raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
            
            provider_config["enabled"] = enabled
            config_manager.update_provider_config(provider_name, provider_config)
            
            return {"success": True, "provider": provider_name, "enabled": enabled}
            
        except Exception as e:
            logger.error(f"Failed to toggle provider {provider_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/providers/{provider_name}/test")
    async def test_provider(provider_name: str):
        """Test a specific provider."""
        try:
            result = await api_gateway.test_provider(provider_name)
            return result
        except Exception as e:
            logger.error(f"Failed to test provider {provider_name}: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    @app.post("/api/chat")
    async def chat_endpoint(request: Request):
        """Chat endpoint for testing providers."""
        try:
            data = await request.json()
            message = data.get("message", "")
            provider = data.get("provider")
            api_format = data.get("format", "openai")  # openai, anthropic, gemini
            
            if not message:
                raise HTTPException(status_code=400, detail="Message is required")
            
            # Create a mock API request based on the format
            if api_format == "openai":
                request_data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": message}],
                    "stream": False
                }
            elif api_format == "anthropic":
                request_data = {
                    "model": "claude-3-sonnet-20240229",
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 1000
                }
            elif api_format == "gemini":
                request_data = {
                    "contents": [{"parts": [{"text": message}]}],
                    "generationConfig": {"maxOutputTokens": 1000}
                }
            else:
                raise HTTPException(status_code=400, detail="Invalid API format")
            
            # Process through the gateway
            response = await api_gateway.process_request(
                request_data=request_data,
                headers={"content-type": "application/json"},
                provider_override=provider
            )
            
            return {
                "success": True,
                "response": response,
                "provider": provider,
                "format": api_format
            }
            
        except Exception as e:
            logger.error(f"Chat endpoint failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    # Universal API endpoints (OpenAI compatible)
    @app.post("/v1/chat/completions")
    async def openai_chat_completions(request: Request):
        """OpenAI-compatible chat completions endpoint."""
        try:
            request_data = await request.json()
            headers = dict(request.headers)
            
            response = await api_gateway.process_request(request_data, headers)
            return response
            
        except Exception as e:
            logger.error(f"OpenAI chat completions failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/v1/completions")
    async def openai_completions(request: Request):
        """OpenAI-compatible completions endpoint."""
        try:
            request_data = await request.json()
            headers = dict(request.headers)
            
            response = await api_gateway.process_request(request_data, headers)
            return response
            
        except Exception as e:
            logger.error(f"OpenAI completions failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Anthropic compatible endpoints
    @app.post("/v1/messages")
    async def anthropic_messages(request: Request):
        """Anthropic-compatible messages endpoint."""
        try:
            request_data = await request.json()
            headers = dict(request.headers)
            
            response = await api_gateway.process_request(request_data, headers)
            return response
            
        except Exception as e:
            logger.error(f"Anthropic messages failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Gemini compatible endpoints
    @app.post("/v1/models/{model_name}:generateContent")
    async def gemini_generate_content(model_name: str, request: Request):
        """Gemini-compatible generate content endpoint."""
        try:
            request_data = await request.json()
            request_data["model"] = model_name  # Add model to request data
            headers = dict(request.headers)
            
            response = await api_gateway.process_request(request_data, headers)
            return response
            
        except Exception as e:
            logger.error(f"Gemini generate content failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/v1/models")
    async def list_models():
        """List available models (OpenAI compatible)."""
        return {
            "object": "list",
            "data": [
                {
                    "id": "universal-gateway",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "universal-gateway",
                    "permission": [],
                    "root": "universal-gateway",
                    "parent": None
                }
            ]
        }
    
    # Admin API endpoints
    @app.post("/api/admin/save-config")
    async def save_admin_config(request: Request):
        """Save admin configuration changes."""
        try:
            data = await request.json()
            providers_config = data.get("providers", {})
            
            # Update provider configurations
            for name, config in providers_config.items():
                if hasattr(api_gateway.provider_manager, 'update_provider_config'):
                    await api_gateway.provider_manager.update_provider_config(name, config)
            
            # Save to config file
            config_manager.save_config({
                "providers": providers_config,
                "last_updated": "admin_panel"
            })
            
            return {"success": True, "message": "Configuration saved successfully"}
            
        except Exception as e:
            logger.error(f"Failed to save admin config: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    @app.get("/api/admin/system-settings")
    async def get_system_settings():
        """Get current system settings."""
        try:
            config = config_manager.load_config()
            return {
                "timeout": config.get("default_timeout", 60),
                "retries": config.get("max_retries", 3),
                "logging": config.get("enable_logging", True)
            }
        except Exception as e:
            logger.error(f"Failed to get system settings: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )
    
    @app.post("/api/admin/system-settings")
    async def save_system_settings(request: Request):
        """Save system settings."""
        try:
            settings = await request.json()
            
            # Update configuration
            config = config_manager.load_config()
            config.update({
                "default_timeout": settings.get("timeout", 60),
                "max_retries": settings.get("retries", 3),
                "enable_logging": settings.get("logging", True)
            })
            
            config_manager.save_config(config)
            
            return {"success": True, "message": "System settings saved successfully"}
            
        except Exception as e:
            logger.error(f"Failed to save system settings: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    @app.post("/api/providers/bulk-enable")
    async def bulk_enable_providers():
        """Enable all providers."""
        try:
            providers = await api_gateway.get_available_providers()
            enabled_count = 0
            total_count = len(providers)
            
            for name in providers.keys():
                try:
                    # Enable each provider
                    response = await api_gateway.provider_manager.toggle_provider(name, True)
                    if response:
                        enabled_count += 1
                except Exception as e:
                    logger.warning(f"Failed to enable provider {name}: {e}")
            
            return {
                "success": True,
                "enabled_count": enabled_count,
                "total_count": total_count,
                "message": f"Enabled {enabled_count} out of {total_count} providers"
            }
            
        except Exception as e:
            logger.error(f"Bulk enable failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    @app.post("/api/providers/bulk-disable")
    async def bulk_disable_providers():
        """Disable all providers."""
        try:
            providers = await api_gateway.get_available_providers()
            disabled_count = 0
            total_count = len(providers)
            
            for name in providers.keys():
                try:
                    # Disable each provider
                    response = await api_gateway.provider_manager.toggle_provider(name, False)
                    if response:
                        disabled_count += 1
                except Exception as e:
                    logger.warning(f"Failed to disable provider {name}: {e}")
            
            return {
                "success": True,
                "disabled_count": disabled_count,
                "total_count": total_count,
                "message": f"Disabled {disabled_count} out of {total_count} providers"
            }
            
        except Exception as e:
            logger.error(f"Bulk disable failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
