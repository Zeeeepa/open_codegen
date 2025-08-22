#!/usr/bin/env python3
"""
Example Anthropic API call that will be intercepted by the OpenAI Codegen Adapter.
"""

import anthropic
import os

# Set environment variable to point to our local server
os.environ["ANTHROPIC_API_BASE"] = "http://127.0.0.1:8001"

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)
message = client.messages.create(
    model="claude-opus-4-1-20250805",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude"}
    ]
)
print(message.content)
