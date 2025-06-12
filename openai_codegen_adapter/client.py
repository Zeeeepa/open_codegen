"""
Unified Codegen SDK client with comprehensive reliability, performance, and monitoring features.
This single client replaces all previous client implementations with a unified architecture.
"""

import asyncio
import logging
import time
import json
from typing import Optional, AsyncGenerator, Dict, Any, Union
from enum import Enum
from codegen import Agent
from codegen_api_client.exceptions import ApiException
from .config import CodegenConfig

logger = logging.getLogger(__name__)


class ClientMode(Enum):
    """Client operation modes for different reliability/performance profiles."""
    BASIC = "basic"           # Simple, fast operation
    RELIABLE = "reliable"     # Enhanced reliability with retries
    PERFORMANCE = "performance"  # Maximum performance with caching
    PRODUCTION = "production"    # Full production features


class CodegenClient:
    """
    Unified Codegen client with configurable reliability and performance features.
    
    Features:
    - Multiple operation modes (basic, reliable, performance, production)
    - Response caching for identical prompts
    - Retry mechanism with exponential backoff
    - Adaptive polling intervals
    - Multiple result extraction strategies
    - Comprehensive error handling and recovery
    - Performance monitoring and statistics
    """
    
    def __init__(self, config: CodegenConfig, mode: ClientMode = ClientMode.PRODUCTION):
        self.config = config
        self.mode = mode
        self.agent = None
        
        # Performance features
        self.response_cache = {} if mode in [ClientMode.PERFORMANCE, ClientMode.PRODUCTION] else None
        self.stats = {
            "requests_total": 0,
            "requests_cached": 0,
            "requests_failed": 0,
            "requests_retried": 0,
            "average_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Configuration based on mode
        self._configure_for_mode()
        self._initialize_agent()
    
    def _configure_for_mode(self):
        """Configure client settings based on operation mode."""
        if self.mode == ClientMode.BASIC:
            self.max_retries = 1
            self.max_wait_time = 30
            self.poll_interval = 2
            self.enable_caching = False
            self.enable_adaptive_polling = False
            
        elif self.mode == ClientMode.RELIABLE:
            self.max_retries = 3
            self.max_wait_time = 60
            self.poll_interval = 1
            self.enable_caching = False
            self.enable_adaptive_polling = True
            
        elif self.mode == ClientMode.PERFORMANCE:
            self.max_retries = 2
            self.max_wait_time = 45
            self.poll_interval = 0.5
            self.enable_caching = True
            self.enable_adaptive_polling = True
            
        else:  # PRODUCTION
            self.max_retries = 3
            self.max_wait_time = 45
            self.poll_interval = 0.5
            self.enable_caching = True
            self.enable_adaptive_polling = True
    
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
            logger.info(f"✅ Codegen client initialized (mode: {self.mode.value}, org_id: {self.config.org_id})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Codegen agent: {e}")
            raise
    
    async def run_task(self, prompt: str, stream: bool = False, **kwargs) -> AsyncGenerator[str, None]:
        """
        Run a task with configurable reliability and performance features.
        
        Args:
            prompt: The prompt to send to the agent
            stream: Whether to stream the response
            **kwargs: Additional options (max_retries, timeout, etc.)
            
        Yields:
            Response chunks if streaming, or final response if not streaming
        """
        if not self.agent:
            raise RuntimeError("Codegen agent not initialized")
        
        start_time = time.time()
        self.stats["requests_total"] += 1
        
        # Override settings with kwargs if provided
        max_retries = kwargs.get('max_retries', self.max_retries)
        timeout = kwargs.get('timeout', self.max_wait_time)
        
        # Check cache first (if enabled)
        if self.enable_caching and self.response_cache is not None:
            prompt_hash = hash(prompt)
            if prompt_hash in self.response_cache:
                cached_response = self.response_cache[prompt_hash]
                self.stats["requests_cached"] += 1
                self.stats["cache_hits"] += 1
                logger.info(f"🎯 Using cached response for prompt hash: {prompt_hash}")
                yield cached_response
                return
            else:
                self.stats["cache_misses"] += 1
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.stats["requests_retried"] += 1
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retries}")
                
                # Create the task
                task = self.agent.run(prompt)
                logger.info(f"🚀 Created task with ID: {task.id}")
                
                if stream:
                    # Streaming response
                    async for chunk in self._stream_task(task, timeout):
                        yield chunk
                        # Cache substantial chunks for performance modes
                        if self.enable_caching and len(chunk) > 50:
                            self._cache_response(prompt, chunk)
                else:
                    # Non-streaming response
                    result = await self._wait_for_completion(task, timeout)
                    if result and result.strip():
                        # Cache successful responses
                        if self.enable_caching:
                            self._cache_response(prompt, result)
                        
                        # Update stats
                        elapsed = time.time() - start_time
                        self._update_response_time_stats(elapsed)
                        
                        yield result
                        return
                    else:
                        logger.warning(f"⚠️ Empty result on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff
                            await asyncio.sleep(wait_time)
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
                    self.stats["requests_failed"] += 1
                    error_msg = f"Failed after {max_retries} attempts. Last error: {str(last_error)}"
                    logger.error(f"💥 {error_msg}")
                    yield error_msg
    
    async def _wait_for_completion(self, task, timeout: float) -> str:
        """
        Wait for task completion with adaptive polling and multiple extraction strategies.
        """
        start_time = time.time()
        initial_poll_interval = self.poll_interval
        max_poll_interval = 3.0
        current_poll_interval = initial_poll_interval
        
        logger.info(f"⏳ Waiting for task {task.id} completion (max {timeout}s)")
        
        consecutive_same_status = 0
        last_status = None
        
        while time.time() - start_time < timeout:
            try:
                # Refresh task status
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                # Adaptive polling (if enabled)
                if self.enable_adaptive_polling:
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
                    return self._extract_result(task)
                
                # Check if failed
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    logger.warning(f"⚠️ Task {task.id} failed with status: {status}")
                    # Try to extract any partial result before giving up
                    partial_result = self._extract_result(task)
                    if partial_result and partial_result.strip():
                        return partial_result
                    return f"Task failed with status: {status}"
                
                # Sleep with current interval
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
            final_result = self._extract_result(task)
            if final_result and final_result.strip():
                logger.info(f"🎯 Recovered result from timed-out task!")
                return final_result
        except Exception as e:
            logger.error(f"❌ Final extraction failed: {e}")
        
        elapsed = time.time() - start_time
        return f"Task timed out after {elapsed:.1f} seconds. Please try again with a simpler request."
    
    def _extract_result(self, task) -> str:
        """
        Extract result using multiple strategies based on client mode.
        """
        logger.debug(f"🔍 Extracting result for task {task.id} (mode: {self.mode.value})")
        
        # Strategy 1: Try common result attributes
        result_attributes = [
            'result', 'output', 'response', 'content', 'text', 
            'message', 'data', 'answer', 'completion', 'generated_text'
        ]
        
        for attr in result_attributes:
            if hasattr(task, attr):
                value = getattr(task, attr)
                if value:
                    result_text = self._convert_to_text(value)
                    if result_text and result_text.strip():
                        logger.info(f"✅ Found result in task.{attr} ({len(result_text)} chars)")
                        return result_text.strip()
        
        # Strategy 2: Try method calls (for reliable/production modes)
        if self.mode in [ClientMode.RELIABLE, ClientMode.PRODUCTION]:
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
                                result_text = self._convert_to_text(value)
                                if result_text and result_text.strip():
                                    logger.info(f"✅ Found result via {method_name}() ({len(result_text)} chars)")
                                    return result_text.strip()
                    except Exception as e:
                        logger.debug(f"Failed to call {method_name}(): {e}")
        
        # Strategy 3: Deep inspection (for production mode only)
        if self.mode == ClientMode.PRODUCTION:
            try:
                if hasattr(task, '__dict__'):
                    task_dict = task.__dict__
                    for key, value in task_dict.items():
                        if any(keyword in key.lower() for keyword in ['result', 'output', 'response']):
                            if value:
                                result_text = self._convert_to_text(value)
                                if result_text and result_text.strip():
                                    logger.info(f"✅ Found result in task.{key} ({len(result_text)} chars)")
                                    return result_text.strip()
            except Exception as e:
                logger.debug(f"Failed to access task.__dict__: {e}")
        
        # If nothing found
        logger.warning(f"⚠️ No result found for task {task.id}")
        return "Task completed successfully but no response content was found."
    
    def _convert_to_text(self, value) -> str:
        """Convert various value types to text."""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Try common text keys
            text_keys = ['text', 'content', 'message', 'response', 'output', 'result', 'answer']
            for key in text_keys:
                if key in value and value[key]:
                    return str(value[key])
            
            # Try to find any substantial text content
            for key, val in value.items():
                if isinstance(val, str) and len(val) > 10:
                    return val
            
            # Fallback to JSON representation for production mode
            if self.mode == ClientMode.PRODUCTION:
                try:
                    json_str = json.dumps(value, indent=2)
                    if len(json_str) > 50:
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
                    converted = self._convert_to_text(item)
                    if converted and len(converted) > 10:
                        return converted
            return ""
        else:
            return str(value) if value else ""
    
    async def _stream_task(self, task, timeout: float) -> AsyncGenerator[str, None]:
        """
        Stream task results with progress tracking.
        """
        start_time = time.time()
        poll_interval = max(1.0, self.poll_interval * 2)  # Slower polling for streaming
        max_polls = int(timeout / poll_interval)
        last_content = ""
        content_updates = 0
        
        logger.info(f"🌊 Streaming task {task.id}")
        
        for attempt in range(max_polls):
            try:
                task.refresh()
                status = str(task.status).upper()
                elapsed = time.time() - start_time
                
                # Check for completion
                if status in ["COMPLETE", "COMPLETED", "FINISHED", "DONE"]:
                    # Get final result
                    final_result = self._extract_result(task)
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
                    
                    logger.info(f"✅ Stream completed for task {task.id} ({content_updates} updates)")
                    return
                
                # Check for failure
                if status in ["FAILED", "ERROR", "CANCELLED"]:
                    yield f"Task failed with status: {status}"
                    return
                
                # Try to get partial content
                current_content = self._extract_result(task)
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
                logger.error(f"❌ Streaming error: {e}")
                await asyncio.sleep(poll_interval)
                continue
        
        # Timeout
        if content_updates > 0:
            yield f"\n\n[Stream completed with {content_updates} updates after {timeout}s timeout]"
        else:
            yield f"Stream timed out after {timeout} seconds with no content received."
    
    def _cache_response(self, prompt: str, response: str):
        """Cache response for future use."""
        if self.response_cache is not None:
            prompt_hash = hash(prompt)
            self.response_cache[prompt_hash] = response
            logger.debug(f"📦 Cached response for prompt hash: {prompt_hash}")
    
    def _update_response_time_stats(self, elapsed_time: float):
        """Update response time statistics."""
        if self.stats["requests_total"] == 1:
            self.stats["average_response_time"] = elapsed_time
        else:
            # Running average
            total_requests = self.stats["requests_total"]
            current_avg = self.stats["average_response_time"]
            self.stats["average_response_time"] = ((current_avg * (total_requests - 1)) + elapsed_time) / total_requests
    
    def count_tokens(self, text: str) -> int:
        """Enhanced token estimation."""
        if not text:
            return 0
        
        # More accurate token estimation
        word_count = len(text.split())
        char_based_estimate = len(text) // 4
        
        # Use the higher estimate for safety
        return max(word_count, char_based_estimate, 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        stats = self.stats.copy()
        stats["mode"] = self.mode.value
        stats["cache_enabled"] = self.enable_caching
        stats["cache_size"] = len(self.response_cache) if self.response_cache else 0
        return stats
    
    def clear_cache(self):
        """Clear the response cache."""
        if self.response_cache is not None:
            cache_size = len(self.response_cache)
            self.response_cache.clear()
            logger.info(f"🧹 Cleared cache ({cache_size} entries)")
    
    def set_mode(self, mode: ClientMode):
        """Change client operation mode."""
        old_mode = self.mode
        self.mode = mode
        self._configure_for_mode()
        logger.info(f"🔄 Changed client mode from {old_mode.value} to {mode.value}")
    
    # Backward compatibility methods
    async def run_task_simple(self, prompt: str) -> str:
        """Simple non-streaming task execution for backward compatibility."""
        async for result in self.run_task(prompt, stream=False):
            return result
        return "No response generated"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (backward compatibility)."""
        return {
            "cached_responses": len(self.response_cache) if self.response_cache else 0,
            "cache_size_bytes": sum(len(str(v)) for v in self.response_cache.values()) if self.response_cache else 0,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"]
        }

