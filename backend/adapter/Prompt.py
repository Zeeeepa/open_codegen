"""
Prompt management module for OpenAI Codegen Adapter.
Provides a clean interface for loading and managing system messages.
Integrates with the existing SystemMessageManager for storage.
"""

import logging
from typing import Optional, Dict, Any
from backend.adapter.system_message_manager import get_system_message_manager

logger = logging.getLogger(__name__)

# Default system message for fast responding coding agent
DEFAULT_SYSTEM_MESSAGE = "you are A fast responding coding agent- respond in a single message"

class PromptManager:
    """
    Manages system prompts and messages for the adapter.
    Provides a clean interface for loading, retrieving, and updating system messages.
    """
    
    def __init__(self):
        """Initialize the prompt manager with the system message manager."""
        self.system_message_manager = get_system_message_manager()
        self._ensure_default_message()
    
    def _ensure_default_message(self):
        """
        Ensure the default system message is set if no custom message exists.
        This guarantees that the fast responding coding agent message is used by default.
        """
        if not self.system_message_manager.get_system_message():
            logger.info("Setting default system message for fast responding coding agent")
            self.system_message_manager.save_system_message(DEFAULT_SYSTEM_MESSAGE)
    
    def get_system_message(self, user_id: str = "default") -> str:
        """
        Get the system message for a user.
        Falls back to the default message if no custom message is set.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            str: The system message content
        """
        message = self.system_message_manager.get_system_message(user_id)
        if not message:
            return DEFAULT_SYSTEM_MESSAGE
        return message
    
    def set_system_message(self, message: str, user_id: str = "default") -> bool:
        """
        Set a custom system message for a user.
        
        Args:
            message: The system message content
            user_id: User identifier (default for single-user setup)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        return self.system_message_manager.save_system_message(message, user_id)
    
    def reset_to_default(self, user_id: str = "default") -> bool:
        """
        Reset to the default system message for a user.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            bool: True if reset successfully, False otherwise
        """
        return self.set_system_message(DEFAULT_SYSTEM_MESSAGE, user_id)
    
    def get_system_message_info(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get system message information including metadata.
        
        Args:
            user_id: User identifier (default for single-user setup)
            
        Returns:
            dict: Message information with metadata
        """
        info = self.system_message_manager.get_system_message_info(user_id)
        
        # Add information about whether this is the default message
        message = info.get("message")
        info["is_default"] = message == DEFAULT_SYSTEM_MESSAGE if message else False
        
        return info
    
    def get_model_specific_message(self, model: str, user_id: str = "default") -> str:
        """
        Get a model-specific system message if available.
        Falls back to the default message for the user if no model-specific message exists.
        
        Args:
            model: The model identifier (e.g., "gpt-3.5-turbo", "claude-3-sonnet")
            user_id: User identifier (default for single-user setup)
            
        Returns:
            str: The system message content
        """
        # This is a placeholder for future model-specific message support
        # Currently just returns the user's system message
        return self.get_system_message(user_id)

# Global instance for easy access
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

