#!/usr/bin/env python3
"""
Codegen Integration Module
=========================

Simple integration module that adds response retrieval functionality to the existing
OpenAI Codegen Adapter server. This module provides:

1. Agent run creation and monitoring
2. Response extraction for context retrieval
3. Integration with existing server endpoints
4. Simplified API for AI prompting context

Usage:
    from codegen_integration import CodegenClient, get_agent_response_for_context
    
    # Simple usage
    client = CodegenClient()
    context_text = get_agent_response_for_context("Analyze this codebase")
"""

import os
import sys
import time
import json
import requests
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class AgentRunResult:
    """Simple container for agent run results"""
    agent_run_id: int
    status: str
    result: Optional[str]
    web_url: Optional[str]
    error: Optional[str] = None
    
    def get_context_text(self, max_length: Optional[int] = None) -> str:
        """Extract clean text for AI context"""
        if not self.result:
            return ""
        
        text = self.result.strip()
        
        # Clean up markdown and formatting for AI consumption
        text = text.replace("```", "")
        text = text.replace("**", "")
        text = text.replace("__", "")
        text = text.replace("##", "")
        text = text.replace("#", "")
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = ' '.join(lines)
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text

class CodegenClient:
    """
    Simple client for interacting with Codegen API.
    
    This client provides a simplified interface for:
    - Creating agent runs
    - Monitoring completion
    - Extracting responses for AI context
    """
    
    def __init__(
        self,
        organization_id: Optional[int] = None,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 300,
        poll_interval: int = 10
    ):
        """
        Initialize Codegen client.
        
        Args:
            organization_id: Codegen org ID (from env CODEGEN_ORG_ID)
            api_token: API token (from env CODEGEN_TOKEN)  
            base_url: API base URL (from env CODEGEN_BASE_URL)
            timeout: Default timeout for operations
            poll_interval: Polling interval in seconds
        """
        self.organization_id = organization_id or int(os.getenv('CODEGEN_ORG_ID', '323'))
        self.api_token = api_token or os.getenv('CODEGEN_TOKEN', '')
        self.base_url = base_url or os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        # Setup session with authentication
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            })
    
    def create_agent_run(self, prompt: str) -> int:
        """
        Create a new agent run.
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            agent_run_id: ID of the created agent run
            
        Raises:
            RuntimeError: If creation fails
        """
        url = f"{self.base_url}/v1/organizations/{self.organization_id}/agent/run"
        
        payload = {"prompt": prompt}
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            agent_run_id = data.get('id')
            
            if not agent_run_id:
                raise RuntimeError(f"No agent run ID in response: {data}")
            
            logger.info(f"Created agent run {agent_run_id}")
            return agent_run_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create agent run: {e}")
            raise RuntimeError(f"Failed to create agent run: {e}")
    
    def get_agent_run(self, agent_run_id: int) -> AgentRunResult:
        """
        Get agent run status and result.
        
        Args:
            agent_run_id: ID of the agent run
            
        Returns:
            AgentRunResult: Current status and result
        """
        url = f"{self.base_url}/v1/organizations/{self.organization_id}/agent/run/{agent_run_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return AgentRunResult(
                agent_run_id=data.get('id', agent_run_id),
                status=data.get('status', 'unknown'),
                result=data.get('result'),
                web_url=data.get('web_url'),
                error=None
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get agent run {agent_run_id}: {e}")
            return AgentRunResult(
                agent_run_id=agent_run_id,
                status='error',
                result=None,
                web_url=None,
                error=str(e)
            )
    
    def wait_for_completion(self, agent_run_id: int, timeout: Optional[int] = None) -> AgentRunResult:
        """
        Wait for agent run to complete.
        
        Args:
            agent_run_id: ID of the agent run
            timeout: Maximum time to wait (defaults to self.timeout)
            
        Returns:
            AgentRunResult: Final result
            
        Raises:
            TimeoutError: If timeout is exceeded
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        
        logger.info(f"Waiting for agent run {agent_run_id} to complete...")
        
        while True:
            result = self.get_agent_run(agent_run_id)
            
            # Check if completed
            if result.status.lower() in ['completed', 'failed', 'cancelled', 'error']:
                logger.info(f"Agent run {agent_run_id} finished with status: {result.status}")
                return result
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Agent run {agent_run_id} did not complete within {timeout} seconds")
            
            # Progress update
            if int(elapsed) % 30 == 0:  # Log every 30 seconds
                logger.info(f"Agent run {agent_run_id} still running... ({elapsed:.0f}s elapsed)")
            
            time.sleep(self.poll_interval)
    
    def create_and_wait(self, prompt: str, timeout: Optional[int] = None) -> AgentRunResult:
        """
        Create agent run and wait for completion.
        
        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait
            
        Returns:
            AgentRunResult: Final result
        """
        agent_run_id = self.create_agent_run(prompt)
        return self.wait_for_completion(agent_run_id, timeout)

# Convenience functions for easy integration

def get_agent_response_for_context(
    prompt: str,
    max_length: Optional[int] = 4000,
    timeout: int = 300
) -> str:
    """
    Simple function to get agent response formatted for AI context.
    
    Args:
        prompt: The prompt to send to the agent
        max_length: Maximum length of returned text
        timeout: Maximum time to wait for completion
        
    Returns:
        Clean text response suitable for AI context
        
    Example:
        context = get_agent_response_for_context("Analyze this codebase")
        ai_prompt = f"Based on this analysis: {context}, suggest improvements"
    """
    try:
        client = CodegenClient(timeout=timeout)
        result = client.create_and_wait(prompt, timeout)
        
        if result.status.lower() == 'completed' and result.result:
            return result.get_context_text(max_length)
        else:
            logger.warning(f"Agent run failed or returned no result: {result.status}")
            return ""
            
    except Exception as e:
        logger.error(f"Failed to get agent response: {e}")
        return ""

def create_context_retrieval_endpoint():
    """
    Create a Flask/FastAPI endpoint for context retrieval.
    This can be integrated into the existing server.
    """
    def context_endpoint(prompt: str, max_length: int = 4000, timeout: int = 300):
        """Endpoint handler for context retrieval"""
        try:
            context_text = get_agent_response_for_context(prompt, max_length, timeout)
            
            return {
                "success": True,
                "context_text": context_text,
                "length": len(context_text),
                "truncated": len(context_text) >= max_length
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context_text": "",
                "length": 0,
                "truncated": False
            }
    
    return context_endpoint

# Integration with existing server
def add_context_endpoints_to_app(app):
    """
    Add context retrieval endpoints to existing Flask/FastAPI app.
    
    Args:
        app: Flask or FastAPI application instance
    """
    
    # Try to detect app type and add appropriate routes
    if hasattr(app, 'route'):  # Flask
        @app.route('/api/context/retrieve', methods=['POST'])
        def retrieve_context():
            from flask import request, jsonify
            
            data = request.get_json()
            prompt = data.get('prompt', '')
            max_length = data.get('max_length', 4000)
            timeout = data.get('timeout', 300)
            
            if not prompt:
                return jsonify({"error": "Prompt is required"}), 400
            
            endpoint = create_context_retrieval_endpoint()
            result = endpoint(prompt, max_length, timeout)
            
            return jsonify(result)
    
    elif hasattr(app, 'post'):  # FastAPI
        @app.post('/api/context/retrieve')
        def retrieve_context(data: dict):
            prompt = data.get('prompt', '')
            max_length = data.get('max_length', 4000)
            timeout = data.get('timeout', 300)
            
            if not prompt:
                return {"error": "Prompt is required"}
            
            endpoint = create_context_retrieval_endpoint()
            return endpoint(prompt, max_length, timeout)

# Example usage and testing
def test_integration():
    """Test the integration functionality"""
    
    print("🧪 Testing Codegen Integration...")
    
    # Test environment setup
    org_id = os.getenv('CODEGEN_ORG_ID')
    token = os.getenv('CODEGEN_TOKEN')
    
    if not org_id or not token:
        print("❌ Missing environment variables:")
        print("   - CODEGEN_ORG_ID:", "✅" if org_id else "❌")
        print("   - CODEGEN_TOKEN:", "✅" if token else "❌")
        return False
    
    try:
        # Test simple context retrieval
        print("🔄 Testing context retrieval...")
        context = get_agent_response_for_context(
            "Hello! Please respond with a brief greeting.",
            max_length=500,
            timeout=60
        )
        
        if context:
            print(f"✅ Context retrieved: {len(context)} characters")
            print(f"📝 Preview: {context[:100]}...")
            return True
        else:
            print("❌ No context retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_integration()

