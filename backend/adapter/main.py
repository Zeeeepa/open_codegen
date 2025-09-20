#!/usr/bin/env python3
"""
Main entry point for the OpenAI Codegen Adapter.
Can be run directly or as a module.
"""

import os
import sys
import uvicorn

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Start the adapter server."""
    print("🚀 Starting OpenAI Codegen Adapter")
    
    # Check credentials
    org_id = os.getenv("CODEGEN_ORG_ID")
    token = os.getenv("CODEGEN_TOKEN")
    
    if not org_id or not token:
        print("❌ Missing credentials!")
        print("Please set environment variables:")
        print("   export CODEGEN_ORG_ID=your_org_id")
        print("   export CODEGEN_TOKEN=your_token")
        sys.exit(1)
    
    print(f"✅ Credentials configured for org: {org_id}")
    print("🌐 Server starting at: http://localhost:8001")
    
    # Start the server
    uvicorn.run(
        "openai_codegen_adapter.server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
