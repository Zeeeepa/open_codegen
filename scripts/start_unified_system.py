#!/usr/bin/env python3
"""
Unified System Startup Script
Starts all components of the AI Provider Gateway system
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.registry.service_registry import service_registry
from backend.services.service_manager import service_manager
from backend.gateway.api_gateway import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedSystemManager:
    """Manages the entire unified AI provider system"""
    
    def __init__(self):
        self.service_registry = service_registry
        self.service_manager = service_manager
        self.gateway_process = None
        
    async def start_system(self):
        """Start the complete unified system"""
        logger.info("🚀 Starting Unified AI Provider Gateway System...")
        
        try:
            # Step 1: Initialize service registry
            logger.info("📋 Initializing service registry...")
            self.service_registry.save_config()
            
            # Step 2: Start all provider services
            logger.info("🔧 Starting all AI provider services...")
            results = await self.service_manager.start_all_services()
            
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            logger.info(f"✅ Started {successful}/{total} provider services")
            
            if successful == 0:
                logger.warning("⚠️ No providers started successfully. System will run in limited mode.")
            
            # Step 3: Wait for services to be ready
            logger.info("⏳ Waiting for services to be ready...")
            await asyncio.sleep(10)
            
            # Step 4: Start health monitoring
            logger.info("🏥 Starting health monitoring...")
            asyncio.create_task(self.service_manager.health_monitor_loop())
            
            # Step 5: Start API Gateway
            logger.info("🌐 Starting API Gateway...")
            await self.start_gateway()
            
            logger.info("🎉 Unified AI Provider Gateway System is now running!")
            self.print_system_info()
            
            # Keep the system running
            await self.keep_running()
            
        except Exception as e:
            logger.error(f"❌ Failed to start system: {e}")
            await self.shutdown_system()
            raise
    
    async def start_gateway(self):
        """Start the API Gateway"""
        import uvicorn
        
        # Start gateway in background
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=7999,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        
        # Run server in background task
        asyncio.create_task(server.serve())
        
        # Wait a bit for server to start
        await asyncio.sleep(3)
    
    def print_system_info(self):
        """Print system information"""
        services = self.service_registry.get_all_services()
        healthy_services = self.service_registry.get_healthy_services()
        
        print("\n" + "="*80)
        print("🤖 AI PROVIDER GATEWAY SYSTEM - READY")
        print("="*80)
        print(f"📊 Total Providers: {len(services)}")
        print(f"✅ Healthy Providers: {len(healthy_services)}")
        print(f"🌐 API Gateway: http://localhost:7999")
        print(f"📱 Dashboard: http://localhost:7999 (serve frontend/enhanced_index.html)")
        print("\n🔗 Key Endpoints:")
        print("   • OpenAI API: http://localhost:7999/v1/chat/completions")
        print("   • Health Check: http://localhost:7999/health")
        print("   • Providers: http://localhost:7999/providers")
        print("   • Models: http://localhost:7999/v1/models")
        print("   • Test: http://localhost:7999/v1/test")
        
        print("\n🔧 Provider Services:")
        for name, service in services.items():
            status_emoji = "✅" if service.status.value == "healthy" else "❌" if service.status.value == "unhealthy" else "⏸️"
            print(f"   {status_emoji} {name}: http://localhost:{service.port} ({service.status.value})")
        
        print("\n💡 Usage Examples:")
        print("   # Test with curl:")
        print("   curl -X POST http://localhost:7999/v1/chat/completions \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"model\":\"gpt-3.5-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'")
        print("\n   # Test specific provider:")
        print("   curl -X POST 'http://localhost:7999/v1/chat/completions?provider=qwen-api' \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"model\":\"qwen-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'")
        
        print("\n🎛️ Management:")
        print("   • Start provider: POST /providers/{name}/start")
        print("   • Stop provider: POST /providers/{name}/stop")
        print("   • Start all: POST /providers/start-all")
        print("   • Stop all: POST /providers/stop-all")
        print("="*80)
    
    async def keep_running(self):
        """Keep the system running"""
        try:
            while True:
                await asyncio.sleep(60)
                
                # Periodic status update
                healthy_count = len(self.service_registry.get_healthy_services())
                total_count = len(self.service_registry.get_all_services())
                logger.info(f"💓 System heartbeat: {healthy_count}/{total_count} providers healthy")
                
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal...")
            await self.shutdown_system()
    
    async def shutdown_system(self):
        """Gracefully shutdown the system"""
        logger.info("🛑 Shutting down Unified AI Provider Gateway System...")
        
        try:
            # Stop all provider services
            await self.service_manager.stop_all_services()
            logger.info("✅ All provider services stopped")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        
        logger.info("👋 System shutdown complete")

async def main():
    """Main entry point"""
    print("🚀 Unified AI Provider Gateway System")
    print("=====================================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Create system manager and start
    system = UnifiedSystemManager()
    
    try:
        await system.start_system()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
