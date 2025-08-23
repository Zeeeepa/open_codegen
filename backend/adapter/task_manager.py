"""
Task management for Codegen SDK integration.
Handles task creation, polling, and streaming with proper error handling.
"""

import asyncio
import logging
import random
import time
from typing import AsyncGenerator, Optional

from codegen.agents import Agent
from codegen_api_client.exceptions import ApiException

logger = logging.getLogger(__name__)

class CodegenTaskManager:
    """Manages Codegen tasks with proper polling and error handling."""
    
    def __init__(self, agent: Agent, max_retries: int = 60, base_delay: int = 2, webhook_handler = None):
        self.agent = agent
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.webhook_handler = webhook_handler
        logger.info(f"Initialized CodegenTaskManager with max_retries={max_retries}, base_delay={base_delay}, webhook_handler={'enabled' if webhook_handler else 'disabled'}")
    
    async def run_task(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        timeout: int = 300
    ) -> AsyncGenerator[str, None]:
        """
        Run a task and handle polling/streaming.
        
        Args:
            prompt: The prompt to send to the agent
            model: The Codegen model to use
            stream: Whether to stream the response
            timeout: Maximum time to wait for completion in seconds
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent:
            raise RuntimeError("Codegen agent not initialized")
        
        # Add model selection to prompt if specified
        if model:
            prompt = f"[MODEL: {model}]\n{prompt}"
            logger.info(f"Using model: {model}")
        
        # Run the task
        try:
            task = self.agent.run(prompt)
            task_id = task.id
            logger.info(f"Created task with ID: {task_id}")
            
            # Register task with webhook handler if available
            event = None
            if self.webhook_handler:
                logger.info(f"Registering task {task_id} with webhook handler")
                event = self.webhook_handler.register_task(task_id)
            
            if stream:
                logger.info(f"Streaming response for task {task_id}")
                async for chunk in self._stream_response(task, timeout, event):
                    yield chunk
            else:
                logger.info(f"Waiting for completion of task {task_id}")
                
                # If webhook handler is available, wait for webhook callback
                if self.webhook_handler and event:
                    logger.info(f"Using webhook for task {task_id}")
                    
                    # Wait for webhook callback with timeout
                    success = await self.webhook_handler.wait_for_task(task_id, timeout)
                    
                    if success:
                        # Get result from webhook handler
                        result = self.webhook_handler.get_task_result(task_id)
                        if result:
                            logger.info(f"Got result from webhook for task {task_id}")
                            yield result
                        else:
                            # Fallback to polling if webhook didn't provide result
                            logger.warning(f"Webhook didn't provide result for task {task_id}, falling back to polling")
                            result = await self._poll_until_complete(task, timeout)
                            yield result
                    else:
                        # Fallback to polling if webhook timed out
                        logger.warning(f"Webhook timed out for task {task_id}, falling back to polling")
                        result = await self._poll_until_complete(task, timeout)
                        yield result
                else:
                    # Use traditional polling if webhook handler is not available
                    result = await self._poll_until_complete(task, timeout)
                    yield result
                
        except Exception as e:
            logger.error(f"Error running task: {e}")
            raise
    
    async def _poll_until_complete(self, task, timeout: int) -> str:
        """Poll task until completion with exponential backoff."""
        start_time = time.time()
        retry_count = 0
        
        while retry_count < self.max_retries:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                logger.error(f"Task {task.id} polling exceeded timeout of {timeout}s")
                raise TimeoutError(f"Task polling exceeded timeout of {timeout}s")
            
            try:
                task.refresh()
                status = task.status.upper() if hasattr(task.status, 'upper') else str(task.status).upper()
                
                logger.debug(f"Task {task.id} status: {status} (attempt {retry_count+1}/{self.max_retries}, elapsed {elapsed_time:.1f}s)")
                
                if status == "COMPLETE":
                    logger.info(f"Task {task.id} completed successfully after {elapsed_time:.1f}s")
                    
                    # Extract result using multiple methods
                    for attr in ['result', 'output', 'response', 'content']:
                        if hasattr(task, attr):
                            result = getattr(task, attr)
                            if result:
                                logger.info(f"Extracted result from task.{attr}")
                                return result
                    
                    # If no result found
                    logger.warning(f"Task {task.id} completed but no result found")
                    return "Task completed but no result found"
                
                elif status == "FAILED":
                    error_msg = getattr(task, 'error', 'Task failed with unknown error')
                    logger.error(f"Task {task.id} failed: {error_msg}")
                    raise RuntimeError(f"Codegen task failed: {error_msg}")
                
                # Use exponential backoff with jitter
                delay = min(self.base_delay * (1.5 ** retry_count) * (0.9 + 0.2 * random.random()), 30)
                logger.debug(f"Task {task.id} still in progress, waiting {delay:.1f}s...")
                await asyncio.sleep(delay)
                retry_count += 1
                
            except ApiException as e:
                if e.status == 429:  # Rate limit
                    retry_after = 5
                    if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                        retry_after = int(e.headers['Retry-After'])
                    
                    logger.warning(f"Rate limit hit for task {task.id}, waiting {retry_after + 2}s...")
                    await asyncio.sleep(retry_after + 2)  # Add buffer
                    retry_count += 1
                else:
                    logger.error(f"API error for task {task.id}: {e}")
                    raise
            except Exception as e:
                if not isinstance(e, TimeoutError) and not isinstance(e, RuntimeError):
                    logger.error(f"Unexpected error polling task {task.id}: {e}")
                    await asyncio.sleep(self.base_delay)
                    retry_count += 1
                else:
                    raise
        
        logger.error(f"Task {task.id} polling exceeded maximum retries ({self.max_retries})")
        raise RuntimeError(f"Task polling exceeded maximum retries ({self.max_retries})")
    
    async def _stream_response(self, task, timeout: int, event=None) -> AsyncGenerator[str, None]:
        """Stream response by polling for partial results."""
        start_time = time.time()
        last_content = ""
        retry_count = 0
        task_id = task.id
        
        # Initial delay to allow task to start
        await asyncio.sleep(self.base_delay)
        
        # Yield empty chunk to start the stream
        yield ""
        
        while retry_count < self.max_retries:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                logger.error(f"Task {task_id} streaming exceeded timeout of {timeout}s")
                raise TimeoutError(f"Task streaming exceeded timeout of {timeout}s")
            
            # Check if webhook has received a completion event
            if self.webhook_handler and event and event.is_set():
                logger.info(f"Webhook received completion for task {task_id}")
                result = self.webhook_handler.get_task_result(task_id)
                if result and result != last_content:
                    new_content = result[len(last_content):]
                    if new_content:
                        logger.debug(f"Yielding final chunk from webhook: {len(new_content)} chars")
                        yield new_content
                break
            
            try:
                task.refresh()
                status = task.status.upper() if hasattr(task.status, 'upper') else str(task.status).upper()
                
                if status == "COMPLETE":
                    # Final chunk
                    if hasattr(task, 'result') and task.result:
                        if task.result != last_content:
                            new_content = task.result[len(last_content):]
                            if new_content:
                                logger.debug(f"Yielding final chunk: {len(new_content)} chars")
                                yield new_content
                    break
                    
                elif status == "FAILED":
                    error_msg = getattr(task, 'error', 'Task failed with unknown error')
                    logger.error(f"Task {task_id} failed during streaming: {error_msg}")
                    raise RuntimeError(f"Codegen task failed: {error_msg}")
                    
                elif status in ["ACTIVE", "RUNNING", "PENDING"]:
                    # Try to get partial results
                    partial_result = None
                    
                    # Check various attributes for partial results
                    for attr in ['partial_result', 'result', 'output', 'response', 'content']:
                        if hasattr(task, attr):
                            attr_value = getattr(task, attr)
                            if attr_value and isinstance(attr_value, str) and attr_value != last_content:
                                partial_result = attr_value
                                break
                    
                    if partial_result and partial_result != last_content:
                        new_content = partial_result[len(last_content):]
                        if new_content:
                            logger.debug(f"Yielding partial chunk: {len(new_content)} chars")
                            yield new_content
                            last_content = partial_result
                
                # Use exponential backoff with jitter for polling
                delay = min(self.base_delay * (1.2 ** retry_count) * (0.9 + 0.2 * random.random()), 10)
                await asyncio.sleep(delay)
                retry_count += 1
                
            except ApiException as e:
                if e.status == 429:  # Rate limit
                    retry_after = 5
                    if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                        retry_after = int(e.headers['Retry-After'])
                    
                    logger.warning(f"Rate limit hit during streaming for task {task.id}, waiting {retry_after + 2}s...")
                    await asyncio.sleep(retry_after + 2)
                    retry_count += 1
                else:
                    logger.error(f"API error during streaming for task {task.id}: {e}")
                    raise
            except Exception as e:
                if not isinstance(e, TimeoutError) and not isinstance(e, RuntimeError):
                    logger.error(f"Unexpected error during streaming for task {task.id}: {e}")
                    await asyncio.sleep(self.base_delay)
                    retry_count += 1
                else:
                    raise
        
        if retry_count >= self.max_retries:
            logger.error(f"Task {task.id} streaming exceeded maximum retries ({self.max_retries})")
            raise RuntimeError(f"Task streaming exceeded maximum retries ({self.max_retries})")
