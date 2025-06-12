# Web UI Dashboard Guide

The OpenAI Codegen Adapter includes a comprehensive web dashboard for managing service providers, running tests, and monitoring API calls in real-time.

## 🌟 Features

### 🔧 **Service Configuration Panel**
- Configure base URLs for OpenAI, Anthropic, and Google APIs
- Real-time status indicators for each service
- Save configurations locally in browser storage
- Easy switching between different endpoints

### 🧪 **Interactive Testing**
- One-click test buttons for each service provider
- Real-time test execution with loading indicators
- Automatic error handling and reporting
- Integration with existing test scripts

### 💬 **Real-Time Message History**
- Live display of all API calls and responses
- Timestamp tracking for each interaction
- Service identification for each message
- Formatted display of prompts and responses
- Auto-scrolling and message limiting (last 50 messages)

### 📊 **Session Statistics**
- Total API calls counter
- Success rate calculation
- Last used service tracking
- Last call timestamp

## 🚀 Quick Start

### 1. Install Dashboard Dependencies
```bash
pip install -r requirements-dashboard.txt
```

### 2. Start the Dashboard
```bash
python start_dashboard.py
```

### 3. Open in Browser
Navigate to: **http://127.0.0.1:8888**

## 🔧 Configuration

### Service Endpoints
The dashboard allows you to configure three main service endpoints:

1. **OpenAI API endpoint**: `http://localhost:8887/v1`
2. **Anthropic API endpoint**: `http://localhost:8887/v1`
3. **Google API endpoint**: `http://localhost:8887/v1`

### Default Configuration
By default, all services point to the local adapter at `http://localhost:8887/v1`. You can modify these URLs to:

- Point to different local servers (Ollama, LM Studio, etc.)
- Use official cloud APIs directly
- Test different adapter configurations

### Saving Configuration
- Click the **Save** button next to each service to store the URL
- Configurations are saved in browser localStorage
- Settings persist between browser sessions

## 🧪 Testing Services

### Test Buttons
Each service has a dedicated test button:

- **🤖 Test OpenAI**: Runs `test_openai_enhanced.py`
- **🧠 Test Anthropic**: Runs `test_anthropic_enhanced.py`
- **🌟 Test Google**: Runs `test_google_enhanced.py`

### Test Process
1. Click a test button
2. The button shows "⏳ Testing..." state
3. Loading indicator appears
4. Test script executes in the background
5. Results appear in the message history
6. Statistics update automatically

### Test Scripts
The dashboard uses enhanced test scripts that output JSON for better integration:

- `test_openai_enhanced.py` - Tests OpenAI compatibility
- `test_anthropic_enhanced.py` - Tests Anthropic compatibility  
- `test_google_enhanced.py` - Tests Google Gemini compatibility

## 💬 Message History

### Message Format
Each message in the history shows:

```
[SERVICE] [TIMESTAMP]
Prompt: [User's prompt/question]
Response: [AI's response]
```

### Example Message
```
OPENAI                           07/06/2025, 16:12:07
Prompt: Explain quantum computing in simple terms.

Response: Quantum computing is a revolutionary technology that uses the principles of quantum mechanics to process information. Unlike classical computers that use bits (0s and 1s), quantum computers use quantum bits or "qubits" that can exist in multiple states simultaneously...
```

### Message Features
- **Service Identification**: Color-coded badges for each service
- **Timestamps**: Precise timing for each interaction
- **Formatted Display**: Clean, readable layout
- **Auto-Scrolling**: New messages appear at the top
- **Message Limiting**: Keeps only the last 50 messages for performance

## 📊 Statistics Panel

### Metrics Tracked
1. **Total Calls**: Number of API calls made in the session
2. **Success Rate**: Percentage of successful calls
3. **Last Service**: Most recently used service (OPENAI, ANTHROPIC, GEMINI)
4. **Last Call**: Timestamp of the most recent API call

### Real-Time Updates
Statistics update automatically after each test:
- Counters increment immediately
- Success rate recalculates
- Last service and timestamp update

## 🎨 User Interface

### Design Features
- **Modern Design**: Clean, professional interface
- **Responsive Layout**: Works on desktop and mobile
- **Color-Coded Services**: Easy visual identification
- **Status Indicators**: Live service status with pulse animation
- **Loading States**: Clear feedback during operations

### Color Scheme
- **OpenAI**: Blue theme
- **Anthropic**: Purple theme  
- **Google**: Green theme
- **Success**: Green indicators
- **Error**: Red indicators
- **Loading**: Orange/amber states

## 🔧 Advanced Usage

### Custom Endpoints
You can configure the dashboard to work with any OpenAI-compatible API:

```
# Local Ollama
http://localhost:11434/v1

# Local LM Studio  
http://localhost:1234/v1

# Official OpenAI
https://api.openai.com/v1

# Custom local server
http://localhost:8080/v1
```

### Environment Variables
The test scripts respect environment variables:

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"
export ANTHROPIC_BASE_URL="http://localhost:8887/v1"
export GOOGLE_BASE_URL="http://localhost:8887/v1"
```

### Integration with Main Adapter
The dashboard works alongside the main adapter:

1. Start the main adapter: `python -m openai_codegen_adapter.main`
2. Start the dashboard: `python start_dashboard.py`
3. Configure dashboard to point to adapter: `http://localhost:8887/v1`
4. Run tests to see real-time API interactions

## 🚨 Troubleshooting

### Common Issues

#### Dashboard Won't Start
```bash
# Install missing dependencies
pip install -r requirements-dashboard.txt

# Check Python version (3.8+ required)
python --version
```

#### Tests Fail
```bash
# Check if adapter is running
curl http://localhost:8887/health

# Verify endpoint URLs in dashboard
# Check browser console for errors
```

#### No Messages Appear
- Ensure test scripts are executable
- Check that enhanced test scripts exist
- Verify endpoint URLs are correct
- Look for errors in browser console

#### Status Indicators Show Offline
- Check if the target service is running
- Verify the endpoint URL is correct
- Test the endpoint manually with curl

### Debug Mode
To see detailed logs, run the dashboard server directly:

```bash
python web_ui/dashboard_server.py --host 127.0.0.1 --port 8888
```

## 🔗 API Endpoints

The dashboard server provides these API endpoints:

- `GET /` - Main dashboard interface
- `GET /health` - Health check
- `GET /api/providers` - List available providers
- `POST /api/test` - Run service tests
- `GET /api/status/{service}` - Check service status

## 🎯 Use Cases

### Development
- Test different AI providers quickly
- Monitor API call patterns
- Debug adapter configurations
- Compare responses between services

### Demonstration
- Show real-time AI interactions
- Display service capabilities
- Present adapter functionality
- Monitor system performance

### Monitoring
- Track API usage patterns
- Monitor success rates
- Identify failing services
- Analyze response times

## 🤝 Contributing

To enhance the dashboard:

1. **Frontend**: Modify `web_ui/templates/dashboard.html`
2. **Backend**: Update `web_ui/dashboard_server.py`
3. **Test Scripts**: Enhance `test_*_enhanced.py` files
4. **Styling**: Add CSS to the HTML template
5. **Features**: Add new API endpoints and UI components

## 📄 License

The dashboard is part of the OpenAI Codegen Adapter project and follows the same license terms.

