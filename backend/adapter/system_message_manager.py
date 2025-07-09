"""
System Message Manager for OpenAI Codegen Adapter.
Handles storage and retrieval of system messages for conversation context.
"""

import os
import json
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemMessageManager:
    """Manages system messages for the OpenAI Codegen adapter."""
    
    def __init__(self, storage_path: str = "system_message.json"):
        """
        Initialize the system message manager.
        
        Args:
            storage_path: Path to store the system message file
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure the storage directory exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_system_message(self) -> Optional[str]:
        """
        Get the current system message.
        
        Returns:
            The system message string, or None if not set
        """
        try:
            if not self.storage_path.exists():
                return None
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('message')
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning(f"Error reading system message: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading system message: {e}")
            return None
    
    def save_system_message(self, message: str) -> bool:
        """
        Save a system message.
        
        Args:
            message: The system message to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            data = {
                'message': message.strip(),
                'timestamp': str(os.path.getmtime(self.storage_path) if self.storage_path.exists() else 0)
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"System message saved: {len(message)} characters")
            return True
        except Exception as e:
            logger.error(f"Error saving system message: {e}")
            return False
    
    def clear_system_message(self) -> bool:
        """
        Clear the current system message.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            logger.info("System message cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing system message: {e}")
            return False
    
    def has_system_message(self) -> bool:
        """
        Check if a system message is currently set.
        
        Returns:
            True if a system message exists, False otherwise
        """
        message = self.get_system_message()
        return message is not None and len(message.strip()) > 0


# Global instance
_system_message_manager = None

def get_system_message_manager() -> SystemMessageManager:
    """
    Get the global system message manager instance.
    
    Returns:
        SystemMessageManager instance
    """
    global _system_message_manager
    if _system_message_manager is None:
        _system_message_manager = SystemMessageManager()
    return _system_message_manager

