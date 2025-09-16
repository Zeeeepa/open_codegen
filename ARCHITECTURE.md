# OpenAI Codegen Adapter - Architecture Documentation

## 🏗️ System Architecture

The OpenAI Codegen Adapter is a comprehensive system that provides OpenAI API interception, multi-provider AI routing, and a modern web management interface.

## 📁 Project Structure

```
open_codegen/
├── backend/                          # Backend Python application
│   ├── adapter/                      # Core adapter components (existing)
│   │   ├── server.py                 # Main FastAPI server
│   │   ├── codegen_client.py         # Codegen API client
│   │   ├── models.py                 # Pydantic models
│   │   ├── streaming.py              # Streaming response handling
│   │   └── ...                       # Other adapter components
│   ├── providers/                    # AI provider integrations (new)
│   │   ├── __init__.py
│   │   └── zai_provider.py           # Z.ai GLM-4.5 integration
│   ├── interceptor/                  # DNS/API interception (existing)
│   ├── api_manager.py                # Web UI API manager (new)
│   ├── chat_handler.py               # Multi-provider chat routing (new)
│   ├── endpoint_manager.py           # Dynamic endpoint management (new)
│   ├── web_scraper.py                # Website API discovery (new)
│   ├── web_ui_integration.py         # UI integration layer (new)
│   ├── enhanced_server.py            # Enhanced server runner (existing)
│   └── requirements.txt              # Python dependencies
├── frontend/                         # React web interface (new)
│   ├── public/
│   │   └── index.html                # Main HTML template
│   ├── src/
│   │   ├── components/               # React components
│   │   │   ├── App.jsx               # Main application component
│   │   │   ├── Sidebar.jsx           # Navigation sidebar
│   │   │   ├── ChatInterface.jsx     # AI chat interface
│   │   │   ├── EndpointManager.jsx   # Endpoint management
│   │   │   ├── WebsiteManager.jsx    # Website analysis
│   │   │   ├── ConfigManager.jsx     # Configuration management
│   │   │   └── Dashboard.jsx         # System dashboard
│   │   ├── services/                 # API service layer
│   │   │   ├── chatService.js        # Chat API communication
│   │   │   ├── configService.js      # Configuration API
│   │   │   └── endpointService.js    # Endpoint API
│   │   ├── index.js                  # React entry point
│   │   └── index.css                 # Global styles
│   └── package.json                  # Node.js dependencies
├── deploy/                           # Deployment scripts (new)
│   └── windows/
│       ├── install.ps1               # Windows installer
│       └── uninstall.ps1             # Windows uninstaller
├── data/                             # Application data (created at runtime)
│   ├── endpoints.json                # Stored endpoints
│   ├── websites.json                 # Analyzed websites
│   └── logs/                         # Application logs
├── start_with_ui.py                  # Integrated startup script (new)
├── README.md                         # Project documentation
├── ARCHITECTURE.md                   # This file
└── requirements.txt                  # Root Python dependencies
```

## 🔧 Core Components

### 1. Backend Architecture

#### Existing Components (Enhanced)
- **FastAPI Server**: Core HTTP server with OpenAI API compatibility
- **Codegen Client**: Integration with Codegen's AI services
- **Request/Response Transformers**: Convert between API formats
- **Streaming Handlers**: Real-time response streaming
- **DNS Interceptor**: Transparent API call interception

#### New Components
- **API Manager**: Web UI backend API endpoints
- **Chat Handler**: Multi-provider chat routing and streaming
- **Provider System**: Modular AI provider integrations
- **Endpoint Manager**: Dynamic API endpoint creation and testing
- **Web Scraper**: Website analysis and API discovery
- **UI Integration**: Seamless frontend/backend integration

### 2. Frontend Architecture

#### React Application
- **Material-UI**: Modern, responsive component library
- **React Router**: Client-side routing for SPA experience
- **Axios**: HTTP client for API communication
- **Chart.js**: Data visualization for dashboard
- **React Hot Toast**: User notifications

#### Component Hierarchy
```
App (Root)
├── Sidebar (Navigation)
├── ChatInterface (AI Chat)
│   ├── Message Components
│   ├── Provider Selector
│   └── Streaming Handler
├── EndpointManager (API Management)
│   ├── Endpoint List
│   ├── Endpoint Editor
│   └── Test Interface
├── WebsiteManager (Website Analysis)
│   ├── URL Input
│   ├── Analysis Progress
│   └── Results Display
├── ConfigManager (Settings)
│   ├── API Key Management
│   ├── Provider Settings
│   └── Server Configuration
└── Dashboard (Monitoring)
    ├── Statistics Cards
    ├── Performance Charts
    └── Activity Logs
```

## 🔄 Data Flow

### 1. API Interception Flow
```
Client Application
    ↓ (OpenAI API call)
DNS Interceptor
    ↓ (routes to local server)
FastAPI Server
    ↓ (processes request)
Request Transformer
    ↓ (converts format)
Provider Router
    ↓ (selects provider)
AI Provider (OpenAI/Anthropic/Gemini/Z.ai/Codegen)
    ↓ (returns response)
Response Transformer
    ↓ (converts back to OpenAI format)
Client Application
```

### 2. Web UI Data Flow
```
React Frontend
    ↓ (HTTP requests)
API Manager
    ↓ (routes to appropriate handler)
Chat Handler / Endpoint Manager / Web Scraper
    ↓ (processes request)
Provider APIs / Database / File System
    ↓ (returns data)
React Frontend (updates UI)
```

### 3. Chat Flow
```
User Input (Frontend)
    ↓
Chat Service (Frontend)
    ↓ (POST /api/chat)
API Manager
    ↓
Chat Handler
    ↓ (routes by provider)
Provider Integration
    ↓ (streaming response)
Frontend (real-time updates)
```

## 🔌 Provider Integration

### Provider Interface
Each provider implements a common interface:

```python
class ProviderInterface:
    async def chat_completion(messages, model, stream=False, **kwargs)
    async def get_models()
    async def test_connection()
    def format_messages(messages)
    def get_provider_info()
```

### Supported Providers

| Provider | Implementation | Features |
|----------|----------------|----------|
| OpenAI | Via Codegen Client | Chat, Streaming, Embeddings |
| Anthropic | Via Codegen Client | Chat, Streaming |
| Google Gemini | Via Codegen Client | Chat, Streaming, Vision |
| Z.ai | Direct Integration | Chat, Streaming, GLM-4.5/4.5V |
| Codegen | Direct Integration | All Codegen Features |

## 💾 Data Storage

### File-Based Storage
- **Configuration**: Environment variables and JSON files
- **Endpoints**: JSON file with endpoint definitions
- **Websites**: JSON file with analysis results
- **Logs**: Rotating log files with configurable levels

### Data Models

#### Endpoint Model
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "method": "GET|POST|PUT|DELETE|PATCH",
  "url": "string",
  "headers": "object",
  "body": "string",
  "provider": "string",
  "variables": "array",
  "created_at": "datetime",
  "test_results": "object"
}
```

#### Website Model
```json
{
  "id": "uuid",
  "url": "string",
  "name": "string",
  "endpoints": "array",
  "links": "array",
  "analysis_date": "datetime",
  "confidence_scores": "object"
}
```

## 🔐 Security Architecture

### API Key Management
- Environment variable storage
- Masked display in UI
- Secure transmission (HTTPS)
- No logging of sensitive data

### Network Security
- CORS configuration
- HTTPS support with self-signed certificates
- Firewall rule management (Windows)
- Request rate limiting (planned)

### Access Control
- Local-only access by default
- Configurable host binding
- Service mode with restricted permissions

## 🚀 Deployment Architecture

### Development Mode
```
Python Backend (port 8000)
    ↕ (proxy)
React Dev Server (port 3000)
```

### Production Mode
```
FastAPI Server (port 8000)
    ├── API endpoints (/api/*)
    ├── OpenAI compatibility (/v1/*)
    └── Static files (React build)
```

### Windows Service Mode
```
NSSM Service Manager
    ↓
Python Service Wrapper
    ↓
FastAPI Application
    ├── Web UI
    ├── API Server
    └── DNS Interceptor
```

## 📊 Monitoring & Observability

### Logging Levels
- **DEBUG**: Detailed request/response logging
- **INFO**: General operation information
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions requiring attention

### Metrics Collection
- Request count and success rates
- Response time percentiles
- Provider availability
- System resource usage

### Health Checks
- Provider connectivity tests
- Database/file system access
- Memory and CPU usage
- Service status monitoring

## 🔄 Extension Points

### Adding New Providers
1. Create provider class in `backend/providers/`
2. Implement required interface methods
3. Add to chat handler routing
4. Update frontend provider list
5. Add configuration options

### Adding New Features
1. Backend API endpoints in `api_manager.py`
2. Frontend components in `src/components/`
3. Service layer in `src/services/`
4. Update navigation and routing

### Custom Endpoints
- Dynamic endpoint creation via UI
- AI-assisted endpoint generation
- Variable substitution support
- Provider routing configuration

## 🧪 Testing Strategy

### Backend Testing
- Unit tests for each component
- Integration tests for API endpoints
- Provider connectivity tests
- Performance benchmarks

### Frontend Testing
- Component unit tests
- Integration tests for user flows
- E2E tests with Playwright
- Accessibility testing

### System Testing
- Full stack integration tests
- Load testing for concurrent users
- Failover and recovery testing
- Security penetration testing

## 📈 Performance Considerations

### Backend Optimization
- Async/await throughout
- Connection pooling for providers
- Response caching (planned)
- Request queuing and rate limiting

### Frontend Optimization
- Code splitting and lazy loading
- Memoization for expensive operations
- Virtual scrolling for large lists
- Service worker for offline support (planned)

### Scalability
- Horizontal scaling support (planned)
- Load balancer compatibility
- Database migration path (planned)
- Microservices architecture (future)

## 🔮 Future Enhancements

### Planned Features
- Database backend (PostgreSQL/SQLite)
- User authentication and authorization
- API usage analytics and billing
- Plugin system for custom providers
- Docker containerization
- Kubernetes deployment
- Real-time collaboration features
- Advanced monitoring dashboard

### Integration Opportunities
- CI/CD pipeline integration
- Slack/Discord bot interface
- VS Code extension
- Browser extension for API interception
- Mobile app for monitoring

---

This architecture provides a solid foundation for a comprehensive AI API management system while maintaining flexibility for future enhancements and integrations.

