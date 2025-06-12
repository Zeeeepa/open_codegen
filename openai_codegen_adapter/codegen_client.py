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
                            # Enhanced result extraction with better debugging and multiple extraction methods
                            result_content = None
                            extraction_method = None
                            
                            # Log task attributes for debugging
                            available_attrs = [attr for attr in dir(task) if not attr.startswith('_')]
                            logger.debug(f"Task {task.id} available attributes: {available_attrs}")
                            
                            # Method 1: Check task.result
                            if hasattr(task, 'result') and task.result is not None:
                                result_content = task.result
                                extraction_method = "task.result"
                                logger.info(f"Task {task.id} completed with result from task.result")
                            
                            # Method 2: Check task.output (alternative attribute)
                            elif hasattr(task, 'output') and task.output is not None:
                                result_content = task.output
                                extraction_method = "task.output"
                                logger.info(f"Task {task.id} completed with result from task.output")
                            
                            # Method 3: Check task.response (another alternative)
                            elif hasattr(task, 'response') and task.response is not None:
                                result_content = task.response
                                extraction_method = "task.response"
                                logger.info(f"Task {task.id} completed with result from task.response")
                            
                            # Method 4: Check task.content (yet another alternative)
                            elif hasattr(task, 'content') and task.content is not None:
                                result_content = task.content
                                extraction_method = "task.content"
                                logger.info(f"Task {task.id} completed with result from task.content")
                            
                            # Method 5: Try to refresh and get result again
                            elif hasattr(task, 'get_result'):
                                try:
                                    result_content = task.get_result()
                                    extraction_method = "task.get_result()"
                                    logger.info(f"Task {task.id} completed with result from task.get_result()")
                                except Exception as e:
                                    logger.warning(f"Failed to get result via get_result(): {e}")
                            
                            # Method 6: Check for nested result structures (common in API responses)
                            elif hasattr(task, 'data') and task.data is not None:
                                data = task.data
                                if isinstance(data, dict):
                                    # Try common response keys
                                    for key in ['content', 'text', 'message', 'response', 'result', 'output']:
                                        if key in data and data[key]:
                                            result_content = data[key]
                                            extraction_method = f"task.data['{key}']"
                                            logger.info(f"Task {task.id} completed with result from task.data['{key}']")
                                            break
                                elif hasattr(data, '__str__') and str(data).strip():
                                    result_content = str(data)
                                    extraction_method = "task.data (converted to string)"
                                    logger.info(f"Task {task.id} completed with result from task.data (string conversion)")
                            
                            # Method 7: Try alternative attribute names that might contain results
                            if result_content is None:
                                for attr in ['message', 'text', 'body', 'value', 'answer', 'completion']:
                                    if hasattr(task, attr):
                                        attr_value = getattr(task, attr)
                                        if attr_value and isinstance(attr_value, str) and attr_value.strip():
                                            result_content = attr_value
                                            extraction_method = f"task.{attr}"
                                            logger.info(f"Task {task.id} completed with result from task.{attr}")
                                            break
                            
                            # Process and yield the result content
                            if result_content is not None:
                                logger.info(f"Task {task.id} extracted content using method: {extraction_method}")
                                
                                # Handle different content types
                                if isinstance(result_content, str):
                                    content_str = result_content.strip()
                                    if content_str:
                                        yield content_str
                                    else:
                                        logger.warning(f"Task {task.id} result is empty string")
                                        yield "Task completed but returned empty content."
                                elif isinstance(result_content, dict):
                                    # Handle dictionary responses (common in API responses)
                                    if 'content' in result_content:
                                        yield str(result_content['content']).strip()
                                    elif 'text' in result_content:
                                        yield str(result_content['text']).strip()
                                    elif 'message' in result_content:
                                        yield str(result_content['message']).strip()
                                    else:
                                        # Convert entire dict to string as fallback
                                        yield str(result_content)
                                elif isinstance(result_content, list):
                                    # Handle list responses
                                    if result_content and len(result_content) > 0:
                                        first_item = result_content[0]
                                        if isinstance(first_item, dict):
                                            # Extract from first dict item
                                            for key in ['content', 'text', 'message']:
                                                if key in first_item:
                                                    yield str(first_item[key]).strip()
                                                    break
                                            else:
                                                yield str(first_item)
                                        else:
                                            yield str(first_item).strip()
                                    else:
                                        yield "Task completed but returned empty list."
                                elif hasattr(result_content, '__str__'):
                                    content_str = str(result_content).strip()
                                    if content_str and content_str != 'None':
                                        yield content_str
                                    else:
                                        logger.warning(f"Task {task.id} result converted to empty/None string")
                                        yield "Task completed but returned empty content."
                                else:
                                    logger.warning(f"Task {task.id} result is unexpected type: {type(result_content)}")
                                    yield f"Task completed with result type: {type(result_content).__name__}"
                            else:
                                # Enhanced debugging for when no result is found
                                logger.warning(f"Task {task.id} completed but no result found after all extraction methods")
                                
                                # Log detailed attribute inspection
                                for attr in available_attrs:
                                    if not attr.startswith('_') and hasattr(task, attr):
                                        try:
                                            attr_value = getattr(task, attr)
                                            attr_type = type(attr_value).__name__
                                            attr_repr = repr(attr_value)[:100] if attr_value is not None else 'None'
                                            logger.debug(f"Task {task.id} attribute {attr}: {attr_type} = {attr_repr}")
                                        except Exception as e:
                                            logger.debug(f"Task {task.id} attribute {attr}: Error accessing - {e}")
                                
                                # Last resort: return a more informative message
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
