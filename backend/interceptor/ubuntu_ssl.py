"""
Ubuntu SSL Certificate Management for OpenAI API Interception
Handles SSL certificate generation and installation for HTTPS interception.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
import tempfile

logger = logging.getLogger(__name__)

class UbuntuSSLManager:
    """Manages SSL certificates for Ubuntu systems."""
    
    CERT_DIR = "/usr/local/share/ca-certificates/openai-interceptor"
    CA_CERT_NAME = "openai-interceptor-ca.crt"
    SERVER_CERT_NAME = "api.openai.com.crt"
    SERVER_KEY_NAME = "api.openai.com.key"
    
    def __init__(self):
        self.cert_dir = Path(self.CERT_DIR)
        self.ca_cert_path = self.cert_dir / self.CA_CERT_NAME
        self.server_cert_path = self.cert_dir / self.SERVER_CERT_NAME
        self.server_key_path = self.cert_dir / self.SERVER_KEY_NAME
    
    def is_root(self) -> bool:
        """Check if running with root privileges."""
        return os.geteuid() == 0
    
    def ensure_cert_directory(self) -> bool:
        """Ensure certificate directory exists."""
        try:
            self.cert_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Certificate directory ready: {self.cert_dir}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create certificate directory: {e}")
            return False
    
    def check_openssl_available(self) -> bool:
        """Check if OpenSSL is available."""
        try:
            result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ OpenSSL available: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ OpenSSL not available")
                return False
        except FileNotFoundError:
            logger.error("❌ OpenSSL not found. Install with: sudo apt install openssl")
            return False
    
    def generate_ca_certificate(self) -> bool:
        """Generate a Certificate Authority certificate."""
        if not self.check_openssl_available():
            return False
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_key = Path(temp_dir) / "ca.key"
                temp_cert = Path(temp_dir) / "ca.crt"
                
                # Generate CA private key
                subprocess.run([
                    "openssl", "genrsa", "-out", str(temp_key), "4096"
                ], check=True, capture_output=True)
                
                # Generate CA certificate
                subprocess.run([
                    "openssl", "req", "-new", "-x509", "-days", "3650",
                    "-key", str(temp_key), "-out", str(temp_cert),
                    "-subj", "/C=US/ST=CA/L=San Francisco/O=OpenAI Interceptor/CN=OpenAI Interceptor CA"
                ], check=True, capture_output=True)
                
                # Copy to final location
                temp_cert.rename(self.ca_cert_path)
                logger.info(f"✅ Generated CA certificate: {self.ca_cert_path}")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to generate CA certificate: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error generating CA certificate: {e}")
            return False
    
    def generate_server_certificate(self) -> bool:
        """Generate server certificate for api.openai.com."""
        if not self.check_openssl_available():
            return False
        
        if not self.ca_cert_path.exists():
            logger.error("❌ CA certificate not found. Generate CA first.")
            return False
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_ca_key = Path(temp_dir) / "ca.key"
                temp_server_key = Path(temp_dir) / "server.key"
                temp_server_csr = Path(temp_dir) / "server.csr"
                temp_server_cert = Path(temp_dir) / "server.crt"
                temp_config = Path(temp_dir) / "server.conf"
                
                # We need to regenerate CA key for signing (in production, store securely)
                subprocess.run([
                    "openssl", "genrsa", "-out", str(temp_ca_key), "4096"
                ], check=True, capture_output=True)
                
                # Generate server private key
                subprocess.run([
                    "openssl", "genrsa", "-out", str(temp_server_key), "2048"
                ], check=True, capture_output=True)
                
                # Create config file for SAN
                config_content = """[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = OpenAI Interceptor
CN = api.openai.com

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = api.openai.com
DNS.2 = openai.com
DNS.3 = www.openai.com
DNS.4 = *.openai.com
"""
                temp_config.write_text(config_content)
                
                # Generate certificate signing request
                subprocess.run([
                    "openssl", "req", "-new", "-key", str(temp_server_key),
                    "-out", str(temp_server_csr), "-config", str(temp_config)
                ], check=True, capture_output=True)
                
                # Sign the certificate with our CA
                subprocess.run([
                    "openssl", "x509", "-req", "-in", str(temp_server_csr),
                    "-CA", str(self.ca_cert_path), "-CAkey", str(temp_ca_key),
                    "-CAcreateserial", "-out", str(temp_server_cert),
                    "-days", "365", "-extensions", "v3_req", "-extfile", str(temp_config)
                ], check=True, capture_output=True)
                
                # Copy to final locations
                temp_server_cert.rename(self.server_cert_path)
                temp_server_key.rename(self.server_key_path)
                
                # Set proper permissions
                os.chmod(self.server_key_path, 0o600)
                
                logger.info(f"✅ Generated server certificate: {self.server_cert_path}")
                logger.info(f"✅ Generated server key: {self.server_key_path}")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to generate server certificate: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error generating server certificate: {e}")
            return False
    
    def install_ca_certificate(self) -> bool:
        """Install CA certificate to Ubuntu's trust store."""
        if not self.is_root():
            logger.error("❌ Root privileges required to install CA certificate")
            return False
        
        if not self.ca_cert_path.exists():
            logger.error("❌ CA certificate not found")
            return False
        
        try:
            # Update CA certificates
            subprocess.run(["update-ca-certificates"], check=True, capture_output=True)
            logger.info("✅ CA certificate installed to system trust store")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install CA certificate: {e}")
            return False
    
    def remove_certificates(self) -> bool:
        """Remove all interceptor certificates."""
        if not self.is_root():
            logger.error("❌ Root privileges required to remove certificates")
            return False
        
        try:
            if self.cert_dir.exists():
                import shutil
                shutil.rmtree(self.cert_dir)
                logger.info("✅ Removed certificate directory")
            
            # Update CA certificates to remove from trust store
            subprocess.run(["update-ca-certificates"], check=True, capture_output=True)
            logger.info("✅ Updated system trust store")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to remove certificates: {e}")
            return False
    
    def verify_certificate(self) -> bool:
        """Verify the generated certificate."""
        if not self.server_cert_path.exists():
            logger.error("❌ Server certificate not found")
            return False
        
        try:
            # Verify certificate details
            result = subprocess.run([
                "openssl", "x509", "-in", str(self.server_cert_path),
                "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            if "api.openai.com" in result.stdout:
                logger.info("✅ Certificate verification passed")
                return True
            else:
                logger.error("❌ Certificate verification failed")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to verify certificate: {e}")
            return False
    
    def get_certificate_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """Get paths to server certificate and key."""
        if self.server_cert_path.exists() and self.server_key_path.exists():
            return str(self.server_cert_path), str(self.server_key_path)
        return None, None
    
    def setup_certificates(self) -> bool:
        """Complete certificate setup process."""
        logger.info("🚀 Setting up SSL certificates for OpenAI API interception...")
        
        if not self.is_root():
            logger.error("❌ Root privileges required. Run with sudo.")
            return False
        
        # Ensure directory exists
        if not self.ensure_cert_directory():
            return False
        
        # Generate CA certificate
        if not self.ca_cert_path.exists():
            logger.info("📜 Generating CA certificate...")
            if not self.generate_ca_certificate():
                return False
        else:
            logger.info("ℹ️ CA certificate already exists")
        
        # Generate server certificate
        if not self.server_cert_path.exists() or not self.server_key_path.exists():
            logger.info("🔐 Generating server certificate...")
            if not self.generate_server_certificate():
                return False
        else:
            logger.info("ℹ️ Server certificate already exists")
        
        # Install CA certificate
        if not self.install_ca_certificate():
            return False
        
        # Verify certificate
        if not self.verify_certificate():
            return False
        
        logger.info("✅ SSL certificate setup completed successfully")
        logger.info("🎉 HTTPS interception is now ready!")
        return True
    
    def status(self) -> dict:
        """Get certificate status."""
        return {
            "ca_cert_exists": self.ca_cert_path.exists(),
            "server_cert_exists": self.server_cert_path.exists(),
            "server_key_exists": self.server_key_path.exists(),
            "cert_directory_exists": self.cert_dir.exists(),
            "openssl_available": self.check_openssl_available(),
            "root_access": self.is_root()
        }


def main():
    """CLI interface for SSL certificate management."""
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Ubuntu SSL Manager for OpenAI API Interception")
    parser.add_argument("action", choices=["setup", "remove", "status", "verify"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    ssl_manager = UbuntuSSLManager()
    
    if args.action == "setup":
        success = ssl_manager.setup_certificates()
        sys.exit(0 if success else 1)
    elif args.action == "remove":
        success = ssl_manager.remove_certificates()
        sys.exit(0 if success else 1)
    elif args.action == "status":
        status = ssl_manager.status()
        print("SSL Certificate Status:")
        print(f"  CA certificate exists: {status['ca_cert_exists']}")
        print(f"  Server certificate exists: {status['server_cert_exists']}")
        print(f"  Server key exists: {status['server_key_exists']}")
        print(f"  Certificate directory exists: {status['cert_directory_exists']}")
        print(f"  OpenSSL available: {status['openssl_available']}")
        print(f"  Root access: {status['root_access']}")
    elif args.action == "verify":
        success = ssl_manager.verify_certificate()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
