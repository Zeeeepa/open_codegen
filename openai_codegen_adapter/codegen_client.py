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
                            # Enhanced task result retrieval with better debugging
                            result_content = None
                            
                            # Log all available attributes for debugging
                            available_attrs = [attr for attr in dir(task) if not attr.startswith('_')]
                            logger.debug(f"Task {task.id} completed. Available attributes: {available_attrs}")
                            
                            # Method 1: Check task.result
                            if hasattr(task, 'result') and task.result:
                                result_content = task.result
                                logger.info(f"✅ Task {task.id} completed with result from task.result")
                                logger.debug(f"Result type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # Method 2: Check task.output (alternative attribute)
                            elif hasattr(task, 'output') and task.output:
                                result_content = task.output
                                logger.info(f"✅ Task {task.id} completed with result from task.output")
                                logger.debug(f"Output type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # Method 3: Check task.response (another alternative)
                            elif hasattr(task, 'response') and task.response:
                                result_content = task.response
                                logger.info(f"✅ Task {task.id} completed with result from task.response")
                                logger.debug(f"Response type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # Method 4: Check task.content (yet another alternative)
                            elif hasattr(task, 'content') and task.content:
                                result_content = task.content
                                logger.info(f"✅ Task {task.id} completed with result from task.content")
                                logger.debug(f"Content type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # Method 5: Try to refresh and get result again
                            elif hasattr(task, 'get_result'):
                                try:
                                    result_content = task.get_result()
                                    logger.info(f"✅ Task {task.id} completed with result from task.get_result()")
                                    logger.debug(f"Get_result type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                                except Exception as e:
                                    logger.warning(f"Failed to get result via get_result(): {e}")
                            
                            # Method 6: Check for messages or text attributes
                            elif hasattr(task, 'messages') and task.messages:
                                result_content = task.messages
                                logger.info(f"✅ Task {task.id} completed with result from task.messages")
                                logger.debug(f"Messages type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # Method 7: Try to access the task's data attribute
                            elif hasattr(task, 'data') and task.data:
                                result_content = task.data
                                logger.info(f"✅ Task {task.id} completed with result from task.data")
                                logger.debug(f"Data type: {type(result_content)}, Content preview: {str(result_content)[:200]}...")
                            
                            # If we found content, process and yield it
                            if result_content:
                                # Handle different result types
                                if isinstance(result_content, str) and result_content.strip():
                                    yield result_content.strip()
                                elif isinstance(result_content, dict):
                                    # Try to extract text from dict
                                    if 'text' in result_content:
                                        yield str(result_content['text']).strip()
                                    elif 'content' in result_content:
                                        yield str(result_content['content']).strip()
                                    elif 'message' in result_content:
                                        yield str(result_content['message']).strip()
                                    else:
                                        # Convert entire dict to string as fallback
                                        yield str(result_content).strip()
                                elif isinstance(result_content, list):
                                    # Handle list of messages or content
                                    if result_content:
                                        if isinstance(result_content[0], dict):
                                            # Extract text from first dict item
                                            first_item = result_content[0]
                                            if 'text' in first_item:
                                                yield str(first_item['text']).strip()
                                            elif 'content' in first_item:
                                                yield str(first_item['content']).strip()
                                            else:
                                                yield str(first_item).strip()
                                        else:
                                            # Join list items
                                            yield " ".join(str(item) for item in result_content).strip()
                                elif hasattr(result_content, '__str__'):
                                    content_str = str(result_content).strip()
                                    if content_str:
                                        yield content_str
                                    else:
                                        logger.warning(f"Task {task.id} result converted to empty string")
                                        yield "Task completed but returned empty content."
                                else:
                                    logger.warning(f"Task {task.id} result is not a string: {type(result_content)}")
                                    yield f"Task completed with result type: {type(result_content).__name__}"
                            else:
                                # Enhanced fallback: try to get any text-like attributes
                                logger.warning(f"Task {task.id} completed but no result found in standard attributes")
                                
                                # Try to get any text-like attributes
                                for attr in ['message', 'text', 'body', 'value', 'answer']:
                                    if hasattr(task, attr):
                                        attr_value = getattr(task, attr)
                                        if attr_value and isinstance(attr_value, str) and attr_value.strip():
                                            logger.info(f"Found content in task.{attr}")
                                            yield attr_value.strip()
                                            break
                                else:
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
