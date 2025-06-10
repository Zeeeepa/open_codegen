"""
Fixed Codegen SDK client wrapper with reliable response handling.
Simplified version that ensures API responses are properly returned to users.
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator
from codegen import Agent
from codegen_api_client.exceptions import ApiException
from .config import CodegenConfig

logger = logging.getLogger(__name__)


class CodegenClientFixed:
    """Simplified Codegen client that ensures responses are returned to users."""
    
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
            logger.info(f"✅ Initialized Codegen agent for org_id: {self.config.org_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Codegen agent: {e}")
            raise
    
    async def run_task(self, prompt: str, stream: bool = False) -> AsyncGenerator[str, None]:
        """
        Run a task with simplified, reliable response handling.
        
        Args:
            prompt: The prompt to send to the agent
            stream: Whether to stream the response
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent:
            raise RuntimeError("Codegen agent not initialized")
        
        try:
            # Create the task
            task = self.agent.run(prompt)
            logger.info(f"🚀 Created task with ID: {task.id}")
            
            if stream:
                # For streaming, use simplified polling
                async for chunk in self._stream_task_simple(task):
                    yield chunk
            else:
                # For non-streaming, use simplified completion check
                result = await self._wait_for_completion_simple(task)
                if result:
                    yield result
                else:
                    yield "Task completed but no response was generated."
                        
        except Exception as e:
            logger.error(f"❌ Error running Codegen task: {e}")
            # Always yield something to the user, even on error
            yield f"Error: {str(e)}"
    
    async def _wait_for_completion_simple(self, task) -> str:
        """
        Simplified completion waiting with faster polling and reliable response extraction.
        """
        start_time = time.time()
        max_wait_time = 120  # 2 minutes max
        poll_interval = 2   # Poll every 2 seconds (much faster)
        max_polls = max_wait_time // poll_interval
        
        logger.info(f"⏳ Waiting for task {task.id} completion (max {max_wait_time}s)")
        
        for attempt in range(max_polls):
            try:
                # Refresh task status
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                logger.debug(f"📊 Task {task.id} | Status: {status} | Attempt: {attempt + 1} | Time: {elapsed:.1f}s")
                
                # Check if completed
                if status in ["COMPLETE", "COMPLETED", "FINISHED", "DONE"]:
                    logger.info(f"✅ Task {task.id} completed in {elapsed:.1f}s")
                    return self._extract_result_simple(task)
                
                # Check if failed
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    logger.warning(f"⚠️ Task {task.id} failed with status: {status}")
                    return f"Task failed with status: {status}"
                
                # Continue polling
                await asyncio.sleep(poll_interval)
                
            except ApiException as e:
                if e.status == 429:  # Rate limit
                    logger.warning(f"⏱️ Rate limit hit, waiting 10s...")
                    await asyncio.sleep(10)
                    continue
                else:
                    logger.error(f"❌ API error: {e}")
                    return f"API error: {str(e)}"
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(poll_interval)
                continue
        
        # Timeout reached
        elapsed = time.time() - start_time
        logger.error(f"⏰ Task {task.id} timed out after {elapsed:.1f}s")
        return f"Task timed out after {elapsed:.1f} seconds. Please try again with a simpler request."
    
    def _extract_result_simple(self, task) -> str:
        """
        Simplified result extraction that tries common attributes in order.
        """
        logger.debug(f"🔍 Extracting result from task {task.id}")
        
        # List of attributes to try, in order of preference
        result_attributes = [
            'result',
            'output', 
            'response',
            'content',
            'text',
            'message',
            'data'
        ]
        
        for attr in result_attributes:
            if hasattr(task, attr):
                value = getattr(task, attr)
                if value:
                    result_text = self._convert_to_text(value)
                    if result_text and result_text.strip():
                        logger.info(f"✅ Found result in task.{attr} ({len(result_text)} chars)")
                        return result_text.strip()
        
        # Try method calls
        method_calls = ['get_result', 'get_output', 'get_response']
        for method_name in method_calls:
            if hasattr(task, method_name):
                try:
                    method = getattr(task, method_name)
                    if callable(method):
                        value = method()
                        if value:
                            result_text = self._convert_to_text(value)
                            if result_text and result_text.strip():
                                logger.info(f"✅ Found result via {method_name}() ({len(result_text)} chars)")
                                return result_text.strip()
                except Exception as e:
                    logger.debug(f"Failed to call {method_name}(): {e}")
        
        # Last resort: check all attributes
        all_attrs = [attr for attr in dir(task) if not attr.startswith('_')]
        logger.debug(f"🔍 Available task attributes: {all_attrs}")
        
        # If nothing found, return a helpful message
        logger.warning(f"⚠️ No result found for task {task.id}")
        return "Task completed successfully but no response content was found."
    
    def _convert_to_text(self, value) -> str:
        """
        Convert various value types to text.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Try common text keys
            for key in ['text', 'content', 'message', 'response', 'output']:
                if key in value and value[key]:
                    return str(value[key])
            # Fallback to string representation
            return str(value)
        elif isinstance(value, list):
            if value:
                # If list of dicts, try to extract text
                if isinstance(value[0], dict):
                    for item in value:
                        for key in ['text', 'content', 'message']:
                            if key in item and item[key]:
                                return str(item[key])
                # Join list items
                return " ".join(str(item) for item in value)
            return ""
        else:
            return str(value) if value else ""
    
    async def _stream_task_simple(self, task) -> AsyncGenerator[str, None]:
        """
        Simplified streaming with faster updates.
        """
        start_time = time.time()
        max_wait_time = 120
        poll_interval = 3  # Poll every 3 seconds for streaming
        max_polls = max_wait_time // poll_interval
        last_content = ""
        
        logger.info(f"🌊 Starting stream for task {task.id}")
        
        for attempt in range(max_polls):
            try:
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                # Check for completion
                if status in ["COMPLETE", "COMPLETED", "FINISHED", "DONE"]:
                    # Get final result
                    final_result = self._extract_result_simple(task)
                    if final_result and final_result != last_content:
                        # Yield any new content
                        if len(final_result) > len(last_content):
                            new_content = final_result[len(last_content):]
                            if new_content.strip():
                                yield new_content
                        else:
                            # Completely new content
                            yield final_result
                    logger.info(f"✅ Stream completed for task {task.id}")
                    return
                
                # Check for failure
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    yield f"Task failed with status: {status}"
                    return
                
                # Try to get partial content (if available)
                current_content = self._extract_result_simple(task)
                if current_content and current_content != last_content:
                    if len(current_content) > len(last_content):
                        new_content = current_content[len(last_content):]
                        if new_content.strip():
                            yield new_content
                            last_content = current_content
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"❌ Streaming error: {e}")
                await asyncio.sleep(poll_interval)
                continue
        
        # Timeout
        yield f"Stream timed out after {max_wait_time} seconds."
    
    def count_tokens(self, text: str) -> int:
        """Simple token estimation."""
        return max(1, len(text) // 4)

