"""
Metrics and monitoring utilities for the OpenAI Codegen Adapter.
Tracks API usage, performance, and health metrics.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    tokens_input: int = 0
    tokens_output: int = 0
    model: Optional[str] = None
    api_format: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """Collects and aggregates metrics for the adapter."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.requests: deque = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'total_tokens_input': 0,
            'total_tokens_output': 0,
            'errors': 0
        })
        self.model_stats = defaultdict(lambda: {
            'count': 0,
            'total_tokens': 0,
            'avg_duration': 0
        })
        self.start_time = datetime.now()
    
    def record_request(self, metrics: RequestMetrics) -> None:
        """Record metrics for a completed request."""
        self.requests.append(metrics)
        
        # Update endpoint stats
        endpoint_key = f"{metrics.method} {metrics.endpoint}"
        stats = self.endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_duration'] += metrics.duration_ms
        stats['total_tokens_input'] += metrics.tokens_input
        stats['total_tokens_output'] += metrics.tokens_output
        
        if metrics.status_code >= 400:
            stats['errors'] += 1
        
        # Update model stats
        if metrics.model:
            model_stats = self.model_stats[metrics.model]
            model_stats['count'] += 1
            model_stats['total_tokens'] += metrics.tokens_input + metrics.tokens_output
            
            # Update average duration
            if model_stats['count'] == 1:
                model_stats['avg_duration'] = metrics.duration_ms
            else:
                model_stats['avg_duration'] = (
                    (model_stats['avg_duration'] * (model_stats['count'] - 1) + metrics.duration_ms) 
                    / model_stats['count']
                )
        
        logger.info(f"📊 Request recorded: {endpoint_key} - {metrics.duration_ms:.2f}ms - {metrics.status_code}")
    
    def get_summary_stats(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for the specified time window."""
        now = datetime.now()
        
        # Filter requests by time window if specified
        if time_window_minutes:
            cutoff_time = now - timedelta(minutes=time_window_minutes)
            filtered_requests = [r for r in self.requests if r.timestamp >= cutoff_time]
        else:
            filtered_requests = list(self.requests)
        
        if not filtered_requests:
            return {
                "total_requests": 0,
                "time_window_minutes": time_window_minutes,
                "uptime_minutes": (now - self.start_time).total_seconds() / 60
            }
        
        # Calculate basic stats
        total_requests = len(filtered_requests)
        successful_requests = sum(1 for r in filtered_requests if r.status_code < 400)
        error_requests = total_requests - successful_requests
        
        durations = [r.duration_ms for r in filtered_requests]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        total_tokens_input = sum(r.tokens_input for r in filtered_requests)
        total_tokens_output = sum(r.tokens_output for r in filtered_requests)
        
        # Calculate requests per minute
        if time_window_minutes:
            rpm = total_requests / time_window_minutes
        else:
            uptime_minutes = (now - self.start_time).total_seconds() / 60
            rpm = total_requests / max(uptime_minutes, 1)
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_requests": error_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "requests_per_minute": rpm,
            "avg_duration_ms": avg_duration,
            "min_duration_ms": min_duration,
            "max_duration_ms": max_duration,
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_tokens": total_tokens_input + total_tokens_output,
            "time_window_minutes": time_window_minutes,
            "uptime_minutes": (now - self.start_time).total_seconds() / 60
        }
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Get statistics by endpoint."""
        stats = {}
        for endpoint, data in self.endpoint_stats.items():
            if data['count'] > 0:
                stats[endpoint] = {
                    "requests": data['count'],
                    "avg_duration_ms": data['total_duration'] / data['count'],
                    "total_tokens_input": data['total_tokens_input'],
                    "total_tokens_output": data['total_tokens_output'],
                    "error_rate": data['errors'] / data['count'],
                    "errors": data['errors']
                }
        return stats
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics by model."""
        return dict(self.model_stats)
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent requests for debugging."""
        recent = list(self.requests)[-limit:]
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "endpoint": r.endpoint,
                "method": r.method,
                "status_code": r.status_code,
                "duration_ms": r.duration_ms,
                "tokens_input": r.tokens_input,
                "tokens_output": r.tokens_output,
                "model": r.model,
                "api_format": r.api_format
            }
            for r in recent
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the adapter."""
        recent_stats = self.get_summary_stats(time_window_minutes=5)
        
        # Determine health status
        if recent_stats["total_requests"] == 0:
            status = "idle"
        elif recent_stats["success_rate"] >= 0.95:
            status = "healthy"
        elif recent_stats["success_rate"] >= 0.8:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "uptime_minutes": recent_stats["uptime_minutes"],
            "recent_requests": recent_stats["total_requests"],
            "recent_success_rate": recent_stats["success_rate"],
            "recent_avg_duration_ms": recent_stats.get("avg_duration_ms", 0),
            "timestamp": datetime.now().isoformat()
        }


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, metrics_collector: MetricsCollector, endpoint: str, method: str = "POST"):
        self.metrics_collector = metrics_collector
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
        self.metrics = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.metrics = RequestMetrics(
            endpoint=self.endpoint,
            method=self.method,
            status_code=200,  # Default, will be updated
            duration_ms=0  # Will be calculated
        )
        return self.metrics
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.duration_ms = duration_ms
            
            # Set error status if exception occurred
            if exc_type:
                self.metrics.status_code = 500
            
            self.metrics_collector.record_request(self.metrics)


# Global metrics collector instance
metrics_collector = MetricsCollector()

