"""
Enhanced Codegen client with model selection and prompt template support.
"""

import logging
from typing import AsyncGenerator, Optional

from codegen.agents import Agent

from backend.adapter.auth import CodegenAuth
from backend.adapter.config import EnhancedCodegenConfig
from backend.adapter.model_mapper import ModelMapper
from backend.adapter.task_manager import CodegenTaskManager
from backend.adapter.enhanced_transformer import PromptTemplate

logger = logging.getLogger(__name__)

class EnhancedCodegenClient:
    """Enhanced wrapper for Codegen SDK with model selection and prompt templates."""
    
    def __init__(
        self,
        config: EnhancedCodegenConfig,
        auth: Optional[CodegenAuth] = None,
        model_mapper: Optional[ModelMapper] = None,
        prompt_template: Optional[PromptTemplate] = None,
        webhook_handler = None
    ):
        self.config = config
        self.auth = auth or CodegenAuth()
        self.model_mapper = model_mapper or ModelMapper(config.model_mapping)
        self.prompt_template = prompt_template or PromptTemplate(config)
        self.webhook_handler = webhook_handler
        self.agent = None
        self.task_manager = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Codegen agent."""
        try:
            # Get credentials from auth
            credentials = self.auth.get_credentials()
            
            # Override with config if provided
            org_id = self.config.org_id or credentials["org_id"]
            token = self.config.token or credentials["token"]
            
            kwargs = {
                "org_id": org_id,
                "token": token
            }
            
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            
            # Store webhook URL for task manager if webhook_handler is provided
            if self.webhook_handler:
                # Get the server's external URL from environment or use localhost
                import os
                server_host = os.environ.get("SERVER_HOST", "localhost")
                server_port = os.environ.get("SERVER_PORT", "8001")
                webhook_url = f"http://{server_host}:{server_port}/webhook/codegen"
                # Note: We don't pass webhook_url to Agent directly, but to task_manager
                logger.info(f"Using webhook URL: {webhook_url}")
            
            self.agent = Agent(**kwargs)
            self.task_manager = CodegenTaskManager(
                self.agent,
                max_retries=self.config.max_retries,
                base_delay=self.config.base_delay,
                webhook_handler=self.webhook_handler
            )
            
            logger.info(f"Initialized enhanced Codegen client for org_id: {org_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen agent: {e}")
            raise
    
    async def run_task(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Run a task with the Codegen agent.
        
        Args:
            prompt: The prompt to send to the agent
            model: The Codegen model to use
            stream: Whether to stream the response
            timeout: Maximum time to wait for completion in seconds
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent or not self.task_manager:
            raise RuntimeError("Codegen agent not initialized")
        
        # Apply prompt template
        prompt = self.prompt_template.apply(prompt)
        
        # Use provided timeout or default from config
        timeout_value = timeout or self.config.timeout
        
        # Run the task
        async for chunk in self.task_manager.run_task(
            prompt=prompt,
            model=model,
            stream=stream,
            timeout=timeout_value
        ):
            yield chunk
    
    def validate(self) -> bool:
        """Validate client configuration."""
        return self.agent is not None


def create_enhanced_client(
    config: EnhancedCodegenConfig,
    auth: Optional[CodegenAuth] = None,
    model_mapper: Optional[ModelMapper] = None,
    prompt_template: Optional[PromptTemplate] = None,
    webhook_handler = None
) -> EnhancedCodegenClient:
    """Create an enhanced Codegen client."""
    return EnhancedCodegenClient(
        config=config,
        auth=auth,
        model_mapper=model_mapper,
        prompt_template=prompt_template,
        webhook_handler=webhook_handler
    )
