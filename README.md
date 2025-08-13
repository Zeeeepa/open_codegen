# OpenAI Codegen Adapter - Transparent API Interception

Transform any OpenAI API application to use Codegen SDK **without code changes**!

## 🚀 Quick Start (Ubuntu)

### Option 1: Auto-Transparent Mode (Recommended)
**One command starts everything - DNS interception, server, and cleanup!**

```bash
# Start transparent interception (auto-manages everything)
sudo python3 server.py

# Test with any OpenAI application (no code changes needed!)
python3 test_standard_ports.py
```

**Features:**
- ✅ Automatically enables DNS interception
- ✅ Runs on standard HTTP port 80 (true transparency!)
- ✅ Starts the interceptor server  
- ✅ Cleans up DNS settings on exit (Ctrl+C)
- ✅ Works with any existing OpenAI application

### Option 2: Manual Installation
**Traditional installation with separate setup steps**

```bash
# One-command installation
sudo ./install-ubuntu.sh

# Test transparent interception
python3 test_transparent_mode.py
```

### Option 3: Direct Mode (Manual Configuration)
**Requires changing base_url in applications**

```bash
# Start the server in direct mode
TRANSPARENT_MODE=false python3 server.py

# Test with modified client
python test.py
```

## 🔄 Transparent Mode Features

✅ **Zero Code Changes** - Existing OpenAI applications work immediately  
✅ **DNS Interception** - Redirects `api.openai.com` to local server  
✅ **HTTPS Support** - Full SSL certificate management  
✅ **Systemd Integration** - Runs as Ubuntu service  
✅ **Multi-API Support** - OpenAI, Anthropic, Google Gemini compatible

## 🧪 Testing

### Test Transparent Interception
```bash
# Test standard port transparent mode (recommended)
python3 test_standard_ports.py

# Test auto-transparent mode (legacy)
python3 test_auto_transparent.py

# Test manual transparent mode
python3 test_transparent_mode.py

# Test specific APIs
python test.py              # OpenAI API
python test_anthropic.py    # Anthropic API  
python test_google.py       # Google Gemini API

# Test Prompt module
python tests/validate_prompt.py  # Validate the Prompt module
```

### Example: Transparent Usage
```python
# This code works WITHOUT modification after installation!
from openai import OpenAI

client = OpenAI(api_key="your-key")  # No base_url needed!

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
# ✅ Automatically routed to Codegen SDK
```

## 📋 Management Commands

### Service Management
```bash
sudo systemctl status openai-interceptor    # Check status
sudo systemctl start openai-interceptor     # Start service
sudo systemctl stop openai-interceptor      # Stop service
sudo systemctl restart openai-interceptor   # Restart service
sudo journalctl -u openai-interceptor -f    # View logs
```

### DNS & SSL Management
```bash
sudo python3 -m interceptor.ubuntu_dns status    # DNS status
sudo python3 -m interceptor.ubuntu_dns enable    # Enable DNS
sudo python3 -m interceptor.ubuntu_dns disable   # Disable DNS

sudo python3 -m interceptor.ubuntu_ssl status    # SSL status
sudo python3 -m interceptor.ubuntu_ssl setup     # Setup SSL
sudo python3 -m interceptor.ubuntu_ssl remove    # Remove SSL
```

### Uninstall
```bash
sudo ./uninstall-ubuntu.sh  # Complete removal
```

## 🔧 API Endpoints

### OpenAI Compatible
- **`/v1/chat/completions`** - OpenAI chat completions
- **`/v1/completions`** - OpenAI text completions
- **`/v1/models`** - List available models

### Anthropic Compatible
- **`/v1/messages`** - Anthropic Claude messages
- **`/v1/anthropic/completions`** - Anthropic completions

### Google Gemini Compatible
- **`/v1/gemini/generateContent`** - Google Gemini content generation
- **`/v1/gemini/completions`** - Google Gemini completions

## 🤖 System Message Configuration

The adapter now includes a Prompt module that allows you to customize the system message used for all requests. By default, it uses a fast-responding coding agent prompt:

```
"you are A fast responding coding agent- respond in a single message"
```

### Customizing System Messages

You can customize the system message through the API:

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

You can also use the Prompt module programmatically:

```python
from backend.adapter.Prompt import get_prompt_manager

# Get the prompt manager
prompt_manager = get_prompt_manager()

# Get the current system message
system_message = prompt_manager.get_system_message()

# Set a custom system message
prompt_manager.set_system_message("Your custom system message here")

# Reset to the default message
prompt_manager.reset_to_default()
```

## Usage Examples

### OpenAI Client
```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",
    base_url="http://localhost:8887/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic Client
```python
import requests

response = requests.post(
    "http://localhost:8887/v1/messages",
    json={
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello!"}]
    },
    headers={"x-api-key": "dummy-key"}
)
```

## Environment Configuration Examples

### OpenAI Environment Setup
```python
from openai import OpenAI

def main():
    client = OpenAI(
        api_key="dummy-key",  # Server doesn't validate this
        base_url="http://localhost:8887/v1"  # Point to our server
    )
```

### Anthropic Environment Setup
```python
import anthropic

def main():
    client = anthropic.Anthropic(
        api_key="dummy-key",  # Server doesn't validate this
        base_url="http://localhost:8887/v1"  # Point to our server
    )
```

### Google Gemini Environment Setup
```python
import requests

def main():
    # Point Gemini requests to our server
    base_url = "http://localhost:8887/v1/gemini"
    
    response = requests.post(
        f"{base_url}/generateContent",
        json={"contents": [{"role": "user", "parts": [{"text": "Hello!"}]}]}
    )
```

## Files

- **`server.py`** - Starts the FastAPI server
- **`test.py`** - Simple OpenAI client test with modified baseURL
- **`test_anthropic.py`** - Anthropic API compatibility test
- **`test_google.py`** - Google Gemini API compatibility test
- **`.env.example`** - Environment configuration template
- **`backend/adapter/`** - Core adapter implementation
- **`backend/adapter/Prompt.py`** - System message management
- **`tests/validate_prompt.py`** - Validation script for the Prompt module

## How it Works

1. The server runs on `localhost:8887` and provides both OpenAI and Anthropic-compatible endpoints
2. Tests use standard clients but point to our local server
3. Requests are transformed and sent to Codegen API
4. Responses are transformed back to the appropriate API format
5. The Prompt module ensures all requests use the fast-responding coding agent system message

That's it! 🚀

