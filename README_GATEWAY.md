# Universal AI API Gateway

🚀 **ONE COMMAND STARTUP** - Intercepts OpenAI/Gemini/Anthropic API calls and routes through 9 providers

## 🎯 What This System Does

```
ANY API Call → Universal Parser → WebChat Interface → 9 Providers → WebChat Response → Original API Format
     ↓              ↓                    ↓                ↓              ↓                    ↓
OpenAI API    → Format Detector → Chat Interface → z.ai, k2, grok, qwen → Chat Response → OpenAI JSON
Gemini API    → Bidirectional   → Chat Interface → copilot, ChatGPT, Bing → Chat Response → Gemini JSON  
Claude API    → Converter       → Chat Interface → codegen, talkai        → Chat Response → Claude JSON
```

## 🔥 Key Features

✅ **Universal API Compatibility** - OpenAI, Gemini, Anthropic APIs all supported  
✅ **WebChat Interface Conversion** - All APIs become chat conversations  
✅ **9 Provider Integration** - z.ai, k2, grok, qwen, copilot, ChatGPT, Bing, codegen, talkai  
✅ **Bidirectional Format Conversion** - Perfect API format preservation  
✅ **Web Management Interface** - Turn on/off, priorities, testing, monitoring  
✅ **Chat Testing Interface** - Real-time provider testing via chat  
✅ **One Command Startup** - `python main.py` and everything works!

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Gateway
```bash
python main.py
```

### 3. Access Interfaces
- **🎮 Web Interface**: http://localhost:8000
- **🔗 API Gateway**: http://localhost:8000/v1/
- **📊 Management**: http://localhost:8000/admin
- **💬 Chat Interface**: http://localhost:8000/chat

## 🌐 API Endpoints

### Universal Endpoints (Auto-Detection)
- `POST /v1/chat/completions` - OpenAI compatible
- `POST /v1/completions` - OpenAI compatible
- `POST /v1/messages` - Anthropic compatible
- `POST /v1/models/{model}:generateContent` - Gemini compatible

### Management API
- `GET /api/health` - System health check
- `GET /api/providers` - List all providers
- `POST /api/providers/{name}/toggle` - Enable/disable provider
- `POST /api/providers/{name}/test` - Test provider
- `POST /api/chat` - Chat interface endpoint

## 🔧 Provider Configuration

The system supports 9 providers with different integration patterns:

### 1. **Z.AI Provider** (Priority 1)
- **Integration**: SDK-based with ZAIClient
- **Features**: Auto-auth, guest tokens, streaming
- **Status**: Stub implementation (ready for SDK integration)

### 2. **K2Think Provider** (Priority 2)  
- **Integration**: OpenAI-compatible proxy
- **Features**: FastAPI-based, UTF-8 handling
- **Status**: Stub implementation (ready for API integration)

### 3. **Qwen Provider** (Priority 3)
- **Integration**: OpenAI-compatible with compressed tokens
- **Features**: Vision, multimodal, web search, thinking mode
- **Status**: Stub implementation (ready for API integration)

### 4. **Grok Provider** (Priority 4)
- **Integration**: Playwright-based browser automation
- **Features**: x-statsig-id capture, streaming
- **Status**: Stub implementation (ready for browser automation)

### 5. **ChatGPT Provider** (Priority 5)
- **Integration**: chat2api service integration
- **Features**: Token refresh, conversation management
- **Status**: Stub implementation (ready for service integration)

### 6. **Bing Provider** (Priority 6)
- **Integration**: EdgeGPT with preprocessing
- **Features**: Reference handling, async support
- **Status**: Stub implementation (ready for EdgeGPT integration)

### 7. **Codegen Provider** (Priority 7)
- **Integration**: Existing REST API implementation
- **Features**: Model selection, streaming, webhook support
- **Status**: ✅ **IMPLEMENTED** - Uses existing EnhancedCodegenClient

### 8. **Copilot Provider** (Priority 8)
- **Integration**: GitHub Copilot Chat API
- **Features**: Direct GitHub API calls
- **Status**: Stub implementation (ready for GitHub API integration)

### 9. **TalkAI Provider** (Priority 9)
- **Integration**: Custom implementation needed
- **Status**: Stub implementation (needs custom development)

## 🎮 Web Interface Features

### Main Dashboard
- **System Status**: Real-time health monitoring
- **Provider Management**: Enable/disable providers with toggle switches
- **Priority Settings**: Adjust provider priorities
- **Quick Actions**: Access chat, admin, and API docs

### Chat Interface
- **Provider Selection**: Choose specific provider or auto load-balance
- **Format Selection**: Send as OpenAI/Anthropic/Gemini call
- **Real-time Testing**: Test providers with actual messages
- **Response Display**: See which provider responded

### Admin Panel
- **Provider Configuration**: Manage credentials and settings
- **Security Settings**: API keys, rate limiting, access controls
- **System Monitoring**: Logs, metrics, performance data

## 🔄 Load Balancing

The system supports multiple load balancing strategies:

- **Priority**: Always use highest priority available provider
- **Round Robin**: Cycle through enabled providers
- **Performance**: Route based on response times (future)

## 📊 Monitoring & Health Checks

- **Real-time Status**: Provider health monitoring
- **Statistics Tracking**: Request counts, response times, success rates
- **Error Handling**: Graceful fallbacks and error reporting
- **Logging**: Comprehensive logging with structured format

## 🛠️ Development

### Project Structure
```
├── main.py                 # Entry point
├── gateway/               # Core gateway logic
│   ├── startup.py         # System initialization
│   └── api_gateway.py     # Main gateway class
├── providers/             # Provider implementations
│   ├── base_provider.py   # Base provider class
│   ├── zai_provider.py    # Z.AI integration
│   ├── codegen_provider.py # Codegen integration (implemented)
│   └── ...                # Other providers
├── web/                   # Web interface
│   ├── server.py          # FastAPI server
│   ├── routes.py          # API routes
│   └── templates/         # HTML templates
├── formats/               # Format detection & conversion
├── converters/            # API format converters
├── balancing/             # Load balancing logic
├── config/                # Configuration management
└── utils/                 # Utilities and logging
```

### Adding New Providers

1. Create provider class inheriting from `BaseProvider`
2. Implement required methods: `initialize()`, `process_request()`, `health_check()`
3. Add to `ProviderManager.provider_classes`
4. Update configuration in `config_manager.py`

### Environment Variables

```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Provider Credentials
ZAI_USERNAME=your_username
ZAI_PASSWORD=your_password
K2_USERNAME=your_username
K2_PASSWORD=your_password
QWEN_USERNAME=your_username
QWEN_PASSWORD=your_password
GROK_USERNAME=your_username
GROK_PASSWORD=your_password

# Codegen (Already Configured)
CODEGEN_API_TOKEN=your_token
CODEGEN_ORG_ID=323
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run

# Optional: Cloudflare for FlareProx
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
```

## 🎯 Next Steps

1. **Provider Implementation**: Replace stub implementations with actual integrations
2. **Authentication**: Add API key authentication and user management
3. **Rate Limiting**: Implement per-user and per-provider rate limiting
4. **Caching**: Add response caching for improved performance
5. **Metrics**: Add Prometheus metrics and monitoring
6. **FlareProx Integration**: Add Cloudflare Workers for infinite scaling
7. **Streaming**: Implement full streaming support for all providers
8. **Admin Interface**: Complete the admin panel with full configuration

## 📝 License

This project is part of the Universal AI API Gateway system.

---

**🚀 Ready to intercept and route ALL AI API calls through one unified gateway!**
