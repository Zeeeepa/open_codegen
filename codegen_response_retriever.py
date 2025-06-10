#!/usr/bin/env python3
"""
Codegen Response Retriever
==========================

A comprehensive system for retrieving and managing responses from Codegen agent runs.
This module provides functionality to:
- Monitor agent run completion
- Extract response content for context retrieval
- Handle polling and timeout scenarios
- Format responses for AI prompting

Based on the Codegen SDK structure:
- Uses openapi_client.api.agents_api.AgentsApi for API interactions
- Monitors AgentRunResponse.status for completion
- Extracts AgentRunResponse.result for response content
"""

import os
import sys
import time
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

# Import the Codegen API client (assuming it's available)
try:
    from openapi_client.api.agents_api import AgentsApi
    from openapi_client.models.agent_run_response import AgentRunResponse
    from openapi_client.models.create_agent_run_input import CreateAgentRunInput
    from openapi_client.configuration import Configuration
    from openapi_client.api_client import ApiClient
    CODEGEN_SDK_AVAILABLE = True
except ImportError:
    CODEGEN_SDK_AVAILABLE = False
    print("⚠️ Codegen SDK not available. Install openapi_client to use full functionality.")

class AgentRunStatus(Enum):
    """Agent run status enumeration"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

@dataclass
class ResponseContext:
    """Container for response context information"""
    agent_run_id: int
    organization_id: int
    status: AgentRunStatus
    result: Optional[str]
    web_url: Optional[str]
    created_at: Optional[str]
    completion_time: Optional[float]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_run_id": self.agent_run_id,
            "organization_id": self.organization_id,
            "status": self.status.value,
            "result": self.result,
            "web_url": self.web_url,
            "created_at": self.created_at,
            "completion_time": self.completion_time,
            "error_message": self.error_message
        }
    
    def get_context_text(self, max_length: Optional[int] = None) -> str:
        """Extract clean text for AI context prompting"""
        if not self.result:
            return ""
        
        # Clean up the result text for AI consumption
        text = self.result.strip()
        
        # Remove common markdown artifacts that might confuse AI
        text = text.replace("```", "")
        text = text.replace("**", "")
        text = text.replace("__", "")
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text

class CodegenResponseRetriever:
    """
    Main class for retrieving and managing Codegen agent run responses.
    
    This class handles the complete lifecycle of agent run monitoring:
    1. Creating agent runs
    2. Polling for completion
    3. Extracting response content
    4. Formatting for AI context usage
    """
    
    def __init__(
        self,
        organization_id: int,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        default_timeout: int = 300,
        poll_interval: int = 5
    ):
        """
        Initialize the response retriever.
        
        Args:
            organization_id: Codegen organization ID
            api_token: API authentication token (defaults to env var)
            base_url: API base URL (defaults to env var or standard URL)
            default_timeout: Default timeout for agent runs in seconds
            poll_interval: Polling interval in seconds
        """
        self.organization_id = organization_id
        self.default_timeout = default_timeout
        self.poll_interval = poll_interval
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize API client if SDK is available
        if CODEGEN_SDK_AVAILABLE:
            self._setup_api_client(api_token, base_url)
        else:
            self.api_client = None
            self.agents_api = None
    
    def _setup_api_client(self, api_token: Optional[str], base_url: Optional[str]):
        """Setup the Codegen API client"""
        # Get configuration from environment or parameters
        token = api_token or os.getenv('CODEGEN_TOKEN')
        url = base_url or os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
        
        if not token:
            raise ValueError("API token required. Set CODEGEN_TOKEN env var or pass api_token parameter.")
        
        # Configure the API client
        config = Configuration()
        config.host = url
        config.api_key = {'Authorization': f'Bearer {token}'}
        
        self.api_client = ApiClient(config)
        self.agents_api = AgentsApi(self.api_client)
    
    def create_agent_run(self, prompt: str) -> int:
        """
        Create a new agent run with the given prompt.
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            agent_run_id: The ID of the created agent run
            
        Raises:
            RuntimeError: If SDK is not available or API call fails
        """
        if not CODEGEN_SDK_AVAILABLE or not self.agents_api:
            raise RuntimeError("Codegen SDK not available. Cannot create agent runs.")
        
        try:
            input_data = CreateAgentRunInput(prompt=prompt)
            response = self.agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
                org_id=self.organization_id,
                create_agent_run_input=input_data
            )
            
            self.logger.info(f"Created agent run {response.id} for org {self.organization_id}")
            return response.id
            
        except Exception as e:
            self.logger.error(f"Failed to create agent run: {e}")
            raise RuntimeError(f"Failed to create agent run: {e}")
    
    def get_agent_run_status(self, agent_run_id: int) -> ResponseContext:
        """
        Get the current status of an agent run.
        
        Args:
            agent_run_id: The ID of the agent run to check
            
        Returns:
            ResponseContext: Current status and response data
            
        Raises:
            RuntimeError: If SDK is not available or API call fails
        """
        if not CODEGEN_SDK_AVAILABLE or not self.agents_api:
            raise RuntimeError("Codegen SDK not available. Cannot check agent run status.")
        
        try:
            response = self.agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get_1(
                agent_run_id=agent_run_id,
                org_id=self.organization_id
            )
            
            # Parse status
            status_str = response.status or "unknown"
            try:
                status = AgentRunStatus(status_str.lower())
            except ValueError:
                status = AgentRunStatus.UNKNOWN
            
            return ResponseContext(
                agent_run_id=response.id,
                organization_id=response.organization_id,
                status=status,
                result=response.result,
                web_url=response.web_url,
                created_at=response.created_at,
                completion_time=None  # Will be set by polling function
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get agent run status: {e}")
            raise RuntimeError(f"Failed to get agent run status: {e}")
    
    def wait_for_completion(
        self,
        agent_run_id: int,
        timeout: Optional[int] = None,
        progress_callback: Optional[Callable[[ResponseContext], None]] = None
    ) -> ResponseContext:
        """
        Wait for an agent run to complete, polling at regular intervals.
        
        Args:
            agent_run_id: The ID of the agent run to monitor
            timeout: Maximum time to wait in seconds (defaults to default_timeout)
            progress_callback: Optional callback function called on each poll
            
        Returns:
            ResponseContext: Final response context with completion data
            
        Raises:
            TimeoutError: If the agent run doesn't complete within timeout
            RuntimeError: If polling fails
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        self.logger.info(f"Waiting for agent run {agent_run_id} to complete (timeout: {timeout}s)")
        
        while True:
            try:
                context = self.get_agent_run_status(agent_run_id)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(context)
                
                # Check if completed
                if context.status in [AgentRunStatus.COMPLETED, AgentRunStatus.FAILED, AgentRunStatus.CANCELLED]:
                    context.completion_time = time.time() - start_time
                    self.logger.info(f"Agent run {agent_run_id} completed with status: {context.status.value}")
                    return context
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(f"Agent run {agent_run_id} did not complete within {timeout} seconds")
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                if isinstance(e, TimeoutError):
                    raise
                self.logger.error(f"Error polling agent run {agent_run_id}: {e}")
                raise RuntimeError(f"Error polling agent run: {e}")
    
    def create_and_wait(
        self,
        prompt: str,
        timeout: Optional[int] = None,
        progress_callback: Optional[Callable[[ResponseContext], None]] = None
    ) -> ResponseContext:
        """
        Create an agent run and wait for it to complete.
        
        Args:
            prompt: The prompt to send to the agent
            timeout: Maximum time to wait in seconds
            progress_callback: Optional callback function called on each poll
            
        Returns:
            ResponseContext: Final response context with completion data
        """
        agent_run_id = self.create_agent_run(prompt)
        return self.wait_for_completion(agent_run_id, timeout, progress_callback)
    
    def extract_context_for_ai(
        self,
        agent_run_id: int,
        max_length: Optional[int] = 4000,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Extract response content formatted for AI context usage.
        
        Args:
            agent_run_id: The ID of the agent run
            max_length: Maximum length of response text
            include_metadata: Whether to include metadata in response
            
        Returns:
            Dict containing formatted context data for AI prompting
        """
        context = self.get_agent_run_status(agent_run_id)
        
        result = {
            "response_text": context.get_context_text(max_length),
            "status": context.status.value,
            "agent_run_id": agent_run_id
        }
        
        if include_metadata:
            result.update({
                "web_url": context.web_url,
                "created_at": context.created_at,
                "organization_id": context.organization_id
            })
        
        return result

def create_retriever_from_env() -> CodegenResponseRetriever:
    """
    Create a CodegenResponseRetriever using environment variables.
    
    Expected environment variables:
    - CODEGEN_ORG_ID: Organization ID
    - CODEGEN_TOKEN: API token
    - CODEGEN_BASE_URL: API base URL (optional)
    
    Returns:
        Configured CodegenResponseRetriever instance
    """
    org_id = os.getenv('CODEGEN_ORG_ID')
    if not org_id:
        raise ValueError("CODEGEN_ORG_ID environment variable required")
    
    try:
        org_id = int(org_id)
    except ValueError:
        raise ValueError("CODEGEN_ORG_ID must be a valid integer")
    
    return CodegenResponseRetriever(
        organization_id=org_id,
        api_token=os.getenv('CODEGEN_TOKEN'),
        base_url=os.getenv('CODEGEN_BASE_URL')
    )

# Example usage and testing functions
def example_usage():
    """Example of how to use the CodegenResponseRetriever"""
    
    # Create retriever from environment variables
    try:
        retriever = create_retriever_from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Example prompt
    prompt = "Analyze the current codebase and suggest improvements for better maintainability."
    
    def progress_callback(context: ResponseContext):
        print(f"🔄 Status: {context.status.value} - Agent Run ID: {context.agent_run_id}")
    
    try:
        # Create agent run and wait for completion
        print(f"🚀 Creating agent run with prompt: {prompt[:50]}...")
        context = retriever.create_and_wait(
            prompt=prompt,
            timeout=300,  # 5 minutes
            progress_callback=progress_callback
        )
        
        # Extract context for AI usage
        ai_context = retriever.extract_context_for_ai(
            agent_run_id=context.agent_run_id,
            max_length=2000
        )
        
        print(f"✅ Agent run completed!")
        print(f"📊 Status: {context.status.value}")
        print(f"🔗 Web URL: {context.web_url}")
        print(f"⏱️ Completion time: {context.completion_time:.2f}s")
        print(f"📝 Response length: {len(context.result or '')} characters")
        print(f"🤖 AI Context preview: {ai_context['response_text'][:200]}...")
        
        return context
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run example
    example_usage()

