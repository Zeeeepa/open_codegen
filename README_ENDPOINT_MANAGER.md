# 🤖 Universal AI Endpoint Management System

A comprehensive trading bot-style system for managing AI endpoints that can convert ANY web chat interface or REST API into standardized API endpoints. Built with the architecture and flow logic inspired by cryptocurrency trading bots, but designed for AI endpoint orchestration.

## 🎯 Core Features

### 🔄 Universal Conversion Engine
- **Web Chat Interfaces** → Headless Browser → Standardized API Response
- **REST APIs** → Request Transform → Standardized API Response  
- **Custom Interfaces** → AI Analysis → Standardized API Response

### 📈 Trading Bot-Style Management
- **Portfolio View**: Manage endpoints like trading positions
- **ON/OFF Control**: Start/stop endpoints individually
- **Performance Metrics**: Success rates, response times, costs
- **Health Monitoring**: Real-time status and auto-recovery
- **Load Balancing**: Distribute requests across best endpoints

### 🤖 AI-Powered Discovery
- **Interface Analysis**: Multimodal AI analyzes web pages
- **Auto-Configuration**: Generate working configs from URLs
- **Pattern Recognition**: Learn common chat interface patterns
- **Continuous Learning**: Improve detection accuracy over time

## 🏗️ Architecture Overview

```
┌─ DeepSeek Web Chat ─┐
├─ OpenAI API ────────┤
├─ Gemini API ────────┤ → Universal Converter → Standard API Response
├─ DeepInfra API ─────┤
├─ Custom Web Chat ───┤
└─ Any REST API ──────┘
```

### Standardized Response Format
```json
{
  "id": "conv-12345",
  "provider": "deepseek-web",
  "model": "deepseek-chat",
  "response": {
    "content": "AI response text",
    "type": "text",
    "metadata": {}
  },
  "usage": {
    "input_tokens": 50,
    "output_tokens": 100,
    "cost": 0.001
  },
  "session": {
    "id": "sess-67890",
    "persistent": true
  }
}
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd open_codegen

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configuration

Create a `.env` file:

```env
# Database
DATABASE_URL=sqlite:///endpoint_manager.db
DB_ECHO=false

# Default Providers
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run
CODEGEN_TOKEN=your_codegen_token

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Logging
LOG_LEVEL=INFO
```

### 3. Run the System

```bash
# Start the server
python -m backend.main

# Or using uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Interface

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API Usage

### List Endpoints (Trading Portfolio View)
```bash
curl http://localhost:8000/api/endpoints/
```

### Create New Endpoint
```bash
curl -X POST http://localhost:8000/api/endpoints/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeepSeek Web Chat",
    "provider_type": "web_chat",
    "base_url": "https://chat.deepseek.com",
    "login_url": "https://chat.deepseek.com/login",
    "username": "your_email@example.com",
    "password": "your_password",
    "browser_config": {
      "headless": true,
      "anti_detection": true
    }
  }'
```

### Start/Stop Endpoints (Trading Positions)
```bash
# Start endpoint
curl -X POST http://localhost:8000/api/endpoints/deepseek-web-chat/start

# Stop endpoint  
curl -X POST http://localhost:8000/api/endpoints/deepseek-web-chat/stop
```

### OpenAI-Compatible Chat API
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### Test Endpoint
```bash
curl -X POST http://localhost:8000/api/endpoints/deepseek-web-chat/test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is artificial intelligence?",
    "model": "gpt-4"
  }'
```

## 🔧 Supported Provider Types

### 1. REST API (`rest_api`)
- OpenAI API
- Codegen API  
- Gemini API
- DeepInfra API
- DeepSeek API
- Any OpenAI-compatible API

### 2. Web Chat (`web_chat`)
- Z.ai Web Interface
- DeepSeek Web Chat
- Custom web chat interfaces
- Any browser-based AI chat

### 3. API Token (`api_token`)
- Token-based authentication
- API key management
- Custom authentication flows

## 🎮 Management Interface

### Trading Dashboard Features
- **Portfolio View**: All endpoints with status, health, performance
- **Discovery Scanner**: Find new AI services automatically  
- **Testing Terminal**: Live chat interface for testing endpoints
- **Performance Analytics**: Request rates, success rates, costs
- **Instance Controls**: Start/stop/configure individual servers

### One-Click Endpoint Addition
```python
# Natural language endpoint creation
add_endpoint(
    description="Add DeepSeek web chat with my credentials",
    url="https://chat.deepseek.com",
    auto_configure=True
)
```

## 🛠️ Advanced Configuration

### Browser Automation Settings
```json
{
  "browser_config": {
    "headless": true,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "viewport": {"width": 1920, "height": 1080},
    "timeout": 30000,
    "anti_detection": true,
    "proxy": {
      "server": "http://proxy:8080",
      "username": "user",
      "password": "pass"
    }
  }
}
```

### Model Mapping
```json
{
  "model_mapping": {
    "gpt-4": "deepseek-chat",
    "gpt-3.5-turbo": "deepseek-coder",
    "claude-3-opus": "deepseek-chat"
  }
}
```

### Rate Limiting & Performance
```json
{
  "max_requests_per_minute": 60,
  "max_concurrent_requests": 5,
  "timeout_seconds": 30,
  "retry_attempts": 3,
  "health_check_interval": 300
}
```

## 📊 Monitoring & Metrics

### Endpoint Metrics
- **Success Rate**: Percentage of successful requests
- **Response Time**: Average response time in milliseconds
- **Uptime**: Percentage of time endpoint was available
- **Cost Tracking**: Cost per request and total costs
- **Request Volume**: Total and recent request counts

### Health Monitoring
- **Automatic Health Checks**: Every 5 minutes
- **Auto-Recovery**: Restart failed endpoints
- **Alert System**: Notifications for endpoint failures
- **Performance Optimization**: Automatic load balancing

## 🔒 Security Features

### Browser Security
- **Anti-Detection**: Bypass bot detection systems
- **Fingerprinting**: Unique browser fingerprints per session
- **Session Persistence**: Maintain login states across restarts
- **Sandboxed Execution**: Isolated browser environments

### API Security
- **Token Management**: Secure API key storage
- **Rate Limiting**: Prevent abuse and overuse
- **Request Validation**: Input sanitization and validation
- **Audit Logging**: Complete request/response logging

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
EXPOSE 8000

CMD ["python", "-m", "backend.main"]
```

### Production Configuration
```env
# Production settings
DATABASE_URL=postgresql://user:pass@localhost/endpoint_manager
REDIS_URL=redis://localhost:6379
LOG_LEVEL=WARNING
RELOAD=false

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

## 🤝 Integration Examples

### With Existing Applications
```python
import requests

# Use as drop-in OpenAI replacement
response = requests.post("http://localhost:8000/v1/chat/completions", 
    json={
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
```

### With LangChain
```python
from langchain.llms import OpenAI

# Point to your endpoint manager
llm = OpenAI(
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="not-needed"
)
```

## 📈 Performance Optimization

### Load Balancing Strategies
- **Success Rate**: Route to highest success rate endpoint
- **Response Time**: Route to fastest responding endpoint  
- **Round Robin**: Distribute requests evenly
- **Weighted**: Route based on endpoint capacity

### Caching & Session Management
- **Response Caching**: Cache frequent responses
- **Session Persistence**: Maintain conversation context
- **Connection Pooling**: Reuse HTTP connections
- **Background Processing**: Async request handling

## 🐛 Troubleshooting

### Common Issues

1. **Browser Automation Fails**
   ```bash
   # Install browsers
   playwright install chromium
   
   # Check browser path
   playwright install --help
   ```

2. **Database Connection Issues**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Reset database
   rm endpoint_manager.db
   python -m backend.main
   ```

3. **Endpoint Not Responding**
   ```bash
   # Check endpoint health
   curl http://localhost:8000/api/endpoints/endpoint-name/health
   
   # Restart endpoint
   curl -X POST http://localhost:8000/api/endpoints/endpoint-name/stop
   curl -X POST http://localhost:8000/api/endpoints/endpoint-name/start
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DB_ECHO=true

# Run with reload
python -m backend.main
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by cryptocurrency trading bot architectures
- Built on FastAPI, SQLAlchemy, and Playwright
- Integrates with existing Codegen and Z.ai systems
- Supports the broader AI development ecosystem

---

**Ready to transform how you interact with AI services? Start managing your AI endpoints like a professional trader manages their portfolio!** 🚀
