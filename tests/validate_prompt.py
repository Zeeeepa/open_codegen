#!/usr/bin/env python3
"""
Validation script for the Prompt module.
This script tests the Prompt module by running the unit tests and integration tests,
and then performs a manual validation of the system message functionality.
"""

import os
import sys
import unittest
import logging
import json
from pathlib import Path

# Add the parent directory to the path so we can import the backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_unit_tests():
    """Run the unit tests for the Prompt module."""
    logger.info("Running unit tests for Prompt module...")
    from tests.test_prompt import TestPromptManager
    
    # Create a test suite with the TestPromptManager tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPromptManager)
    
    # Run the tests
    result = unittest.TextTestRunner().run(suite)
    
    # Check if all tests passed
    if result.wasSuccessful():
        logger.info("✅ All unit tests passed!")
        return True
    else:
        logger.error("❌ Unit tests failed!")
        return False

def run_integration_tests():
    """Run the integration tests for the Prompt module."""
    logger.info("Running integration tests for Prompt module...")
    from tests.test_prompt_integration import TestPromptIntegration
    
    # Create a test suite with the TestPromptIntegration tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPromptIntegration)
    
    # Run the tests
    result = unittest.TextTestRunner().run(suite)
    
    # Check if all tests passed
    if result.wasSuccessful():
        logger.info("✅ All integration tests passed!")
        return True
    else:
        logger.error("❌ Integration tests failed!")
        return False

def validate_prompt_manager():
    """Manually validate the PromptManager functionality."""
    logger.info("Manually validating PromptManager functionality...")
    
    # Import the PromptManager and DEFAULT_SYSTEM_MESSAGE
    from backend.adapter.Prompt import PromptManager, DEFAULT_SYSTEM_MESSAGE, get_prompt_manager
    
    # Create a temporary storage file
    import tempfile
    temp_dir = tempfile.TemporaryDirectory()
    storage_path = Path(temp_dir.name) / "test_system_messages.json"
    
    # Create a SystemMessageManager with the temporary storage file
    from backend.adapter.system_message_manager import SystemMessageManager
    system_message_manager = SystemMessageManager(str(storage_path))
    
    # Create a PromptManager with the SystemMessageManager
    with unittest.mock.patch('backend.adapter.Prompt.get_system_message_manager', return_value=system_message_manager):
        # Reset the global prompt manager instance
        import backend.adapter.Prompt
        backend.adapter.Prompt._prompt_manager = None
        
        # Get the prompt manager
        prompt_manager = get_prompt_manager()
        
        # Verify that the default message is set
        message = prompt_manager.get_system_message()
        if message != DEFAULT_SYSTEM_MESSAGE:
            logger.error(f"❌ Default message not set correctly! Got: {message}")
            return False
        
        # Set a custom message
        custom_message = "This is a custom system message for testing."
        result = prompt_manager.set_system_message(custom_message)
        if not result:
            logger.error("❌ Failed to set custom message!")
            return False
        
        # Verify that the custom message is returned
        message = prompt_manager.get_system_message()
        if message != custom_message:
            logger.error(f"❌ Custom message not returned correctly! Got: {message}")
            return False
        
        # Reset to default
        result = prompt_manager.reset_to_default()
        if not result:
            logger.error("❌ Failed to reset to default message!")
            return False
        
        # Verify that the default message is returned
        message = prompt_manager.get_system_message()
        if message != DEFAULT_SYSTEM_MESSAGE:
            logger.error(f"❌ Default message not returned after reset! Got: {message}")
            return False
        
        # Get system message info
        info = prompt_manager.get_system_message_info()
        if not info["is_default"]:
            logger.error("❌ is_default flag not set correctly in message info!")
            return False
        
        logger.info("✅ Manual validation of PromptManager passed!")
        return True

def validate_request_transformer():
    """Manually validate the request transformer with the Prompt module."""
    logger.info("Manually validating request transformer with Prompt module...")
    
    # Import the necessary modules
    from backend.adapter.models import ChatRequest, Message
    from backend.adapter.request_transformer import chat_request_to_prompt
    from backend.adapter.Prompt import PromptManager, DEFAULT_SYSTEM_MESSAGE, get_prompt_manager
    
    # Create a temporary storage file
    import tempfile
    temp_dir = tempfile.TemporaryDirectory()
    storage_path = Path(temp_dir.name) / "test_system_messages.json"
    
    # Create a SystemMessageManager with the temporary storage file
    from backend.adapter.system_message_manager import SystemMessageManager
    system_message_manager = SystemMessageManager(str(storage_path))
    
    # Create a PromptManager with the SystemMessageManager
    with unittest.mock.patch('backend.adapter.Prompt.get_system_message_manager', return_value=system_message_manager):
        # Reset the global prompt manager instance
        import backend.adapter.Prompt
        backend.adapter.Prompt._prompt_manager = None
        
        # Create a chat request
        request = ChatRequest(
            model="gpt-3.5-turbo",
            messages=[
                Message(role="user", content="Hello, how are you?")
            ]
        )
        
        # Convert the request to a prompt
        prompt = chat_request_to_prompt(request)
        
        # Verify that the prompt includes the default system message
        if DEFAULT_SYSTEM_MESSAGE not in prompt:
            logger.error(f"❌ Default system message not included in prompt! Prompt: {prompt}")
            return False
        
        # Set a custom message
        custom_message = "This is a custom system message for testing."
        prompt_manager = get_prompt_manager()
        prompt_manager.set_system_message(custom_message)
        
        # Convert the request to a prompt again
        prompt = chat_request_to_prompt(request)
        
        # Verify that the prompt includes the custom system message
        if custom_message not in prompt:
            logger.error(f"❌ Custom system message not included in prompt! Prompt: {prompt}")
            return False
        
        logger.info("✅ Manual validation of request transformer passed!")
        return True

def main():
    """Run all validation tests."""
    logger.info("Starting validation of Prompt module...")
    
    # Run unit tests
    unit_tests_passed = run_unit_tests()
    
    # Run integration tests
    integration_tests_passed = run_integration_tests()
    
    # Manually validate the PromptManager
    prompt_manager_valid = validate_prompt_manager()
    
    # Manually validate the request transformer
    request_transformer_valid = validate_request_transformer()
    
    # Check if all validations passed
    if unit_tests_passed and integration_tests_passed and prompt_manager_valid and request_transformer_valid:
        logger.info("✅ All validations passed! The Prompt module is working correctly.")
        return 0
    else:
        logger.error("❌ Some validations failed! Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

