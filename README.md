# Open Codegen - Unified API System

A simple, unified system for accessing OpenAI, Anthropic, and Google APIs through a single interface.

## Features

- **Unified Interface**: Single server handling all three major AI providers
- **Simple Names**: Clean, straightforward file structure
- **Web UI Access**: All APIs accessible via HTTP endpoints
- **Comprehensive Testing**: 3 focused tests covering all providers

## Quick Start

1. **Start the server:**
   ```bash
   python server.py
   ```

2. **Run all tests:**
   ```bash
   python run_tests.py
   ```

## API Endpoints

### OpenAI API
- **Endpoint**: `POST /v1/chat/completions`
- **Format**: Standard OpenAI chat completions format

### Anthropic API  
- **Endpoint**: `POST /v1/anthropic/completions`
- **Format**: Anthropic messages format

### Google API
- **Endpoint**: `POST /v1/gemini/generateContent`
- **Format**: Google Gemini format

## Testing

The system includes 3 simple tests:

1. **`test_openai_api.py`** - Tests OpenAI message sending/receiving
2. **`test_anthropic_api.py`** - Tests Anthropic message sending/receiving  
3. **`test_google_api.py`** - Tests Google message sending/receiving

Run individual tests:
```bash
python test_openai_api.py
python test_anthropic_api.py
python test_google_api.py
```

Or run all tests at once:
```bash
python run_tests.py
```

## Architecture

- **`server.py`** - Main server entry point
- **`openai_codegen_adapter/`** - Core adapter implementation
- **Unified routing** through Codegen SDK
- **Simple, clean codebase** with minimal complexity

## Health Check

Check if the server is running:
```bash
curl http://localhost:8887/health
```

All endpoints are accessible via the web interface and return proper JSON responses with token usage statistics.

