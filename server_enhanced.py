#!/usr/bin/env python3
"""
Enhanced FastAPI server for OpenAI Codegen Adapter.
Includes comprehensive error handling, metrics, health monitoring, and middleware.
Supports OpenAI, Anthropic, and Google Gemini APIs.
"""

import logging
import uvicorn
from fastapi import FastAPI

from openai_codegen_adapter.server import app as original_app
from openai_codegen_adapter.middleware import setup_middleware
from openai_codegen_adapter.health import health_router
from openai_codegen_adapter.config import get_server_config

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('adapter.log')
    ]
)

logger = logging.getLogger(__name__)

def create_enhanced_app() -> FastAPI:
    """Create enhanced FastAPI app with all middleware and features."""
    
    # Use the original app as base
    app = original_app
    
    # Set up middleware
    setup_middleware(app)
    
    # Include health router
    app.include_router(health_router)
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 OpenAI Codegen Adapter starting up...")
        logger.info("✨ Features enabled:")
        logger.info("   • OpenAI API compatibility")
        logger.info("   • Anthropic Claude API compatibility") 
        logger.info("   • Google Gemini API compatibility")
        logger.info("   • Enhanced error handling")
        logger.info("   • Comprehensive metrics")
        logger.info("   • Health monitoring")
        logger.info("   • Request/response middleware")
        logger.info("🎯 Ready to serve requests!")
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 OpenAI Codegen Adapter shutting down...")
        logger.info("📊 Final metrics summary:")
        
        from openai_codegen_adapter.metrics import metrics_collector
        stats = metrics_collector.get_summary_stats()
        logger.info(f"   • Total requests: {stats.get('total_requests', 0)}")
        logger.info(f"   • Success rate: {stats.get('success_rate', 0)*100:.1f}%")
        logger.info(f"   • Uptime: {stats.get('uptime_minutes', 0):.1f} minutes")
        logger.info("👋 Goodbye!")
    
    return app


def main():
    """Main entry point for the enhanced server."""
    # Get server configuration
    server_config = get_server_config()
    
    # Create enhanced app
    app = create_enhanced_app()
    
    # Log startup information
    logger.info("🔧 Server Configuration:")
    logger.info(f"   • Host: {server_config.host}")
    logger.info(f"   • Port: {server_config.port}")
    logger.info(f"   • Log Level: {server_config.log_level}")
    logger.info(f"   • CORS Origins: {server_config.cors_origins}")
    
    # Run the server
    uvicorn.run(
        app,
        host=server_config.host,
        port=server_config.port,
        log_level=server_config.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()

