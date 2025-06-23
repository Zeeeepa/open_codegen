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
import threading
import time
import ssl
import ipaddress
from pathlib import Path
from .interceptor.ubuntu_dns import UbuntuDNSManager

# Global DNS manager instance for cleanup
dns_manager = None
dns_enabled_by_server = False

def generate_self_signed_cert(cert_path="server.crt", key_path="server.key"):
    """Generate a self-signed certificate for HTTPS interception."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Codegen"),
            x509.NameAttribute(NameOID.COMMON_NAME, "api.openai.com"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("api.openai.com"),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return True
    except ImportError:
        print("⚠️ cryptography package not available for certificate generation")
        return False
    except Exception as e:
        print(f"⚠️ Failed to generate certificate: {e}")
        return False

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
    
    # Parse command line arguments
    import sys
    port_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            port_arg = int(sys.argv[i + 1])
            break
    
    # Auto-detect transparent mode if not explicitly set
    # Disable transparent mode if custom port is specified
    if port_arg and port_arg not in [80, 443]:
        transparent_mode = False
        print(f"🔧 Custom port {port_arg} specified - running in DIRECT ACCESS mode")
    else:
        transparent_mode = os.getenv('TRANSPARENT_MODE', 'true').lower() == 'true'
    
    # In transparent mode, we should use standard ports (80/443) for true transparency
    # Users can override with BIND_PRIVILEGED_PORTS=false if needed
    bind_privileged = os.getenv('BIND_PRIVILEGED_PORTS', 'true' if transparent_mode else 'false').lower() == 'true'
    
    # Setup signal handlers for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_dns_interception)
    
    # Setup transparent mode if enabled
    if transparent_mode:
        setup_transparent_mode()
    
    # Get server configuration
    host = os.getenv('SERVER_HOST', '0.0.0.0' if transparent_mode else '127.0.0.1')
    port = port_arg if port_arg else int(os.getenv('SERVER_PORT', '80' if bind_privileged else '8001'))
    https_port = int(os.getenv('HTTPS_PORT', '443' if bind_privileged else '8443'))
    
    # SSL configuration
    ssl_cert_path = os.getenv('SSL_CERT_PATH')
    ssl_key_path = os.getenv('SSL_KEY_PATH')
    
    print("🚀 Starting OpenAI Codegen Adapter Server")
    print("=" * 50)
    
    if transparent_mode:
        print("🔄 Mode: TRANSPARENT INTERCEPTION")
        print(f"🌐 Intercepting: api.openai.com -> {host}")
        
        if bind_privileged:
            print(f"📍 HTTP Server: http://{host}:{port} (standard port)")
            print(f"🔐 HTTPS Server: https://{host}:{https_port} (standard port)")
            print("✅ Using standard ports 80/443 - True transparent interception!")
            print("🎯 OpenAI clients work with ZERO code changes!")
        else:
            print(f"📍 HTTP Server: http://{host}:{port} (non-standard port)")
            print("⚠️ OpenAI clients need base_url='http://api.openai.com:8001/v1' to work")
        
        print("🎯 Applications using OpenAI API will automatically use Codegen!")
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
    
    # Auto-generate SSL certificates if needed for transparent mode
    if transparent_mode and bind_privileged:
        if not ssl_cert_path:
            ssl_cert_path = "server.crt"
        if not ssl_key_path:
            ssl_key_path = "server.key"
        
        # Generate self-signed certificate if it doesn't exist
        if not (Path(ssl_cert_path).exists() and Path(ssl_key_path).exists()):
            print("🔐 Generating self-signed certificate for HTTPS interception...")
            if generate_self_signed_cert(ssl_cert_path, ssl_key_path):
                print("✅ Self-signed certificate generated successfully")
            else:
                print("⚠️ Failed to generate certificate, HTTPS will be disabled")
                ssl_cert_path = None
                ssl_key_path = None

    # Start servers
    servers = []
    
    def start_http_server():
        """Start HTTP server in a separate thread."""
        try:
            print(f"🌐 Starting HTTP server on port {port}...")
            uvicorn.run(
                "backend.adapter.server:app",
                host=host,
                port=port,
                log_level="error",  # Reduce log noise
                reload=False
            )
        except Exception as e:
            print(f"❌ HTTP server failed: {e}")

    def start_https_server():
        """Start HTTPS server in a separate thread."""
        try:
            print(f"🔐 Starting HTTPS server on port {https_port}...")
            uvicorn.run(
                "backend.adapter.server:app",
                host=host,
                port=https_port,
                ssl_certfile=ssl_cert_path,
                ssl_keyfile=ssl_key_path,
                log_level="error",  # Reduce log noise
                reload=False
            )
        except Exception as e:
            print(f"❌ HTTPS server failed: {e}")

    try:
        # In transparent mode with privileged ports, run both HTTP and HTTPS
        if transparent_mode and bind_privileged:
            # Start HTTP server in background thread
            http_thread = threading.Thread(target=start_http_server, daemon=True)
            http_thread.start()
            servers.append(http_thread)
            
            # Give HTTP server time to start
            time.sleep(1)
            
            # Start HTTPS server if certificates are available
            if ssl_cert_path and ssl_key_path and Path(ssl_cert_path).exists() and Path(ssl_key_path).exists():
                https_thread = threading.Thread(target=start_https_server, daemon=True)
                https_thread.start()
                servers.append(https_thread)
                
                # Give HTTPS server time to start
                time.sleep(1)
                
                print("🎉 Both HTTP and HTTPS servers started successfully!")
                print("✅ True transparent interception enabled - OpenAI clients work with zero code changes!")
            else:
                print("⚠️ HTTPS server not started - SSL certificates not available")
                print("🔧 OpenAI clients will need to use HTTP: base_url='http://api.openai.com/v1'")
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down servers...")
                
        else:
            # Single server mode (legacy behavior)
            if ssl_cert_path and ssl_key_path and Path(ssl_cert_path).exists() and Path(ssl_key_path).exists():
                start_https_server()
            else:
                start_http_server()
                
    except PermissionError:
        print("❌ Permission denied. For privileged ports, run with sudo.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
