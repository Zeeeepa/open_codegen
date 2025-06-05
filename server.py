#!/usr/bin/env python3
"""
Simple server launcher for OpenAI Codegen Adapter
"""

import uvicorn
from openai_codegen_adapter.server import app

if __name__ == "__main__":
    print("🚀 Starting OpenAI Codegen Adapter...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8887,
        log_level="info"
    )

