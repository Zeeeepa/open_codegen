# 🚀 Universal AI Endpoint Manager

**Trading bot-style AI endpoint management integrated into open_codegen**

Transform any web chat interface or REST API into a standardized, manageable AI endpoint with persistent sessions, health monitoring, and performance tracking.

## 🎯 Overview

The Universal AI Endpoint Manager enhances the existing `open_codegen` project by adding sophisticated endpoint management capabilities similar to cryptocurrency trading bots. It can convert ANY AI interface into a standardized API endpoint that can be controlled, monitored, and scaled individually.

### Key Features

- 🤖 **Universal Conversion**: Convert web chat interfaces and REST APIs into standardized endpoints
- 📊 **Trading Bot-Style Management**: Start/stop endpoints like trading positions with real-time metrics
- 🔄 **Persistent Sessions**: Maintain conversation continuity across restarts and scaling
- 🎯 **AI-Assisted Discovery**: Automatically detect and configure new AI services
- 📈 **Performance Monitoring**: Track success rates, response times, and costs
- 🌐 **Scalable Architecture**: Handle hundreds of concurrent endpoints

## 🏗️ Architecture

```
┌─ Web Chat Interfaces ─┐
├─ REST APIs ───────────┤  →  Universal Converter  →  Standard API Response
├─ Custom Interfaces ───┤
└─ Any AI Service ──────┘
```

### Core Components

1. **Universal Endpoint Manager** - Main orchestration system
2. **Endpoint Registry** - Persistent configuration storage
3. **Session Manager** - Conversation continuity management
4. **Health Monitor** - Real-time endpoint monitoring
5. **Provider Factory** - Dynamic provider creation
6. **Web UI Dashboard** - Trading bot-style interface

## 🚀 Quick Start

### 1. Installation

The Universal AI Endpoint Manager is integrated into the existing `open_codegen` project:

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/open_codegen.git
cd open_codegen

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Enhanced Server

```bash
# Start the Universal AI Endpoint Manager server
python -m backend.adapter.universal_server
```

### 3. Access the Dashboard

Open your browser to `http://localhost:8001` to access the trading bot-style dashboard.

## 📊 Trading Bot-Style Interface

The system provides a familiar trading bot interface for managing AI endpoints:

### Dashboard Features

- **Portfolio View**: All endpoints with status, health, and performance metrics
- **Individual Controls**: Start/stop endpoints like trading positions
- **Real-time Metrics**: Success rates, response times, request counts
- **Performance Analytics**: Cost tracking and optimization insights

### Endpoint Types Supported

| Type | Description | Example |
|------|-------------|---------|
| `WEB_CHAT` | Web chat interfaces | DeepSeek, ChatGPT web |
| `REST_API` | Standard REST APIs | OpenAI, Anthropic |
| `CODEGEN_API` | Codegen API integration | Built-in support |
| `ZAI_WEB` | Z.ai web chat interface | Z.ai integration |
| `CUSTOM_WEB` | Any custom web interface | User-defined |

## 🔧 API Usage

### Add a New Endpoint

```python
import requests

# Add OpenAI API endpoint
endpoint_data = {
    "name": "openai_gpt4",
    "display_name": "OpenAI GPT-4",
    "endpoint_type": "openai_api",
    "url": "https://api.openai.com/v1",
    "model_name": "gpt-4",
    "credentials": {
        "api_key": "your-api-key"
    },
    "priority": 10
}

response = requests.post("http://localhost:8001/endpoints", json=endpoint_data)
print(response.json())
```

### Start an Endpoint

```python
# Start the endpoint (like opening a trading position)
endpoint_id = "your-endpoint-id"
response = requests.post(f"http://localhost:8001/endpoints/{endpoint_id}/start")
print(response.json())
```

### Send a Chat Request

```python
# Send a request to the endpoint
chat_data = {
    "prompt": "Hello, how can you help me today?",
    "temperature": 0.7
}

response = requests.post(
    f"http://localhost:8001/endpoints/{endpoint_id}/chat", 
    json=chat_data
)
print(response.json())
```

### Monitor System Metrics

```python
# Get trading bot-style system metrics
response = requests.get("http://localhost:8001/system/metrics")
metrics = response.json()

print(f"Running Endpoints: {metrics['running_endpoints']}")
print(f"Success Rate: {metrics['success_rate']:.1f}%")
print(f"Requests/sec: {metrics['requests_per_second']:.2f}")
```

## 🌐 Web Chat Interface Integration

### Supported Web Chat Interfaces

- **Z.ai Web Chat**: Direct integration with Z.ai
- **DeepSeek Web Chat**: Browser automation support
- **Custom Web Interfaces**: AI-assisted configuration

### Example: Adding Z.ai Web Chat

```python
zai_config = {
    "name": "zai_web_1",
    "display_name": "Z.ai Web Chat #1",
    "endpoint_type": "zai_web",
    "url": "https://z.ai/chat",
    "model_name": "z-ai-model",
    "credentials": {
        "username": "your_username",
        "password": "your_password"
    },
    "browser_config": {
        "headless": True,
        "anti_detection": True,
        "fingerprint_rotation": True
    },
    "persistent_session": True
}
```

## 📈 Performance Monitoring

### Endpoint Metrics

Each endpoint tracks comprehensive metrics similar to trading bot performance:

- **Request Statistics**: Total, successful, failed requests
- **Performance Metrics**: Average response time, success rate
- **Cost Tracking**: Token usage and estimated costs
- **Health Status**: Real-time health monitoring
- **Uptime Tracking**: Continuous availability monitoring

### System-Wide Analytics

- **Portfolio Performance**: Overall system success rates
- **Resource Utilization**: Memory and CPU usage
- **Throughput Metrics**: Requests per second across all endpoints
- **Error Analysis**: Failure patterns and recovery metrics

## 🔄 Session Management

### Persistent Conversations

The system maintains conversation continuity across:

- **Server Restarts**: Sessions persist through system downtime
- **Endpoint Scaling**: Conversations continue during scaling operations
- **Browser Automation**: Web chat sessions maintain state
- **Cookie Management**: Automatic cookie and fingerprint handling

### Session Features

- **Automatic Cleanup**: Expired sessions are automatically removed
- **State Persistence**: Browser state, cookies, and headers saved
- **Conversation Tracking**: Multi-turn conversation support
- **Session Analytics**: Usage statistics and performance tracking

## 🛠️ Configuration

### Environment Variables

```bash
# Server configuration
ENDPOINT_MANAGER_PORT=8001
ENDPOINT_MANAGER_HOST=0.0.0.0

# Monitoring settings
HEALTH_CHECK_INTERVAL=60
PERFORMANCE_MONITORING=true
AUTO_RESTART_FAILED_ENDPOINTS=true

# Session management
SESSION_TIMEOUT=3600
SESSION_CLEANUP_INTERVAL=300
```

### Configuration Files

- `config/endpoints.json` - Endpoint configurations
- `config/sessions.json` - Active session states
- `config/settings.json` - System settings

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_universal_manager.py
```

Expected output:
```
🚀 Starting Universal AI Endpoint Manager Tests...
🧪 Testing Endpoint Models...
✅ Endpoint Models test passed!
🧪 Testing Standard Response...
✅ Standard Response test passed!
🧪 Testing Trading Bot-Style Operations...
✅ Trading Bot-Style Operations test passed!
🧪 Testing Web Chat Configuration...
✅ Web Chat Configuration test passed!
🎉 All tests passed! Universal AI Endpoint Manager is working correctly.
```

## 🔗 Integration with Existing Projects

### Z.ai Integration

Leverages existing Z.ai projects:
- [ZtoApi](https://github.com/Zeeeepa/ZtoApi) - OpenAI-compatible API proxy
- [web-ui-python-sdk](https://github.com/Zeeeepa/web-ui-python-sdk) - Python SDK
- [ZtoApits](https://github.com/Zeeeepa/ZtoApits) - TypeScript implementation

### Browser Automation

Integrates with sandbox environments:
- [tinygen](https://github.com/lhendre/tinygen) - Lightweight sandbox
- [grainchain](https://github.com/codegen-sh/grainchain) - Langchain for sandboxes

## 🚀 Deployment

### Production Deployment

```bash
# Using Docker
docker build -t universal-ai-manager .
docker run -p 8001:8001 universal-ai-manager

# Using systemd
sudo systemctl enable universal-ai-manager
sudo systemctl start universal-ai-manager
```

### Scaling

The system supports horizontal scaling:

- **Load Balancing**: Distribute requests across multiple instances
- **Auto-scaling**: Automatic instance management based on demand
- **Health Monitoring**: Automatic failover and recovery
- **Session Replication**: Shared session state across instances

## 📚 Advanced Features

### AI-Assisted Endpoint Discovery

```python
# Automatically discover and configure new endpoints
discovered = await ai_scanner.discover_endpoints(
    url="https://new-ai-service.com/chat",
    analyze_interface=True,
    generate_config=True
)

# Deploy discovered endpoint
await endpoint_manager.deploy(discovered.config)
```

### Custom Provider Development

```python
class CustomWebChatProvider(BaseProvider):
    async def send_request(self, prompt: str, **kwargs) -> StandardResponse:
        # Custom implementation for specific web chat interface
        # Handle authentication, session management, response parsing
        pass
```

### Webhook Integration

```python
# Receive notifications for endpoint events
@app.post("/webhooks/endpoint-status")
async def endpoint_status_webhook(event: EndpointEvent):
    if event.status == "failed":
        await auto_restart_endpoint(event.endpoint_id)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [open_codegen](https://github.com/Zeeeepa/open_codegen) project
- Inspired by cryptocurrency trading bot architectures
- Integrates with multiple AI service providers and web interfaces

---

**Ready to transform your AI workflow with trading bot-style endpoint management? Get started today!** 🚀
