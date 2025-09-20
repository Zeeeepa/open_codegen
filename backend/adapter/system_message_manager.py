"""
System message management for Codegen integration.
Handles saving and loading system messages.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SystemMessageManager:
    """Manages system messages for Codegen integration."""
    
    CONFIG_DIR = Path("~/.config/codegen-adapter").expanduser()
    CONFIG_FILE = CONFIG_DIR / "system_message.json"
    
    def __init__(self):
        """Initialize the system message manager."""
        self.message = None
        self.created_at = None
        self._load_message()
    
    def _load_message(self):
        """Load system message from file."""
        if not self.CONFIG_FILE.exists():
            logger.info(f"System message file not found at {self.CONFIG_FILE}")
            return
        
        try:
            with open(self.CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.message = data.get("message")
                self.created_at = data.get("created_at")
                logger.info(f"Loaded system message from {self.CONFIG_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load system message: {e}")
    
    def save_system_message(self, message: str) -> bool:
        """Save system message to file."""
        if not message:
            logger.warning("Cannot save empty system message")
            return False
        
        try:
            # Create config directory if it doesn't exist
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save message to file
            self.message = message
            self.created_at = datetime.now().isoformat()
            
            with open(self.CONFIG_FILE, "w") as f:
                json.dump({
                    "message": self.message,
                    "created_at": self.created_at
                }, f)
            
            logger.info(f"Saved system message to {self.CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save system message: {e}")
            return False
    
    def clear_system_message(self) -> bool:
        """Clear system message."""
        try:
            if self.CONFIG_FILE.exists():
                self.CONFIG_FILE.unlink()
                logger.info(f"Removed system message file {self.CONFIG_FILE}")
            
            self.message = None
            self.created_at = None
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear system message: {e}")
            return False
    
    def get_system_message(self) -> Optional[str]:
        """Get system message."""
        return self.message
    
    def get_system_message_info(self) -> Dict:
        """Get system message information."""
        return {
            "message": self.message,
            "created_at": self.created_at,
            "character_count": len(self.message) if self.message else 0,
            "has_message": self.message is not None
        }


# Singleton instance
_system_message_manager = None

def get_system_message_manager() -> SystemMessageManager:
    """Get system message manager instance."""
    global _system_message_manager
    if _system_message_manager is None:
        _system_message_manager = SystemMessageManager()
    return _system_message_manager

