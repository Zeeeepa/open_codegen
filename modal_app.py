"""
Modal deployment configuration for the OpenAI Codegen Adapter.
Supports OpenAI, Anthropic, and Google Gemini APIs with environment-aware base URLs.
"""

import modal
import os
from pathlib import Path

# Create Modal app
app = modal.App("openai-codegen-adapter")

# Define the container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "python-dotenv",
        "httpx",
        "aiofiles",
        "python-multipart"
    ])
    .copy_local_dir("openai_codegen_adapter", "/app/openai_codegen_adapter")
    .copy_local_file("server.py", "/app/server.py")
    .copy_local_file(".env.example", "/app/.env.example")
)

# Mount for configuration files
config_mount = modal.Mount.from_local_dir(
    ".",
    remote_path="/app",
    condition=lambda pth: pth.suffix in [".py", ".env"]
)

@app.function(
    image=image,
    mounts=[config_mount],
    secrets=[
        modal.Secret.from_name("codegen-secrets"),  # Contains CODEGEN_ORG_ID and CODEGEN_TOKEN
    ],
    allow_concurrent_inputs=100,
    timeout=300,
    cpu=2,
    memory=1024
)
@modal.asgi_app()
def fastapi_app():
    """
    Create and configure the FastAPI app for Modal deployment.
    """
    import sys
    sys.path.append("/app")
    
    from openai_codegen_adapter.server import app as fastapi_app
    from openai_codegen_adapter.config import get_server_config
    
    # Configure for Modal deployment
    server_config = get_server_config()
    
    # Override host and port for Modal
    server_config.host = "0.0.0.0"
    server_config.port = 8000  # Modal uses port 8000
    
    return fastapi_app


@app.local_entrypoint()
def deploy():
    """
    Deploy the app to Modal.
    """
    print("🚀 Deploying OpenAI Codegen Adapter to Modal...")
    print("📋 Supported APIs:")
    print("   • OpenAI Compatible: /v1/chat/completions, /v1/completions")
    print("   • Anthropic Compatible: /v1/messages, /v1/anthropic/completions")
    print("   • Google Gemini Compatible: /v1/gemini/generateContent, /v1/gemini/completions")
    print("   • Models List: /v1/models")
    print("   • Health Check: /health")
    print("\n✅ Deployment complete! Your app is now available at the Modal URL.")
    print("💡 Use the Modal URL as your base_url for all three API clients.")


if __name__ == "__main__":
    # For local development, you can run this to deploy
    deploy.remote()

