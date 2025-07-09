"""
System Message Manager for OpenAI Codegen Adapter.
Handles persistent storage and retrieval of user-configured system messages.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemMessageManager:
    """Manages system message storage and retrieval."""
    
    def __init__(self, storage_path: str = "backend/data/system_messages.json"):
        """
        Initialize the system message manager.
        
        Args:
            storage_path: Path to the JSON file for storing system messages
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Ensure the storage file exists with proper structure."""
        if not self.storage_path.exists():
            default_data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "system_messages": {},
                "default_message": None
            }
            self._write_data(default_data)
            logger.info(f"Created system message storage at {self.storage_path}")
    
    def _read_data(self) -> Dict[str, Any]:
        """Read data from storage file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading system message storage: {e}")
            # Return default structure if file is corrupted
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "system_messages": {},
                "default_message": None
            }
    
    def _write_data(self, data: Dict[str, Any]):
        """Write data to storage file."""
        try:
            data["updated_at"] = datetime.now().isoformat()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing system message storage: {e}")
            raise
    
    def save_system_message(self, message: str, user_id: str = "default") -> bool:
        """
        Save a system message for a user.
        
        Args:
            message: The system message content
            user_id: User identifier (default for single-user setup)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            data = self._read_data()
            
            # Store the message with metadata
            data["system_messages"][user_id] = {
                "message": message.strip(),
                "created_at": datetime.now().isoformat(),
                "character_count": len(message.strip())
            }
            
            # Update default message for backward compatibility
            data["default_message"] = message.strip()
            
            self._write_data(data)
            logger.info(f"System message saved for user {user_id} ({len(message.strip())} characters)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save system message: {e}")
            return False
    
    def get_system_message(self, user_id: str = "default") -> Optional[str]:
        """
        Get the system message for a user.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            str: The system message content, or None if not found
        """
        try:
            data = self._read_data()
            
            # Try to get user-specific message first
            if user_id in data["system_messages"]:
                message_data = data["system_messages"][user_id]
                return message_data["message"]
            
            # Fallback to default message for backward compatibility
            return data.get("default_message")
            
        except Exception as e:
            logger.error(f"Failed to get system message: {e}")
            return None
    
    def clear_system_message(self, user_id: str = "default") -> bool:
        """
        Clear the system message for a user.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            data = self._read_data()
            
            # Remove user-specific message
            if user_id in data["system_messages"]:
                del data["system_messages"][user_id]
            
            # Clear default message if this was the default user
            if user_id == "default":
                data["default_message"] = None
            
            self._write_data(data)
            logger.info(f"System message cleared for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear system message: {e}")
            return False
    
    def get_system_message_info(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get system message information including metadata.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            dict: Message information with metadata
        """
        try:
            data = self._read_data()
            
            if user_id in data["system_messages"]:
                message_data = data["system_messages"][user_id]
                return {
                    "message": message_data["message"],
                    "created_at": message_data["created_at"],
                    "character_count": message_data["character_count"],
                    "has_message": True
                }
            
            return {
                "message": None,
                "created_at": None,
                "character_count": 0,
                "has_message": False
            }
            
        except Exception as e:
            logger.error(f"Failed to get system message info: {e}")
            return {
                "message": None,
                "created_at": None,
                "character_count": 0,
                "has_message": False
            }
    
    def list_all_messages(self) -> Dict[str, Dict[str, Any]]:
        """
        List all stored system messages.
        
        Returns:
            dict: All system messages with metadata
        """
        try:
            data = self._read_data()
            return data.get("system_messages", {})
        except Exception as e:
            logger.error(f"Failed to list system messages: {e}")
            return {}

# Global instance for easy access
_system_message_manager = None

def get_system_message_manager() -> SystemMessageManager:
    """Get the global system message manager instance."""
    global _system_message_manager
    if _system_message_manager is None:
        _system_message_manager = SystemMessageManager()
    return _system_message_manager

