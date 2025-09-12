# Multi-AI Provider System

A unified interface for integrating multiple AI providers (both API-based and web automation) into the Open Codegen project.

## Overview

This system provides a standardized way to interact with various AI providers through a common interface, supporting both direct API calls and web automation for providers that don't offer APIs.

## Architecture

### Core Components

1. **BaseProvider** - Abstract base class defining the unified interface
2. **ProviderFactory** - Factory pattern for creating provider instances
3. **ProviderManager** - Manages provider lifecycle and operations
4. **Web Automation Framework** - Browser automation with stealth techniques

### Provider Types

- **API_BASED** - Direct API calls (Codegen, OpenAI, Anthropic, etc.)
- **WEB_AUTOMATION** - Browser automation (Claude Web, Z.AI, etc.)
- **CUSTOM_WEB** - Configurable web automation

## Features

### API-based Providers
- ✅ Codegen API integration with model mapping
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting handling
- ✅ Streaming support
- ✅ Token usage tracking

### Web Automation
- ✅ Stealth browser with advanced evasion techniques
- ✅ Human-like interaction simulation
- ✅ Session management
- ✅ Authentication handling
- ✅ UI state tracking

### Common Features
- ✅ Unified response format
- ✅ Health monitoring
- ✅ Error handling and recovery
- ✅ Concurrent operations
- ✅ Resource cleanup

## Quick Start

### 1. Install Dependencies

```bash
pip install aiohttp playwright asyncio-throttle
playwright install chromium
```

### 2. Basic Usage

```python
from backend.providers import ProviderManager, ProviderFactory
from backend.providers.base_provider import ProviderContext

# Create provider manager
manager = ProviderManager()

# Create Codegen API provider
codegen_provider = ProviderFactory.create_provider("codegen_api", {
    "type": "api_based",
    "base_url": "https://codegen-sh--rest-api.modal.run",
    "org_id": "323"
})

# Add to manager
await manager.add_provider(codegen_provider)

# Set authentication context
context = ProviderContext(
    provider_name="codegen_api",
    auth_type="token",
    credentials={"token": "your-token-here"}
)

await manager.set_provider_context("codegen_api", context)

# Send message
response = await manager.send_message("codegen_api", "Hello, what is your model name?")
print(response.content)
```

### 3. Web Automation Example

```python
from backend.automation import StealthBrowser

# Create stealth browser
browser = StealthBrowser("my_browser", headless=False)
await browser.initialize()

# Navigate and interact
await browser.navigate("https://example.com")
await browser.type_text("#input", "Hello world")
await browser.click_element("#submit")

# Get response
response = await browser.get_text("#response")
print(response)

await browser.cleanup()
```

## Configuration

### Provider Configuration

```python
provider_config = {
    "type": "api_based",  # or "web_automation"
    "base_url": "https://api.example.com",
    "timeout": 300,
    "max_retries": 20,
    "model_mapping": {
        "gpt-4": "provider-advanced",
        "gpt-3.5-turbo": "provider-standard"
    }
}
```

### Web Provider Configuration

```python
web_config = {
    "type": "web_automation",
    "base_url": "https://chat.example.com",
    "login_required": True,
    "session_timeout": 3600,
    "headless": True,
    "selectors": {
        "chat_input": "#chat-input",
        "send_button": "#send-button",
        "response_area": ".response"
    }
}
```

## Authentication

### API Token Authentication

```python
context = ProviderContext(
    provider_name="my_provider",
    auth_type="token",
    credentials={"token": "your-api-token"}
)
```

### Username/Password Authentication

```python
context = ProviderContext(
    provider_name="my_provider",
    auth_type="username_password",
    credentials={
        "username": "your-username",
        "password": "your-password"
    }
)
```

### Cookie-based Authentication

```python
context = ProviderContext(
    provider_name="my_provider",
    auth_type="cookies",
    credentials={
        "cookies": [
            {"name": "session", "value": "abc123", "domain": ".example.com"}
        ]
    }
)
```

## Provider Status

Providers can be in one of these states:

- `INACTIVE` - Provider is disabled
- `INITIALIZING` - Provider is starting up
- `ACTIVE` - Provider is ready and operational
- `BUSY` - Provider is processing a request
- `ERROR` - Provider encountered an error
- `RATE_LIMITED` - Provider is rate limited
- `AUTHENTICATION_REQUIRED` - Needs authentication

## Model Mapping

The system supports automatic model mapping for different providers:

```python
model_mapping = {
    # OpenAI models
    'gpt-3.5-turbo': 'codegen-standard',
    'gpt-4': 'codegen-advanced',
    
    # Anthropic models
    'claude-3-sonnet-20240229': 'codegen-advanced',
    'claude-3-haiku-20240307': 'codegen-standard',
    
    # Gemini models
    'gemini-1.5-pro': 'codegen-advanced',
    'gemini-pro': 'codegen-standard'
}
```

## Stealth Techniques

The web automation framework includes advanced stealth techniques:

- Browser fingerprint randomization
- Human-like behavior simulation
- WebDriver detection evasion
- Canvas/WebGL fingerprint protection
- Mouse movement simulation
- Keyboard input randomization

## Error Handling

The system provides comprehensive error handling:

```python
try:
    response = await manager.send_message("provider", "Hello")
    if response.success:
        print(response.content)
    else:
        print(f"Error: {response.error}")
except Exception as e:
    print(f"Exception: {str(e)}")
```

## Monitoring and Health Checks

```python
# Check individual provider health
healthy = await manager.test_provider("codegen_api")

# Check all providers
health_status = await manager.health_check_all()

# Get provider statistics
stats = await manager.get_provider_stats()
```

## Extending the System

### Creating a New API Provider

```python
from backend.providers.base_provider import BaseProvider, ProviderType
from backend.providers.provider_factory import register_provider

@register_provider("my_api")
class MyAPIProvider(BaseProvider):
    async def initialize(self, context):
        # Initialize your provider
        pass
    
    async def send_message(self, message, **kwargs):
        # Implement message sending
        pass
    
    async def stream_message(self, message, **kwargs):
        # Implement streaming
        pass
    
    async def health_check(self):
        # Implement health check
        pass
    
    async def cleanup(self):
        # Cleanup resources
        pass
```

### Creating a New Web Provider

```python
from backend.automation.web_provider_base import WebProviderBase
from backend.providers.provider_factory import register_provider

@register_provider("my_web")
class MyWebProvider(WebProviderBase):
    def __init__(self, name, provider_type, config):
        super().__init__(name, provider_type, config)
        
        # Set your selectors
        self.selectors.update({
            'chat_input': '#my-input',
            'send_button': '#my-send',
            'response_area': '.my-response'
        })
    
    async def _authenticate(self):
        # Implement authentication
        pass
    
    async def _wait_for_response(self):
        # Implement response waiting
        pass
```

## Environment Variables

```bash
# Codegen API
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=your-token
CODEGEN_TIMEOUT=300
CODEGEN_MAX_RETRIES=20
CODEGEN_BASE_DELAY=2
CODEGEN_DEFAULT_MODEL=codegen-standard
```

## Best Practices

1. **Always use context managers** for resource cleanup
2. **Implement proper error handling** with retries
3. **Monitor provider health** regularly
4. **Use stealth techniques** for web automation
5. **Respect rate limits** and implement backoff
6. **Validate inputs** before sending to providers
7. **Log operations** for debugging and monitoring

## Troubleshooting

### Common Issues

1. **Provider not initializing**
   - Check authentication credentials
   - Verify network connectivity
   - Check provider-specific requirements

2. **Web automation failing**
   - Ensure Playwright is installed: `playwright install`
   - Check if selectors are correct
   - Verify the target website is accessible

3. **Rate limiting**
   - Implement proper delays between requests
   - Use exponential backoff
   - Monitor usage limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new providers:

1. Extend the appropriate base class
2. Implement all required methods
3. Add comprehensive error handling
4. Include tests
5. Update documentation
6. Register with the factory

## License

This project is part of the Open Codegen system and follows the same licensing terms.
