"""
Endpoint models for Universal AI Endpoint Manager

Defines the core data structures for managing AI endpoints with trading bot-style architecture.
Similar to the cryptocurrency bot's account and transaction models but adapted for AI services.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class EndpointType(Enum):
    """Types of AI endpoints supported"""
    REST_API = "rest_api"
    WEB_CHAT = "web_chat"
    CODEGEN_API = "codegen_api"
    OPENAI_API = "openai_api"
    ANTHROPIC_API = "anthropic_api"
    GEMINI_API = "gemini_api"
    DEEPINFRA_API = "deepinfra_api"
    DEEPSEEK_API = "deepseek_api"
    ZAI_WEB = "zai_web"
    CUSTOM_WEB = "custom_web"

class EndpointStatus(Enum):
    """Status of endpoints - similar to crypto bot's transaction status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"

class HealthStatus(Enum):
    """Health status of endpoints"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class EndpointCredentials:
    """Secure credential storage for endpoints"""
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    base_url: Optional[str] = None
    additional_headers: Dict[str, str] = field(default_factory=dict)
    custom_auth: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "username": self.username,
            "password": self.password,
            "base_url": self.base_url,
            "additional_headers": self.additional_headers,
            "custom_auth": self.custom_auth
        }

@dataclass
class BrowserConfig:
    """Configuration for browser automation endpoints"""
    headless: bool = True
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30
    anti_detection: bool = True
    fingerprint_rotation: bool = True
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "headless": self.headless,
            "user_agent": self.user_agent,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "timeout": self.timeout,
            "anti_detection": self.anti_detection,
            "fingerprint_rotation": self.fingerprint_rotation,
            "proxy_enabled": self.proxy_enabled,
            "proxy_url": self.proxy_url
        }

@dataclass
class EndpointMetrics:
    """Performance metrics for endpoints - similar to crypto bot's performance tracking"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_start: Optional[datetime] = None
    total_tokens_used: int = 0
    estimated_cost: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
    
    @property
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds"""
        if self.uptime_start is None:
            return 0.0
        return (datetime.now() - self.uptime_start).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "average_response_time": self.average_response_time,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "uptime_start": self.uptime_start.isoformat() if self.uptime_start else None,
            "uptime_seconds": self.uptime_seconds,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self.estimated_cost
        }

@dataclass
class EndpointConfig:
    """
    Main endpoint configuration class - similar to crypto bot's account configuration
    Represents a single AI endpoint that can be managed like a trading position
    """
    
    # Basic identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    display_name: str = ""
    endpoint_type: EndpointType = EndpointType.REST_API
    
    # Connection details
    url: str = ""
    credentials: EndpointCredentials = field(default_factory=EndpointCredentials)
    
    # Configuration
    model_name: str = ""
    default_model: str = ""
    supported_models: List[str] = field(default_factory=list)
    
    # Browser automation (for web chat endpoints)
    browser_config: Optional[BrowserConfig] = None
    
    # Status and health
    status: EndpointStatus = EndpointStatus.STOPPED
    health: HealthStatus = HealthStatus.UNKNOWN
    
    # Performance and monitoring
    metrics: EndpointMetrics = field(default_factory=EndpointMetrics)
    
    # Trading bot-style settings
    priority: int = 1  # Higher number = higher priority
    auto_restart: bool = True
    max_concurrent_requests: int = 10
    rate_limit_per_minute: int = 60
    
    # Session management
    persistent_session: bool = True
    session_timeout: int = 3600  # 1 hour
    
    # Advanced settings
    retry_attempts: int = 3
    timeout: int = 300
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_health_check: Optional[datetime] = None
    
    # AI-assisted discovery data
    discovered_by_ai: bool = False
    ai_confidence_score: float = 0.0
    ai_analysis_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization setup"""
        if not self.display_name:
            self.display_name = self.name
        
        if not self.name:
            self.name = f"{self.endpoint_type.value}_{self.id[:8]}"
        
        # Set up browser config for web chat endpoints
        if self.endpoint_type in [EndpointType.WEB_CHAT, EndpointType.ZAI_WEB, EndpointType.CUSTOM_WEB]:
            if self.browser_config is None:
                self.browser_config = BrowserConfig()
    
    def update_status(self, new_status: EndpointStatus):
        """Update endpoint status with timestamp"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == EndpointStatus.RUNNING and self.metrics.uptime_start is None:
            self.metrics.uptime_start = datetime.now()
        elif new_status == EndpointStatus.STOPPED:
            self.metrics.uptime_start = None
    
    def update_health(self, new_health: HealthStatus):
        """Update health status with timestamp"""
        self.health = new_health
        self.last_health_check = datetime.now()
        self.updated_at = datetime.now()
    
    def record_request(self, success: bool, response_time: float, tokens_used: int = 0, cost: float = 0.0):
        """Record a request for metrics tracking - similar to crypto bot's transaction recording"""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = datetime.now()
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update average response time
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) 
                / self.metrics.total_requests
            )
        
        self.metrics.total_tokens_used += tokens_used
        self.metrics.estimated_cost += cost
        self.updated_at = datetime.now()
    
    def is_healthy(self) -> bool:
        """Check if endpoint is healthy"""
        return self.health in [HealthStatus.EXCELLENT, HealthStatus.GOOD, HealthStatus.FAIR]
    
    def is_running(self) -> bool:
        """Check if endpoint is running"""
        return self.status == EndpointStatus.RUNNING
    
    def can_handle_request(self) -> bool:
        """Check if endpoint can handle a new request"""
        return self.is_running() and self.is_healthy()
    
    def get_model_identifier(self) -> str:
        """Get unique model identifier for this endpoint - similar to crypto bot's asset identification"""
        if self.endpoint_type == EndpointType.WEB_CHAT:
            # For web chat endpoints, create unique identifiers like webdeepseek1, webdeepseek8
            base_name = self.name.lower().replace(" ", "").replace("-", "").replace("_", "")
            return f"web{base_name}{self.id[:1]}"
        else:
            return f"{self.endpoint_type.value}_{self.model_name or self.default_model}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "endpoint_type": self.endpoint_type.value,
            "url": self.url,
            "credentials": self.credentials.to_dict(),
            "model_name": self.model_name,
            "default_model": self.default_model,
            "supported_models": self.supported_models,
            "browser_config": self.browser_config.to_dict() if self.browser_config else None,
            "status": self.status.value,
            "health": self.health.value,
            "metrics": self.metrics.to_dict(),
            "priority": self.priority,
            "auto_restart": self.auto_restart,
            "max_concurrent_requests": self.max_concurrent_requests,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "persistent_session": self.persistent_session,
            "session_timeout": self.session_timeout,
            "retry_attempts": self.retry_attempts,
            "timeout": self.timeout,
            "custom_config": self.custom_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "discovered_by_ai": self.discovered_by_ai,
            "ai_confidence_score": self.ai_confidence_score,
            "ai_analysis_data": self.ai_analysis_data,
            "model_identifier": self.get_model_identifier()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EndpointConfig':
        """Create EndpointConfig from dictionary"""
        # Handle datetime fields
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        last_health_check = None
        if data.get("last_health_check"):
            last_health_check = datetime.fromisoformat(data["last_health_check"])
        
        # Handle credentials
        credentials_data = data.get("credentials", {})
        credentials = EndpointCredentials(**credentials_data)
        
        # Handle browser config
        browser_config = None
        if data.get("browser_config"):
            browser_config = BrowserConfig(**data["browser_config"])
        
        # Handle metrics
        metrics_data = data.get("metrics", {})
        metrics = EndpointMetrics()
        for key, value in metrics_data.items():
            if hasattr(metrics, key) and key not in ["success_rate", "error_rate", "uptime_seconds"]:
                if key in ["last_request_time", "uptime_start"] and value:
                    setattr(metrics, key, datetime.fromisoformat(value))
                else:
                    setattr(metrics, key, value)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            endpoint_type=EndpointType(data.get("endpoint_type", EndpointType.REST_API.value)),
            url=data.get("url", ""),
            credentials=credentials,
            model_name=data.get("model_name", ""),
            default_model=data.get("default_model", ""),
            supported_models=data.get("supported_models", []),
            browser_config=browser_config,
            status=EndpointStatus(data.get("status", EndpointStatus.STOPPED.value)),
            health=HealthStatus(data.get("health", HealthStatus.UNKNOWN.value)),
            metrics=metrics,
            priority=data.get("priority", 1),
            auto_restart=data.get("auto_restart", True),
            max_concurrent_requests=data.get("max_concurrent_requests", 10),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 60),
            persistent_session=data.get("persistent_session", True),
            session_timeout=data.get("session_timeout", 3600),
            retry_attempts=data.get("retry_attempts", 3),
            timeout=data.get("timeout", 300),
            custom_config=data.get("custom_config", {}),
            created_at=created_at,
            updated_at=updated_at,
            last_health_check=last_health_check,
            discovered_by_ai=data.get("discovered_by_ai", False),
            ai_confidence_score=data.get("ai_confidence_score", 0.0),
            ai_analysis_data=data.get("ai_analysis_data", {})
        )
