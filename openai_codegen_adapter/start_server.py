#!/usr/bin/env python3
"""
Startup script for OpenAI Codegen Adapter
"""

import sys
import os
import uvicorn
from config import get_codegen_config, get_server_config, validate_config


def main():
    """Main startup function"""
    print("🚀 Starting OpenAI Codegen Adapter...")
    print("=" * 50)
    
    # Validate configuration
    if not validate_config():
        print("\n❌ Configuration validation failed!")
        print("Please set the required environment variables:")
        print("  - CODEGEN_API_TOKEN")
        print("  - CODEGEN_ORG_ID")
        print("\nExample:")
        print('  export CODEGEN_API_TOKEN="sk-your-token-here"')
        print('  export CODEGEN_ORG_ID="your-org-id"')
        sys.exit(1)
    
    # Get configuration
    codegen_config = get_codegen_config()
    server_config = get_server_config()
    
    print("✅ Configuration validated successfully!")
    print(f"📡 Server will start on {codegen_config.host}:{codegen_config.port}")
    print(f"🔗 Codegen API: {codegen_config.base_url}")
    print(f"📊 Log Level: {codegen_config.log_level}")
    print("=" * 50)
    
    try:
        # Import the FastAPI app
        from server import app
        
        # Start the server
        uvicorn.run(
            app,
            host=codegen_config.host,
            port=codegen_config.port,
            log_level=codegen_config.log_level.lower(),
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        print("Make sure you're in the correct directory and all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

