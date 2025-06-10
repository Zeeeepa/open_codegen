# Quick Start Guide - Service Provider Configuration

This guide helps you quickly set up the OpenAI Codegen Adapter with different AI service providers for local development.

## 🚀 Quick Setup

### 1. Choose Your Setup Method

#### Option A: Official Cloud Providers (Recommended for Production)
```bash
# Use official OpenAI
export OPENAI_BASE_URL="https://api.openai.com"
export OPENAI_API_KEY="sk-your-openai-key"

# Use official Anthropic
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
```

#### Option B: Local Development (Free, No API Keys Required)
```bash
# Use local Ollama server
export OPENAI_BASE_URL="http://localhost:11434"

# Use local LM Studio
export OPENAI_BASE_URL="http://localhost:1234"
```

### 2. Set Codegen Credentials
```bash
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="sk-your-codegen-token"
```

### 3. Start the Adapter
```bash
python -m openai_codegen_adapter.main
```

## 🛠️ Configuration Tools

### Use the Configuration CLI
```bash
# List all available providers
python scripts/configure_providers.py --list

# Configure OpenAI to use local Ollama
python scripts/configure_providers.py --provider openai --url http://localhost:11434

# Generate .env template
python scripts/configure_providers.py --generate-env

# Test connection
python scripts/configure_providers.py --test-connection openai
```

### Manual .env Configuration
```bash
# Copy the template
cp .env.example .env

# Edit with your values
nano .env
```

## 🏠 Local Development Setups

### Setup 1: Ollama (Easiest)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama2

# Configure adapter
export OPENAI_BASE_URL="http://localhost:11434"
python -m openai_codegen_adapter.main
```

### Setup 2: LM Studio
```bash
# Download and install LM Studio from https://lmstudio.ai
# Start the local server on port 1234
# Configure adapter
export OPENAI_BASE_URL="http://localhost:1234"
python -m openai_codegen_adapter.main
```

### Setup 3: Text Generation WebUI
```bash
# Clone and setup text-generation-webui
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
./start_linux.sh --api --listen

# Configure adapter
export OPENAI_BASE_URL="http://localhost:5000"
python -m openai_codegen_adapter.main
```

## 🧪 Testing Your Setup

### Test with curl
```bash
# Test health endpoint
curl http://localhost:8887/health

# Test models endpoint
curl http://localhost:8887/v1/models

# Test chat completion
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

# Configure client to use your adapter
client = openai.OpenAI(
    base_url="http://localhost:8887/v1",
    api_key="dummy"  # Not needed for local development
)

# Test chat completion
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## 🔧 Common Configurations

### Configuration 1: Multi-Provider Setup
```bash
# Use different providers for different endpoints
export OPENAI_BASE_URL="http://localhost:11434"      # Ollama for chat
export ANTHROPIC_BASE_URL="https://api.anthropic.com" # Official Anthropic
export GOOGLE_AI_STUDIO_BASE_URL="https://generativelanguage.googleapis.com"
```

### Configuration 2: Development vs Production
```bash
# Development
export OPENAI_BASE_URL="http://localhost:8080"
export LOG_LEVEL="debug"

# Production
export OPENAI_BASE_URL="https://api.openai.com"
export LOG_LEVEL="info"
```

### Configuration 3: Docker Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  codegen-adapter:
    build: .
    ports:
      - "8887:8887"
    environment:
      - OPENAI_BASE_URL=http://host.docker.internal:11434
      - CODEGEN_ORG_ID=${CODEGEN_ORG_ID}
      - CODEGEN_TOKEN=${CODEGEN_TOKEN}
```

## 🚨 Troubleshooting

### Issue: Connection Refused
```bash
# Check if your local server is running
curl http://localhost:11434/api/tags  # For Ollama
curl http://localhost:1234/v1/models  # For LM Studio

# Test connection with the CLI tool
python scripts/configure_providers.py --test-connection openai
```

### Issue: Model Not Found
```bash
# List available models
curl http://localhost:8887/v1/models

# For Ollama, pull the model first
ollama pull llama2
```

### Issue: Authentication Failed
```bash
# Check your API keys
python scripts/configure_providers.py --show-config

# For local development, authentication is usually not required
export OPENAI_API_KEY="dummy"
```

## 📚 Next Steps

1. **Read the full documentation**: [SERVICE_PROVIDER_CONFIGURATION.md](SERVICE_PROVIDER_CONFIGURATION.md)
2. **Explore all providers**: Use `--list` to see all supported providers
3. **Set up multiple providers**: Configure different providers for different use cases
4. **Monitor performance**: Use debug logging to optimize your setup

## 🤝 Need Help?

- Check the [troubleshooting section](SERVICE_PROVIDER_CONFIGURATION.md#troubleshooting)
- Use the configuration CLI tool for guided setup
- Test connections before deploying to production

