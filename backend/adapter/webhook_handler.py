"""
Webhook handler for Codegen API callbacks.
Manages task state and response handling for asynchronous operations.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from fastapi import Request

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles webhook callbacks from Codegen API."""
    
    def __init__(self):
        self.tasks = {}  # Store task state by task_id
        self.callbacks = {}  # Store callback functions by task_id
        self.results = {}  # Store task results by task_id
        self.events = {}  # Store asyncio events by task_id
        self.cleanup_interval = 3600  # Cleanup old tasks every hour
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old task data."""
        asyncio.create_task(self._cleanup_old_tasks())
    
    async def _cleanup_old_tasks(self):
        """Periodically clean up old task data."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                now = datetime.now()
                expired_tasks = []
                
                for task_id, task_data in self.tasks.items():
                    if task_data.get("created_at") and now - task_data["created_at"] > timedelta(hours=24):
                        expired_tasks.append(task_id)
                
                for task_id in expired_tasks:
                    logger.info(f"Cleaning up expired task data for task {task_id}")
                    self._remove_task(task_id)
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def _remove_task(self, task_id: str):
        """Remove all data for a task."""
        self.tasks.pop(task_id, None)
        self.callbacks.pop(task_id, None)
        self.results.pop(task_id, None)
        self.events.pop(task_id, None)
    
    def register_task(self, task_id: str, callback: Optional[Callable] = None) -> asyncio.Event:
        """
        Register a new task for webhook callbacks.
        
        Args:
            task_id: The Codegen task ID
            callback: Optional callback function to call when task completes
            
        Returns:
            An asyncio Event that will be set when the task completes
        """
        logger.info(f"Registering task {task_id} for webhook callbacks")
        
        # Create task data
        self.tasks[task_id] = {
            "status": "PENDING",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Store callback if provided
        if callback:
            self.callbacks[task_id] = callback
        
        # Create and store event
        event = asyncio.Event()
        self.events[task_id] = event
        
        return event
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle incoming webhook from Codegen API.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            Response data to send back to Codegen API
        """
        try:
            # Parse webhook payload
            payload = await request.json()
            logger.info(f"Received webhook: {json.dumps(payload)[:200]}...")
            
            # Extract task ID and status
            task_id = payload.get("task_id")
            if not task_id:
                logger.warning(f"Webhook missing task_id: {payload}")
                return {"status": "error", "message": "Missing task_id"}
            
            # Update task status
            status = payload.get("status", "UNKNOWN").upper()
            result = payload.get("result")
            
            # Store task data
            self.tasks[task_id] = {
                "status": status,
                "updated_at": datetime.now(),
                "payload": payload
            }
            
            # Store result if available
            if result:
                self.results[task_id] = result
            
            # If task is complete, trigger callback and set event
            if status in ["COMPLETE", "COMPLETED", "DONE", "SUCCESS"]:
                logger.info(f"Task {task_id} completed successfully")
                
                # Call callback if registered
                if task_id in self.callbacks and self.callbacks[task_id]:
                    try:
                        self.callbacks[task_id](task_id, result, None)
                    except Exception as e:
                        logger.error(f"Error in callback for task {task_id}: {e}")
                
                # Set event to unblock waiting coroutines
                if task_id in self.events:
                    self.events[task_id].set()
            
            # If task failed, log error and set event
            elif status in ["FAILED", "ERROR"]:
                error = payload.get("error", "Unknown error")
                logger.error(f"Task {task_id} failed: {error}")
                
                # Call callback with error if registered
                if task_id in self.callbacks and self.callbacks[task_id]:
                    try:
                        self.callbacks[task_id](task_id, None, error)
                    except Exception as e:
                        logger.error(f"Error in callback for task {task_id}: {e}")
                
                # Set event to unblock waiting coroutines
                if task_id in self.events:
                    self.events[task_id].set()
            
            return {"status": "success", "task_id": task_id}
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        Get the result for a completed task.
        
        Args:
            task_id: The Codegen task ID
            
        Returns:
            The task result or None if not available
        """
        return self.results.get(task_id)
    
    def get_task_status(self, task_id: str) -> str:
        """
        Get the current status of a task.
        
        Args:
            task_id: The Codegen task ID
            
        Returns:
            The task status or "UNKNOWN" if not found
        """
        task_data = self.tasks.get(task_id, {})
        return task_data.get("status", "UNKNOWN")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for a task to complete.
        
        Args:
            task_id: The Codegen task ID
            timeout: Optional timeout in seconds
            
        Returns:
            True if task completed successfully, False if timed out or failed
        """
        if task_id not in self.events:
            logger.warning(f"Task {task_id} not registered for waiting")
            return False
        
        try:
            # Wait for the event to be set
            await asyncio.wait_for(self.events[task_id].wait(), timeout=timeout)
            
            # Check if task completed successfully
            status = self.get_task_status(task_id)
            return status in ["COMPLETE", "COMPLETED", "DONE", "SUCCESS"]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task {task_id}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for task {task_id}: {e}")
            return False

