# Context Retrieval for AI Prompting

The OpenAI Codegen Adapter now includes powerful context retrieval capabilities that enhance AI prompting by extracting and formatting responses from Codegen agent runs.

## 🎯 Overview

Context retrieval allows you to:

- **Extract responses** from Codegen agent runs for AI context
- **Format content** for optimal AI prompting
- **Chain multiple contexts** for comprehensive analysis
- **Integrate seamlessly** with existing AI workflows

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create .env file with your credentials
echo "CODEGEN_ORG_ID=323" > .env
echo "CODEGEN_TOKEN=your-token-here" >> .env
```

### 2. Start the Server
```bash
python server.py
```

### 3. Test Context Retrieval
```bash
# Test the integration
python test_context_retrieval.py

# Run usage examples
python example_context_usage.py
```

## 📡 API Endpoints

### Synchronous Context Retrieval
```bash
POST /api/context/retrieve
{
  "prompt": "Analyze this codebase and suggest improvements",
  "max_length": 4000,
  "timeout": 300
}
```

**Response:**
```json
{
  "success": true,
  "context_text": "Clean text response...",
  "length": 1234,
  "truncated": false,
  "agent_run_id": 12345,
  "web_url": "https://...",
  "status": "completed"
}
```

### Asynchronous Context Creation
```bash
POST /api/context/create
{
  "prompt": "Perform detailed code analysis"
}
```

**Response:**
```json
{
  "success": true,
  "agent_run_id": 12345,
  "status": "running",
  "web_url": "https://..."
}
```

### Status Monitoring
```bash
GET /api/context/status/{agent_run_id}
```

**Response:**
```json
{
  "agent_run_id": 12345,
  "status": "completed",
  "result": "Full response text...",
  "web_url": "https://...",
  "context_text": "Clean text for AI...",
  "error": null
}
```

## 💻 Usage Examples

### 1. Simple Context Retrieval
```python
from codegen_integration import get_agent_response_for_context

# Get context for AI prompting
context = get_agent_response_for_context(
    "Analyze the current codebase structure",
    max_length=3000,
    timeout=180
)

# Use in AI prompt
ai_prompt = f"""
Based on this analysis: {context}

Please suggest specific improvements for:
1. Code maintainability
2. Performance optimization
3. Architecture enhancement
"""
```

### 2. API Integration
```python
import requests

# Create async agent run
response = requests.post("http://localhost:8887/api/context/create", json={
    "prompt": "Analyze testing strategy and suggest improvements"
})

agent_run_id = response.json()["agent_run_id"]

# Poll for completion
status_response = requests.get(f"http://localhost:8887/api/context/status/{agent_run_id}")
context_text = status_response.json()["context_text"]
```

### 3. Context Chaining
```python
from codegen_integration import get_agent_response_for_context

# Get multiple contexts
arch_context = get_agent_response_for_context(
    "Analyze the software architecture",
    max_length=1500
)

perf_context = get_agent_response_for_context(
    "Analyze performance bottlenecks",
    max_length=1500
)

# Combine for comprehensive analysis
combined_prompt = f"""
ARCHITECTURE ANALYSIS:
{arch_context}

PERFORMANCE ANALYSIS:
{perf_context}

Create a comprehensive improvement roadmap addressing both areas.
"""
```

### 4. Error Handling
```python
import requests
import time

def get_context_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8887/api/context/retrieve",
                json={"prompt": prompt, "timeout": 180},
                timeout=200
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('context_text')
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)  # Wait before retry
    
    return None
```

## 🎯 Use Cases

### 1. Code Analysis Enhancement
```python
# Get comprehensive code analysis
analysis = get_agent_response_for_context(
    "Analyze code quality, architecture, and suggest improvements"
)

# Use for targeted improvements
improvement_prompt = f"Based on: {analysis}\nSuggest 5 specific improvements"
```

### 2. Documentation Generation
```python
# Get project overview
overview = get_agent_response_for_context(
    "Provide project overview, structure, and key components"
)

# Generate documentation
doc_prompt = f"Create README.md based on: {overview}"
```

### 3. Architecture Planning
```python
# Get architecture analysis
arch_analysis = get_agent_response_for_context(
    "Analyze current architecture and identify improvement areas"
)

# Plan improvements
planning_prompt = f"""
Current architecture: {arch_analysis}

Create a 6-month improvement roadmap with:
1. Priority improvements
2. Implementation timeline
3. Resource requirements
"""
```

### 4. Testing Strategy
```python
# Analyze current testing
test_analysis = get_agent_response_for_context(
    "Analyze testing strategy, coverage, and quality"
)

# Improve testing
testing_prompt = f"""
Current testing analysis: {test_analysis}

Suggest improvements for:
1. Test coverage
2. Test quality
3. Testing automation
4. Performance testing
"""
```

## ⚙️ Configuration

### Environment Variables
- `CODEGEN_ORG_ID` - Your Codegen organization ID
- `CODEGEN_TOKEN` - Your Codegen API token
- `CODEGEN_BASE_URL` - API base URL (optional, defaults to https://api.codegen.com)

### Client Configuration
```python
from codegen_integration import CodegenClient

# Custom configuration
client = CodegenClient(
    organization_id=323,
    api_token="your-token",
    base_url="https://api.codegen.com",
    timeout=300,
    poll_interval=10
)
```

## 🧪 Testing

### Basic Testing
```bash
# Test server availability
python test_context_retrieval.py --server-only

# Test direct integration
python test_context_retrieval.py --skip-api

# Test API endpoints
python test_context_retrieval.py --skip-direct
```

### Comprehensive Testing
```bash
# Run all tests
python test_context_retrieval.py

# Custom server URL
python test_context_retrieval.py --base-url http://localhost:8888
```

### Example Testing
```bash
# Run usage examples
python example_context_usage.py
```

## 🔧 Advanced Usage

### Custom Context Processing
```python
from codegen_integration import CodegenClient

client = CodegenClient(timeout=300)

# Create and monitor agent run
agent_run_id = client.create_agent_run("Custom analysis prompt")
result = client.wait_for_completion(agent_run_id)

# Extract and process context
context_text = result.get_context_text(max_length=5000)

# Custom processing
processed_context = context_text.replace('\n', ' ').strip()
```

### Batch Context Retrieval
```python
import asyncio
import requests

async def get_multiple_contexts(prompts):
    """Get multiple contexts concurrently"""
    tasks = []
    
    for prompt in prompts:
        # Create agent runs
        response = requests.post(
            "http://localhost:8887/api/context/create",
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            agent_run_id = response.json()["agent_run_id"]
            tasks.append(agent_run_id)
    
    # Wait for all to complete
    contexts = []
    for agent_run_id in tasks:
        # Poll for completion (simplified)
        while True:
            status_response = requests.get(
                f"http://localhost:8887/api/context/status/{agent_run_id}"
            )
            
            if status_response.status_code == 200:
                data = status_response.json()
                if data["status"].lower() == "completed":
                    contexts.append(data["context_text"])
                    break
            
            await asyncio.sleep(10)
    
    return contexts
```

## 🐛 Troubleshooting

### Common Issues

1. **Context retrieval not available**
   - Ensure `codegen_integration.py` is in the project root
   - Check environment variables are set correctly
   - Verify server is running with context endpoints

2. **Agent runs timing out**
   - Increase timeout values in requests
   - Check Codegen service status
   - Verify API token permissions

3. **Server connection errors**
   - Ensure server is running on correct port
   - Check firewall settings
   - Verify base URL configuration

4. **Empty context responses**
   - Check agent run status for errors
   - Verify prompt is clear and actionable
   - Ensure sufficient timeout for complex analysis

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
python server.py
```

### Health Checks
```bash
# Check server health
curl http://localhost:8887/health

# Test context retrieval
curl -X POST http://localhost:8887/api/context/retrieve \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "timeout": 30}'
```

## 📈 Performance Tips

1. **Optimize Timeouts**
   - Use shorter timeouts for simple queries
   - Increase timeouts for complex analysis
   - Consider async endpoints for long-running tasks

2. **Context Length Management**
   - Set appropriate max_length values
   - Use context chaining for comprehensive analysis
   - Clean and format context text for AI consumption

3. **Error Handling**
   - Implement retry logic for network issues
   - Handle timeout scenarios gracefully
   - Monitor agent run status regularly

4. **Caching**
   - Cache frequently used contexts
   - Store agent run results for reuse
   - Implement context versioning for updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Need help?** Check the examples in `example_context_usage.py` or run the test suite with `python test_context_retrieval.py`.

