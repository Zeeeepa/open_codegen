#!/usr/bin/env python3
"""
Demo script for the Web UI functionality.
Shows how to start the server and access the Web UI.
Creates a Gradio interface on port 7860 that connects to the main server on port 8001.
"""

import subprocess
import time
import webbrowser
import os
import signal
import sys
import requests
import json
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    print("⚠️  Gradio not installed. Install with: pip install gradio")

def test_openai_api(message, model="gpt-3.5-turbo", max_tokens=100):
    """Test the OpenAI API endpoint."""
    try:
        response = requests.post(
            "http://localhost:8001/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": max_tokens
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-key"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def test_anthropic_api(message, model="claude-3-sonnet-20240229", max_tokens=100):
    """Test the Anthropic API endpoint."""
    try:
        response = requests.post(
            "http://localhost:8001/v1/messages",
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": max_tokens
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-key"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"]
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def test_gemini_api(message, max_tokens=100):
    """Test the Gemini API endpoint."""
    try:
        response = requests.post(
            "http://localhost:8001/v1/gemini/completions",
            json={
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {"maxOutputTokens": max_tokens}
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-key"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_server_status():
    """Get the server status."""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            return "🟢 Server is running"
        else:
            return f"🔴 Server error: HTTP {response.status_code}"
    except Exception as e:
        return f"🔴 Server not reachable: {str(e)}"

def create_gradio_interface():
    """Create the Gradio interface."""
    if not GRADIO_AVAILABLE:
        return None
    
    with gr.Blocks(title="OpenAI Codegen Adapter - Web UI Demo") as demo:
        gr.Markdown("# 🚀 OpenAI Codegen Adapter - Web UI Demo")
        gr.Markdown("Test the routing server that connects multiple AI providers to Codegen SDK")
        
        # Server status
        with gr.Row():
            status_btn = gr.Button("Check Server Status", variant="secondary")
            status_output = gr.Textbox(label="Server Status", interactive=False)
        
        status_btn.click(get_server_status, outputs=status_output)
        
        # API Testing Tabs
        with gr.Tabs():
            # OpenAI Tab
            with gr.TabItem("OpenAI API"):
                gr.Markdown("### Test OpenAI-compatible endpoint")
                with gr.Row():
                    with gr.Column():
                        openai_input = gr.Textbox(
                            label="Message", 
                            placeholder="Enter your message here...",
                            value="Hello! What can you help me with?"
                        )
                        openai_model = gr.Dropdown(
                            choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                            value="gpt-3.5-turbo",
                            label="Model"
                        )
                        openai_tokens = gr.Slider(10, 500, value=100, label="Max Tokens")
                        openai_btn = gr.Button("Test OpenAI API", variant="primary")
                    with gr.Column():
                        openai_output = gr.Textbox(label="Response", lines=10)
                
                openai_btn.click(
                    test_openai_api,
                    inputs=[openai_input, openai_model, openai_tokens],
                    outputs=openai_output
                )
            
            # Anthropic Tab
            with gr.TabItem("Anthropic API"):
                gr.Markdown("### Test Anthropic Claude endpoint")
                with gr.Row():
                    with gr.Column():
                        anthropic_input = gr.Textbox(
                            label="Message", 
                            placeholder="Enter your message here...",
                            value="Hello! What can you help me with?"
                        )
                        anthropic_model = gr.Dropdown(
                            choices=["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                            value="claude-3-sonnet-20240229",
                            label="Model"
                        )
                        anthropic_tokens = gr.Slider(10, 500, value=100, label="Max Tokens")
                        anthropic_btn = gr.Button("Test Anthropic API", variant="primary")
                    with gr.Column():
                        anthropic_output = gr.Textbox(label="Response", lines=10)
                
                anthropic_btn.click(
                    test_anthropic_api,
                    inputs=[anthropic_input, anthropic_model, anthropic_tokens],
                    outputs=anthropic_output
                )
            
            # Gemini Tab
            with gr.TabItem("Gemini API"):
                gr.Markdown("### Test Google Gemini endpoint")
                with gr.Row():
                    with gr.Column():
                        gemini_input = gr.Textbox(
                            label="Message", 
                            placeholder="Enter your message here...",
                            value="Hello! What can you help me with?"
                        )
                        gemini_tokens = gr.Slider(10, 500, value=100, label="Max Tokens")
                        gemini_btn = gr.Button("Test Gemini API", variant="primary")
                    with gr.Column():
                        gemini_output = gr.Textbox(label="Response", lines=10)
                
                gemini_btn.click(
                    test_gemini_api,
                    inputs=[gemini_input, gemini_tokens],
                    outputs=gemini_output
                )
        
        # API Information
        gr.Markdown("""
        ### 🔗 API Endpoints
        - **OpenAI**: `POST http://localhost:8001/v1/chat/completions`
        - **Anthropic**: `POST http://localhost:8001/v1/messages`
        - **Gemini**: `POST http://localhost:8001/v1/gemini/completions`
        - **Health**: `GET http://localhost:8001/health`
        - **Status**: `GET http://localhost:8001/api/status`
        """)
    
    return demo

def main():
    """Demo the Web UI functionality."""
    print("🚀 OpenAI Codegen Adapter - Web UI Demo")
    print("=" * 50)
    
    # Set environment variables
    os.environ['CODEGEN_ORG_ID'] = "323"
    os.environ['CODEGEN_TOKEN'] = "sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
    
    print("📋 Starting the OpenAI Codegen Adapter server...")
    print("🔗 Server will be available at: http://localhost:8001")
    print("🎛️ Web UI will be available at: http://localhost:7860")
    print("📡 API endpoints at: http://localhost:8001/v1")
    print()
    
    try:
        # Start the server
        process = subprocess.Popen(
            ["python3", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Launch Gradio interface if available
        if GRADIO_AVAILABLE:
            print("🎛️ Starting Gradio Web UI on port 7860...")
            demo = create_gradio_interface()
            if demo:
                # Launch Gradio in a separate thread
                demo.launch(
                    server_name="0.0.0.0",
                    server_port=7860,
                    share=False,
                    inbrowser=True,
                    prevent_thread_lock=True
                )
                print("✅ Gradio Web UI started at: http://localhost:7860")
            else:
                print("❌ Failed to create Gradio interface")
        else:
            print("⚠️  Gradio not available, opening static Web UI...")
            webbrowser.open("http://localhost:8001")
        
        print()
        print("✅ Server is running!")
        print("📖 Web UI Features:")
        print("   • Real-time service status (ON/OFF)")
        print("   • Toggle button to enable/disable service")
        print("   • Health monitoring")
        print("   • Beautiful, responsive interface")
        print()
        print("🎯 Try these actions in the Web UI:")
        print("   1. View the current service status")
        print("   2. Click 'Turn Off' to disable the service")
        print("   3. Click 'Turn On' to re-enable the service")
        print("   4. Watch the real-time status updates")
        print()
        print("🔧 API Testing:")
        print("   • Status: curl http://localhost:8001/api/status")
        print("   • Toggle: curl -X POST http://localhost:8001/api/toggle")
        print("   • Health: curl http://localhost:8001/health")
        print()
        print("Press Ctrl+C to stop the server...")
        
        # Keep the server running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Server stopped successfully!")
            
    except FileNotFoundError:
        print("❌ Error: Could not find server.py")
        print("   Make sure you're in the correct directory")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
