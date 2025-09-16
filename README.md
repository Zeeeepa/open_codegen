# OpenAI Codegen Adapter with Web UI

A comprehensive OpenAI API interception and routing system with a modern web interface, supporting multiple AI providers including OpenAI, Anthropic, Google Gemini, Z.ai, and Codegen.

## 🚀 Features

### Core Functionality
- **OpenAI API Interception**: Transparently intercepts OpenAI API calls and routes them to any provider
- **Multi-Provider Support**: OpenAI, Anthropic Claude, Google Gemini, Z.ai GLM-4.5, and Codegen
- **Streaming Support**: Real-time streaming responses for all providers
- **Web UI**: Modern React-based interface for management and chat

### Web Interface
- **AI Chat Interface**: Multi-provider chat with conversation history
- **Endpoint Manager**: Create, test, and manage custom API endpoints
- **Website Analyzer**: Discover API endpoints from websites automatically
- **Configuration Manager**: Easy setup and management of API keys and settings
- **Dashboard**: System monitoring and performance metrics

### Advanced Features
- **AI-Assisted Endpoint Generation**: Natural language to API endpoint conversion
- **Website API Discovery**: Automatic detection of API endpoints from web pages
- **Client Endpoint Creation**: Generate endpoints for any website to work with any AI provider
- **Windows Service Mode**: Run as a Windows service with automatic startup
- **DNS Interception**: Transparent API call interception without code changes

## 📦 Installation

### Windows (Recommended)

1. **Download the installer script**:
   ```powershell
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/open_codegen/main/deploy/windows/install.ps1" -OutFile "install.ps1"
   ```

2. **Run as Administrator**:
   ```powershell
   PowerShell -ExecutionPolicy Bypass -File install.ps1
   ```

3. **For service mode**:
   ```powershell
   PowerShell -ExecutionPolicy Bypass -File install.ps1 -ServiceMode
   ```

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/open_codegen.git
   cd open_codegen
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Install and build frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure environment**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your API keys
   ```

5. **Start the server**:
   ```bash
   python -m backend.enhanced_server
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Core Configuration
CODEGEN_API_KEY=your_codegen_api_key_here
CODEGEN_BASE_URL=https://api.codegen.com
SERVER_PORT=8000

# Provider API Keys
OPENAI_API_KEY=sk-your_openai_key
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
GEMINI_API_KEY=your_gemini_key
ZAI_API_KEY=your_zai_key  # Optional

# Server Settings
LOG_LEVEL=INFO
ENABLE_WEB_UI=true
ENABLE_CORS=true
ENABLE_STREAMING=true

# Advanced Settings
DNS_INTERCEPTION=false
TRANSPARENT_MODE=false
```

### Web UI Configuration

Access the web interface at `http://localhost:8000` and configure:

1. **API Keys**: Add your provider API keys
2. **Default Provider**: Choose your preferred AI provider
3. **Model Settings**: Configure temperature, max tokens, etc.
4. **Server Settings**: Port, logging, CORS settings

## 🎯 Usage

### Web Interface

1. **Chat Interface**: 
   - Select any AI provider (OpenAI, Anthropic, Gemini, Z.ai, Codegen)
   - Start chatting with real-time streaming responses
   - View conversation history and export chats

2. **Endpoint Manager**:
   - Create custom API endpoints
   - Test endpoints with different providers
   - Use AI to generate endpoints from natural language

3. **Website Manager**:
   - Analyze websites to discover API endpoints
   - Create client endpoints for any website
   - Route website APIs through any AI provider

### API Interception

The system can intercept OpenAI API calls transparently:

```python
import openai

# Your existing OpenAI code works unchanged
client = openai.OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",  # Will be routed to your configured provider
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Direct API Usage

```python
import requests

# Chat with any provider
response = requests.post("http://localhost:8000/api/chat", json={
    "message": "Hello, world!",
    "provider": "anthropic",  # or "openai", "gemini", "zai", "codegen"
    "model": "claude-3-sonnet",
    "stream": True
})
```

## 🏗️ Architecture

### Backend Components

- **Enhanced Server**: Main FastAPI server with interception capabilities
- **Provider Integrations**: Modular provider implementations
- **Chat Handler**: Multi-provider chat routing and streaming
- **Endpoint Manager**: Dynamic endpoint creation and testing
- **Web Scraper**: Website analysis and API discovery
- **API Manager**: Web UI backend API

### Frontend Components

- **React App**: Modern Material-UI interface
- **Chat Interface**: Real-time chat with multiple providers
- **Management Panels**: Endpoint, website, and configuration management
- **Dashboard**: System monitoring and analytics

### Provider Support

| Provider | Chat | Streaming | Models | Status |
|----------|------|-----------|---------|--------|
| OpenAI | ✅ | ✅ | GPT-4, GPT-3.5 | Full |
| Anthropic | ✅ | ✅ | Claude-3 Opus/Sonnet | Full |
| Google Gemini | ✅ | ✅ | Gemini Pro/Vision | Full |
| Z.ai | ✅ | ✅ | GLM-4.5/4.5V | Full |
| Codegen | ✅ | ✅ | All Models | Full |

## 🔧 Development

### Backend Development

```bash
# Install development dependencies
pip install -r backend/requirements.txt

# Run in development mode
python -m backend.enhanced_server --reload

# Run tests
pytest backend/tests/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Adding New Providers

1. Create a new provider class in `backend/providers/`
2. Implement the required methods (chat_completion, streaming, etc.)
3. Add provider to the chat handler routing
4. Update the frontend provider list

## 🚀 Deployment

### Windows Service

The installer can configure the application as a Windows service:

```powershell
# Install as service
PowerShell -ExecutionPolicy Bypass -File install.ps1 -ServiceMode

# Start service
net start "OpenAI-Codegen-Adapter"

# Stop service
net stop "OpenAI-Codegen-Adapter"
```

### Docker (Coming Soon)

```bash
# Build and run with Docker
docker build -t openai-codegen-adapter .
docker run -p 8000:8000 openai-codegen-adapter
```

## 📊 Monitoring

### Dashboard Features

- **Request Statistics**: Total requests, success rates, response times
- **Provider Status**: Health checks for all configured providers
- **Performance Metrics**: Response time trends and system health
- **Activity Logs**: Recent API calls and system events

### Logging

Logs are stored in:
- **Windows**: `%LOCALAPPDATA%\OpenAI-Codegen-Adapter\logs\`
- **Linux/Mac**: `./logs/`

Log levels: DEBUG, INFO, WARNING, ERROR

## 🔒 Security

### API Key Management

- API keys are stored securely in environment variables
- Web UI masks sensitive information
- Configuration export excludes sensitive data

### Network Security

- HTTPS support with self-signed certificates
- CORS configuration for web UI security
- Firewall rules automatically configured on Windows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Q: The web interface doesn't load**
A: Check that the server is running on the correct port and CORS is enabled.

**Q: API calls are not being intercepted**
A: Ensure DNS interception is enabled and you're running as Administrator on Windows.

**Q: Provider authentication fails**
A: Verify your API keys are correctly set in the configuration.

### Getting Help

- 📖 [Documentation](https://github.com/your-repo/open_codegen/wiki)
- 🐛 [Issue Tracker](https://github.com/your-repo/open_codegen/issues)
- 💬 [Discussions](https://github.com/your-repo/open_codegen/discussions)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [React](https://reactjs.org/) and [Material-UI](https://mui.com/) for the frontend
- [Codegen](https://codegen.com/) for the core AI capabilities
- All the AI providers for their amazing APIs

---

**Made with ❤️ for the AI development community**

