# API Router System

A unified API router that allows you to use the Codegen SDK with applications designed for OpenAI, Anthropic, and Google APIs.

## What This Does

This system acts as a proxy/router that:

1. Accepts requests in the format of OpenAI, Anthropic, or Google APIs
2. Routes these requests to the Codegen SDK
3. Transforms the Codegen SDK responses back into the format expected by the original API client

## Key Features

- **Zero Configuration**: No API keys required
- **Drop-in Replacement**: Works with existing applications by just changing the API URL
- **Multiple API Formats**: Supports OpenAI, Anthropic, and Google/Gemini API formats
- **Web UI**: Includes a simple web interface for testing

## How to Use

### 1. Start the Server

```bash
./start_server.sh
```

The server will start on port 8887 by default.

### 2. Configure Your Applications

In your applications that use OpenAI, Anthropic, or Google APIs, simply change the API base URL to point to this server:

#### OpenAI

```
OPENAI_API_BASE=http://localhost:8887/v1
```

#### Anthropic

```
ANTHROPIC_API_URL=http://localhost:8887/v1
```

#### Google/Gemini

```
GEMINI_API_URL=http://localhost:8887/v1
```

### 3. That's It!

Your applications will now send requests to this router, which will forward them to the Codegen SDK and return responses in the expected format.

## Supported Endpoints

- **OpenAI**: `/v1/chat/completions`
- **Anthropic**: `/v1/anthropic/completions` and `/v1/messages`
- **Google/Gemini**: `/v1/gemini/completions` and `/v1/gemini/generateContent`

## Configuration

By default, the router will send requests to the Codegen SDK at `http://localhost:8000/api/generate`. You can change this by setting the `CODEGEN_API_URL` environment variable:

```bash
export CODEGEN_API_URL=http://your-codegen-sdk-url/api/generate
./start_server.sh
```

## Web UI

The system includes a web UI for testing, which you can access at:

```
http://localhost:8887/
```

This UI allows you to:
- Check the server health
- Test requests to all three API formats
- View the responses in real-time

## How It Works

1. When a request comes in to one of the API endpoints, the router extracts the prompt/message
2. The router sends this prompt to the Codegen SDK
3. When the Codegen SDK responds, the router formats the response to match what the original API client expects
4. The formatted response is returned to the client

This allows applications designed to work with OpenAI, Anthropic, or Google APIs to seamlessly use the Codegen SDK instead, with no code changes required beyond changing the API URL.

