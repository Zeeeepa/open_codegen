"""
Database models for AI Endpoint Management System
SQLite-based models for the open_codegen project
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os


class ProviderType(str, Enum):
    """Types of AI providers supported"""
    REST_API = "rest_api"
    WEB_CHAT = "web_chat"
    API_TOKEN = "api_token"  # Updated from HYBRID


class EndpointStatus(str, Enum):
    """Status of endpoint instances"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AuthType(str, Enum):
    """Authentication types for endpoints"""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH = "oauth"
    COOKIE_SESSION = "cookie_session"
    CUSTOM = "custom"


@dataclass
class RestApiConfig:
    """Configuration for REST API providers"""
    api_base_url: str
    auth_type: str
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: Optional[int] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class WebChatConfig:
    """Configuration for web chat providers"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    login_url: Optional[str] = None
    input_selector: Optional[str] = None
    send_button_selector: Optional[str] = None
    response_selector: Optional[str] = None
    new_chat_selector: Optional[str] = None
    model_selector: Optional[str] = None
    wait_for_response: int = 10
    browser_profile: Optional[str] = None
    use_stealth: bool = True
    custom_headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.custom_headers is None:
            self.custom_headers = {}


@dataclass
class EndpointConfig:
    """Main configuration for AI endpoints"""
    id: str
    user_id: str
    name: str
    model_name: str
    description: Optional[str]
    provider_type: str
    provider_name: str
    config_data: Dict[str, Any]
    status: str
    is_enabled: bool
    priority: int
    max_concurrent_requests: int
    timeout_seconds: int
    retry_attempts: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EndpointConfig':
        """Create EndpointConfig from dictionary"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert EndpointConfig to dictionary"""
        return asdict(self)


@dataclass
class SessionState:
    """Persistent session state for endpoints"""
    id: str
    endpoint_id: str
    session_data: Dict[str, Any]
    browser_profile_path: Optional[str]
    auth_tokens: Dict[str, str]
    cookies: Dict[str, str]
    last_activity: str
    conversation_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create SessionState from dictionary"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert SessionState to dictionary"""
        return asdict(self)


@dataclass
class EndpointMetrics:
    """Performance and usage metrics for endpoints"""
    id: str
    endpoint_id: str
    response_time_ms: int
    success: bool
    error_message: Optional[str]
    input_tokens: int
    output_tokens: int
    request_id: str
    user_agent: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EndpointMetrics':
        """Create EndpointMetrics from dictionary"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert EndpointMetrics to dictionary"""
        return asdict(self)


class DatabaseManager:
    """SQLite database manager for AI endpoints"""
    
    def __init__(self, db_path: str = "backend/database/endpoints.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            # Create endpoint_configs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_configs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    description TEXT,
                    provider_type TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'stopped',
                    is_enabled BOOLEAN NOT NULL DEFAULT 1,
                    priority INTEGER NOT NULL DEFAULT 1,
                    max_concurrent_requests INTEGER NOT NULL DEFAULT 1,
                    timeout_seconds INTEGER NOT NULL DEFAULT 30,
                    retry_attempts INTEGER NOT NULL DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, model_name)
                )
            """)
            
            # Create session_states table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_states (
                    id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    session_data TEXT NOT NULL,
                    browser_profile_path TEXT,
                    auth_tokens TEXT NOT NULL,
                    cookies TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    conversation_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (endpoint_id) REFERENCES endpoint_configs (id) ON DELETE CASCADE,
                    UNIQUE(endpoint_id)
                )
            """)
            
            # Create endpoint_metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_metrics (
                    id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    response_time_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    request_id TEXT NOT NULL,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (endpoint_id) REFERENCES endpoint_configs (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint_configs_user_status ON endpoint_configs(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint_configs_provider_enabled ON endpoint_configs(provider_type, is_enabled)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_endpoint_created ON endpoint_metrics(endpoint_id, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_success_created ON endpoint_metrics(success, created_at)")
            
            conn.commit()
    
    # Endpoint Config CRUD operations
    def create_endpoint_config(self, config: EndpointConfig) -> EndpointConfig:
        """Create a new endpoint configuration"""
        now = datetime.utcnow().isoformat()
        config.created_at = now
        config.updated_at = now
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO endpoint_configs (
                    id, user_id, name, model_name, description, provider_type,
                    provider_name, config_data, status, is_enabled, priority,
                    max_concurrent_requests, timeout_seconds, retry_attempts,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.id, config.user_id, config.name, config.model_name,
                config.description, config.provider_type, config.provider_name,
                json.dumps(config.config_data), config.status, config.is_enabled,
                config.priority, config.max_concurrent_requests, config.timeout_seconds,
                config.retry_attempts, config.created_at, config.updated_at
            ))
            conn.commit()
        
        return config
    
    def get_endpoint_config(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """Get endpoint configuration by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM endpoint_configs WHERE id = ?", (endpoint_id,)
            ).fetchone()
            
            if row:
                data = dict(row)
                data['config_data'] = json.loads(data['config_data'])
                return EndpointConfig.from_dict(data)
            return None
    
    def get_user_endpoint_configs(self, user_id: str) -> List[EndpointConfig]:
        """Get all endpoint configurations for a user"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM endpoint_configs WHERE user_id = ? ORDER BY priority, name",
                (user_id,)
            ).fetchall()
            
            configs = []
            for row in rows:
                data = dict(row)
                data['config_data'] = json.loads(data['config_data'])
                configs.append(EndpointConfig.from_dict(data))
            
            return configs
    
    def update_endpoint_config(self, config: EndpointConfig) -> EndpointConfig:
        """Update endpoint configuration"""
        config.updated_at = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE endpoint_configs SET
                    name = ?, model_name = ?, description = ?, provider_type = ?,
                    provider_name = ?, config_data = ?, status = ?, is_enabled = ?,
                    priority = ?, max_concurrent_requests = ?, timeout_seconds = ?,
                    retry_attempts = ?, updated_at = ?
                WHERE id = ?
            """, (
                config.name, config.model_name, config.description, config.provider_type,
                config.provider_name, json.dumps(config.config_data), config.status,
                config.is_enabled, config.priority, config.max_concurrent_requests,
                config.timeout_seconds, config.retry_attempts, config.updated_at, config.id
            ))
            conn.commit()
        
        return config
    
    def delete_endpoint_config(self, endpoint_id: str) -> bool:
        """Delete endpoint configuration"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM endpoint_configs WHERE id = ?", (endpoint_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_active_endpoints(self, user_id: str) -> List[EndpointConfig]:
        """Get all active (enabled and running) endpoints for a user"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM endpoint_configs 
                WHERE user_id = ? AND is_enabled = 1 AND status = 'running'
                ORDER BY priority, name
            """, (user_id,)).fetchall()
            
            configs = []
            for row in rows:
                data = dict(row)
                data['config_data'] = json.loads(data['config_data'])
                configs.append(EndpointConfig.from_dict(data))
            
            return configs
    
    # Session State CRUD operations
    def create_session_state(self, session: SessionState) -> SessionState:
        """Create a new session state"""
        now = datetime.utcnow().isoformat()
        session.created_at = now
        session.updated_at = now
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO session_states (
                    id, endpoint_id, session_data, browser_profile_path,
                    auth_tokens, cookies, last_activity, conversation_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id, session.endpoint_id, json.dumps(session.session_data),
                session.browser_profile_path, json.dumps(session.auth_tokens),
                json.dumps(session.cookies), session.last_activity,
                session.conversation_count, session.created_at, session.updated_at
            ))
            conn.commit()
        
        return session
    
    def get_session_state(self, endpoint_id: str) -> Optional[SessionState]:
        """Get session state for an endpoint"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_states WHERE endpoint_id = ?", (endpoint_id,)
            ).fetchone()
            
            if row:
                data = dict(row)
                data['session_data'] = json.loads(data['session_data'])
                data['auth_tokens'] = json.loads(data['auth_tokens'])
                data['cookies'] = json.loads(data['cookies'])
                return SessionState.from_dict(data)
            return None
    
    def update_session_state(self, session: SessionState) -> SessionState:
        """Update session state"""
        session.updated_at = datetime.utcnow().isoformat()
        session.last_activity = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE session_states SET
                    session_data = ?, browser_profile_path = ?, auth_tokens = ?,
                    cookies = ?, last_activity = ?, conversation_count = ?,
                    updated_at = ?
                WHERE endpoint_id = ?
            """, (
                json.dumps(session.session_data), session.browser_profile_path,
                json.dumps(session.auth_tokens), json.dumps(session.cookies),
                session.last_activity, session.conversation_count,
                session.updated_at, session.endpoint_id
            ))
            conn.commit()
        
        return session
    
    # Metrics operations
    def record_endpoint_metrics(self, metrics: EndpointMetrics) -> EndpointMetrics:
        """Record endpoint performance metrics"""
        metrics.created_at = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO endpoint_metrics (
                    id, endpoint_id, response_time_ms, success, error_message,
                    input_tokens, output_tokens, request_id, user_agent,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.id, metrics.endpoint_id, metrics.response_time_ms,
                metrics.success, metrics.error_message, metrics.input_tokens,
                metrics.output_tokens, metrics.request_id,
                metrics.user_agent, metrics.created_at
            ))
            conn.commit()
        
        return metrics
    
    def get_endpoint_metrics(self, endpoint_id: str, limit: int = 100) -> List[EndpointMetrics]:
        """Get recent metrics for an endpoint"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM endpoint_metrics 
                WHERE endpoint_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (endpoint_id, limit)).fetchall()
            
            metrics = []
            for row in rows:
                data = dict(row)
                metrics.append(EndpointMetrics.from_dict(data))
            
            return metrics
    
    def get_endpoint_stats(self, endpoint_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated statistics for an endpoint"""
        with self.get_connection() as conn:
            # Get stats for the last N hours
            cutoff_time = datetime.utcnow().replace(microsecond=0)
            cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)
            cutoff_str = cutoff_time.isoformat()
            
            row = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens
                FROM endpoint_metrics 
                WHERE endpoint_id = ? AND created_at >= ?
            """, (endpoint_id, cutoff_str)).fetchone()
            
            if row:
                stats = dict(row)
                stats['success_rate'] = (
                    stats['successful_requests'] / stats['total_requests'] 
                    if stats['total_requests'] > 0 else 0
                )
                return stats
            
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0
            }


# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
