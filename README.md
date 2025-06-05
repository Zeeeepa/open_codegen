# OpenAI Codegen Adapter - Simple Setup

## Quick Start

### 1. Configure Environment
Copy `.env.example` to `.env` and update with your credentials:
```bash
cp .env.example .env
# Edit .env with your actual CODEGEN_ORG_ID and CODEGEN_TOKEN
```

### 2. Start the Server

**Basic Server:**
```bash
python server.py
```

**Enhanced Server (with metrics, health monitoring, and middleware):**
```bash
python server_enhanced.py
```

Both start the server at `http://localhost:8887` with full API compatibility.

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

**Comprehensive Test Suite:**
```bash
python test_all_endpoints.py
```
This tests all endpoints (OpenAI, Anthropic, Gemini, health checks, error handling).

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

### Health & Monitoring
- **`/health`** - Basic health check
- **`/health/detailed`** - Detailed health with metrics and system info
- **`/health/metrics`** - Comprehensive metrics and statistics
- **`/health/readiness`** - Kubernetes-style readiness check
- **`/health/liveness`** - Kubernetes-style liveness check
- **`/health/config`** - Configuration status (without sensitive data)

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

## Files

- **`server.py`** - Starts the FastAPI server
- **`test.py`** - Simple OpenAI client test with modified baseURL
- **`test_anthropic.py`** - Anthropic API compatibility test
- **`test_google.py`** - Google Gemini API compatibility test
- **`test_all_endpoints.py`** - Comprehensive test suite
- **`.env.example`** - Environment configuration template
- **`openai_codegen_adapter/`** - Core adapter implementation

## How it Works

1. The server runs on `localhost:8887` and provides both OpenAI and Anthropic-compatible endpoints
2. Tests use standard clients but point to our local server
3. Requests are transformed and sent to Codegen API
4. Responses are transformed back to the appropriate API format

That's it! 🚀
