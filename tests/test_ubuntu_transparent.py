"""
Test suite for Ubuntu transparent OpenAI API interception.
Tests DNS interception, SSL certificates, and end-to-end functionality.
"""

import unittest
import subprocess
import socket
import requests
import os
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interceptor.ubuntu_dns import UbuntuDNSManager
from interceptor.ubuntu_ssl import UbuntuSSLManager

class TestUbuntuTransparentInterception(unittest.TestCase):
    """Test transparent interception functionality on Ubuntu."""
    
    def setUp(self):
        """Set up test environment."""
        self.dns_manager = UbuntuDNSManager()
        self.ssl_manager = UbuntuSSLManager()
        self.test_domain = "api.openai.com"
        self.interceptor_ip = "127.0.0.1"
    
    def test_dns_manager_initialization(self):
        """Test DNS manager initializes correctly."""
        self.assertIsInstance(self.dns_manager, UbuntuDNSManager)
        self.assertEqual(self.dns_manager.redirect_ip, "127.0.0.1")
        self.assertIn("api.openai.com", self.dns_manager.domains_to_intercept)
    
    def test_ssl_manager_initialization(self):
        """Test SSL manager initializes correctly."""
        self.assertIsInstance(self.ssl_manager, UbuntuSSLManager)
        self.assertTrue(self.ssl_manager.cert_dir.name.endswith("openai-interceptor"))
    
    def test_dns_status_check(self):
        """Test DNS status checking functionality."""
        status = self.dns_manager.status()
        self.assertIsInstance(status, dict)
        self.assertIn("enabled", status)
        self.assertIn("backup_exists", status)
        self.assertIn("dns_test_passed", status)
        self.assertIn("root_access", status)
    
    def test_ssl_status_check(self):
        """Test SSL status checking functionality."""
        status = self.ssl_manager.status()
        self.assertIsInstance(status, dict)
        self.assertIn("ca_cert_exists", status)
        self.assertIn("server_cert_exists", status)
        self.assertIn("server_key_exists", status)
        self.assertIn("openssl_available", status)
        self.assertIn("root_access", status)
    
    def test_hosts_file_reading(self):
        """Test hosts file can be read."""
        lines = self.dns_manager.read_hosts_file()
        self.assertIsInstance(lines, list)
        # Should at least have localhost entry
        localhost_found = any("127.0.0.1" in line and "localhost" in line for line in lines)
        self.assertTrue(localhost_found, "localhost entry not found in hosts file")
    
    def test_openssl_availability(self):
        """Test OpenSSL is available on the system."""
        available = self.ssl_manager.check_openssl_available()
        if not available:
            self.skipTest("OpenSSL not available on this system")
        self.assertTrue(available)
    
    @unittest.skipUnless(os.geteuid() == 0, "Root privileges required")
    def test_dns_interception_cycle(self):
        """Test complete DNS interception enable/disable cycle."""
        # Get initial status
        initial_status = self.dns_manager.status()
        
        # If already enabled, disable first
        if initial_status["enabled"]:
            success = self.dns_manager.disable_interception()
            self.assertTrue(success, "Failed to disable existing interception")
        
        # Enable interception
        success = self.dns_manager.enable_interception()
        self.assertTrue(success, "Failed to enable DNS interception")
        
        # Verify it's enabled
        status = self.dns_manager.status()
        self.assertTrue(status["enabled"], "DNS interception not enabled")
        
        # Test DNS resolution
        try:
            ip = socket.gethostbyname(self.test_domain)
            self.assertEqual(ip, self.interceptor_ip, f"DNS not intercepted: {ip}")
        except socket.gaierror:
            self.fail("DNS resolution failed")
        
        # Disable interception
        success = self.dns_manager.disable_interception()
        self.assertTrue(success, "Failed to disable DNS interception")
        
        # Verify it's disabled
        status = self.dns_manager.status()
        self.assertFalse(status["enabled"], "DNS interception still enabled")
    
    @unittest.skipUnless(os.geteuid() == 0, "Root privileges required")
    def test_ssl_certificate_generation(self):
        """Test SSL certificate generation and installation."""
        # Clean up any existing certificates
        if self.ssl_manager.cert_dir.exists():
            self.ssl_manager.remove_certificates()
        
        # Setup certificates
        success = self.ssl_manager.setup_certificates()
        self.assertTrue(success, "Failed to setup SSL certificates")
        
        # Verify certificates exist
        status = self.ssl_manager.status()
        self.assertTrue(status["ca_cert_exists"], "CA certificate not created")
        self.assertTrue(status["server_cert_exists"], "Server certificate not created")
        self.assertTrue(status["server_key_exists"], "Server key not created")
        
        # Verify certificate paths
        cert_path, key_path = self.ssl_manager.get_certificate_paths()
        self.assertIsNotNone(cert_path, "Certificate path is None")
        self.assertIsNotNone(key_path, "Key path is None")
        self.assertTrue(Path(cert_path).exists(), "Certificate file doesn't exist")
        self.assertTrue(Path(key_path).exists(), "Key file doesn't exist")
        
        # Verify certificate
        success = self.ssl_manager.verify_certificate()
        self.assertTrue(success, "Certificate verification failed")
        
        # Clean up
        success = self.ssl_manager.remove_certificates()
        self.assertTrue(success, "Failed to remove certificates")
    
    def test_service_file_exists(self):
        """Test systemd service file exists and is valid."""
        service_file = Path("systemd/openai-interceptor.service")
        self.assertTrue(service_file.exists(), "Service file not found")
        
        content = service_file.read_text()
        self.assertIn("[Unit]", content)
        self.assertIn("[Service]", content)
        self.assertIn("[Install]", content)
        self.assertIn("openai_codegen_adapter.server", content)
    
    def test_installation_scripts_exist(self):
        """Test installation scripts exist and are executable."""
        install_script = Path("install-ubuntu.sh")
        uninstall_script = Path("uninstall-ubuntu.sh")
        
        self.assertTrue(install_script.exists(), "Install script not found")
        self.assertTrue(uninstall_script.exists(), "Uninstall script not found")
        
        # Check if scripts are executable (on Unix systems)
        if os.name == 'posix':
            install_stat = install_script.stat()
            uninstall_stat = uninstall_script.stat()
            
            # Check owner execute permission
            self.assertTrue(install_stat.st_mode & 0o100, "Install script not executable")
            self.assertTrue(uninstall_stat.st_mode & 0o100, "Uninstall script not executable")
    
    def test_transparent_mode_configuration(self):
        """Test transparent mode environment variables."""
        # Test with transparent mode enabled
        os.environ['TRANSPARENT_MODE'] = 'true'
        os.environ['BIND_PRIVILEGED_PORTS'] = 'true'
        
        from openai_codegen_adapter.config import get_server_config
        config = get_server_config()
        
        self.assertTrue(config.transparent_mode)
        self.assertTrue(config.bind_privileged_ports)
        
        # Clean up
        del os.environ['TRANSPARENT_MODE']
        del os.environ['BIND_PRIVILEGED_PORTS']
    
    def test_server_startup_dry_run(self):
        """Test server startup configuration without actually starting."""
        # Set test environment
        os.environ['TRANSPARENT_MODE'] = 'true'
        os.environ['SERVER_HOST'] = '127.0.0.1'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['HTTPS_PORT'] = '8443'
        
        from openai_codegen_adapter.config import get_server_config
        config = get_server_config()
        
        self.assertEqual(config.host, '127.0.0.1')
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.https_port, 8443)
        self.assertTrue(config.transparent_mode)
        
        # Clean up
        for key in ['TRANSPARENT_MODE', 'SERVER_HOST', 'SERVER_PORT', 'HTTPS_PORT']:
            if key in os.environ:
                del os.environ[key]


class TestEndToEndInterception(unittest.TestCase):
    """End-to-end tests for transparent interception."""
    
    @unittest.skipUnless(os.geteuid() == 0, "Root privileges required")
    def test_full_interception_setup(self):
        """Test complete interception setup and teardown."""
        dns_manager = UbuntuDNSManager()
        ssl_manager = UbuntuSSLManager()
        
        try:
            # Setup DNS interception
            dns_success = dns_manager.enable_interception()
            self.assertTrue(dns_success, "DNS setup failed")
            
            # Setup SSL certificates
            ssl_success = ssl_manager.setup_certificates()
            self.assertTrue(ssl_success, "SSL setup failed")
            
            # Verify DNS resolution
            ip = socket.gethostbyname("api.openai.com")
            self.assertEqual(ip, "127.0.0.1", "DNS interception not working")
            
            # Verify certificates exist
            cert_path, key_path = ssl_manager.get_certificate_paths()
            self.assertIsNotNone(cert_path)
            self.assertIsNotNone(key_path)
            
        finally:
            # Clean up
            dns_manager.disable_interception()
            ssl_manager.remove_certificates()


def run_tests():
    """Run all tests with proper output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUbuntuTransparentInterception))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndInterception))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
