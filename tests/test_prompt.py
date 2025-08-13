"""
Unit tests for the Prompt module.
Tests the functionality of the PromptManager class and its integration with SystemMessageManager.
"""

import unittest
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.adapter.Prompt import PromptManager, DEFAULT_SYSTEM_MESSAGE


class TestPromptManager(unittest.TestCase):
    """Test cases for the PromptManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary file for the system message storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "test_system_messages.json"
        
        # Create a mock SystemMessageManager
        self.mock_system_message_manager = MagicMock()
        self.mock_system_message_manager.get_system_message.return_value = None
        self.mock_system_message_manager.save_system_message.return_value = True
        self.mock_system_message_manager.get_system_message_info.return_value = {
            "message": None,
            "created_at": None,
            "character_count": 0,
            "has_message": False
        }
        
        # Create a patcher for the get_system_message_manager function
        self.patcher = patch('backend.adapter.Prompt.get_system_message_manager', 
                            return_value=self.mock_system_message_manager)
        self.mock_get_system_message_manager = self.patcher.start()
        
        # Reset the global prompt manager instance
        from backend.adapter.Prompt import _prompt_manager
        if '_prompt_manager' in globals():
            globals()['_prompt_manager'] = None
    
    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_init_sets_default_message(self):
        """Test that the constructor sets the default message if none exists."""
        prompt_manager = PromptManager()
        
        # Verify that save_system_message was called with the default message
        self.mock_system_message_manager.save_system_message.assert_called_once_with(DEFAULT_SYSTEM_MESSAGE)
    
    def test_get_system_message_returns_default_if_none_set(self):
        """Test that get_system_message returns the default message if none is set."""
        prompt_manager = PromptManager()
        
        # Configure mock to return None (no message set)
        self.mock_system_message_manager.get_system_message.return_value = None
        
        # Get the system message
        message = prompt_manager.get_system_message()
        
        # Verify that the default message is returned
        self.assertEqual(message, DEFAULT_SYSTEM_MESSAGE)
    
    def test_get_system_message_returns_custom_message(self):
        """Test that get_system_message returns the custom message if one is set."""
        prompt_manager = PromptManager()
        
        # Configure mock to return a custom message
        custom_message = "This is a custom system message"
        self.mock_system_message_manager.get_system_message.return_value = custom_message
        
        # Get the system message
        message = prompt_manager.get_system_message()
        
        # Verify that the custom message is returned
        self.assertEqual(message, custom_message)
    
    def test_set_system_message(self):
        """Test that set_system_message calls the system message manager."""
        prompt_manager = PromptManager()
        
        # Set a custom message
        custom_message = "This is a custom system message"
        result = prompt_manager.set_system_message(custom_message)
        
        # Verify that save_system_message was called with the custom message
        self.mock_system_message_manager.save_system_message.assert_called_with(custom_message, "default")
        self.assertTrue(result)
    
    def test_reset_to_default(self):
        """Test that reset_to_default sets the message to the default."""
        prompt_manager = PromptManager()
        
        # Reset to default
        result = prompt_manager.reset_to_default()
        
        # Verify that save_system_message was called with the default message
        self.mock_system_message_manager.save_system_message.assert_called_with(DEFAULT_SYSTEM_MESSAGE, "default")
        self.assertTrue(result)
    
    def test_get_system_message_info(self):
        """Test that get_system_message_info returns the correct information."""
        prompt_manager = PromptManager()
        
        # Configure mock to return message info
        self.mock_system_message_manager.get_system_message_info.return_value = {
            "message": DEFAULT_SYSTEM_MESSAGE,
            "created_at": "2023-01-01T00:00:00",
            "character_count": len(DEFAULT_SYSTEM_MESSAGE),
            "has_message": True
        }
        
        # Get the system message info
        info = prompt_manager.get_system_message_info()
        
        # Verify that the info includes the is_default flag
        self.assertTrue(info["is_default"])
        self.assertEqual(info["message"], DEFAULT_SYSTEM_MESSAGE)
    
    def test_get_model_specific_message(self):
        """Test that get_model_specific_message returns the appropriate message."""
        prompt_manager = PromptManager()
        
        # Configure mock to return a custom message
        custom_message = "This is a custom system message"
        self.mock_system_message_manager.get_system_message.return_value = custom_message
        
        # Get the model-specific message
        message = prompt_manager.get_model_specific_message("gpt-3.5-turbo")
        
        # Verify that the custom message is returned
        self.assertEqual(message, custom_message)


if __name__ == "__main__":
    unittest.main()

