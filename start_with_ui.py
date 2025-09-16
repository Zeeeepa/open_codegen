#!/usr/bin/env python3
"""
OpenAI Codegen Adapter with Web UI Startup Script

This script starts the OpenAI Codegen Adapter with the integrated web UI,
providing both API interception capabilities and a modern management interface.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the existing server components
from backend.adapter.server import app as existing_app
from backend.web_ui_integration import integrate_web_ui, setup_web_ui_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/server.log') if Path('logs').exists() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description='OpenAI Codegen Adapter with Web UI')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--no-ui', action='store_true', help='Disable web UI integration')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    logger.info("🚀 Starting OpenAI Codegen Adapter with Web UI")
    logger.info("=" * 50)
    
    # Setup environment
    setup_web_ui_environment()
    
    # Integrate web UI unless disabled
    if not args.no_ui:
        try:
            integrate_web_ui(existing_app)
            logger.info("✅ Web UI integration completed")
        except Exception as e:
            logger.error(f"❌ Web UI integration failed: {e}")
            logger.warning("⚠️ Continuing without web UI...")
    else:
        logger.info("⚠️ Web UI integration disabled")
    
    # Print startup information
    logger.info(f"🌐 Server starting on http://{args.host}:{args.port}")
    logger.info(f"📊 Web UI available at: http://localhost:{args.port}")
    logger.info(f"🔌 API endpoints available at: http://localhost:{args.port}/api/")
    logger.info(f"📖 OpenAI API compatibility: http://localhost:{args.port}/v1/")
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "start_with_ui:existing_app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

