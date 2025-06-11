# OpenAI Codegen Adapter

A unified API server that routes OpenAI, Anthropic, and Google API requests to the Codegen SDK.

## Features

- OpenAI-compatible API endpoints
- Anthropic Claude API compatibility
- Google Gemini API compatibility
- Web UI for testing and configuration
- Direct integration with Codegen SDK

## Setup

1. Clone this repository
2. Create a `.env` file with your Codegen credentials:

```
CODEGEN_ORG_ID=your_org_id_here
CODEGEN_TOKEN=sk-your-codegen-token-here
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the server:

```bash
python server.py
```

Or use the provided script:

```bash
./start_server.sh
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| CODEGEN_ORG_ID | Your Codegen organization ID | (required) |
| CODEGEN_TOKEN | Your Codegen API token | (required) |
| SERVER_HOST | Host to bind the server to | localhost |
| SERVER_PORT | Port to run the server on | 8887 |
| LOG_LEVEL | Logging level | info |

## API Endpoints

### OpenAI

- **POST** `/v1/chat/completions` - OpenAI chat completions API

### Anthropic

- **POST** `/v1/anthropic/completions` - Anthropic completions API

### Google

- **POST** `/v1/gemini/completions` - Google Gemini completions API
- **POST** `/v1/gemini/generateContent` - Google Gemini generateContent API

## Using with Existing Applications

### OpenAI

```
OPENAI_API_BASE=http://localhost:8887/v1
```

### Anthropic

```
ANTHROPIC_API_URL=http://localhost:8887/v1
```

### Google

```
GEMINI_API_URL=http://localhost:8887/v1
```

## Testing

Run the included test scripts:

```bash
./test_openai.py
./test_anthropic.py
./test_google.py
```

## How It Works

This server acts as a proxy that:

1. Receives API requests in OpenAI, Anthropic, or Google format
2. Extracts the prompt/message content
3. Uses the Codegen SDK to process the request
4. Formats the response back into the appropriate API format

## License

MIT

