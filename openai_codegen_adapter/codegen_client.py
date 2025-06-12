"""
Codegen SDK client wrapper with error handling and response management.
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator, Dict, Any
from codegen import Agent
from .config import CodegenConfig

logger = logging.getLogger(__name__)


class CodegenClient:
    """Wrapper for Codegen SDK with async support and error handling."""
    
    def __init__(self, config: CodegenConfig):
        self.config = config
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Codegen agent."""
        try:
            kwargs = {
                "org_id": self.config.org_id,
                "token": self.config.token
            }
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
                
            self.agent = Agent(**kwargs)
            logger.info(f"Initialized Codegen agent for org_id: {self.config.org_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen agent: {e}")
            raise
    
    async def run_task(self, prompt: str, stream: bool = False) -> AsyncGenerator[str, None]:
        """
        Run a task with the Codegen agent.
        
        Args:
            prompt: The prompt to send to the agent
            stream: Whether to stream the response
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent:
            raise RuntimeError("Codegen agent not initialized")
        
        try:
            # Run the task
            task = self.agent.run(prompt=prompt)
            task_id = task.id
            logger.info(f"Created Codegen SDK task: {task_id}")
            
            # Wait for the task to complete (with timeout)
            start_time = time.time()
            timeout = self.config.timeout
            
            while time.time() - start_time < timeout:
                # Refresh the task to get the latest status
                task.refresh()
                
                if task.status == "completed":
                    generated_text = task.result
                    logger.info(f"Codegen SDK task completed successfully: {task_id}")
                    yield generated_text
                    break
                elif task.status in ["failed", "error"]:
                    logger.error(f"Codegen SDK task failed: {task_id}, status: {task.status}")
                    error_message = getattr(task, 'error', f"Task {task.status}")
                    yield f"Error: {error_message}. Please try again later."
                    break
                
                # Wait before checking again
                await asyncio.sleep(1)
            else:
                # Timeout reached
                logger.error(f"Codegen SDK task timed out: {task_id}")
                yield "Error: Task timed out. Please try again later."
        
        except Exception as e:
            logger.error(f"Error running Codegen agent: {e}")
            yield f"Error: {str(e)}. Please try again later."

