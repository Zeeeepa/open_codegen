# OpenAI Codegen Adapter - Simple Setup

## Quick Start

### 1. Start the Server
```bash
python server.py
```
This starts the OpenAI-compatible server at `http://localhost:8887`

### 2. Test the Server
```bash
python test.py
```
This sends a test message using OpenAI client with modified baseURL.

## Files

- **`server.py`** - Starts the FastAPI server
- **`test.py`** - Simple OpenAI client test with modified baseURL
- **`openai_codegen_adapter/`** - Core adapter implementation

## How it Works

1. The server runs on `localhost:8887` and provides OpenAI-compatible endpoints
2. The test uses standard OpenAI Python client but points to our local server
3. Requests are transformed and sent to Codegen API
4. Responses are transformed back to OpenAI format

That's it! 🚀

