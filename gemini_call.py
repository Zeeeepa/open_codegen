#!/usr/bin/env python3
"""
Example Google Gemini API call that will be intercepted by the OpenAI Codegen Adapter.
"""

import google.generativeai as genai
import os

# Set environment variable to point to our local server
os.environ["GEMINI_API_BASE"] = "http://127.0.0.1:8001"

# Configure the Gemini API
genai.configure(api_key="my_api_key")

# Create a model instance
model = genai.GenerativeModel(model_name="gemini-ultra-2025-08-01")

# Generate content
response = model.generate_content("Hello, Gemini")

print(response.text)
