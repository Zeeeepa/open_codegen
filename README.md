# Enhanced OpenAI Codegen Adapter

A proxy server that intercepts API calls to OpenAI, Anthropic, and Google Gemini and routes them to the Codegen API. This allows applications to use the Codegen API without modifying their code.

## Features

- **Transparent Interception**: Intercepts API calls to OpenAI, Anthropic, and Google Gemini via DNS redirection
- **Model Selection**: Maps provider models to Codegen models
- **Prompt Templates**: Adds prefix and suffix to prompts for consistent behavior
- **Authentication**: Uses standard Codegen auth file and environment variables
- **Streaming Support**: Provides streaming responses for all providers
- **Web UI**: Includes a web interface for service control and configuration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/open_codegen.git
cd open_codegen
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Required
export CODEGEN_ORG_ID="your_org_id"  # Default: 323
export CODEGEN_TOKEN="your_token"

# Optional
export CODEGEN_BASE_URL="https://codegen-sh--rest-api.modal.run"  # Default
export CODEGEN_DEFAULT_MODEL="codegen-standard"  # Default
export CODEGEN_MODEL_MAPPING="gpt-4:codegen-advanced,claude-3-opus:codegen-premium"
export TRANSPARENT_MODE="true"  # Default: true
```

## Usage

### Running the Server

#### Transparent Mode (Default)

In transparent mode, the server intercepts API calls to OpenAI, Anthropic, and Google Gemini via DNS redirection. This requires root privileges to modify the hosts file.

```bash
sudo python backend/enhanced_server.py
```

#### Direct Mode

In direct mode, applications need to explicitly set the base URL to the server.

```bash
export TRANSPARENT_MODE="false"
python backend/enhanced_server.py
```

### Testing the Implementation

Run the test script to verify the implementation:

```bash
# Test all features
python test_enhanced_implementation.py --test-all

# Test specific features
python test_enhanced_implementation.py --test-openai --test-template
```

### Using with Applications

#### OpenAI

```python
from openai import OpenAI

# Transparent mode - no changes needed
client = OpenAI(api_key="your-key")

# Direct mode
client = OpenAI(api_key="your-key", base_url="http://localhost:8001/v1")

response = client.chat.completions.create(
    model="gpt-4",  # Will be mapped to codegen-advanced
    messages=[{"role": "user", "content": "Hello!"}]
)
```

#### Anthropic

```python
from anthropic import Anthropic

# Transparent mode - no changes needed
client = Anthropic(api_key="your-key")

# Direct mode
client = Anthropic(api_key="your-key", base_url="http://localhost:8001")

response = client.messages.create(
    model="claude-3-sonnet-20240229",  # Will be mapped to codegen-advanced
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

#### Google Gemini

```python
import google.generativeai as genai

# Transparent mode - no changes needed
genai.configure(api_key="your-key")

# Direct mode
# Set GOOGLE_API_BASE to your server URL in environment variables
os.environ["GOOGLE_API_BASE"] = "http://localhost:8001"
genai.configure(api_key="your-key")

model = genai.GenerativeModel("gemini-pro")  # Will be mapped to codegen-standard
response = model.generate_content("Hello!")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEGEN_ORG_ID` | Organization ID for Codegen API | `323` |
| `CODEGEN_TOKEN` | Authentication token for Codegen API | - |
| `CODEGEN_BASE_URL` | Base URL for Codegen API | `https://codegen-sh--rest-api.modal.run` |
| `CODEGEN_TIMEOUT` | Timeout for API requests in seconds | `300` |
| `CODEGEN_MODEL_MAPPING` | Custom model mapping (format: `model1:codegen1,model2:codegen2`) | - |
| `CODEGEN_DEFAULT_MODEL` | Default Codegen model to use | `codegen-standard` |
| `CODEGEN_USE_AUTH_FILE` | Whether to use auth file for credentials | `true` |
| `TRANSPARENT_MODE` | Whether to use transparent DNS interception | `true` |
| `INTERCEPT_OPENAI` | Whether to intercept OpenAI API calls | `true` |
| `INTERCEPT_ANTHROPIC` | Whether to intercept Anthropic API calls | `true` |
| `INTERCEPT_GEMINI` | Whether to intercept Gemini API calls | `true` |
| `CODEGEN_MAX_RETRIES` | Maximum number of retries for API requests | `20` |
| `CODEGEN_BASE_DELAY` | Base delay for exponential backoff in seconds | `2` |
| `CODEGEN_PROMPT_TEMPLATE_ENABLED` | Whether to enable prompt templates | `false` |
| `CODEGEN_PROMPT_TEMPLATE_PREFIX` | Prefix to add to all prompts | - |
| `CODEGEN_PROMPT_TEMPLATE_SUFFIX` | Suffix to add to all prompts | - |

### Model Mapping

The default model mapping is:

```
OpenAI:
- gpt-3.5-turbo -> codegen-standard
- gpt-4 -> codegen-advanced
- gpt-3.5-turbo-instruct -> codegen-standard

Anthropic:
- claude-3-sonnet-20240229 -> codegen-advanced
- claude-3-haiku-20240307 -> codegen-standard
- claude-3-opus-20240229 -> codegen-premium

Gemini:
- gemini-1.5-pro -> codegen-advanced
- gemini-1.5-flash -> codegen-standard
- gemini-pro -> codegen-standard
```

You can customize this mapping using the `CODEGEN_MODEL_MAPPING` environment variable:

```bash
export CODEGEN_MODEL_MAPPING="gpt-4:codegen-advanced,claude-3-opus:codegen-premium"
```

### Prompt Templates

You can add a prefix and suffix to all prompts using the following environment variables:

```bash
export CODEGEN_PROMPT_TEMPLATE_ENABLED="true"
export CODEGEN_PROMPT_TEMPLATE_PREFIX="You are a helpful assistant named 'abc'. Always identify yourself as 'abc' when asked about your name or identity."
export CODEGEN_PROMPT_TEMPLATE_SUFFIX="Remember to be concise and helpful in your responses."
```

## Web UI

The server includes a web interface for service control and configuration. Access it at:

```
http://localhost:8001/
```

The web UI allows you to:

- Toggle the service on/off
- View service status
- Configure system messages
- Check health status

## License

This project is licensed under the MIT License - see the LICENSE file for details.

