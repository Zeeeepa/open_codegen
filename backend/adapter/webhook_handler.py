"""
Webhook handler for Codegen API callbacks.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from fastapi import Request

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles webhook callbacks from Codegen API."""
    
    def __init__(self):
        """Initialize the webhook handler."""
        self.tasks = {}  # Store task state by task_id
        self.callbacks = {}  # Store callback functions by task_id
        self.results = {}  # Store task results by task_id
        self.events = {}  # Store asyncio events by task_id
        self.cleanup_interval = 3600  # Cleanup old tasks every hour
        self.last_cleanup = datetime.now()
        logger.info("Initialized WebhookHandler")
    
    def register_task(self, task_id: str, callback: Optional[Callable] = None) -> asyncio.Event:
        """
        Register a task for webhook callbacks.
        
        Args:
            task_id: The ID of the task to register
            callback: Optional callback function to call when the task completes
            
        Returns:
            asyncio.Event: An event that will be set when the task completes
        """
        self.tasks[task_id] = {
            "status": "PENDING",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        if callback:
            self.callbacks[task_id] = callback
        
        # Create an event for this task
        event = asyncio.Event()
        self.events[task_id] = event
        
        logger.info(f"Registered task {task_id} for webhook callbacks")
        
        # Cleanup old tasks if needed
        self._cleanup_old_tasks()
        
        return event
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle a webhook callback from Codegen API.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            Dict[str, Any]: Response to send back to Codegen API
        """
        try:
            # Parse the webhook payload
            payload = await request.json()
            logger.info(f"Received webhook payload: {payload}")
            
            # Extract task ID and status
            task_id = payload.get("task_id")
            status = payload.get("status", "UNKNOWN").upper()
            result = payload.get("result")
            
            if not task_id:
                logger.warning("Webhook payload missing task_id")
                return {"status": "error", "message": "Missing task_id"}
            
            # Update task status
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = status
                self.tasks[task_id]["updated_at"] = datetime.now()
                
                # Store result if provided
                if result:
                    self.results[task_id] = result
                
                # Set event if task is complete
                if status in ["COMPLETE", "FAILED"]:
                    if task_id in self.events:
                        logger.info(f"Setting event for task {task_id} with status {status}")
                        self.events[task_id].set()
                    
                    # Call callback if registered
                    if task_id in self.callbacks and self.callbacks[task_id]:
                        try:
                            self.callbacks[task_id](task_id, status, result)
                        except Exception as e:
                            logger.error(f"Error calling callback for task {task_id}: {e}")
                
                return {"status": "success", "task_id": task_id}
            else:
                logger.warning(f"Received webhook for unknown task {task_id}")
                return {"status": "error", "message": f"Unknown task {task_id}"}
        
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        Get the result of a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Optional[Any]: The task result, or None if not available
        """
        return self.results.get(task_id)
    
    def get_task_status(self, task_id: str) -> str:
        """
        Get the status of a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            str: The task status, or "UNKNOWN" if not found
        """
        if task_id in self.tasks:
            return self.tasks[task_id]["status"]
        return "UNKNOWN"
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for a task to complete.
        
        Args:
            task_id: The ID of the task to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if the task completed, False if timed out
        """
        if task_id not in self.events:
            logger.warning(f"Attempted to wait for unregistered task {task_id}")
            return False
        
        try:
            logger.info(f"Waiting for task {task_id} with timeout {timeout}s")
            return await asyncio.wait_for(self.events[task_id].wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task {task_id}")
            return False
    
    def _cleanup_old_tasks(self):
        """Clean up old tasks to prevent memory leaks."""
        now = datetime.now()
        
        # Only clean up once per interval
        if (now - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        self.last_cleanup = now
        
        # Find tasks older than cleanup_interval
        old_tasks = []
        for task_id, task in self.tasks.items():
            if (now - task["updated_at"]).total_seconds() > self.cleanup_interval:
                old_tasks.append(task_id)
        
        # Remove old tasks
        for task_id in old_tasks:
            logger.info(f"Cleaning up old task {task_id}")
            self.tasks.pop(task_id, None)
            self.callbacks.pop(task_id, None)
            self.results.pop(task_id, None)
            self.events.pop(task_id, None)
        
        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old tasks")

