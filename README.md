# Unified API System

A consolidated API system that provides a unified interface for OpenAI, Anthropic, and Google APIs with a simple web UI.

## Features

- **Unified API Interface**: Single, consistent interface for all three providers
- **Web UI**: Simple control panel for testing and monitoring
- **Test Suite**: Three focused tests for each provider
- **Simplified Codebase**: Clean, consolidated structure with minimal dependencies

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages: `fastapi`, `uvicorn`, `codegen`, `codegen-api-client`

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

Use the provided start script:

```bash
./start_server.sh
```

This will:
- Start the server on port 8887
- Provide access information for the Web UI and API endpoints
- Run the server in the background

### Accessing the Web UI

Open your browser and navigate to:
```
http://localhost:8887/
```

### API Endpoints

- **OpenAI**: `POST http://localhost:8887/v1/chat/completions`
- **Anthropic**: `POST http://localhost:8887/v1/anthropic/completions`
- **Google**: `POST http://localhost:8887/v1/gemini/generateContent`

### Running Tests

To run all tests:
```bash
python run_tests.py
```

To run individual tests:
```bash
python test_openai_api.py
python test_anthropic_api.py
python test_google_api.py
```

## Project Structure

- `server.py` - FastAPI server with all endpoints
- `client.py` - Unified client for all providers
- `config.py` - Configuration management
- `models.py` - Data models
- `run_tests.py` - Test runner
- `test_openai_api.py` - OpenAI API test
- `test_anthropic_api.py` - Anthropic API test
- `test_google_api.py` - Google API test
- `static/` - Web UI files

## Stopping the Server

To stop the server:
```bash
pkill -f 'python server.py'
```

