# OpenAI Codegen Adapter

A FastAPI-based adapter that provides OpenAI API compatibility for the Codegen SDK, with full support for Anthropic Claude and Google Vertex AI APIs.

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

## 🚀 Features

### Full OpenAI API Compatibility
- ✅ **Chat Completions** - `/v1/chat/completions`
- ✅ **Text Completions** - `/v1/completions`
- ✅ **Models List** - `/v1/models`
- ✅ **Embeddings** - `/v1/embeddings`
- ✅ **Audio Transcription** - `/v1/audio/transcriptions`
- ✅ **Audio Translation** - `/v1/audio/translations`
- ✅ **Image Generation** - `/v1/images/generations`

### Anthropic Claude API Support
- ✅ **Messages API** - `/v1/messages` (Official Anthropic endpoint)
- ✅ **Legacy Completions** - `/v1/anthropic/completions`
- ✅ **Streaming Support** - Server-Sent Events (SSE)
- ✅ **All Claude Models** - claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-3-5-sonnet

### Google Vertex AI Support
- ✅ **Official Vertex AI** - `/v1/models/{model}:generateContent`
- ✅ **Streaming Vertex AI** - `/v1/models/{model}:streamGenerateContent`
- ✅ **Legacy Gemini** - `/v1/gemini/completions`, `/v1/gemini/generateContent`
- ✅ **All Gemini Models** - gemini-1.5-pro, gemini-1.5-flash, gemini-pro, gemini-2.0-flash-exp

### Additional Features
- 🔄 **Streaming Support** - Real-time response streaming for all services
- 🛡️ **Error Handling** - OpenAI-compatible error responses
- 📊 **Usage Tracking** - Token usage estimation and reporting
- 🎛️ **Web UI** - Built-in control panel for service management
- 🔍 **Health Monitoring** - Health check and status endpoints

## 📋 API Endpoints

### OpenAI Compatible Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/v1/models` | GET | List available models | ✅ Working |
| `/v1/chat/completions` | POST | Create chat completion | ✅ Working |
| `/v1/completions` | POST | Create text completion | ✅ Working |
| `/v1/embeddings` | POST | Create embeddings | ✅ Working |
| `/v1/audio/transcriptions` | POST | Transcribe audio | ✅ Working |
| `/v1/audio/translations` | POST | Translate audio | ✅ Working |
| `/v1/images/generations` | POST | Generate images | ✅ Working |

### Anthropic Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/v1/messages` | POST | Official Anthropic Messages API | ✅ Working |
| `/v1/anthropic/completions` | POST | Legacy Anthropic completions | ✅ Working |

### Google Vertex AI Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/v1/models/{model}:generateContent` | POST | Official Vertex AI endpoint | ✅ Working |
| `/v1/models/{model}:streamGenerateContent` | POST | Official Vertex AI streaming | ✅ Working |
| `/v1/gemini/completions` | POST | Legacy Gemini completions | ✅ Working |
| `/v1/gemini/generateContent` | POST | Legacy Gemini generate content | ✅ Working |

### Utility Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/health` | GET | Health check | ✅ Working |
| `/api/status` | GET | Service status | ✅ Working |
| `/api/toggle` | POST | Toggle service on/off | ✅ Working |
| `/` | GET | Web UI | ✅ Working |

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Codegen SDK access
- API keys for desired services

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Zeeeepa/open_codegen.git
   cd open_codegen
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   export CODEGEN_API_KEY="your_codegen_api_key"
   export CODEGEN_ORG_ID="your_org_id"
   ```

4. **Start the server**
   ```bash
   python -m openai_codegen_adapter.main
   ```

5. **Access the API**
   - API Base URL: `http://localhost:8887`
   - Web UI: `http://localhost:8887`
   - Health Check: `http://localhost:8887/health`

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

## 📖 Usage Examples

### OpenAI Chat Completions
```bash
curl -X POST http://localhost:8887/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Anthropic Messages
```bash
curl -X POST http://localhost:8887/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "Hello Claude!"}],
    "max_tokens": 100
  }'
```

### Google Vertex AI
```bash
curl -X POST http://localhost:8887/v1/models/gemini-1.5-pro:generateContent \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Hello Gemini!"}]}],
    "generationConfig": {"maxOutputTokens": 100}
  }'
```

### OpenAI Embeddings
```bash
curl -X POST http://localhost:8887/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "Text to embed"
  }'
```

## 🧪 Comprehensive Testing

Run the comprehensive test suite to validate all endpoints:

```bash
python test_comprehensive_api.py
```

This will test:
- All OpenAI API endpoints
- All Anthropic API endpoints
- All Google Vertex AI endpoints
- Error handling and response formats
- Streaming functionality

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CODEGEN_API_KEY` | Your Codegen API key | ✅ Yes |
| `CODEGEN_ORG_ID` | Your Codegen organization ID | ✅ Yes |
| `SERVER_HOST` | Server host (default: 0.0.0.0) | ❌ No |
| `SERVER_PORT` | Server port (default: 8887) | ❌ No |

### Supported Models

#### OpenAI Models
- `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- `text-embedding-ada-002`
- `whisper-1`
- `dall-e-3`

#### Anthropic Models
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20241022`

#### Google Models
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-pro`
- `gemini-2.0-flash-exp`

## 🛠️ Development

### Project Structure
```
openai_codegen_adapter/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── server.py                # FastAPI server and endpoints
├── models.py                # Pydantic models for requests/responses
├── config.py                # Configuration management
├── codegen_client.py        # Codegen SDK client wrapper
├── streaming.py             # OpenAI streaming support
├── response_transformer.py  # Response format transformations
├── request_transformer.py   # Request format transformations
├── anthropic_streaming.py   # Anthropic streaming support
├── anthropic_transformer.py # Anthropic format transformations
├── gemini_streaming.py      # Gemini streaming support
└── gemini_transformer.py    # Gemini format transformations
```

### Adding New Endpoints

1. **Define models** in `models.py`
2. **Add endpoint** in `server.py`
3. **Implement transformers** if needed
4. **Add tests** in `test_comprehensive_api.py`
5. **Update documentation**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/open_codegen/issues)
- **Documentation**: This README and inline code documentation
- **Testing**: Use `test_comprehensive_api.py` for validation

## 🎯 Roadmap

- [ ] Enhanced streaming performance
- [ ] Additional model support
- [ ] Rate limiting and quotas
- [ ] Authentication middleware
- [ ] Metrics and monitoring
- [ ] Docker containerization

---

**Made with ❤️ for the AI development community**

