"""
Codegen SDK client wrapper with error handling and response management.
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator
from codegen import Agent
from codegen_api_client.exceptions import ApiException
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
            task = self.agent.run(prompt)
            
            if stream:
                # For streaming, we'll poll the task status and yield partial results
                async for chunk in self._stream_task_response(task):
                    yield chunk
            else:
                # For non-streaming, wait for completion and return full result
                await asyncio.sleep(0.1)  # Small delay to allow task to start
                
                # Poll task status until completion
                while True:
                    task.refresh()
                    status = task.status.upper() if hasattr(task.status, 'upper') else str(task.status).upper()
                    
                    if status == "COMPLETE":
                        if hasattr(task, 'result') and task.result:
                            yield task.result
                        else:
                            yield "Task completed successfully."
                        break
                    elif status == "FAILED":
                        error_msg = getattr(task, 'error', 'Task failed with unknown error')
                        raise RuntimeError(f"Codegen task failed: {error_msg}")
                    elif status in ["PENDING", "ACTIVE", "RUNNING"]:
                        await asyncio.sleep(2)  # Wait before next poll (increased to avoid rate limits)
                    else:
                        # Unknown status, wait a bit more
                        await asyncio.sleep(2)
                        
        except Exception as e:
            logger.error(f"Error running Codegen task: {e}")
            raise
    
    async def _stream_task_response(self, task) -> AsyncGenerator[str, None]:
        """
        Stream task response by polling status and yielding partial results.
        
        This is a simplified streaming implementation since we don't know
        the exact streaming capabilities of the Codegen SDK.
        """
        last_content = ""
        
        while True:
            await asyncio.sleep(1)  # Poll every 1 second (increased to avoid rate limits)
            task.refresh()
            status = task.status.upper() if hasattr(task.status, 'upper') else str(task.status).upper()
            
            if status == "COMPLETE":
                if hasattr(task, 'result') and task.result:
                    # Yield any remaining content
                    if task.result != last_content:
                        new_content = task.result[len(last_content):]
                        if new_content:
                            yield new_content
                break
            elif status == "FAILED":
                error_msg = getattr(task, 'error', 'Task failed with unknown error')
                raise RuntimeError(f"Codegen task failed: {error_msg}")
            elif status in ["ACTIVE", "RUNNING"]:
                # Try to get partial results if available
                if hasattr(task, 'partial_result') and task.partial_result:
                    if task.partial_result != last_content:
                        new_content = task.partial_result[len(last_content):]
                        if new_content:
                            yield new_content
                            last_content = task.partial_result
                # If no partial results, yield a small indicator
                elif not last_content:
                    yield ""  # Empty chunk to indicate streaming started
                    last_content = " "  # Mark that we've started

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for a given text.
        This is a simple approximation - in production you might want
        to use a proper tokenizer.
        """
        # Simple approximation: ~4 characters per token
        return max(1, len(text) // 4)
