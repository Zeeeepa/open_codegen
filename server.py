#!/usr/bin/env python3
"""
Simple server launcher for OpenAI Codegen Adapter
"""

import uvicorn
from openai_codegen_adapter.server import app
from openai_codegen_adapter.config import get_server_config

if __name__ == "__main__":
    print("🚀 Starting OpenAI Codegen Adapter...")
    server_config = get_server_config()
    uvicorn.run(
        app,
        host=server_config.host,
        port=server_config.port,
        log_level=server_config.log_level
    )

