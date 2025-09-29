#!/usr/bin/env python3
"""
Universal AI API Gateway - Main Entry Point
Intercepts OpenAI/Gemini/Anthropic API calls and routes through 9 providers
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from gateway.startup import SystemInitializer
from web.server import WebServer
from utils.logger import setup_logging

def main():
    """Main entry point - starts the entire system with one command."""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 Starting Universal AI API Gateway...")
    print("=" * 60)
    print("🎯 ANY API Call → Universal Parser → WebChat Interface → 9 Providers")
    print("📡 OpenAI/Gemini/Anthropic → z.ai, k2, grok, qwen, copilot, ChatGPT, Bing, codegen, talkai")
    print("=" * 60)
    
    try:
        # Initialize system
        initializer = SystemInitializer()
        
        # Check dependencies
        print("🔍 Checking dependencies...")
        if not initializer.check_dependencies():
            print("❌ Dependency check failed!")
            return 1
        
        # Validate configuration
        print("⚙️  Validating configuration...")
        if not initializer.validate_config():
            print("❌ Configuration validation failed!")
            return 1
        
        # Initialize providers
        print("🔌 Initializing providers...")
        if not asyncio.run(initializer.initialize_providers()):
            print("❌ Provider initialization failed!")
            return 1
        
        # Start web server
        print("🌐 Starting web interface...")
        web_server = WebServer(initializer.api_gateway)
        
        print("✅ System ready!")
        print("🎮 Web Interface: http://localhost:8000")
        print("🔗 API Gateway: http://localhost:8000/v1/")
        print("📊 Management: http://localhost:8000/admin")
        print("💬 Chat Interface: http://localhost:8000/chat")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        
        # Run the web server
        asyncio.run(web_server.run())
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        return 0
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        print(f"❌ System startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
