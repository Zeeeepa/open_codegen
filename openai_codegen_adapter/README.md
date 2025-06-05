# OpenAI Codegen Adapter

A FastAPI-based server that provides OpenAI-compatible API endpoints for the Codegen platform, enabling seamless integration with OpenAI client libraries.

## Features

- **OpenAI Chat Completions API** - Compatible with OpenAI's chat completions format
- **OpenAI Text Completions API** - Support for legacy text completions
- **Anthropic Claude API** - Native support for Anthropic's Claude models
- **Google Gemini API** - Integration with Google's Gemini models
- **Streaming Support** - Real-time streaming responses for all endpoints
- **Enhanced Logging** - Comprehensive request/response tracking and debugging

## Quick Start

### Installation

```bash
pip install fastapi uvicorn
```

### Running the Server

```bash
cd openai_codegen_adapter
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### Using with OpenAI Client

```python
from openai import OpenAI

# Point to your local adapter
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-codegen-token"
)

# Use exactly like OpenAI
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)

print(response.choices[0].message.content)
```

### Using with Codegen SDK

```python
from codegen import Agent

# Create an agent
agent = Agent(org_id="323", token="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99")

# Run a task
task = agent.run("Generate response as if this prompt was sent to openai api - 'user input'")

# Check status and get result
task.refresh()
if task.status == "completed":
    print(task.result)
```

## API Endpoints

### OpenAI Compatible

- `POST /v1/chat/completions` - Chat completions (streaming & non-streaming)
- `POST /v1/completions` - Text completions (streaming & non-streaming)

### Anthropic Compatible

- `POST /v1/anthropic/messages` - Claude messages API
- `POST /v1/anthropic/completions` - Claude completions API

### Google Gemini Compatible

- `POST /v1/gemini/generateContent` - Gemini content generation
- `POST /v1/gemini/completions` - Gemini completions

### Health & Info

- `GET /health` - Health check endpoint
- `GET /v1/models` - List available models

## Configuration

The adapter uses environment variables for configuration:

```bash
export CODEGEN_API_TOKEN="your-token"
export CODEGEN_ORG_ID="your-org-id"
export LOG_LEVEL="INFO"
```

## Streaming Support

All endpoints support streaming responses. Enable streaming by setting `"stream": true` in your request:

```python
# OpenAI streaming
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Error Handling

The adapter provides detailed error responses compatible with OpenAI's error format:

```json
{
  "error": {
    "message": "Invalid request format",
    "type": "invalid_request_error",
    "code": "invalid_request"
  }
}
```

## Logging

Enhanced logging provides detailed tracking of requests and responses:

```
🚀 REQUEST START | Endpoint: /v1/chat/completions
   📊 Request Data: {"model": "gpt-3.5-turbo", "messages": [...]}
   🕐 Timestamp: 2024-01-15T10:30:00.000Z

🌊 Initiating streaming response...
📦 Collected 1247 tokens in 2.3s

✅ REQUEST END | Status: 200 | Duration: 2.34s
```

## Development

### Running Tests

```bash
python test_gemini_fix.py
```

### Code Structure

- `server.py` - Main FastAPI application and endpoints
- `models.py` - Pydantic models for request/response validation
- `streaming.py` - Streaming response handlers
- `gemini_streaming.py` - Gemini-specific streaming logic
- `anthropic_streaming.py` - Anthropic-specific streaming logic
- `codegen_client.py` - Codegen platform integration

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check your Codegen API token and org ID
   - Verify the Codegen service is accessible
   - Check server logs for detailed error messages

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

3. **Streaming Not Working**
   - Verify client supports streaming
   - Check network connectivity
   - Enable debug logging for detailed traces

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL="DEBUG"
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Codegen platform. See the main repository for license information.

