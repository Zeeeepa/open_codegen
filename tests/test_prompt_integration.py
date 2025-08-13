"""
Integration tests for the Prompt module.
Tests the integration of the Prompt module with the request transformer and server.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.adapter.models import ChatRequest, Message
from backend.adapter.request_transformer import chat_request_to_prompt
from backend.adapter.Prompt import PromptManager, DEFAULT_SYSTEM_MESSAGE, get_prompt_manager


class TestPromptIntegration(unittest.TestCase):
    """Test cases for the integration of the Prompt module with other components."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock SystemMessageManager
        self.mock_system_message_manager = MagicMock()
        self.mock_system_message_manager.get_system_message.return_value = DEFAULT_SYSTEM_MESSAGE
        self.mock_system_message_manager.save_system_message.return_value = True
        
        # Create a patcher for the get_system_message_manager function
        self.patcher = patch('backend.adapter.Prompt.get_system_message_manager', 
                            return_value=self.mock_system_message_manager)
        self.mock_get_system_message_manager = self.patcher.start()
        
        # Reset the global prompt manager instance
        import backend.adapter.Prompt
        backend.adapter.Prompt._prompt_manager = None
    
    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()
    
    def test_chat_request_to_prompt_uses_default_system_message(self):
        """Test that chat_request_to_prompt uses the default system message."""
        # Create a chat request without a system message
        request = ChatRequest(
            model="gpt-3.5-turbo",
            messages=[
                Message(role="user", content="Hello, how are you?")
            ]
        )
        
        # Convert the request to a prompt
        prompt = chat_request_to_prompt(request)
        
        # Verify that the prompt includes the default system message
        self.assertIn(f"System: {DEFAULT_SYSTEM_MESSAGE}", prompt)
        self.assertIn("Human: Hello, how are you?", prompt)
        self.assertIn("Assistant:", prompt)
    
    def test_chat_request_to_prompt_overrides_system_message(self):
        """Test that chat_request_to_prompt overrides the system message in the request."""
        # Create a chat request with a system message
        request = ChatRequest(
            model="gpt-3.5-turbo",
            messages=[
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello, how are you?")
            ]
        )
        
        # Convert the request to a prompt
        prompt = chat_request_to_prompt(request)
        
        # Verify that the prompt includes our default system message, not the one in the request
        self.assertIn(f"System: {DEFAULT_SYSTEM_MESSAGE}", prompt)
        self.assertNotIn("System: You are a helpful assistant.", prompt)
        self.assertIn("Human: Hello, how are you?", prompt)
        self.assertIn("Assistant:", prompt)
    
    def test_chat_request_to_prompt_with_custom_system_message(self):
        """Test that chat_request_to_prompt uses a custom system message if set."""
        # Set a custom system message
        custom_message = "You are a custom assistant with special abilities."
        self.mock_system_message_manager.get_system_message.return_value = custom_message
        
        # Create a chat request without a system message
        request = ChatRequest(
            model="gpt-3.5-turbo",
            messages=[
                Message(role="user", content="Hello, how are you?")
            ]
        )
        
        # Convert the request to a prompt
        prompt = chat_request_to_prompt(request)
        
        # Verify that the prompt includes the custom system message
        self.assertIn(f"System: {custom_message}", prompt)
        self.assertIn("Human: Hello, how are you?", prompt)
        self.assertIn("Assistant:", prompt)
    
    def test_model_specific_message_integration(self):
        """Test that model-specific messages are used in the request transformer."""
        # Create a mock PromptManager that returns different messages for different models
        class MockPromptManager(PromptManager):
            def get_model_specific_message(self, model, user_id="default"):
                if model == "gpt-3.5-turbo":
                    return "You are a GPT-3.5 assistant."
                elif model == "gpt-4":
                    return "You are a GPT-4 assistant."
                elif model == "claude-3-sonnet-20240229":
                    return "You are a Claude assistant."
                else:
                    return DEFAULT_SYSTEM_MESSAGE
        
        # Replace the global prompt manager with our mock
        with patch('backend.adapter.request_transformer.get_prompt_manager', return_value=MockPromptManager()):
            # Test with GPT-3.5
            request_gpt35 = ChatRequest(
                model="gpt-3.5-turbo",
                messages=[Message(role="user", content="Hello")]
            )
            prompt_gpt35 = chat_request_to_prompt(request_gpt35)
            self.assertIn("System: You are a GPT-3.5 assistant.", prompt_gpt35)
            
            # Test with GPT-4
            request_gpt4 = ChatRequest(
                model="gpt-4",
                messages=[Message(role="user", content="Hello")]
            )
            prompt_gpt4 = chat_request_to_prompt(request_gpt4)
            self.assertIn("System: You are a GPT-4 assistant.", prompt_gpt4)
            
            # Test with Claude
            request_claude = ChatRequest(
                model="claude-3-sonnet-20240229",
                messages=[Message(role="user", content="Hello")]
            )
            prompt_claude = chat_request_to_prompt(request_claude)
            self.assertIn("System: You are a Claude assistant.", prompt_claude)


if __name__ == "__main__":
    unittest.main()

