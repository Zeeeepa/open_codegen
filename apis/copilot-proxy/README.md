# GitHub Copilot Proxy API - 14th Provider

OpenAI-compatible API wrapper for GitHub Copilot, allowing you to use Copilot through standard OpenAI API calls.

## Features

- 🔐 **GitHub Authentication**: Automatic device flow authentication with GitHub
- 🔄 **Token Management**: Automatic token refresh every 25 minutes
- 🌐 **OpenAI Compatible**: Standard `/v1/chat/completions` endpoint
- 🎯 **Language Detection**: Automatic programming language detection from context
- 📊 **Health Monitoring**: Built-in health check endpoint
- 🚀 **FastAPI**: Modern async Python web framework

## Quick Start

### 1. Install Dependencies
```bash
cd apis/copilot-proxy
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python main.py --port 8013
```

### 3. Authenticate with GitHub
When you first start the server, it will prompt you to authenticate:
```
🔐 GitHub Copilot Authentication Required!
📱 Please visit: https://github.com/login/device
🔑 Enter code: XXXX-XXXX
```

Visit the URL and enter the code to authenticate your GitHub Copilot access.

### 4. Test the API
```bash
curl -X POST http://localhost:8013/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "copilot-codex",
    "messages": [
      {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
    ]
  }'
```

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status and token validity.

### List Models
```
GET /v1/models
```
Returns available Copilot models:
- `copilot-codex` - Main code completion model
- `copilot-chat` - Chat-optimized model  
- `copilot-code` - Code-focused model

### Chat Completions
```
POST /v1/chat/completions
```
OpenAI-compatible chat completions endpoint.

**Request Body:**
```json
{
  "model": "copilot-codex",
  "messages": [
    {"role": "user", "content": "Your prompt here"}
  ],
  "max_tokens": 1000,
  "temperature": 0.0
}
```

## Language Detection

The API automatically detects programming languages from your prompts:

- **Python** (default)
- **JavaScript/Node.js** - keywords: "javascript", "js", "node", "react"
- **Java** - keywords: "java", "spring", "maven"
- **Go** - keywords: "go", "golang"
- **Rust** - keywords: "rust", "cargo"
- **C++** - keywords: "c++", "cpp", "cmake"
- **HTML/CSS** - keywords: "html", "css", "web"

## Integration with Unified Dashboard

This provider is automatically integrated into the unified dashboard as the 14th provider:

- **Provider ID**: `copilot-proxy`
- **Name**: GitHub Copilot Proxy
- **Type**: `copilot`
- **Endpoint**: `http://localhost:8013`
- **Models**: `["copilot-codex", "copilot-chat", "copilot-code"]`

## Authentication Requirements

You need:
1. **GitHub Account** with Copilot access
2. **Active GitHub Copilot Subscription**
3. **Network access** to GitHub APIs

## Error Handling

The API handles various error conditions:
- **Authentication failures** - Returns 401 with re-auth instructions
- **Token expiration** - Automatic token refresh
- **Network errors** - Graceful error responses
- **Invalid requests** - Proper HTTP error codes

## Logging

The server provides detailed logging:
- ✅ Successful operations
- ❌ Errors and failures  
- 🔄 Token refresh events
- 🧪 API requests and responses

## Command Line Options

```bash
python main.py --help
```

Options:
- `--port` - Port to run server on (default: 8013)
- `--host` - Host to bind to (default: 0.0.0.0)

## Security Notes

- Tokens are stored locally in `.copilot_token` file
- Automatic token refresh prevents expiration
- All GitHub API calls use official Copilot endpoints
- No sensitive data is logged or exposed
