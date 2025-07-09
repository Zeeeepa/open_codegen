# 🚀 Codegen AI Proxy

**Transparent API Gateway for OpenAI, Anthropic & Gemini → Codegen API**

A lightweight Docker container that intercepts AI API calls and routes them to Codegen API with automatic system message injection. **Zero code changes required** - just point your existing applications to the proxy!

## ✨ Features

- 🔄 **Drop-in Replacement**: No code changes required in existing applications
- 🐳 **Docker-Ready**: One-command deployment with docker-compose
- 🎯 **Zero Configuration**: Works out of the box with Web UI setup
- 🌐 **Multi-Provider Support**: OpenAI, Anthropic, and Gemini API compatibility
- 🎛️ **Interactive Web UI**: Beautiful settings dialog for credential management
- 🔍 **Credential Verification**: Real-time validation of Codegen credentials
- 🎨 **System Message Injection**: Automatic prompt enhancement
- 📊 **Monitoring**: Health checks and status endpoints
- 🪟 **Windows-Friendly**: PowerShell setup script included

## 🚀 Quick Start

### 1. Docker Deployment (Recommended)
```bash
# Clone the repository
git clone https://github.com/Zeeeepa/open_codegen.git
cd open_codegen

# Start the proxy (no credentials needed initially)
docker-compose up -d

# Access Web UI to configure credentials
open http://localhost:8000
```

### 2. Windows PowerShell Setup
```powershell
# Download and run setup script
.\setup-windows.ps1

# Or with credentials
.\setup-windows.ps1 -CodegenOrgId "323" -CodegenToken "sk-..."
```

```bash
# Set environment variables
export CODEGEN_ORG_ID="323"
export CODEGEN_TOKEN="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
export DEFAULT_SYSTEM_MESSAGE="You are a helpful AI assistant."

# Start with Docker
docker-compose up -d
```

## 🌐 Web UI Configuration

The proxy includes a **beautiful Web UI** for easy configuration:

### **Access the Interface**
- Open **http://localhost:8000** in your browser
- Click **"⚙️ Configure Codegen"** to open settings dialog

### **Configure Credentials**
1. **Organization ID**: Your Codegen organization ID (e.g., `323`)
2. **API Token**: Your Codegen API token (e.g., `sk-ce027fa7-...`)
3. **System Message**: Default message for all requests (e.g., `your name is "Bubu"`)
4. **Base URL**: Codegen API endpoint (usually default is fine)

### **Automatic Verification**
- Click **"🔍 Verify & Save"** to test credentials
- Real-time validation against Codegen API
- Configuration saved only if verification succeeds
- Status updates immediately upon successful setup

## 📡 API Endpoints

Once configured, the proxy exposes these **100% compatible** endpoints:

| Provider | Original API | Proxy URL |
|----------|-------------|-----------|
| **OpenAI** | `api.openai.com/v1/chat/completions` | `localhost:8000/v1/chat/completions` |
| **Anthropic** | `api.anthropic.com/v1/messages` | `localhost:8000/v1/messages` |
| **Gemini** | `generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent` | `localhost:8000/v1/models/gemini-pro:generateContent` |

## 💡 Usage Examples

### OpenAI Python Client
```python
import openai

# Just change the base URL - everything else stays the same!
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"  # Proxy handles auth

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What is your name?"}]
)

# Will respond with your configured system message!
print(response.choices[0].message.content)
```

### Anthropic Python Client
```python
import anthropic

# Point to proxy
client = anthropic.Anthropic(
    api_key="any-key",
    base_url="http://localhost:8000"
)

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Environment Variable Method
```bash
# Set environment variable once
export OPENAI_API_BASE=http://localhost:8000/v1

# All OpenAI client libraries will use the proxy automatically
python your_existing_script.py
```

### cURL Testing
```bash
# Test OpenAI API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🐳 Docker Deployment

### Docker Compose (Recommended)
```yaml
version: '3.8'
services:
  codegen-proxy:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CODEGEN_ORG_ID=323
      - CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99
      - DEFAULT_SYSTEM_MESSAGE=You are a helpful assistant.
    restart: unless-stopped
```

### Docker Run
```bash
docker build -t codegen-proxy .
docker run -d \
  -p 8000:8000 \
  -e CODEGEN_ORG_ID=323 \
  -e CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99 \
  --name codegen-proxy \
  codegen-proxy
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99

# Optional
CODEGEN_BASE_URL=https://api.codegen.com
DEFAULT_SYSTEM_MESSAGE=You are a helpful AI assistant.
LOG_LEVEL=INFO
LOG_REQUESTS=true
```

### Configuration File (Advanced)
Create `config/config.yaml`:
```yaml
codegen:
  org_id: "323"
  token: "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
  base_url: "https://api.codegen.com"

system_message: "You are a helpful AI assistant."

logging:
  level: "INFO"
  log_requests: true
```

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CODEGEN_ORG_ID=323
export CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99

# Run locally
python main.py
```

### Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test configuration endpoint
curl http://localhost:8000/api/config

# Test OpenAI compatibility
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}'
```

## 📋 System Requirements

- **Docker** (recommended) or Python 3.11+
- **2GB RAM** minimum
- **Network access** to Codegen API
- **Web browser** for configuration UI

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Status Endpoint
```bash
curl http://localhost:8000/status
```

### Configuration API
```bash
# Get current config (without sensitive data)
curl http://localhost:8000/api/config

# Verify credentials
curl -X POST http://localhost:8000/api/config/verify \
  -H "Content-Type: application/json" \
  -d '{"org_id": "323", "token": "sk-..."}'
```

### Logs
```bash
# Docker logs
docker logs codegen-proxy

# Follow logs
docker logs -f codegen-proxy
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Connection refused" error**
- Check if Docker container is running: `docker ps`
- Verify port 8000 is not in use: `netstat -an | grep 8000`

**2. "Invalid credentials" error**
- Use Web UI to verify credentials: http://localhost:8000
- Check Organization ID and Token are correct
- Ensure network access to Codegen API

**3. "System message not working"**
- Configure via Web UI or set `DEFAULT_SYSTEM_MESSAGE` environment variable
- Check logs for system message injection: `docker logs codegen-proxy`

**4. Web UI not loading**
- Ensure container is running: `docker ps`
- Check port mapping: `docker port codegen-proxy`
- Try accessing directly: `curl http://localhost:8000/health`

### Debug Mode
```bash
# Enable debug logging
docker run -e LOG_LEVEL=DEBUG -e LOG_REQUESTS=true codegen-proxy
```

## 🎯 How It Works

1. **Web UI Configuration**: Users configure credentials through beautiful settings dialog
2. **Credential Verification**: Real-time validation against Codegen API
3. **Request Interception**: Proxy intercepts OpenAI/Anthropic/Gemini API calls
4. **Format Transformation**: Converts provider-specific formats to Codegen format
5. **System Message Injection**: Automatically adds configured system messages
6. **API Routing**: Forwards requests to Codegen API with proper authentication
7. **Response Transformation**: Converts Codegen responses back to original format
8. **Transparent Operation**: Client applications receive expected response format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/open_codegen/issues)
- **Documentation**: [Wiki](https://github.com/Zeeeepa/open_codegen/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/open_codegen/discussions)

---

**🎯 Perfect for:**
- Migrating from OpenAI/Anthropic/Gemini to Codegen
- Adding system message injection to existing apps
- Centralizing AI API management
- Development and testing environments
- Cost optimization and monitoring

**Made with ❤️ for the developer community**
