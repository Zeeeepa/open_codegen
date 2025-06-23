"""
Codegen SDK client wrapper with error handling and response management.
Fixed version with proper rate limiting and retry logic.
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator
from codegen import Agent
from codegen_api_client.exceptions import ApiException
from backend.adapter.config import CodegenConfig

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
            logger.info(f"Created task with ID: {task.id}")
            
            if stream:
                # For streaming, we'll poll the task status and yield partial results
                async for chunk in self._stream_task_response(task):
                    yield chunk
            else:
                # For non-streaming, wait for completion and return full result
                await asyncio.sleep(1)  # Initial delay to allow task to start
                start_time = time.time()  # Track timing for completion logging
                
                # Poll task status until completion with rate limiting
                retry_count = 0
                max_retries = 20  # Increased for longer tasks
                base_delay = 5  # Start with 5 seconds to avoid rate limits
                
                while retry_count < max_retries:
                    try:
                        task.refresh()
                        status = task.status.upper() if hasattr(task.status, 'upper') else str(task.status).upper()
                        
                        # Enhanced completion tracking logging
                        elapsed_time = time.time() - start_time
                        logger.debug(f"🔍 COMPLETION CHECK | Task: {task.id} | Status: {status} | Attempt: {retry_count + 1} | Duration: {elapsed_time:.2f}s")
                        
                        if status == "COMPLETE":
                            # Try multiple ways to get the task result (original logic preserved)
                            # Simplified and more robust content extraction
                            result_content = None
                            extraction_method = None
                            
                            # Try all possible content attributes in order of preference
                            content_attributes = [
                                ('result', 'task.result'),
                                ('output', 'task.output'), 
                                ('response', 'task.response'),
                                ('content', 'task.content'),
                                ('message', 'task.message'),
                                ('text', 'task.text'),
                                ('data', 'task.data'),
                                ('body', 'task.body')
                            ]
                            
                            for attr_name, attr_desc in content_attributes:
                                if hasattr(task, attr_name):
                                    attr_value = getattr(task, attr_name)
                                    if attr_value is not None and str(attr_value).strip():
                                        result_content = str(attr_value).strip()
                                        extraction_method = attr_desc
                                        logger.info(f"Task {task.id} extracted content from {attr_desc}")
                                        break
                            
                            # Try get_result() method as last resort
                            if not result_content and hasattr(task, 'get_result'):
                                try:
                                    result_value = task.get_result()
                                    if result_value is not None and str(result_value).strip():
                                        result_content = str(result_value).strip()
                                        extraction_method = 'task.get_result()'
                                        logger.info(f"Task {task.id} extracted content from task.get_result()")
                                except Exception as e:
                                    logger.warning(f"Task {task.id} get_result() failed: {e}")
                            
                            # Yield the extracted content or error message
                            if result_content:
                                logger.info(f"Task {task.id} yielding content from {extraction_method}: {len(result_content)} chars")
                                yield result_content
                            else:
                                # Log available attributes for debugging
                                available_attrs = [attr for attr in dir(task) if not attr.startswith('_')]
                                logger.warning(f"Task {task.id} completed but no content found. Available attributes: {available_attrs}")
                                
                                # DEBUG: Log actual values of key attributes
                                debug_info = {}
                                for attr in ['result', 'output', 'response', 'content', 'message', 'text']:
                                    if hasattr(task, attr):
                                        value = getattr(task, attr)
                                        debug_info[attr] = f"{type(value).__name__}: {repr(value)[:100]}"
                                logger.warning(f"Task {task.id} attribute values: {debug_info}")
                                
                                yield "Task completed successfully but no response content was found. This may indicate an issue with the Codegen API response format."
                            break
                        elif status == "FAILED":
                            error_msg = getattr(task, 'error', 'Task failed with unknown error')
                            logger.error(f"Task {task.id} failed: {error_msg}")
                            raise RuntimeError(f"Codegen task failed: {error_msg}")
                        elif status in ["PENDING", "ACTIVE", "RUNNING"]:
                            # Use exponential backoff to avoid rate limits
                            delay = min(base_delay * (1.5 ** retry_count), 30)  # Cap at 30 seconds
                            logger.debug(f"Task {task.id} still {status}, waiting {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            retry_count += 1
                        else:
                            # Unknown status, wait with backoff
                            delay = min(base_delay * (1.5 ** retry_count), 30)
                            logger.warning(f"Task {task.id} unknown status {status}, waiting {delay:.1f}s...")
                            await asyncio.sleep(delay)
                            retry_count += 1
                            
                    except ApiException as e:
                        if e.status == 429:  # Rate limit exceeded
                            # Respect the Retry-After header if present
                            retry_after = 5  # Default to 5 seconds
                            if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                                retry_after = int(e.headers['Retry-After'])
                            
                            logger.warning(f"Rate limit hit for task {task.id}, waiting {retry_after + 2} seconds...")
                            await asyncio.sleep(retry_after + 2)  # Add 2 second buffer
                            retry_count += 1
                            continue
                        else:
                            logger.error(f"API error for task {task.id}: {e}")
                            raise
                    except Exception as e:
                        logger.error(f"Unexpected error polling task {task.id}: {e}")
                        await asyncio.sleep(base_delay)
                        retry_count += 1
                
                if retry_count >= max_retries:
                    logger.error(f"Task {task.id} polling exceeded maximum retries ({max_retries})")
                    raise RuntimeError(f"Task polling exceeded maximum retries ({max_retries})")
                        
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
        retry_count = 0
        max_retries = 20
        base_delay = 5
        
        while retry_count < max_retries:
            try:
                await asyncio.sleep(base_delay)  # Wait before polling
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
                
                retry_count += 1
                
            except ApiException as e:
                if e.status == 429:  # Rate limit exceeded
                    retry_after = 5
                    if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                        retry_after = int(e.headers['Retry-After'])
                    
                    logger.warning(f"Rate limit hit during streaming, waiting {retry_after + 2} seconds...")
                    await asyncio.sleep(retry_after + 2)
                    retry_count += 1
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                await asyncio.sleep(base_delay)
                retry_count += 1

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for a given text.
        This is a simple approximation - in production you might want
        to use a proper tokenizer.
        """
        # Simple approximation: ~4 characters per token
        return max(1, len(text) // 4)
