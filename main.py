#!/usr/bin/env python3
"""
Unified AI Provider Gateway - Simple UI-First Entry Point
Just run: python main.py
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state for API services
api_services = {}
api_processes = {}

class APIService:
    """Simple wrapper for each API service"""
    
    def __init__(self, name, path, entry_point, port, service_type="python"):
        self.name = name
        self.path = path
        self.entry_point = entry_point
        self.port = port
        self.service_type = service_type
        self.status = "stopped"
        self.process = None
        self.last_test = None
        
    def start(self):
        """Start the API service"""
        try:
            if self.process and self.process.poll() is None:
                return {"success": False, "message": "Service already running"}
            
            # Change to service directory
            service_dir = Path(self.path)
            if not service_dir.exists():
                return {"success": False, "message": f"Service directory not found: {self.path}"}
            
            # Determine command based on service type
            if self.service_type == "python":
                cmd = [sys.executable, self.entry_point]
            elif self.service_type == "go":
                cmd = ["go", "run", self.entry_point]
            elif self.service_type == "node":
                cmd = ["node", self.entry_point]
            else:
                return {"success": False, "message": f"Unknown service type: {self.service_type}"}
            
            # Set environment variable for port
            env = os.environ.copy()
            env["PORT"] = str(self.port)
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.status = "starting"
            logger.info(f"Started {self.name} on port {self.port} (PID: {self.process.pid})")
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if self.process.poll() is None:
                self.status = "running"
                return {"success": True, "message": f"Service started on port {self.port}"}
            else:
                stdout, stderr = self.process.communicate()
                self.status = "error"
                return {"success": False, "message": f"Service failed to start: {stderr}"}
                
        except Exception as e:
            self.status = "error"
            return {"success": False, "message": f"Error starting service: {str(e)}"}
    
    def stop(self):
        """Stop the API service"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.status = "stopped"
                logger.info(f"Stopped {self.name}")
                return {"success": True, "message": "Service stopped"}
            else:
                self.status = "stopped"
                return {"success": True, "message": "Service was not running"}
        except Exception as e:
            return {"success": False, "message": f"Error stopping service: {str(e)}"}
    
    def test(self):
        """Test the API service"""
        try:
            import requests
            
            # Try to make a simple request to the service
            test_url = f"http://localhost:{self.port}/health"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                self.last_test = {"success": True, "response_time": response.elapsed.total_seconds()}
                return {"success": True, "message": "Service is healthy", "response_time": response.elapsed.total_seconds()}
            else:
                self.last_test = {"success": False, "status_code": response.status_code}
                return {"success": False, "message": f"Service returned status {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            # Try alternative endpoint
            try:
                test_url = f"http://localhost:{self.port}/"
                response = requests.get(test_url, timeout=5)
                self.last_test = {"success": True, "response_time": response.elapsed.total_seconds()}
                return {"success": True, "message": "Service is responding", "response_time": response.elapsed.total_seconds()}
            except:
                self.last_test = {"success": False, "error": "Connection refused"}
                return {"success": False, "message": "Service is not responding"}
        except Exception as e:
            self.last_test = {"success": False, "error": str(e)}
            return {"success": False, "message": f"Test failed: {str(e)}"}
    
    def get_status(self):
        """Get current status"""
        if self.process and self.process.poll() is None:
            self.status = "running"
        elif self.status == "running":
            self.status = "stopped"
        
        return {
            "name": self.name,
            "status": self.status,
            "port": self.port,
            "type": self.service_type,
            "last_test": self.last_test
        }

def discover_apis():
    """Discover available API services"""
    apis_dir = Path("apis")
    if not apis_dir.exists():
        logger.warning("APIs directory not found")
        return {}
    
    services = {}
    port = 8000
    
    # Known API configurations (15 APIs total)
    api_configs = [
        {"name": "k2think2api3", "entry": "k2think_proxy.py", "type": "python"},
        {"name": "k2think2api2", "entry": "main.py", "type": "python"},
        {"name": "k2Think2Api", "entry": "main.py", "type": "python"},
        {"name": "grok2api", "entry": "app.py", "type": "python"},
        {"name": "OpenAI-Compatible-API-Proxy-for-Z", "entry": "main.go", "type": "go"},
        {"name": "Z.ai2api", "entry": "app.py", "type": "python"},
        {"name": "z.ai2api_python", "entry": "main.py", "type": "python"},
        {"name": "ZtoApi", "entry": "main.go", "type": "go"},
        {"name": "zai-python-sdk", "entry": "client.py", "type": "python"},
        {"name": "ZtoApits", "entry": "index.js", "type": "node"},
        {"name": "qwen-api", "entry": "main.py", "type": "python"},
        {"name": "qwenchat2api", "entry": "main.py", "type": "python"},
        {"name": "codegen", "entry": "main.py", "type": "python"},  # 15th API - Codegen
    ]
    
    for config in api_configs:
        api_path = apis_dir / config["name"]
        entry_file = api_path / config["entry"]
        
        if api_path.exists() and entry_file.exists():
            service = APIService(
                name=config["name"],
                path=str(api_path),
                entry_point=config["entry"],
                port=port,
                service_type=config["type"]
            )
            services[config["name"]] = service
            port += 1
            logger.info(f"Discovered API: {config['name']} -> {entry_file}")
        else:
            logger.warning(f"API not found or missing entry point: {config['name']}")
    
    return services

# Web Routes
@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/services')
def get_services():
    """Get all services status"""
    services_status = {}
    for name, service in api_services.items():
        services_status[name] = service.get_status()
    return jsonify(services_status)

@app.route('/api/services/<service_name>/start', methods=['POST'])
def start_service(service_name):
    """Start a specific service"""
    if service_name not in api_services:
        return jsonify({"success": False, "message": "Service not found"}), 404
    
    result = api_services[service_name].start()
    return jsonify(result)

@app.route('/api/services/<service_name>/stop', methods=['POST'])
def stop_service(service_name):
    """Stop a specific service"""
    if service_name not in api_services:
        return jsonify({"success": False, "message": "Service not found"}), 404
    
    result = api_services[service_name].stop()
    return jsonify(result)

@app.route('/api/services/<service_name>/test', methods=['POST'])
def test_service(service_name):
    """Test a specific service"""
    if service_name not in api_services:
        return jsonify({"success": False, "message": "Service not found"}), 404
    
    result = api_services[service_name].test()
    return jsonify(result)

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def create_directories():
    """Create necessary directories"""
    directories = ['templates', 'static', 'logs', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    """Main entry point"""
    print("🚀 Unified AI Provider Gateway")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Discover APIs
    global api_services
    api_services = discover_apis()
    
    print(f"📋 Discovered {len(api_services)} API services:")
    for name, service in api_services.items():
        print(f"   • {name} ({service.service_type}) -> Port {service.port}")
    
    print("\n🌐 Starting web interface...")
    print("   Dashboard: http://localhost:5000")
    print("   Press Ctrl+C to stop")
    
    # Start Flask app
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        # Stop all running services
        for service in api_services.values():
            if service.status == "running":
                service.stop()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
