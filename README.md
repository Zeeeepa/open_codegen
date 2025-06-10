# OpenAI Codegen Adapter

An adapter that provides OpenAI-compatible API endpoints for Codegen, enabling seamless integration with existing OpenAI client libraries and tools.

## 🌟 Features

- **Full OpenAI API Compatibility**: Drop-in replacement for OpenAI API
- **Enhanced Anthropic Support**: Complete Claude API compatibility with all features
- **Google Vertex AI Integration**: Full multimodal support for Gemini models
- **Multiple Service Providers**: Support for 10+ AI service providers
- **Local Development Support**: Works with Ollama, LM Studio, vLLM, and more
- **Comprehensive Configuration**: Easy setup with environment variables and CLI tools
- **Real Codegen Integration**: Powered by actual Codegen capabilities, not placeholders

## 🚀 Quick Start

### Option 1: Use Official Cloud Providers
```bash
# Set up environment
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="sk-your-codegen-token"
export OPENAI_API_KEY="sk-your-openai-key"

# Start the adapter
python -m openai_codegen_adapter.main
```

### Option 2: Use Local Development (Free)
```bash
# Start Ollama (or any local AI server)
ollama serve
ollama pull llama2

# Configure adapter to use local server
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="sk-your-codegen-token"
export OPENAI_BASE_URL="http://localhost:11434"

# Start the adapter
python -m openai_codegen_adapter.main
```

## 🌐 Supported Service Providers

### Official Cloud Providers
- **OpenAI** - `https://api.openai.com`
- **Anthropic Claude** - `https://api.anthropic.com`
- **Google Vertex AI** - `https://{location}-aiplatform.googleapis.com`
- **Google AI Studio** - `https://generativelanguage.googleapis.com`
- **Azure OpenAI** - `https://{resource}.openai.azure.com`
- **Cohere** - `https://api.cohere.ai`
- **Hugging Face** - `https://api-inference.huggingface.co`
- **Mistral AI** - `https://api.mistral.ai`
- **Together AI** - `https://api.together.xyz`
- **Replicate** - `https://api.replicate.com`

### Local Development Providers
- **Ollama** - `http://localhost:11434`
- **LM Studio** - `http://localhost:1234`
- **Text Generation WebUI** - `http://localhost:5000`
- **vLLM** - `http://localhost:8000`
- **LocalAI** - `http://localhost:8080`

## 🔧 Configuration

### Using the Configuration CLI
```bash
# List all available providers
python scripts/configure_providers.py --list

# Configure a provider
python scripts/configure_providers.py --provider openai --url http://localhost:11434

# Generate .env template
python scripts/configure_providers.py --generate-env

# Test connection
python scripts/configure_providers.py --test-connection openai
```

### Manual Configuration
Create a `.env` file:
```env
# Codegen Configuration
CODEGEN_ORG_ID=your_org_id
CODEGEN_TOKEN=sk-your-codegen-token

# Service Provider URLs (override defaults)
OPENAI_BASE_URL=http://localhost:11434
ANTHROPIC_BASE_URL=https://api.anthropic.com

# API Keys (for cloud providers)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Get up and running in minutes
- **[Service Provider Configuration](docs/SERVICE_PROVIDER_CONFIGURATION.md)** - Complete configuration guide

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

## 🎯 API Compatibility

| Service | Endpoint | Official SDK Compatible | Status |
|---------|----------|------------------------|---------|
| **OpenAI** | `/v1/chat/completions` | ✅ OpenAI Python SDK | 🟢 Full Compatibility |
| **Anthropic** | `/v1/messages` | ✅ Anthropic Python SDK | 🟢 Full Compatibility |
| **Google** | `/v1/models/{model}:generateContent` | ✅ Google Cloud AI SDK | 🟢 Full Compatibility |
| **Embeddings** | `/v1/embeddings` | ✅ OpenAI Python SDK | 🟢 Enhanced with Codegen |
| **Audio** | `/v1/audio/*` | ✅ OpenAI Python SDK | 🟢 Enhanced with Codegen |
| **Images** | `/v1/images/generations` | ✅ OpenAI Python SDK | 🟢 Enhanced with Codegen |

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/open_codegen.git
cd open_codegen

# Install dependencies
pip install -r requirements.txt

# Set up configuration
python scripts/configure_providers.py --generate-env
cp .env.template .env
# Edit .env with your values

# Start the adapter
python -m openai_codegen_adapter.main
```

## 🐳 Docker Support

```yaml
# docker-compose.yml
version: '3.8'
services:
  codegen-adapter:
    build: .
    ports:
      - "8887:8887"
    environment:
      - OPENAI_BASE_URL=http://localhost:11434
      - CODEGEN_ORG_ID=${CODEGEN_ORG_ID}
      - CODEGEN_TOKEN=${CODEGEN_TOKEN}
```
