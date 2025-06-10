# OpenAI Codegen Adapter - Simple Setup

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Get up and running in minutes
- **[Service Provider Configuration](docs/SERVICE_PROVIDER_CONFIGURATION.md)** - Complete configuration guide
- **[Web UI Dashboard](docs/WEB_UI_DASHBOARD.md)** - Interactive dashboard for testing and monitoring

## 🌐 Web UI Dashboard

The adapter includes a comprehensive web dashboard for easy management and testing:

### 🚀 Quick Dashboard Start
```bash
# Install dashboard dependencies
pip install -r requirements-dashboard.txt

# Start the dashboard
python start_dashboard.py

# Open browser to: http://127.0.0.1:8888
```

### ✨ Dashboard Features
- **🔧 Service Configuration**: Configure base URLs for all providers
- **🧪 Interactive Testing**: One-click test buttons for each service
- **💬 Real-Time History**: Live display of API calls and responses
- **📊 Session Statistics**: Track usage, success rates, and timing
- **🎯 Status Monitoring**: Live service status indicators

### 📱 Dashboard Interface
```
🚀 OpenAI Codegen Adapter Dashboard
┌─────────────────────────────────────────────────────────┐
│ 🔧 Service Configuration    │ 📊 Session Statistics      │
│ ┌─────────────────────────┐ │ ┌─────────────────────────┐ │
│ │ OpenAI API              │ │ │ 4 Total Calls           │ │
│ │ http://localhost:8887/v1│ │ │ 100% Success Rate       │ │
│ │ [🟢] [Save] [🤖 Test]   │ │ │ GEMINI Last Service     │ │
│ └─────────────────────────┘ │ │ 10/06/2025 Last Call    │ │
│                             │ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 💬 Session History                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ GEMINI                    10/06/2025, 00:57:32     │ │
│ │ Prompt: What are three facts about space?          │ │
│ │ Response: 🚀 Three Fascinating Space Facts...      │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Test with curl
```bash
curl -X POST http://localhost:8887/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Test with Python
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8887/v1",
    api_key="dummy"  # Not needed for local development
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### Test with Dashboard
1. Open http://127.0.0.1:8888 in your browser
2. Configure service endpoints
3. Click test buttons to run interactive tests
4. View real-time results in the message history

## Quick Start

### 1. Configure Environment
Copy `.env.example` to `.env` and update with your credentials:
```bash
cp .env.example .env
# Edit .env with your actual CODEGEN_ORG_ID and CODEGEN_TOKEN
```

### 2. Start the Server
```bash
python server.py
```
This starts the OpenAI-compatible server at `http://localhost:8887`

### 3. Test the Server

**OpenAI API Test:**
```bash
python test.py
```
This sends a test message using OpenAI client with modified baseURL.

**Anthropic API Test:**
```bash
python test_anthropic.py
```
This tests Anthropic Claude API compatibility.

**Google Gemini API Test:**
```bash
python test_google.py
```
This tests Google Gemini API compatibility.

## API Endpoints

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
