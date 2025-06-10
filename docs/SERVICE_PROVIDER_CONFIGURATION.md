# Service Provider Configuration Guide

This guide explains how to configure base URLs for different AI service providers when using the OpenAI Codegen Adapter locally.

## 🌐 Overview

The OpenAI Codegen Adapter supports multiple AI service providers. Each provider has official base URLs for production use and can be configured for local development and testing.

## 📋 Supported Service Providers

### 🏢 Official Cloud Providers

| Provider | Base URL | API Version | Authentication | Multimodal |
|----------|----------|-------------|----------------|------------|
| **OpenAI** | `https://api.openai.com` | v1 | Bearer Token | ✅ |
| **Anthropic Claude** | `https://api.anthropic.com` | v1 | x-api-key Header | ✅ |
| **Google Vertex AI** | `https://{location}-aiplatform.googleapis.com` | v1 | OAuth 2.0 / Service Account | ✅ |
| **Google AI Studio** | `https://generativelanguage.googleapis.com` | v1beta | API Key | ✅ |
| **Azure OpenAI** | `https://{resource-name}.openai.azure.com` | 2024-02-01 | API Key / Azure AD | ✅ |
| **Cohere** | `https://api.cohere.ai` | v1 | Bearer Token | ❌ |
| **Hugging Face** | `https://api-inference.huggingface.co` | v1 | Bearer Token | ✅ |
| **Mistral AI** | `https://api.mistral.ai` | v1 | Bearer Token | ❌ |
| **Together AI** | `https://api.together.xyz` | v1 | Bearer Token | ✅ |
| **Replicate** | `https://api.replicate.com` | v1 | Bearer Token | ✅ |

### 🏠 Local Development Providers

| Provider | Default URL | Port | Documentation |
|----------|-------------|------|---------------|
| **Ollama** | `http://localhost:11434` | 11434 | [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md) |
| **LM Studio** | `http://localhost:1234` | 1234 | [LM Studio API Docs](https://lmstudio.ai/docs/api/openai-api) |
| **Text Generation WebUI** | `http://localhost:5000` | 5000 | [WebUI API Docs](https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API) |
| **vLLM** | `http://localhost:8000` | 8000 | [vLLM API Docs](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html) |
| **LocalAI** | `http://localhost:8080` | 8080 | [LocalAI API Docs](https://localai.io/features/openai-functions/) |

## 🔧 Configuration Methods

### Method 1: Environment Variables (Recommended)

Set environment variables to override default base URLs:

```bash
# Official providers
export OPENAI_BASE_URL="https://api.openai.com"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export GOOGLE_VERTEX_AI_BASE_URL="https://us-central1-aiplatform.googleapis.com"
export GOOGLE_AI_STUDIO_BASE_URL="https://generativelanguage.googleapis.com"

# Local development
export OPENAI_BASE_URL="http://localhost:8080"  # Use local OpenAI-compatible server
export ANTHROPIC_BASE_URL="http://localhost:8081"  # Use local Anthropic-compatible server
```

### Method 2: Configuration File

Create a `.env` file in your project root:

```env
# .env file
OPENAI_BASE_URL=http://localhost:8080
ANTHROPIC_BASE_URL=http://localhost:8081
GOOGLE_AI_STUDIO_BASE_URL=http://localhost:8082
CODEGEN_ORG_ID=your_org_id
CODEGEN_TOKEN=your_token
```

### Method 3: Python Configuration

Use the configuration module directly in your code:

```python
from config.service_providers import ServiceProviderURLs, get_base_url_from_env

# Get default configuration
openai_config = ServiceProviderURLs.OPENAI
print(f"OpenAI Base URL: {openai_config.base_url}")

# Get URL with environment variable override
actual_url = get_base_url_from_env("OPENAI", openai_config)
print(f"Actual URL to use: {actual_url}")
```

## 🚀 Quick Start Examples

### Example 1: Using Official OpenAI

```bash
export OPENAI_BASE_URL="https://api.openai.com"
export OPENAI_API_KEY="sk-your-openai-key"
python -m openai_codegen_adapter.main
```

### Example 2: Using Local Ollama

```bash
# Start Ollama server
ollama serve

# Configure adapter to use Ollama
export OPENAI_BASE_URL="http://localhost:11434"
python -m openai_codegen_adapter.main
```

### Example 3: Using Local LM Studio

```bash
# Start LM Studio server on port 1234
# Configure adapter to use LM Studio
export OPENAI_BASE_URL="http://localhost:1234"
python -m openai_codegen_adapter.main
```

### Example 4: Using Google Vertex AI

```bash
export GOOGLE_VERTEX_AI_BASE_URL="https://us-central1-aiplatform.googleapis.com"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
python -m openai_codegen_adapter.main
```

## 🔐 Authentication Configuration

### OpenAI
```bash
export OPENAI_API_KEY="sk-your-openai-key"
```

### Anthropic
```bash
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
```

### Google Vertex AI
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
# OR
export GOOGLE_API_KEY="your-google-api-key"
```

### Azure OpenAI
```bash
export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
```

## 🧪 Testing Your Configuration

### Test with curl

```bash
# Test OpenAI endpoint
curl -X POST "$OPENAI_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test Anthropic endpoint
curl -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Test with Python

```python
import requests
import os

# Test OpenAI-compatible endpoint
def test_openai_endpoint():
    url = f"{os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

test_openai_endpoint()
```

## 🐳 Docker Configuration

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  codegen-adapter:
    build: .
    ports:
      - "8887:8887"
    environment:
      - OPENAI_BASE_URL=http://localhost:8080
      - ANTHROPIC_BASE_URL=http://localhost:8081
      - CODEGEN_ORG_ID=${CODEGEN_ORG_ID}
      - CODEGEN_TOKEN=${CODEGEN_TOKEN}
    volumes:
      - ./.env:/app/.env
```

### Using Docker Run

```bash
docker run -p 8887:8887 \
  -e OPENAI_BASE_URL=http://localhost:8080 \
  -e ANTHROPIC_BASE_URL=http://localhost:8081 \
  -e CODEGEN_ORG_ID=your_org_id \
  -e CODEGEN_TOKEN=your_token \
  codegen-adapter
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Error: Connection refused to http://localhost:8080
   ```
   - Ensure your local server is running
   - Check the port number is correct
   - Verify firewall settings

2. **Authentication Failed**
   ```
   Error: 401 Unauthorized
   ```
   - Check your API key is correct
   - Verify the authentication method (Bearer vs x-api-key)
   - Ensure the API key has proper permissions

3. **Model Not Found**
   ```
   Error: 404 Model not found
   ```
   - Check the model name is correct for your provider
   - Verify the model is available in your region/account
   - Use the provider's default model for testing

### Debug Mode

Enable debug logging to see detailed request/response information:

```bash
export LOG_LEVEL=debug
python -m openai_codegen_adapter.main
```

### Health Check

Test if your configuration is working:

```bash
curl http://localhost:8887/health
curl http://localhost:8887/v1/models
```

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/claude/reference)
- [Google Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs/reference/rest)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [LM Studio Documentation](https://lmstudio.ai/docs)

## 🤝 Contributing

To add support for a new service provider:

1. Add the provider configuration to `config/service_providers.py`
2. Update this documentation
3. Add tests for the new provider
4. Submit a pull request

## 📝 License

This configuration is part of the OpenAI Codegen Adapter project and follows the same license terms.

