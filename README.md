# 🚀 Codegen AI Proxy

**Transparent API Gateway for OpenAI, Anthropic & Gemini → Codegen API**

A lightweight Docker container that intercepts AI API calls and routes them to Codegen API with automatic system message injection. **Zero code changes required** - just point your existing applications to the proxy!

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
- **`openai_codegen_adapter/`** - Core adapter implementation

## How it Works

1. The server runs on `localhost:8887` and provides both OpenAI and Anthropic-compatible endpoints
2. Tests use standard clients but point to our local server
3. Requests are transformed and sent to Codegen API
4. Responses are transformed back to the appropriate API format

That's it! 🚀
