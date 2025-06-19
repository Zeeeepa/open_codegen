#!/usr/bin/env python3
"""
OpenAI Codegen Adapter Server Runner
Supports both regular and transparent interception modes.
"""

import os
import uvicorn
import sys
from pathlib import Path

def main():
    """Start the OpenAI Codegen Adapter server."""
    # Set default credentials if not provided
    if not os.getenv('CODEGEN_ORG_ID'):
        os.environ['CODEGEN_ORG_ID'] = "323"
    if not os.getenv('CODEGEN_TOKEN'):
        os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    # Check if running in transparent mode
    transparent_mode = os.getenv('TRANSPARENT_MODE', 'false').lower() == 'true'
    bind_privileged = os.getenv('BIND_PRIVILEGED_PORTS', 'false').lower() == 'true'
    
    # Get server configuration
    host = os.getenv('SERVER_HOST', '0.0.0.0' if transparent_mode else '127.0.0.1')
    port = int(os.getenv('SERVER_PORT', '80' if bind_privileged else '8001'))
    https_port = int(os.getenv('HTTPS_PORT', '443' if bind_privileged else '8443'))
    
    # SSL configuration
    ssl_cert_path = os.getenv('SSL_CERT_PATH')
    ssl_key_path = os.getenv('SSL_KEY_PATH')
    
    print("🚀 Starting OpenAI Codegen Adapter Server")
    print("=" * 50)
    
    if transparent_mode:
        print("🔄 Mode: TRANSPARENT INTERCEPTION")
        print(f"🌐 Intercepting: api.openai.com -> {host}")
        print(f"📍 HTTP Server: http://{host}:{port}")
        
        if ssl_cert_path and ssl_key_path and Path(ssl_cert_path).exists() and Path(ssl_key_path).exists():
            print(f"🔐 HTTPS Server: https://{host}:{https_port}")
            print("✅ SSL certificates found - HTTPS interception enabled")
        else:
            print("⚠️ SSL certificates not found - HTTPS interception disabled")
            print("   Run: sudo python3 -m interceptor.ubuntu_ssl setup")
    else:
        print("🚀 Mode: DIRECT ACCESS")
        print(f"📍 Server: http://{host}:{port}")
        print(f"🔗 OpenAI API endpoint: http://{host}:{port}/v1")
    
    print("=" * 50)
    
    # Check for root privileges if binding to privileged ports
    if bind_privileged and os.geteuid() != 0:
        print("❌ Error: Root privileges required for ports 80/443")
        print("   Run with: sudo python3 server.py")
        sys.exit(1)
    
    # Start HTTP server
    try:
        if ssl_cert_path and ssl_key_path and Path(ssl_cert_path).exists() and Path(ssl_key_path).exists():
            # Start HTTPS server
            print(f"🔐 Starting HTTPS server on port {https_port}...")
            uvicorn.run(
                "openai_codegen_adapter.server:app",
                host=host,
                port=https_port,
                ssl_certfile=ssl_cert_path,
                ssl_keyfile=ssl_key_path,
                log_level="info",
                reload=False
            )
        else:
            # Start HTTP server
            print(f"🌐 Starting HTTP server on port {port}...")
            uvicorn.run(
                "openai_codegen_adapter.server:app",
                host=host,
                port=port,
                log_level="info",
                reload=False
            )
    except PermissionError:
        print("❌ Permission denied. For privileged ports, run with sudo.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
