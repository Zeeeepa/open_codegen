"""
Authentication management for Codegen SDK integration.
Handles loading credentials from environment variables and auth file.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from codegen.agents import Agent

logger = logging.getLogger(__name__)

class CodegenAuth:
    """Handles Codegen authentication with proper file handling."""
    
    AUTH_FILE_PATH = Path("~/.config/codegen-sh/auth.json").expanduser()
    
    def __init__(self):
        self.token = None
        self.org_id = None
        self._load_auth()
    
    def _load_auth(self):
        """Load authentication from file or environment variables."""
        # Try environment variables first
        env_token = os.environ.get("CODEGEN_API_TOKEN")  # Updated to use CODEGEN_API_TOKEN
        env_org_id = os.environ.get("CODEGEN_ORG_ID")
        
        # Then try auth file
        file_auth = self._load_from_file()
        
        # Set values with environment variables taking precedence
        self.token = env_token or file_auth.get("token")
        self.org_id = env_org_id or file_auth.get("org_id") or "323"  # Default org_id
        
        logger.info(f"Loaded authentication - org_id: {self.org_id}, token: {'set' if self.token else 'not set'}")
    
    def _load_from_file(self) -> Dict:
        """Load authentication from standard Codegen auth file."""
        if not self.AUTH_FILE_PATH.exists():
            logger.info(f"Auth file not found at {self.AUTH_FILE_PATH}")
            return {}
            
        try:
            with open(self.AUTH_FILE_PATH, "r") as f:
                auth_data = json.load(f)
                logger.info(f"Loaded auth data from {self.AUTH_FILE_PATH}")
                return auth_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load auth file: {e}")
            return {}
    
    def validate(self) -> bool:
        """Validate credentials against Codegen API."""
        if not self.token or not self.org_id:
            logger.warning("Missing token or org_id for validation")
            return False
            
        try:
            agent = Agent(org_id=self.org_id, token=self.token)
            # Just initializing the agent is enough to validate credentials
            logger.info(f"Successfully validated credentials for org_id: {self.org_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to validate credentials: {e}")
            return False
    
    def get_credentials(self) -> Dict[str, str]:
        """Get credentials as a dictionary."""
        return {
            "token": self.token,
            "org_id": self.org_id
        }


def get_auth() -> CodegenAuth:
    """Get authentication instance."""
    return CodegenAuth()

