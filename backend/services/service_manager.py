#!/usr/bin/env python3
"""
Service Manager for AI Provider Services
Manages starting, stopping, and monitoring all 14 AI provider services
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

from backend.registry.service_registry import service_registry, ServiceStatus, ServiceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages lifecycle of all AI provider services"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_registry = service_registry
        self.startup_timeout = 30  # seconds
        self.shutdown_timeout = 10  # seconds
        
    async def install_dependencies(self, service_name: str) -> bool:
        """Install dependencies for a service"""
        service = self.service_registry.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False
        
        working_dir = Path(service.working_directory)
        if not working_dir.exists():
            logger.error(f"Working directory {working_dir} does not exist")
            return False
        
        try:
            if service.service_type == ServiceType.PYTHON:
                # Check for requirements.txt
                requirements_file = working_dir / "requirements.txt"
                if requirements_file.exists():
                    logger.info(f"Installing Python dependencies for {service_name}...")
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                    ], cwd=working_dir, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to install dependencies for {service_name}: {result.stderr}")
                        return False
                    
            elif service.service_type == ServiceType.GO:
                # Install Go dependencies
                logger.info(f"Installing Go dependencies for {service_name}...")
                result = subprocess.run([
                    "go", "mod", "tidy"
                ], cwd=working_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to install Go dependencies for {service_name}: {result.stderr}")
                    return False
                    
            elif service.service_type in [ServiceType.TYPESCRIPT, ServiceType.NODE]:
                # Install Node.js dependencies
                package_json = working_dir / "package.json"
                if package_json.exists():
                    logger.info(f"Installing Node.js dependencies for {service_name}...")
                    result = subprocess.run([
                        "npm", "install"
                    ], cwd=working_dir, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to install Node.js dependencies for {service_name}: {result.stderr}")
                        return False
            
            logger.info(f"Dependencies installed successfully for {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies for {service_name}: {e}")
            return False
    
    async def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        service = self.service_registry.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False
        
        if service_name in self.processes:
            logger.warning(f"Service {service_name} is already running")
            return True
        
        # Update status to starting
        self.service_registry.update_service_status(service_name, ServiceStatus.STARTING)
        
        try:
            # Install dependencies first
            if not await self.install_dependencies(service_name):
                self.service_registry.update_service_status(service_name, ServiceStatus.ERROR)
                return False
            
            # Prepare environment
            env = os.environ.copy()
            env["PORT"] = str(service.port)
            
            # Set up command
            command_parts = service.start_command.split()
            working_dir = Path(service.working_directory)
            
            logger.info(f"Starting {service_name} on port {service.port}...")
            logger.info(f"Command: {service.start_command}")
            logger.info(f"Working directory: {working_dir}")
            
            # Start the process
            process = subprocess.Popen(
                command_parts,
                cwd=working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[service_name] = process
            
            # Wait a bit for the service to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"Service {service_name} started successfully (PID: {process.pid})")
                
                # Wait for health check to pass
                max_attempts = 15
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)
                    if await self.service_registry.health_check_service(service):
                        logger.info(f"Service {service_name} is healthy")
                        return True
                    logger.info(f"Waiting for {service_name} to become healthy... ({attempt + 1}/{max_attempts})")
                
                logger.warning(f"Service {service_name} started but health check failed")
                self.service_registry.update_service_status(service_name, ServiceStatus.UNHEALTHY)
                return True  # Process started even if health check failed
                
            else:
                # Process died immediately
                stdout, stderr = process.communicate()
                logger.error(f"Service {service_name} failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                self.service_registry.update_service_status(service_name, ServiceStatus.ERROR)
                if service_name in self.processes:
                    del self.processes[service_name]
                return False
                
        except Exception as e:
            logger.error(f"Error starting service {service_name}: {e}")
            self.service_registry.update_service_status(service_name, ServiceStatus.ERROR)
            if service_name in self.processes:
                del self.processes[service_name]
            return False
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop a single service"""
        if service_name not in self.processes:
            logger.warning(f"Service {service_name} is not running")
            self.service_registry.update_service_status(service_name, ServiceStatus.STOPPED)
            return True
        
        try:
            process = self.processes[service_name]
            logger.info(f"Stopping service {service_name} (PID: {process.pid})...")
            
            # Try graceful shutdown first
            process.terminate()
            
            try:
                # Wait for graceful shutdown
                process.wait(timeout=self.shutdown_timeout)
                logger.info(f"Service {service_name} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                logger.warning(f"Force killing service {service_name}")
                process.kill()
                process.wait()
            
            del self.processes[service_name]
            self.service_registry.update_service_status(service_name, ServiceStatus.STOPPED)
            return True
            
        except Exception as e:
            logger.error(f"Error stopping service {service_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a single service"""
        logger.info(f"Restarting service {service_name}...")
        await self.stop_service(service_name)
        await asyncio.sleep(1)
        return await self.start_service(service_name)
    
    async def start_all_services(self) -> Dict[str, bool]:
        """Start all services"""
        logger.info("🚀 Starting all AI provider services...")
        
        services = self.service_registry.get_all_services()
        results = {}
        
        # Start services in batches to avoid overwhelming the system
        batch_size = 3
        service_names = list(services.keys())
        
        for i in range(0, len(service_names), batch_size):
            batch = service_names[i:i + batch_size]
            logger.info(f"Starting batch {i//batch_size + 1}: {batch}")
            
            # Start batch concurrently
            tasks = [self.start_service(name) for name in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(batch, batch_results):
                results[name] = result if not isinstance(result, Exception) else False
                if isinstance(result, Exception):
                    logger.error(f"Exception starting {name}: {result}")
            
            # Wait between batches
            if i + batch_size < len(service_names):
                logger.info("Waiting before starting next batch...")
                await asyncio.sleep(5)
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"✅ Started {successful}/{total} services successfully")
        
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services"""
        logger.info("🛑 Stopping all AI provider services...")
        
        service_names = list(self.processes.keys())
        results = {}
        
        # Stop all services concurrently
        tasks = [self.stop_service(name) for name in service_names]
        stop_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(service_names, stop_results):
            results[name] = result if not isinstance(result, Exception) else False
            if isinstance(result, Exception):
                logger.error(f"Exception stopping {name}: {result}")
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"✅ Stopped {successful}/{total} services successfully")
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {}
        
        for name, service in self.service_registry.get_all_services().items():
            process_info = None
            if name in self.processes:
                process = self.processes[name]
                try:
                    ps_process = psutil.Process(process.pid)
                    process_info = {
                        "pid": process.pid,
                        "cpu_percent": ps_process.cpu_percent(),
                        "memory_mb": ps_process.memory_info().rss / 1024 / 1024,
                        "status": ps_process.status()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_info = {"pid": process.pid, "status": "unknown"}
            
            status[name] = {
                "service_status": service.status.value,
                "port": service.port,
                "response_time": service.response_time,
                "error_count": service.error_count,
                "last_health_check": service.last_health_check,
                "process_info": process_info
            }
        
        return status
    
    async def health_monitor_loop(self):
        """Continuous health monitoring loop"""
        logger.info("Starting health monitoring loop...")
        
        while True:
            try:
                # Check health of all services
                await self.service_registry.health_check_all_services()
                
                # Restart unhealthy services if needed
                for name, service in self.service_registry.get_all_services().items():
                    if service.status == ServiceStatus.ERROR and service.error_count > 3:
                        logger.warning(f"Service {name} has too many errors, attempting restart...")
                        await self.restart_service(name)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop_all_services())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

# Global service manager instance
service_manager = ServiceManager()

async def main():
    """Main function for testing"""
    logger.info("🚀 Service Manager Test")
    
    # Setup signal handlers
    service_manager.setup_signal_handlers()
    
    # Start all services
    results = await service_manager.start_all_services()
    
    # Print status
    status = service_manager.get_service_status()
    for name, info in status.items():
        logger.info(f"{name}: {info['service_status']} on port {info['port']}")
    
    # Start health monitoring
    await service_manager.health_monitor_loop()

if __name__ == "__main__":
    asyncio.run(main())
