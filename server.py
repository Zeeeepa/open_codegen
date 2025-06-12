#!/usr/bin/env python3
"""
Simple server runner for OpenAI Codegen Adapter.
Starts the FastAPI server on localhost:8001
"""

import os
import uvicorn

def main():
    """Start the OpenAI Codegen Adapter server."""
    # Set credentials
    os.environ['CODEGEN_ORG_ID'] = "323"
    os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    print("🚀 Starting OpenAI Codegen Adapter Server")
    print("📍 Server will be available at: http://localhost:8001")
    print("🔗 OpenAI API endpoint: http://localhost:8001/v1")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "openai_codegen_adapter.server:app",
        host="127.0.0.1",
        port=8001,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
