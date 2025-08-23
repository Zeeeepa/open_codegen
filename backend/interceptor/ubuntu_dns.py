"""
DNS interception manager for Ubuntu-based systems.
Handles hosts file modification for transparent interception.
"""

import os
import socket
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class UbuntuDNSManager:
    """Manages DNS interception on Ubuntu-based systems."""
    
    HOSTS_FILE = "/etc/hosts"
    HOSTS_BACKUP = "/etc/hosts.codegen.bak"
    
    # Domains to intercept
    DOMAINS = [
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com"
    ]
    
    def __init__(self):
        """Initialize the DNS manager."""
        self.hosts_file = Path(self.HOSTS_FILE)
        self.hosts_backup = Path(self.HOSTS_BACKUP)
    
    def is_root(self) -> bool:
        """Check if running as root."""
        return os.geteuid() == 0
    
    def backup_hosts(self) -> bool:
        """Backup the hosts file."""
        try:
            if not self.hosts_backup.exists():
                subprocess.run(["cp", self.HOSTS_FILE, self.HOSTS_BACKUP], check=True)
                logger.info(f"Backed up hosts file to {self.HOSTS_BACKUP}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup hosts file: {e}")
            return False
    
    def restore_hosts(self) -> bool:
        """Restore the hosts file from backup."""
        try:
            if self.hosts_backup.exists():
                subprocess.run(["cp", self.HOSTS_BACKUP, self.HOSTS_FILE], check=True)
                logger.info(f"Restored hosts file from {self.HOSTS_BACKUP}")
                return True
            else:
                logger.warning("No hosts backup file found")
                return False
        except Exception as e:
            logger.error(f"Failed to restore hosts file: {e}")
            return False
    
    def add_interception_entries(self) -> bool:
        """Add interception entries to hosts file."""
        try:
            # Read current hosts file
            with open(self.HOSTS_FILE, "r") as f:
                hosts_content = f.read()
            
            # Check if already intercepted
            if "# CODEGEN DNS INTERCEPTION" in hosts_content:
                logger.info("Interception entries already exist in hosts file")
                return True
            
            # Add interception entries
            with open(self.HOSTS_FILE, "a") as f:
                f.write("\n# CODEGEN DNS INTERCEPTION - DO NOT MODIFY\n")
                for domain in self.DOMAINS:
                    f.write(f"127.0.0.1 {domain}\n")
                f.write("# END CODEGEN DNS INTERCEPTION\n")
            
            logger.info(f"Added interception entries to {self.HOSTS_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to add interception entries: {e}")
            return False
    
    def remove_interception_entries(self) -> bool:
        """Remove interception entries from hosts file."""
        try:
            # Read current hosts file
            with open(self.HOSTS_FILE, "r") as f:
                hosts_content = f.readlines()
            
            # Remove interception entries
            in_section = False
            new_content = []
            for line in hosts_content:
                if "# CODEGEN DNS INTERCEPTION" in line:
                    in_section = True
                    continue
                if "# END CODEGEN DNS INTERCEPTION" in line:
                    in_section = False
                    continue
                if not in_section:
                    new_content.append(line)
            
            # Write new hosts file
            with open(self.HOSTS_FILE, "w") as f:
                f.writelines(new_content)
            
            logger.info(f"Removed interception entries from {self.HOSTS_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove interception entries: {e}")
            return False
    
    def enable_interception(self) -> bool:
        """Enable DNS interception."""
        if not self.is_root():
            logger.error("Root privileges required for DNS interception")
            return False
        
        # Backup hosts file
        if not self.backup_hosts():
            return False
        
        # Add interception entries
        if not self.add_interception_entries():
            return False
        
        # Flush DNS cache
        self.flush_dns_cache()
        
        logger.info("DNS interception enabled successfully")
        return True
    
    def disable_interception(self) -> bool:
        """Disable DNS interception."""
        if not self.is_root():
            logger.error("Root privileges required for DNS interception")
            return False
        
        # Remove interception entries
        if not self.remove_interception_entries():
            return False
        
        # Flush DNS cache
        self.flush_dns_cache()
        
        logger.info("DNS interception disabled successfully")
        return True
    
    def flush_dns_cache(self) -> bool:
        """Flush DNS cache."""
        try:
            # Try different methods for different systems
            # Ubuntu/Debian
            subprocess.run(["systemd-resolve", "--flush-caches"], check=False)
            # Ubuntu older versions
            subprocess.run(["service", "systemd-resolved", "restart"], check=False)
            # General Linux
            subprocess.run(["nscd", "-I", "hosts"], check=False)
            
            logger.info("Flushed DNS cache")
            return True
        except Exception as e:
            logger.warning(f"Failed to flush DNS cache: {e}")
            return False
    
    def status(self) -> dict:
        """Get DNS interception status."""
        try:
            # Check if hosts file contains interception entries
            with open(self.HOSTS_FILE, "r") as f:
                hosts_content = f.read()
            
            enabled = "# CODEGEN DNS INTERCEPTION" in hosts_content
            
            # Check if backup exists
            backup_exists = self.hosts_backup.exists()
            
            return {
                "enabled": enabled,
                "backup_exists": backup_exists,
                "hosts_file": str(self.hosts_file),
                "hosts_backup": str(self.hosts_backup),
                "domains": self.DOMAINS
            }
        except Exception as e:
            logger.error(f"Failed to get DNS interception status: {e}")
            return {
                "enabled": False,
                "backup_exists": False,
                "error": str(e)
            }
    
    def test_dns_resolution(self) -> bool:
        """Test if DNS interception is working."""
        try:
            # Try to resolve one of the domains
            ip = socket.gethostbyname("api.openai.com")
            
            # Check if it resolves to localhost
            if ip == "127.0.0.1":
                logger.info("DNS interception is working correctly")
                return True
            else:
                logger.warning(f"DNS interception is not working: api.openai.com resolves to {ip}")
                return False
        except Exception as e:
            logger.error(f"Failed to test DNS resolution: {e}")
            return False

