# Prompt Management

This document provides detailed information about the Prompt module and how to use it to customize system messages in the OpenAI Codegen Adapter.

## Overview

The Prompt module provides a clean interface for managing system messages used in API requests. It ensures that all requests use a consistent system message, which by default is set to:

```
"you are A fast responding coding agent- respond in a single message"
```

This default message instructs the AI to respond quickly and concisely, providing all information in a single message rather than multiple messages.

## Architecture

The Prompt module consists of the following components:

1. **PromptManager**: The main class that provides methods for getting, setting, and managing system messages.
2. **get_prompt_manager()**: A function that returns a global instance of the PromptManager.
3. **Integration with request_transformer.py**: The request transformer uses the Prompt module to get the appropriate system message for each request.

## Usage

### API Endpoints

The Prompt module is integrated with the server's API endpoints, allowing you to manage system messages through HTTP requests:

```bash
# Get the current system message
curl http://localhost:8887/api/system-message

# Set a custom system message
curl -X POST http://localhost:8887/api/system-message \
  -H "Content-Type: application/json" \
  -d '{"message": "Your custom system message here"}'

# Clear the system message (resets to default)
curl -X DELETE http://localhost:8887/api/system-message
```

### Programmatic Usage

You can also use the Prompt module programmatically in your Python code:

```python
from backend.adapter.Prompt import get_prompt_manager

# Get the prompt manager
prompt_manager = get_prompt_manager()

# Get the current system message
system_message = prompt_manager.get_system_message()
print(f"Current system message: {system_message}")

# Set a custom system message
prompt_manager.set_system_message("Your custom system message here")

# Reset to the default message
prompt_manager.reset_to_default()

# Get system message info (includes metadata)
info = prompt_manager.get_system_message_info()
print(f"Message info: {info}")

# Get a model-specific message (for future use)
model_message = prompt_manager.get_model_specific_message("gpt-4")
print(f"Model-specific message: {model_message}")
```

## Advanced Features

### Model-Specific Messages

The Prompt module includes support for model-specific system messages, allowing you to customize the system message based on the model being used. This feature is currently a placeholder for future development, but the interface is already in place:

```python
# Get a model-specific message
model_message = prompt_manager.get_model_specific_message("gpt-4")
```

### Message Metadata

The Prompt module provides access to metadata about the system message, including:

- Whether it's the default message
- When it was created
- The character count
- Whether a message exists

```python
# Get system message info
info = prompt_manager.get_system_message_info()
print(f"Is default: {info['is_default']}")
print(f"Created at: {info['created_at']}")
print(f"Character count: {info['character_count']}")
print(f"Has message: {info['has_message']}")
```

## Testing

The Prompt module includes comprehensive unit tests and integration tests to ensure it works correctly. You can run these tests using the validation script:

```bash
python tests/validate_prompt.py
```

This script runs:

1. Unit tests for the PromptManager class
2. Integration tests for the Prompt module with the request transformer
3. Manual validation of the PromptManager functionality
4. Manual validation of the request transformer with the Prompt module

## Customization

You can customize the default system message by modifying the `DEFAULT_SYSTEM_MESSAGE` constant in `backend/adapter/Prompt.py`:

```python
# Default system message for fast responding coding agent
DEFAULT_SYSTEM_MESSAGE = "you are A fast responding coding agent- respond in a single message"
```

## Future Enhancements

Planned enhancements for the Prompt module include:

1. **Full model-specific message support**: Customize system messages for different models (GPT, Claude, Gemini).
2. **Prompt templating**: Support for dynamic prompt generation based on request parameters.
3. **User-specific messages**: Support for different system messages for different users.
4. **Web UI integration**: A user-friendly interface for managing system messages.
5. **Versioning and A/B testing**: Support for testing different system messages and tracking their performance.

## Troubleshooting

If you encounter issues with the Prompt module, check the following:

1. **System message not being applied**: Make sure the request_transformer.py file is using the Prompt module correctly.
2. **Custom message not being saved**: Check that the system_message_manager.py file has write permissions to the storage file.
3. **Default message not being set**: Verify that the PromptManager._ensure_default_message method is being called during initialization.

For more help, please open an issue on the GitHub repository.

