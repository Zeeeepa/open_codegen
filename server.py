#!/usr/bin/env python3
"""
OpenAI Codegen Adapter Server Runner
Supports both regular and transparent interception modes.
Auto-manages DNS interception and cleanup on exit.
"""

import os
import uvicorn
import sys
import signal
import atexit
import logging
from pathlib import Path
from interceptor.ubuntu_dns import UbuntuDNSManager

# Global DNS manager instance for cleanup
dns_manager = None
dns_enabled_by_server = False

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )

def cleanup_dns_interception():
    """Cleanup DNS interception on exit."""
    global dns_manager, dns_enabled_by_server
    
    if dns_manager and dns_enabled_by_server:
        print("\n🔄 Cleaning up DNS interception...")
        try:
            if dns_manager.disable_interception():
                print("✅ DNS interception disabled successfully")
            else:
                print("⚠️ Failed to disable DNS interception")
        except Exception as e:
            print(f"❌ Error during DNS cleanup: {e}")

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    cleanup_dns_interception()
    sys.exit(0)

def setup_transparent_mode():
    """Setup DNS interception for transparent mode."""
    global dns_manager, dns_enabled_by_server
    
    dns_manager = UbuntuDNSManager()
    
    # Check if we need to enable DNS interception
    status = dns_manager.status()
    
    if not status["enabled"]:
        print("🔧 DNS interception not active, enabling...")
        if not dns_manager.is_root():
            print("❌ Error: Root privileges required for DNS interception")
            print("   Run with: sudo python3 server.py")
            sys.exit(1)
        
        if dns_manager.enable_interception():
            print("✅ DNS interception enabled successfully")
            dns_enabled_by_server = True
        else:
            print("❌ Failed to enable DNS interception")
            sys.exit(1)
    else:
        print("ℹ️ DNS interception already active")
        # Test if it's working
        if not dns_manager.test_dns_resolution():
            print("⚠️ DNS interception is enabled but not working properly")

def main():
    """Start the OpenAI Codegen Adapter server."""
    global dns_manager
    
    setup_logging()
    
    # Set default credentials if not provided
    if not os.getenv('CODEGEN_ORG_ID'):
        os.environ['CODEGEN_ORG_ID'] = "323"
    if not os.getenv('CODEGEN_TOKEN'):
        os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    # Auto-detect transparent mode if not explicitly set
    transparent_mode = os.getenv('TRANSPARENT_MODE', 'true').lower() == 'true'
    bind_privileged = os.getenv('BIND_PRIVILEGED_PORTS', 'false').lower() == 'true'
    
    # Setup signal handlers for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_dns_interception)
    
    # Setup transparent mode if enabled
    if transparent_mode:
        setup_transparent_mode()
    
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
        print("🎯 Applications using OpenAI API will automatically use Codegen!")
        
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
    print("💡 Press Ctrl+C to stop the server and cleanup DNS interception")
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
