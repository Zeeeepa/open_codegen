"""
Enhanced Codegen SDK client wrapper with maximum reliability and performance.
This version includes advanced features for ensuring API responses always reach users.
"""

import asyncio
import logging
import time
import json
from typing import Optional, AsyncGenerator, Dict, Any
from codegen import Agent
from codegen_api_client.exceptions import ApiException
from .config import CodegenConfig

logger = logging.getLogger(__name__)


class CodegenClientEnhanced:
    """Enhanced Codegen client with maximum reliability and performance optimizations."""
    
    def __init__(self, config: CodegenConfig):
        self.config = config
        self.agent = None
        self.response_cache = {}  # Cache for quick response retrieval
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Codegen agent with enhanced error handling."""
        try:
            kwargs = {
                "org_id": self.config.org_id,
                "token": self.config.token
            }
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
                
            self.agent = Agent(**kwargs)
            logger.info(f"✅ Enhanced Codegen agent initialized for org_id: {self.config.org_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced Codegen agent: {e}")
            raise
    
    async def run_task(self, prompt: str, stream: bool = False, max_retries: int = 3) -> AsyncGenerator[str, None]:
        """
        Run a task with enhanced reliability, caching, and retry logic.
        
        Args:
            prompt: The prompt to send to the agent
            stream: Whether to stream the response
            max_retries: Maximum number of retries on failure
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent:
            raise RuntimeError("Enhanced Codegen agent not initialized")
        
        # Check cache first for identical prompts
        prompt_hash = hash(prompt)
        if prompt_hash in self.response_cache:
            cached_response = self.response_cache[prompt_hash]
            logger.info(f"🎯 Using cached response for prompt hash: {prompt_hash}")
            yield cached_response
            return
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 Starting task attempt {attempt + 1}/{max_retries}")
                
                # Create the task
                task = self.agent.run(prompt)
                logger.info(f"📝 Created task with ID: {task.id}")
                
                if stream:
                    # Enhanced streaming with progress tracking
                    async for chunk in self._stream_task_enhanced(task):
                        yield chunk
                        # Cache partial responses for reliability
                        if len(chunk) > 50:  # Only cache substantial chunks
                            self.response_cache[prompt_hash] = chunk
                else:
                    # Enhanced non-streaming with multiple extraction methods
                    result = await self._wait_for_completion_enhanced(task)
                    if result and result.strip():
                        # Cache successful responses
                        self.response_cache[prompt_hash] = result
                        yield result
                        return
                    else:
                        logger.warning(f"⚠️ Empty result on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)  # Brief pause before retry
                            continue
                        else:
                            yield "I apologize, but I wasn't able to generate a response after multiple attempts. Please try rephrasing your request."
                            return
                
                # If we get here, the task completed successfully
                return
                        
            except Exception as e:
                last_error = e
                logger.error(f"❌ Error on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    error_msg = f"Failed after {max_retries} attempts. Last error: {str(last_error)}"
                    logger.error(f"💥 {error_msg}")
                    yield error_msg
    
    async def _wait_for_completion_enhanced(self, task) -> str:
        """
        Enhanced completion waiting with multiple extraction strategies and adaptive polling.
        """
        start_time = time.time()
        max_wait_time = 45  # Reduced to 45 seconds for faster responses
        initial_poll_interval = 0.5  # Start with very fast polling
        max_poll_interval = 3  # Maximum polling interval
        current_poll_interval = initial_poll_interval
        
        logger.info(f"⏳ Enhanced waiting for task {task.id} (max {max_wait_time}s)")
        
        consecutive_same_status = 0
        last_status = None
        
        while time.time() - start_time < max_wait_time:
            try:
                # Refresh task status
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                # Adaptive polling: slow down if status hasn't changed
                if status == last_status:
                    consecutive_same_status += 1
                    if consecutive_same_status > 3:
                        current_poll_interval = min(current_poll_interval * 1.5, max_poll_interval)
                else:
                    consecutive_same_status = 0
                    current_poll_interval = initial_poll_interval
                
                last_status = status
                
                logger.debug(f"📊 Task {task.id} | Status: {status} | Time: {elapsed:.1f}s | Poll: {current_poll_interval:.1f}s")
                
                # Check if completed
                if status in ["COMPLETE", "COMPLETED", "FINISHED", "DONE"]:
                    logger.info(f"✅ Task {task.id} completed in {elapsed:.1f}s")
                    return self._extract_result_enhanced(task)
                
                # Check if failed
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    logger.warning(f"⚠️ Task {task.id} failed with status: {status}")
                    # Try to extract any partial result before giving up
                    partial_result = self._extract_result_enhanced(task)
                    if partial_result and partial_result.strip():
                        return partial_result
                    return f"Task failed with status: {status}"
                
                # Adaptive sleep
                await asyncio.sleep(current_poll_interval)
                
            except ApiException as e:
                if e.status == 429:  # Rate limit
                    logger.warning(f"⏱️ Rate limit hit, waiting 3s...")
                    await asyncio.sleep(3)
                    continue
                else:
                    logger.error(f"❌ API error: {e}")
                    return f"API error: {str(e)}"
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(current_poll_interval)
                continue
        
        # Timeout reached - try one final extraction
        logger.error(f"⏰ Task {task.id} timed out, attempting final extraction...")
        try:
            task.refresh()
            final_result = self._extract_result_enhanced(task)
            if final_result and final_result.strip():
                logger.info(f"🎯 Recovered result from timed-out task!")
                return final_result
        except Exception as e:
            logger.error(f"❌ Final extraction failed: {e}")
        
        elapsed = time.time() - start_time
        return f"Task timed out after {elapsed:.1f} seconds. Please try again with a simpler request."
    
    def _extract_result_enhanced(self, task) -> str:
        """
        Enhanced result extraction with multiple strategies and fallbacks.
        """
        logger.debug(f"🔍 Enhanced result extraction for task {task.id}")
        
        # Strategy 1: Try common result attributes
        result_attributes = [
            'result', 'output', 'response', 'content', 'text', 
            'message', 'data', 'answer', 'completion', 'generated_text'
        ]
        
        for attr in result_attributes:
            if hasattr(task, attr):
                value = getattr(task, attr)
                if value:
                    result_text = self._convert_to_text_enhanced(value)
                    if result_text and result_text.strip():
                        logger.info(f"✅ Found result in task.{attr} ({len(result_text)} chars)")
                        return result_text.strip()
        
        # Strategy 2: Try method calls
        method_calls = [
            'get_result', 'get_output', 'get_response', 'get_content',
            'to_string', 'as_text', 'get_text'
        ]
        for method_name in method_calls:
            if hasattr(task, method_name):
                try:
                    method = getattr(task, method_name)
                    if callable(method):
                        value = method()
                        if value:
                            result_text = self._convert_to_text_enhanced(value)
                            if result_text and result_text.strip():
                                logger.info(f"✅ Found result via {method_name}() ({len(result_text)} chars)")
                                return result_text.strip()
                except Exception as e:
                    logger.debug(f"Failed to call {method_name}(): {e}")
        
        # Strategy 3: Try to access internal state
        try:
            if hasattr(task, '__dict__'):
                task_dict = task.__dict__
                for key, value in task_dict.items():
                    if 'result' in key.lower() or 'output' in key.lower() or 'response' in key.lower():
                        if value:
                            result_text = self._convert_to_text_enhanced(value)
                            if result_text and result_text.strip():
                                logger.info(f"✅ Found result in task.{key} ({len(result_text)} chars)")
                                return result_text.strip()
        except Exception as e:
            logger.debug(f"Failed to access task.__dict__: {e}")
        
        # Strategy 4: Try JSON serialization and look for text content
        try:
            if hasattr(task, 'to_dict'):
                task_data = task.to_dict()
            elif hasattr(task, '__dict__'):
                task_data = task.__dict__
            else:
                task_data = {}
            
            # Look for any text-like content in the serialized data
            def find_text_in_dict(d, path=""):
                if isinstance(d, dict):
                    for k, v in d.items():
                        current_path = f"{path}.{k}" if path else k
                        if isinstance(v, str) and len(v) > 10 and not k.startswith('_'):
                            return v
                        elif isinstance(v, (dict, list)):
                            result = find_text_in_dict(v, current_path)
                            if result:
                                return result
                elif isinstance(d, list):
                    for i, item in enumerate(d):
                        result = find_text_in_dict(item, f"{path}[{i}]")
                        if result:
                            return result
                return None
            
            found_text = find_text_in_dict(task_data)
            if found_text:
                logger.info(f"✅ Found text in serialized data ({len(found_text)} chars)")
                return found_text.strip()
                
        except Exception as e:
            logger.debug(f"Failed to serialize task: {e}")
        
        # Last resort: check all non-private attributes
        try:
            all_attrs = [attr for attr in dir(task) if not attr.startswith('_') and not callable(getattr(task, attr, None))]
            logger.debug(f"🔍 Available task attributes: {all_attrs}")
            
            for attr in all_attrs:
                try:
                    value = getattr(task, attr)
                    if value and isinstance(value, (str, dict, list)):
                        result_text = self._convert_to_text_enhanced(value)
                        if result_text and len(result_text) > 10:
                            logger.info(f"✅ Found result in task.{attr} (fallback)")
                            return result_text.strip()
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Failed to check all attributes: {e}")
        
        # If absolutely nothing found
        logger.warning(f"⚠️ No result found for task {task.id} after enhanced extraction")
        return "Task completed successfully but no response content was found."
    
    def _convert_to_text_enhanced(self, value) -> str:
        """
        Enhanced text conversion with better handling of complex data structures.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Try common text keys first
            text_keys = ['text', 'content', 'message', 'response', 'output', 'result', 'answer']
            for key in text_keys:
                if key in value and value[key]:
                    return str(value[key])
            
            # Try to find any substantial text content
            for key, val in value.items():
                if isinstance(val, str) and len(val) > 10:
                    return val
            
            # Fallback to JSON representation if it looks like structured data
            try:
                json_str = json.dumps(value, indent=2)
                if len(json_str) > 50:  # Only return if substantial
                    return json_str
            except Exception:
                pass
            
            return str(value)
        elif isinstance(value, list):
            if value:
                # If list of dicts, try to extract text
                if isinstance(value[0], dict):
                    for item in value:
                        for key in ['text', 'content', 'message']:
                            if key in item and item[key]:
                                return str(item[key])
                # Join list items if they're strings
                if all(isinstance(item, str) for item in value):
                    return " ".join(value)
                # Try to convert first substantial item
                for item in value:
                    converted = self._convert_to_text_enhanced(item)
                    if converted and len(converted) > 10:
                        return converted
            return ""
        else:
            return str(value) if value else ""
    
    async def _stream_task_enhanced(self, task) -> AsyncGenerator[str, None]:
        """
        Enhanced streaming with better progress tracking and partial content delivery.
        """
        start_time = time.time()
        max_wait_time = 45  # Reduced timeout for streaming
        poll_interval = 1.5  # Optimized polling interval
        max_polls = int(max_wait_time / poll_interval)
        last_content = ""
        content_updates = 0
        
        logger.info(f"🌊 Enhanced streaming for task {task.id}")
        
        for attempt in range(max_polls):
            try:
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                # Check for completion
                if status in ["COMPLETE", "COMPLETED", "FINISHED", "DONE"]:
                    # Get final result
                    final_result = self._extract_result_enhanced(task)
                    if final_result and final_result != last_content:
                        # Yield any new content
                        if len(final_result) > len(last_content):
                            new_content = final_result[len(last_content):]
                            if new_content.strip():
                                yield new_content
                                content_updates += 1
                        else:
                            # Completely new content
                            yield final_result
                            content_updates += 1
                    
                    logger.info(f"✅ Enhanced stream completed for task {task.id} ({content_updates} updates)")
                    return
                
                # Check for failure
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    yield f"Task failed with status: {status}"
                    return
                
                # Try to get partial content (enhanced extraction)
                current_content = self._extract_result_enhanced(task)
                if current_content and current_content != last_content:
                    if len(current_content) > len(last_content):
                        new_content = current_content[len(last_content):]
                        if new_content.strip():
                            yield new_content
                            last_content = current_content
                            content_updates += 1
                            logger.debug(f"📊 Streamed update {content_updates}: +{len(new_content)} chars")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"❌ Enhanced streaming error: {e}")
                await asyncio.sleep(poll_interval)
                continue
        
        # Timeout
        if content_updates > 0:
            yield f"\n\n[Stream completed with {content_updates} updates after {max_wait_time}s timeout]"
        else:
            yield f"Stream timed out after {max_wait_time} seconds with no content received."
    
    def count_tokens(self, text: str) -> int:
        """Enhanced token estimation with better accuracy."""
        if not text:
            return 0
        
        # More accurate token estimation
        # Average English word is ~4 characters, average token is ~0.75 words
        word_count = len(text.split())
        char_based_estimate = len(text) // 4
        
        # Use the higher estimate for safety
        return max(word_count, char_based_estimate, 1)
    
    def clear_cache(self):
        """Clear the response cache."""
        self.response_cache.clear()
        logger.info("🧹 Response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_responses": len(self.response_cache),
            "cache_size_bytes": sum(len(str(v)) for v in self.response_cache.values())
        }

