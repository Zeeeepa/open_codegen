"""
Ubuntu DNS Management for OpenAI API Interception
Handles /etc/hosts modification and systemd-resolved configuration.
"""

import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UbuntuDNSManager:
    """Manages DNS interception for Ubuntu systems."""
    
    HOSTS_FILE = "/etc/hosts"
    HOSTS_BACKUP = "/etc/hosts.openai-interceptor.backup"
    INTERCEPTOR_MARKER = "# OpenAI Interceptor - DO NOT EDIT MANUALLY"
    
    def __init__(self):
        self.domains_to_intercept = [
            "api.openai.com",
            "openai.com",
            "*.openai.com"
        ]
        self.redirect_ip = "127.0.0.1"
    
    def is_root(self) -> bool:
        """Check if running with root privileges."""
        return os.geteuid() == 0
    
    def backup_hosts_file(self) -> bool:
        """Create a backup of the current hosts file."""
        try:
            if not Path(self.HOSTS_BACKUP).exists():
                shutil.copy2(self.HOSTS_FILE, self.HOSTS_BACKUP)
                logger.info(f"✅ Created hosts file backup: {self.HOSTS_BACKUP}")
                return True
            else:
                logger.info("ℹ️ Hosts file backup already exists")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to backup hosts file: {e}")
            return False
    
    def restore_hosts_file(self) -> bool:
        """Restore the original hosts file from backup."""
        try:
            if Path(self.HOSTS_BACKUP).exists():
                shutil.copy2(self.HOSTS_BACKUP, self.HOSTS_FILE)
                os.remove(self.HOSTS_BACKUP)
                logger.info("✅ Restored original hosts file")
                return True
            else:
                logger.warning("⚠️ No backup file found, removing interceptor entries manually")
                return self.remove_interceptor_entries()
        except Exception as e:
            logger.error(f"❌ Failed to restore hosts file: {e}")
            return False
    
    def read_hosts_file(self) -> List[str]:
        """Read the current hosts file content."""
        try:
            with open(self.HOSTS_FILE, 'r') as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"❌ Failed to read hosts file: {e}")
            return []
    
    def write_hosts_file(self, lines: List[str]) -> bool:
        """Write content to the hosts file."""
        try:
            with open(self.HOSTS_FILE, 'w') as f:
                f.writelines(lines)
            logger.info("✅ Updated hosts file")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to write hosts file: {e}")
            return False
    
    def has_interceptor_entries(self) -> bool:
        """Check if interceptor entries already exist in hosts file."""
        lines = self.read_hosts_file()
        return any(self.INTERCEPTOR_MARKER in line for line in lines)
    
    def remove_interceptor_entries(self) -> bool:
        """Remove existing interceptor entries from hosts file."""
        lines = self.read_hosts_file()
        if not lines:
            return False
        
        # Remove lines between our markers
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if self.INTERCEPTOR_MARKER in line:
                if "START" in line:
                    skip_section = True
                elif "END" in line:
                    skip_section = False
                continue
            
            if not skip_section:
                filtered_lines.append(line)
        
        return self.write_hosts_file(filtered_lines)
    
    def add_interceptor_entries(self) -> bool:
        """Add interceptor entries to hosts file."""
        if not self.is_root():
            logger.error("❌ Root privileges required to modify hosts file")
            return False
        
        # Backup first
        if not self.backup_hosts_file():
            return False
        
        # Remove existing entries if any
        if self.has_interceptor_entries():
            logger.info("🔄 Removing existing interceptor entries")
            self.remove_interceptor_entries()
        
        lines = self.read_hosts_file()
        if not lines:
            return False
        
        # Add our entries
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        interceptor_entries = [
            f"\n{self.INTERCEPTOR_MARKER} START - Added {timestamp}\n",
            f"{self.redirect_ip}\tapi.openai.com\n",
            f"{self.redirect_ip}\topenai.com\n",
            f"{self.redirect_ip}\twww.openai.com\n",
            f"{self.INTERCEPTOR_MARKER} END\n"
        ]
        
        lines.extend(interceptor_entries)
        
        if self.write_hosts_file(lines):
            logger.info("✅ Added OpenAI API interception entries to hosts file")
            self.flush_dns_cache()
            return True
        
        return False
    
    def flush_dns_cache(self) -> bool:
        """Flush DNS cache on Ubuntu."""
        try:
            # Try systemd-resolved first (Ubuntu 18.04+)
            result = subprocess.run(
                ["systemctl", "is-active", "systemd-resolved"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                subprocess.run(["systemd-resolve", "--flush-caches"], check=True)
                logger.info("✅ Flushed systemd-resolved DNS cache")
            else:
                # Fallback for older systems
                subprocess.run(["service", "networking", "restart"], check=True)
                logger.info("✅ Restarted networking service")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to flush DNS cache: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error flushing DNS cache: {e}")
            return False
    
    def test_dns_resolution(self) -> bool:
        """Test if DNS interception is working."""
        try:
            import socket
            ip = socket.gethostbyname("api.openai.com")
            if ip == self.redirect_ip:
                logger.info("✅ DNS interception is working correctly")
                return True
            else:
                logger.warning(f"⚠️ DNS interception not working. api.openai.com resolves to {ip}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to test DNS resolution: {e}")
            return False
    
    def enable_interception(self) -> bool:
        """Enable DNS interception."""
        logger.info("🚀 Enabling OpenAI API DNS interception...")
        
        if not self.is_root():
            logger.error("❌ Root privileges required. Run with sudo.")
            return False
        
        success = self.add_interceptor_entries()
        if success:
            logger.info("✅ DNS interception enabled successfully")
            # Test the configuration
            if self.test_dns_resolution():
                logger.info("🎉 OpenAI API calls will now be intercepted!")
            else:
                logger.warning("⚠️ DNS interception enabled but test failed")
        
        return success
    
    def disable_interception(self) -> bool:
        """Disable DNS interception."""
        logger.info("🔄 Disabling OpenAI API DNS interception...")
        
        if not self.is_root():
            logger.error("❌ Root privileges required. Run with sudo.")
            return False
        
        success = self.restore_hosts_file()
        if success:
            self.flush_dns_cache()
            logger.info("✅ DNS interception disabled successfully")
        
        return success
    
    def status(self) -> dict:
        """Get current interception status."""
        return {
            "enabled": self.has_interceptor_entries(),
            "backup_exists": Path(self.HOSTS_BACKUP).exists(),
            "dns_test_passed": self.test_dns_resolution() if self.has_interceptor_entries() else False,
            "root_access": self.is_root()
        }


def main():
    """CLI interface for DNS management."""
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Ubuntu DNS Manager for OpenAI API Interception")
    parser.add_argument("action", choices=["enable", "disable", "status", "test"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    dns_manager = UbuntuDNSManager()
    
    if args.action == "enable":
        success = dns_manager.enable_interception()
        sys.exit(0 if success else 1)
    elif args.action == "disable":
        success = dns_manager.disable_interception()
        sys.exit(0 if success else 1)
    elif args.action == "status":
        status = dns_manager.status()
        print(f"DNS Interception Status:")
        print(f"  Enabled: {status['enabled']}")
        print(f"  Backup exists: {status['backup_exists']}")
        print(f"  DNS test passed: {status['dns_test_passed']}")
        print(f"  Root access: {status['root_access']}")
    elif args.action == "test":
        success = dns_manager.test_dns_resolution()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
