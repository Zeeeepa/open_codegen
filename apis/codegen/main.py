#!/usr/bin/env python3
"""
Codegen API Service - 15th API Implementation
Provides OpenAI-compatible interface to Codegen functionality
"""

import os
import json
from flask import Flask, request, jsonify, Response
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock Codegen functionality for now
class CodegenAPI:
    """Simple Codegen API wrapper"""
    
    def __init__(self):
        self.model = "codegen-v1"
        self.version = "1.0.0"
    
    def chat_completion(self, messages, model="codegen-v1", stream=False, **kwargs):
        """Generate code completion response"""
        
        # Extract the user's request
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Simple mock response for now
        response_content = f"""I understand you want help with: "{user_message}"

As Codegen, I can help you with:
- Code generation and analysis
- Bug fixes and improvements  
- Architecture recommendations
- Code reviews and optimization

This is a mock response from the Codegen API service. In a full implementation, this would connect to the actual Codegen backend to provide intelligent code assistance.

Would you like me to help you with a specific coding task?"""

        if stream:
            return self._stream_response(response_content)
        else:
            return {
                "id": f"codegen-{datetime.now().timestamp()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response_content.split()),
                    "total_tokens": len(user_message.split()) + len(response_content.split())
                }
            }
    
    def _stream_response(self, content):
        """Generate streaming response"""
        words = content.split()
        for i, word in enumerate(words):
            chunk = {
                "id": f"codegen-{datetime.now().timestamp()}",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": self.model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": word + " " if i < len(words) - 1 else word
                    },
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        
        yield "data: [DONE]\n\n"

# Initialize Codegen API
codegen_api = CodegenAPI()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "codegen-api",
        "version": codegen_api.version,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Codegen API Service",
        "version": codegen_api.version,
        "endpoints": [
            "/health",
            "/v1/chat/completions",
            "/v1/models"
        ]
    })

@app.route('/v1/models')
def models():
    """List available models"""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "codegen-v1",
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": "codegen",
            "permission": [],
            "root": "codegen-v1",
            "parent": None
        }]
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        messages = data.get('messages', [])
        model = data.get('model', 'codegen-v1')
        stream = data.get('stream', False)
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        logger.info(f"Chat completion request: {len(messages)} messages, model: {model}, stream: {stream}")
        
        if stream:
            def generate():
                for chunk in codegen_api.chat_completion(messages, model, stream=True):
                    yield chunk
            
            return Response(generate(), mimetype='text/plain')
        else:
            response = codegen_api.chat_completion(messages, model, stream=False)
            return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in chat completions: {str(e)}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": "internal_error"
            }
        }), 500

@app.route('/v1/completions', methods=['POST'])
def completions():
    """Legacy completions endpoint"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        # Convert to chat format
        messages = [{"role": "user", "content": prompt}]
        response = codegen_api.chat_completion(messages)
        
        # Convert back to completions format
        return jsonify({
            "id": response["id"],
            "object": "text_completion",
            "created": response["created"],
            "model": response["model"],
            "choices": [{
                "text": response["choices"][0]["message"]["content"],
                "index": 0,
                "finish_reason": "stop"
            }],
            "usage": response["usage"]
        })
    
    except Exception as e:
        logger.error(f"Error in completions: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8014))  # Default to port 8014 for Codegen
    logger.info(f"Starting Codegen API service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
