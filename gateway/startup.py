"""
System initialization and startup management
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from config.config_manager import ConfigManager
from providers.provider_manager import ProviderManager

logger = logging.getLogger(__name__)

class SystemInitializer:
    """Handles system initialization and startup."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.provider_manager = None
        self.api_gateway = None
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "httpx",
            "websockets",
            "jinja2",
            "python-multipart",
            "pydantic",
            "aiofiles"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("📦 Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ All dependencies satisfied")
        return True
    
    def validate_config(self) -> bool:
        """Validate system configuration."""
        
        try:
            # Load configuration
            config = self.config_manager.load_config()
            
            # Check required settings
            if not config.get("providers"):
                logger.error("No providers configured")
                return False
            
            # Validate provider configurations
            for provider_name, provider_config in config["providers"].items():
                if not provider_config.get("enabled", False):
                    continue
                    
                # Check if required fields are present
                if provider_name in ["zai", "k2", "qwen", "grok"] and not provider_config.get("credentials"):
                    logger.warning(f"No credentials configured for {provider_name}")
            
            logger.info("✅ Configuration validated")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    async def initialize_providers(self) -> bool:
        """Initialize all configured providers."""
        
        try:
            config = self.config_manager.load_config()
            self.provider_manager = ProviderManager(config)
            
            # Initialize each provider
            success_count = 0
            total_count = 0
            
            for provider_name, provider_config in config["providers"].items():
                if not provider_config.get("enabled", False):
                    logger.info(f"⏭️  Skipping disabled provider: {provider_name}")
                    continue
                
                total_count += 1
                logger.info(f"🔌 Initializing {provider_name}...")
                
                try:
                    await self.provider_manager.initialize_provider(provider_name)
                    success_count += 1
                    logger.info(f"✅ {provider_name} initialized successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {provider_name}: {e}")
            
            if success_count == 0:
                logger.error("No providers initialized successfully")
                return False
            
            logger.info(f"✅ Initialized {success_count}/{total_count} providers")
            
            # Create API Gateway with initialized provider manager
            from gateway.api_gateway import APIGateway
            self.api_gateway = APIGateway(config)
            self.api_gateway.provider_manager = self.provider_manager  # Use the initialized one
            
            return True
            
        except Exception as e:
            logger.error(f"Provider initialization failed: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories."""
        
        directories = [
            "logs",
            "data",
            "cache",
            "temp"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def cleanup_old_files(self):
        """Clean up old temporary files."""
        
        try:
            # Clean up old log files (keep last 10)
            log_dir = Path("logs")
            if log_dir.exists():
                log_files = sorted(log_dir.glob("gateway_*.log"))
                if len(log_files) > 10:
                    for old_file in log_files[:-10]:
                        old_file.unlink()
                        logger.debug(f"Removed old log file: {old_file}")
            
            # Clean up temp directory
            temp_dir = Path("temp")
            if temp_dir.exists():
                for temp_file in temp_dir.glob("*"):
                    if temp_file.is_file():
                        temp_file.unlink()
                        logger.debug(f"Removed temp file: {temp_file}")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
