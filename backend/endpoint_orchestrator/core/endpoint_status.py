"""
Endpoint status tracking and health monitoring for the AI Endpoint Orchestrator.

Provides status enums and data structures for tracking endpoint health,
performance metrics, and operational state.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EndpointStatus(str, Enum):
    """Status of endpoint instances - similar to trading position status."""
    STOPPED = "stopped"           # Like a closed position
    STARTING = "starting"         # Like opening a position
    RUNNING = "running"           # Like an active position
    STOPPING = "stopping"        # Like closing a position
    ERROR = "error"              # Like a failed trade
    MAINTENANCE = "maintenance"   # Like a paused strategy
    SCALING = "scaling"          # Like adjusting position size


class HealthStatus(str, Enum):
    """Health status of endpoints - similar to trading performance."""
    EXCELLENT = "excellent"      # Like high-profit trades
    GOOD = "good"               # Like profitable trades
    FAIR = "fair"               # Like break-even trades
    POOR = "poor"               # Like losing trades
    CRITICAL = "critical"       # Like major losses
    UNKNOWN = "unknown"         # Like untested strategy


@dataclass
class PerformanceMetrics:
    """Performance metrics for endpoints - trading bot style analytics."""
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Timing metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    
    # Throughput metrics
    requests_per_minute: float = 0.0
    requests_per_hour: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    
    # Resource metrics
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Trading bot style metrics
    success_rate: float = 0.0
    profit_score: float = 0.0  # Based on success rate and response time
    efficiency_score: float = 0.0  # Requests per resource unit
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    measurement_window_minutes: int = 60
    
    def update_metrics(self, response_time_ms: float, success: bool, cpu_usage: float = 0.0, memory_usage: float = 0.0):
        """Update metrics with new data point."""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update timing metrics
        if response_time_ms < self.min_response_time_ms:
            self.min_response_time_ms = response_time_ms
        if response_time_ms > self.max_response_time_ms:
            self.max_response_time_ms = response_time_ms
        
        # Calculate rolling average
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms) / 
            self.total_requests
        )
        
        # Update rates
        self.success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
        self.error_rate = self.failed_requests / self.total_requests if self.total_requests > 0 else 0.0
        
        # Update resource usage
        self.cpu_usage_percent = cpu_usage
        self.memory_usage_mb = memory_usage
        
        # Calculate trading bot style scores
        self._calculate_scores()
        
        self.last_updated = datetime.utcnow()
    
    def _calculate_scores(self):
        """Calculate trading bot style performance scores."""
        # Profit score: high success rate + low response time = high profit
        if self.avg_response_time_ms > 0:
            response_time_factor = max(0, 1 - (self.avg_response_time_ms / 10000))  # Normalize to 10s max
            self.profit_score = (self.success_rate * 0.7 + response_time_factor * 0.3) * 100
        else:
            self.profit_score = self.success_rate * 100
        
        # Efficiency score: requests per resource unit
        if self.cpu_usage_percent > 0 and self.memory_usage_mb > 0:
            resource_factor = 100 / (self.cpu_usage_percent + self.memory_usage_mb / 100)
            self.efficiency_score = self.requests_per_minute * resource_factor
        else:
            self.efficiency_score = self.requests_per_minute
    
    def get_health_status(self) -> HealthStatus:
        """Determine health status based on metrics."""
        if self.total_requests == 0:
            return HealthStatus.UNKNOWN
        
        if self.success_rate >= 0.95 and self.avg_response_time_ms < 2000:
            return HealthStatus.EXCELLENT
        elif self.success_rate >= 0.90 and self.avg_response_time_ms < 5000:
            return HealthStatus.GOOD
        elif self.success_rate >= 0.80 and self.avg_response_time_ms < 10000:
            return HealthStatus.FAIR
        elif self.success_rate >= 0.60:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL


@dataclass
class EndpointInstance:
    """Individual endpoint instance - like a trading position."""
    instance_id: str
    endpoint_name: str
    model_name: str
    status: EndpointStatus = EndpointStatus.STOPPED
    health: HealthStatus = HealthStatus.UNKNOWN
    
    # Instance details
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Performance tracking
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    
    # Configuration
    config_hash: Optional[str] = None
    priority: int = 1
    
    # Resource allocation
    allocated_cpu: float = 0.0
    allocated_memory_mb: float = 0.0
    
    # Session information (for web chat endpoints)
    session_id: Optional[str] = None
    browser_profile_path: Optional[str] = None
    cookies_saved: bool = False
    
    # Error tracking
    consecutive_errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    def update_status(self, new_status: EndpointStatus, message: Optional[str] = None):
        """Update instance status with logging."""
        old_status = self.status
        self.status = new_status
        self.last_activity = datetime.utcnow()
        
        if new_status == EndpointStatus.RUNNING and old_status != EndpointStatus.RUNNING:
            self.started_at = datetime.utcnow()
        
        logger.info(f"Instance {self.instance_id} status: {old_status} -> {new_status}")
        if message:
            logger.info(f"Instance {self.instance_id}: {message}")
    
    def record_error(self, error_message: str):
        """Record an error for this instance."""
        self.consecutive_errors += 1
        self.last_error = error_message
        self.last_error_time = datetime.utcnow()
        
        # Update health based on error frequency
        if self.consecutive_errors >= 5:
            self.health = HealthStatus.CRITICAL
        elif self.consecutive_errors >= 3:
            self.health = HealthStatus.POOR
        
        logger.error(f"Instance {self.instance_id} error #{self.consecutive_errors}: {error_message}")
    
    def record_success(self, response_time_ms: float):
        """Record a successful request."""
        self.consecutive_errors = 0  # Reset error counter
        self.last_activity = datetime.utcnow()
        
        # Update metrics
        self.metrics.update_metrics(response_time_ms, True)
        
        # Update health status
        self.health = self.metrics.get_health_status()
    
    def is_healthy(self) -> bool:
        """Check if instance is healthy and operational."""
        if self.status != EndpointStatus.RUNNING:
            return False
        
        if self.health in [HealthStatus.CRITICAL, HealthStatus.POOR]:
            return False
        
        # Check if instance has been inactive for too long
        if self.last_activity:
            inactive_duration = datetime.utcnow() - self.last_activity
            if inactive_duration > timedelta(minutes=30):
                return False
        
        return True
    
    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        if self.started_at and self.status == EndpointStatus.RUNNING:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary for API responses."""
        return {
            "instance_id": self.instance_id,
            "endpoint_name": self.endpoint_name,
            "model_name": self.model_name,
            "status": self.status.value,
            "health": self.health.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "uptime_seconds": self.get_uptime_seconds(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "avg_response_time_ms": self.metrics.avg_response_time_ms,
                "profit_score": self.metrics.profit_score,
                "efficiency_score": self.metrics.efficiency_score,
                "requests_per_minute": self.metrics.requests_per_minute
            },
            "consecutive_errors": self.consecutive_errors,
            "last_error": self.last_error,
            "priority": self.priority,
            "session_active": self.session_id is not None,
            "cookies_saved": self.cookies_saved
        }


@dataclass
class EndpointSummary:
    """Summary status for an endpoint with all its instances."""
    endpoint_name: str
    model_name: str
    endpoint_type: str
    total_instances: int = 0
    running_instances: int = 0
    healthy_instances: int = 0
    
    # Aggregate metrics
    total_requests: int = 0
    total_success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    total_profit_score: float = 0.0
    
    # Status distribution
    status_counts: Dict[str, int] = field(default_factory=dict)
    health_counts: Dict[str, int] = field(default_factory=dict)
    
    # Configuration
    enabled: bool = True
    priority: int = 1
    max_instances: int = 10
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_from_instances(self, instances: List[EndpointInstance]):
        """Update summary from list of instances."""
        self.total_instances = len(instances)
        self.running_instances = sum(1 for i in instances if i.status == EndpointStatus.RUNNING)
        self.healthy_instances = sum(1 for i in instances if i.is_healthy())
        
        # Reset counters
        self.status_counts = {}
        self.health_counts = {}
        
        # Aggregate metrics
        if instances:
            self.total_requests = sum(i.metrics.total_requests for i in instances)
            
            # Calculate weighted averages
            total_weight = sum(max(1, i.metrics.total_requests) for i in instances)
            if total_weight > 0:
                self.total_success_rate = sum(
                    i.metrics.success_rate * max(1, i.metrics.total_requests) 
                    for i in instances
                ) / total_weight
                
                self.avg_response_time_ms = sum(
                    i.metrics.avg_response_time_ms * max(1, i.metrics.total_requests)
                    for i in instances
                ) / total_weight
                
                self.total_profit_score = sum(
                    i.metrics.profit_score * max(1, i.metrics.total_requests)
                    for i in instances
                ) / total_weight
        
        # Count status and health distributions
        for instance in instances:
            status = instance.status.value
            health = instance.health.value
            
            self.status_counts[status] = self.status_counts.get(status, 0) + 1
            self.health_counts[health] = self.health_counts.get(health, 0) + 1
        
        self.last_updated = datetime.utcnow()
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall health status for the endpoint."""
        if self.healthy_instances == 0:
            return HealthStatus.CRITICAL
        
        healthy_ratio = self.healthy_instances / max(1, self.total_instances)
        
        if healthy_ratio >= 0.9:
            return HealthStatus.EXCELLENT
        elif healthy_ratio >= 0.7:
            return HealthStatus.GOOD
        elif healthy_ratio >= 0.5:
            return HealthStatus.FAIR
        else:
            return HealthStatus.POOR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary for API responses."""
        return {
            "endpoint_name": self.endpoint_name,
            "model_name": self.model_name,
            "endpoint_type": self.endpoint_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "instances": {
                "total": self.total_instances,
                "running": self.running_instances,
                "healthy": self.healthy_instances,
                "max_allowed": self.max_instances
            },
            "metrics": {
                "total_requests": self.total_requests,
                "success_rate": self.total_success_rate,
                "avg_response_time_ms": self.avg_response_time_ms,
                "profit_score": self.total_profit_score
            },
            "status_distribution": self.status_counts,
            "health_distribution": self.health_counts,
            "overall_health": self.get_overall_health().value,
            "last_updated": self.last_updated.isoformat()
        }
