# OpenCodegen Enhanced 🚀

**A comprehensive OpenAI API proxy with advanced web interface, Supabase integration, and intelligent endpoint management.**

OpenCodegen Enhanced transforms the original proxy server into a full-featured platform for managing AI API interactions with a modern web interface, database persistence, and intelligent endpoint discovery.

## ✨ Key Features

### 🎯 Core Functionality
- **OpenAI API Compatibility**: Drop-in replacement for OpenAI API calls
- **Multiple AI Provider Support**: Route to different AI services seamlessly
- **Transparent Interception**: Intercept existing OpenAI API calls without code changes
- **Real-time Web Dashboard**: Modern React-based interface for monitoring and management

### 🗄️ Database Integration
- **Supabase Integration**: Persistent storage for endpoints, conversations, and configurations
- **Real-time Sync**: Live updates across multiple clients
- **Data Export/Import**: Backup and restore your configurations
- **Multi-user Support**: User-specific endpoint management

### 🤖 Intelligent Features
- **AI-Assisted Endpoint Creation**: Describe endpoints in natural language
- **Website Discovery**: Automatically discover API endpoints from documentation
- **Web Interface Testing**: Test web-based AI interfaces with headless browser automation
- **Response Format Conversion**: Convert any response to OpenAI-compatible format

### 🌐 Web Interface
- **Modern React UI**: Built with TypeScript, Tailwind CSS, and Framer Motion
- **Real-time Chat**: WebSocket-powered chat interface
- **Endpoint Management**: Visual endpoint configuration and testing
- **Settings Panel**: Easy configuration management
- **Responsive Design**: Works on desktop, tablet, and mobile

### 🔧 Advanced Management
- **Custom Endpoint Creation**: Define your own API endpoints
- **Header Management**: Configure authentication and custom headers
- **Variable Substitution**: Dynamic endpoint configuration
- **Testing Suite**: Built-in endpoint testing and validation
- **Error Handling**: Comprehensive error reporting and recovery

## 🚀 Quick Start

### Windows Installation (Recommended)

1. **Download and run the installer:**
   ```powershell
   # Run as Administrator
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Zeeeepa/open_codegen/main/deploy/windows/install.ps1" -OutFile "install.ps1"
   .\install.ps1
   ```

2. **Follow the installation prompts:**
   - The installer will check for dependencies (Python, Node.js, Git)
   - Clone the repository and set up the environment
   - Build the frontend and configure the system
   - Create desktop and start menu shortcuts

3. **Configure your settings:**
   - Edit the `.env` file with your API tokens
   - Optionally set up Supabase for data persistence
   - Run the application using the desktop shortcut

### Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Zeeeepa/open_codegen.git
   cd open_codegen
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-enhanced.txt
   ```

3. **Set up frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the application:**
   ```bash
   python -m backend.api.main
   ```

6. **Open your browser:**
   Navigate to `http://localhost:8001`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# OpenCodegen Enhanced Configuration
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=your_codegen_token_here
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run
CODEGEN_DEFAULT_MODEL=codegen-standard
TRANSPARENT_MODE=false
PORT=8001

# Supabase Configuration (Optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Enhanced Features
ENABLE_WEB_INTERFACE=true
ENABLE_ENDPOINT_MANAGEMENT=true
ENABLE_AI_ASSISTANCE=true
```

### Supabase Setup (Optional)

1. **Create a Supabase project** at [supabase.com](https://supabase.com)

2. **Run the database schema:**
   ```sql
   -- Create endpoints table
   CREATE TABLE endpoints (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL,
     url TEXT NOT NULL,
     method TEXT DEFAULT 'POST',
     headers JSONB DEFAULT '{}',
     model_name TEXT DEFAULT 'custom-model',
     text_input_selector TEXT DEFAULT '',
     send_button_selector TEXT DEFAULT '',
     response_selector TEXT DEFAULT '',
     variables JSONB DEFAULT '{}',
     user_id TEXT,
     is_active BOOLEAN DEFAULT true,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Create conversations table
   CREATE TABLE conversations (
     id TEXT PRIMARY KEY,
     title TEXT NOT NULL,
     user_id TEXT NOT NULL,
     metadata JSONB DEFAULT '{}',
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Create messages table
   CREATE TABLE messages (
     id TEXT PRIMARY KEY,
     conversation_id TEXT REFERENCES conversations(id),
     role TEXT NOT NULL,
     content TEXT NOT NULL,
     endpoint_id TEXT REFERENCES endpoints(id),
     metadata JSONB DEFAULT '{}',
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Configure in the web interface:**
   - Go to Settings in the web interface
   - Enter your Supabase URL and API key
   - Test the connection

## 📖 Usage Examples

### Basic API Proxy

Replace your OpenAI API calls:

```python
# Before
import openai
openai.api_base = "https://api.openai.com/v1"

# After
import openai
openai.api_base = "http://localhost:8001/v1"
```

### Custom Endpoint Creation

1. **Via Web Interface:**
   - Go to Endpoints → Add New
   - Fill in the endpoint details
   - Test the endpoint
   - Save and use

2. **Via API:**
   ```python
   import requests
   
   endpoint_data = {
       "name": "My Custom API",
       "url": "https://api.example.com/chat",
       "method": "POST",
       "headers": {"Authorization": "Bearer your-token"},
       "user_id": "user123"
   }
   
   response = requests.post("http://localhost:8001/api/endpoints", json=endpoint_data)
   ```

### AI-Assisted Endpoint Creation

```python
import requests

# Describe your endpoint in natural language
description = "Create an endpoint for Anthropic's Claude API that accepts messages and returns responses"

response = requests.post("http://localhost:8001/api/endpoints/ai-create", json={
    "description": description,
    "user_id": "user123"
})
```

### Website Discovery

```python
import requests

# Discover API endpoints from documentation
response = requests.post("http://localhost:8001/api/websites/discover", json={
    "url": "https://docs.example.com/api"
})

endpoints = response.json()["endpoints"]
```

## 🏗️ Architecture

### Backend Components

- **FastAPI Server** (`backend/api/main.py`): Main API server with WebSocket support
- **Database Layer** (`backend/database.py`): Supabase integration and data models
- **Endpoint Manager** (`backend/services/endpoint_manager.py`): AI-assisted endpoint management
- **Web Automation** (`backend/services/web_automation.py`): Headless browser automation

### Frontend Components

- **React Application** (`frontend/src/`): Modern TypeScript React app
- **Supabase Context** (`frontend/src/contexts/`): Real-time database integration
- **Component Library** (`frontend/src/components/`): Reusable UI components
- **Pages** (`frontend/src/pages/`): Main application views

### Key Features

1. **Real-time Communication**: WebSocket connections for live updates
2. **Responsive Design**: Mobile-first approach with Tailwind CSS
3. **Type Safety**: Full TypeScript implementation
4. **Error Handling**: Comprehensive error boundaries and recovery
5. **Performance**: Optimized with React Query and lazy loading

## 🔌 API Endpoints

### Core Proxy Endpoints
- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `GET /v1/models` - List available models
- `GET /health` - Health check

### Enhanced Management Endpoints
- `GET /api/endpoints` - List custom endpoints
- `POST /api/endpoints` - Create new endpoint
- `PUT /api/endpoints/{id}` - Update endpoint
- `DELETE /api/endpoints/{id}` - Delete endpoint
- `POST /api/endpoints/test` - Test endpoint
- `POST /api/endpoints/ai-create` - AI-assisted creation

### Chat and Conversation Endpoints
- `POST /api/chat` - Send chat message
- `GET /api/conversations/{id}/messages` - Get conversation messages
- `WebSocket /ws/chat` - Real-time chat

### Supabase Integration Endpoints
- `POST /api/supabase/connect` - Connect to Supabase
- `GET /api/supabase/status` - Connection status

## 🛠️ Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Zeeeepa/open_codegen.git
   cd open_codegen
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-enhanced.txt
   ```

2. **Frontend development:**
   ```bash
   cd frontend
   npm install
   npm start  # Development server
   ```

3. **Backend development:**
   ```bash
   python -m backend.api.main
   ```

### Testing

```bash
# Backend tests
pytest backend/tests/

# Frontend tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be served by the FastAPI server
```

## 🚀 Deployment

### Windows Service

```batch
# Install as Windows Service (run as Administrator)
install-service.bat
```

### Docker Deployment

```bash
# Build and run with Docker
docker build -t opencodegen-enhanced .
docker run -p 8001:8001 -v $(pwd)/.env:/app/.env opencodegen-enhanced
```

### Cloud Deployment

The application can be deployed to:
- **Heroku**: Use the included `Procfile`
- **Railway**: Direct GitHub integration
- **DigitalOcean App Platform**: Auto-deploy from repository
- **AWS/GCP/Azure**: Container or serverless deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the original OpenCodegen proxy
- Powered by FastAPI, React, and Supabase
- UI components inspired by modern design systems
- Special thanks to the open-source community

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Zeeeepa/open_codegen/issues)
- **Documentation**: [Full documentation](https://github.com/Zeeeepa/open_codegen/wiki)
- **Community**: [Join our Discord](https://discord.gg/opencodegen)

---

**OpenCodegen Enhanced** - Transforming AI API interactions with intelligence and elegance. 🚀
