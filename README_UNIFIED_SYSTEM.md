# 🤖 Unified AI Provider Gateway System

A comprehensive, scalable load-balancing API gateway that intercepts OpenAI API calls and routes them intelligently across 14 different AI providers.

## 🎯 **SYSTEM OVERVIEW**

This system creates a **true OpenAI API interception layer** that:
- **Intercepts** all OpenAI API calls from any application
- **Routes** them intelligently across 14 AI providers  
- **Load balances** based on health, performance, or manual selection
- **Provides unified UI** to control everything from one dashboard

## 🏗️ **ARCHITECTURE**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Applications  │───▶│  API Gateway     │───▶│  AI Providers   │
│  (OpenAI API)   │    │  (Port 7999)     │    │  (Ports 8000+)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Load Balancer   │
                       │  Health Monitor  │
                       │  Service Manager │
                       └──────────────────┘
```

## 📋 **14 AI PROVIDERS INCLUDED**

### Original 12 Repositories:
1. **qwen-api** (Port 8000) - Qwen models
2. **qwenchat2api** (Port 8001) - Qwen chat API
3. **k2think2api3** (Port 8002) - K2-Think v3
4. **k2think2api2** (Port 8003) - K2-Think v2  
5. **k2Think2Api** (Port 8004) - K2-Think original
6. **grok2api** (Port 8005) - Grok-2 models
7. **OpenAI-Compatible-API-Proxy-for-Z** (Port 8006) - Z.ai proxy
8. **zai-python-sdk** (Port 8007) - Z.ai Python SDK
9. **z.ai2api_python** (Port 8008) - Z.ai Python API
10. **ZtoApi** (Port 8009) - Z.ai Go implementation
11. **Z.ai2api** (Port 8010) - Z.ai TypeScript
12. **ZtoApits** (Port 8011) - Z.ai TypeScript v2

### Additional Providers:
13. **TalkAI** (Port 8012) - TalkAI service
14. **Copilot Proxy** (Port 8013) - GitHub Copilot integration

## 🚀 **QUICK START**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Complete System
```bash
python scripts/start_unified_system.py
```

### 3. Access the System
- **API Gateway**: http://localhost:7999
- **Dashboard**: Open `frontend/enhanced_index.html` in browser
- **OpenAI API**: http://localhost:7999/v1/chat/completions

## 🎛️ **KEY FEATURES**

### ✅ **OpenAI API Compatibility**
- Drop-in replacement for OpenAI API
- Supports `/v1/chat/completions` and `/v1/completions`
- Compatible with all OpenAI client libraries

### ✅ **Intelligent Load Balancing**
- **Round Robin**: Distribute requests evenly
- **Least Connections**: Route to least busy provider
- **Response Time**: Route to fastest provider
- **Health-Based**: Route to healthiest providers
- **Model-Specific**: Route based on model capabilities

### ✅ **Real-Time Management**
- Start/stop individual providers
- Health monitoring and auto-restart
- Live performance metrics
- Interactive web dashboard

### ✅ **Provider Testing**
- Comprehensive test suite for all providers
- Individual provider testing
- Health check validation
- Response format verification

## 📡 **API ENDPOINTS**

### Core OpenAI Endpoints
```bash
# Chat completions (auto-routed)
POST /v1/chat/completions

# Chat completions (specific provider)
POST /v1/chat/completions?provider=qwen-api

# List available models
GET /v1/models

# Test endpoint
POST /v1/test
```

### Management Endpoints
```bash
# Provider management
POST /providers/{name}/start
POST /providers/{name}/stop
POST /providers/{name}/restart
POST /providers/start-all
POST /providers/stop-all

# System information
GET /providers
GET /health
GET /config
```

## 💻 **USAGE EXAMPLES**

### Using with curl
```bash
# Basic chat completion
curl -X POST http://localhost:7999/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Use specific provider
curl -X POST 'http://localhost:7999/v1/chat/completions?provider=qwen-api' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Using with OpenAI Python Client
```python
import openai

# Point to your gateway instead of OpenAI
openai.api_base = "http://localhost:7999/v1"
openai.api_key = "dummy"  # Not needed for local gateway

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## 🧪 **TESTING**

### Run Comprehensive Tests
```bash
python tests/test_all_providers.py
```

### Test Individual Provider
```bash
curl -X POST http://localhost:7999/v1/test \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Test message",
    "provider": "qwen-api",
    "model": "qwen-turbo"
  }'
```

## 🎨 **WEB DASHBOARD**

The enhanced dashboard provides:
- **Real-time provider status**
- **Interactive chat testing**
- **Provider management controls**
- **System statistics**
- **Load balancing configuration**

Access at: `frontend/enhanced_index.html`

## 🔧 **SYSTEM COMPONENTS**

### 1. Service Registry (`backend/registry/`)
- Manages all 14 provider services
- Port allocation (8000-8013)
- Health monitoring
- Service discovery

### 2. Service Manager (`backend/services/`)
- Starts/stops provider services
- Dependency installation
- Process management
- Health monitoring

### 3. API Gateway (`backend/gateway/`)
- OpenAI API interception
- Request routing
- Response formatting
- CORS handling

### 4. Load Balancer (`backend/routing/`)
- Multiple balancing strategies
- Provider selection logic
- Performance tracking
- Failover handling

### 5. Test Suite (`tests/`)
- Comprehensive provider testing
- Health check validation
- Response format verification
- Performance benchmarking

## 📊 **MONITORING & METRICS**

The system provides comprehensive monitoring:
- **Provider Health**: Real-time status of all 14 providers
- **Response Times**: Average response time per provider
- **Error Rates**: Error count and failure tracking
- **Request Distribution**: Load balancing statistics
- **Uptime Tracking**: Service availability metrics

## 🔄 **LOAD BALANCING STRATEGIES**

1. **Round Robin**: Cycles through providers sequentially
2. **Least Connections**: Routes to provider with fewest active requests
3. **Response Time**: Routes to fastest responding provider
4. **Random**: Randomly selects from healthy providers
5. **Weighted Round Robin**: Uses provider capabilities as weights
6. **Health-Based**: Considers error rates and uptime
7. **Model-Specific**: Routes based on model specialization

## 🛠️ **DEVELOPMENT**

### Project Structure
```
├── apis/                    # 14 cloned AI provider repositories
├── backend/
│   ├── gateway/            # API Gateway
│   ├── registry/           # Service Registry
│   ├── routing/            # Load Balancer
│   └── services/           # Service Manager
├── frontend/               # Web Dashboard
├── scripts/                # Startup Scripts
├── tests/                  # Test Suite
└── config/                 # Configuration Files
```

### Adding New Providers
1. Clone repository to `apis/` folder
2. Add service configuration to `service_registry.py`
3. Ensure OpenAI-compatible endpoints
4. Test with the test suite

## 🚨 **TROUBLESHOOTING**

### Common Issues

**Providers not starting:**
- Check port availability (8000-8013)
- Verify dependencies are installed
- Check provider-specific requirements

**API Gateway not responding:**
- Ensure port 7999 is available
- Check if providers are healthy
- Verify load balancer configuration

**Dashboard not loading:**
- Serve `frontend/enhanced_index.html` with a web server
- Check browser console for errors
- Verify API Gateway is running

### Logs and Debugging
- System logs: Console output from startup script
- Provider logs: Individual service stdout/stderr
- Health checks: `/health` endpoint for each service

## 🎯 **PRODUCTION DEPLOYMENT**

For production deployment:
1. Use proper process manager (systemd, supervisor)
2. Configure reverse proxy (nginx, traefik)
3. Set up monitoring and alerting
4. Use environment variables for configuration
5. Implement proper logging and log rotation

## 📝 **LICENSE**

This project integrates multiple open-source AI provider implementations. Please check individual provider licenses in their respective `apis/` subdirectories.

## 🤝 **CONTRIBUTING**

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 **SUPPORT**

For issues and questions:
- Check the troubleshooting section
- Review provider-specific documentation
- Open an issue with detailed error information

---

**🚀 Ready to unify your AI providers? Start the system and experience the power of intelligent load balancing!**
