"""
Session management for Universal AI Endpoint Manager

Handles persistent sessions for web chat interfaces and conversation continuity.
Similar to the cryptocurrency bot's state management but for AI conversations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    """State information for a persistent session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint_id: str = ""
    conversation_id: Optional[str] = None
    cookies: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    browser_state: Dict[str, Any] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    persistent: bool = True
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session has expired"""
        if not self.persistent:
            return False
        
        expiry_time = self.last_activity + timedelta(seconds=timeout_seconds)
        return datetime.now() > expiry_time
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "endpoint_id": self.endpoint_id,
            "conversation_id": self.conversation_id,
            "cookies": self.cookies,
            "headers": self.headers,
            "browser_state": self.browser_state,
            "last_activity": self.last_activity.isoformat(),
            "created_at": self.created_at.isoformat(),
            "persistent": self.persistent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create SessionState from dictionary"""
        last_activity = datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat()))
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            endpoint_id=data.get("endpoint_id", ""),
            conversation_id=data.get("conversation_id"),
            cookies=data.get("cookies", {}),
            headers=data.get("headers", {}),
            browser_state=data.get("browser_state", {}),
            last_activity=last_activity,
            created_at=created_at,
            persistent=data.get("persistent", True)
        )

class SessionManager:
    """
    Manages persistent sessions for AI endpoints
    
    Similar to the cryptocurrency bot's state management but focused on
    maintaining conversation continuity across web chat interfaces.
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize session manager"""
        self.config_dir = Path(config_dir)
        self.sessions_file = self.config_dir / "sessions.json"
        self.sessions: Dict[str, SessionState] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.default_timeout = 3600  # 1 hour
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"Session manager initialized with config dir: {config_dir}")
    
    async def start(self):
        """Start the session manager"""
        await self.load_sessions()
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Session manager started")
    
    async def stop(self):
        """Stop the session manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.save_sessions()
        logger.info("Session manager stopped")
    
    async def create_session(self, endpoint_id: str, persistent: bool = True) -> SessionState:
        """Create a new session for an endpoint"""
        session = SessionState(
            endpoint_id=endpoint_id,
            persistent=persistent
        )
        
        self.sessions[session.session_id] = session
        await self.save_sessions()
        
        logger.info(f"Created session {session.session_id} for endpoint {endpoint_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get a session by ID"""
        session = self.sessions.get(session_id)
        
        if session and session.is_expired(self.default_timeout):
            logger.info(f"Session {session_id} expired, removing")
            await self.remove_session(session_id)
            return None
        
        if session:
            session.update_activity()
            await self.save_sessions()
        
        return session
    
    async def get_or_create_session(self, endpoint_id: str, session_id: Optional[str] = None) -> SessionState:
        """Get existing session or create new one"""
        if session_id:
            session = await self.get_session(session_id)
            if session and session.endpoint_id == endpoint_id:
                return session
        
        # Create new session
        return await self.create_session(endpoint_id)
    
    async def update_session(self, session_id: str, **updates) -> bool:
        """Update session data"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Update session fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.update_activity()
        await self.save_sessions()
        
        logger.debug(f"Updated session {session_id}")
        return True
    
    async def remove_session(self, session_id: str) -> bool:
        """Remove a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            await self.save_sessions()
            logger.info(f"Removed session {session_id}")
            return True
        return False
    
    async def get_sessions_for_endpoint(self, endpoint_id: str) -> List[SessionState]:
        """Get all sessions for a specific endpoint"""
        return [
            session for session in self.sessions.values()
            if session.endpoint_id == endpoint_id and not session.is_expired(self.default_timeout)
        ]
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired(self.default_timeout)
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            await self.save_sessions()
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    async def load_sessions(self):
        """Load sessions from disk"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                
                self.sessions = {
                    session_id: SessionState.from_dict(session_data)
                    for session_id, session_data in data.items()
                }
                
                logger.info(f"Loaded {len(self.sessions)} sessions from disk")
            else:
                logger.info("No existing sessions file found")
        
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self.sessions = {}
    
    async def save_sessions(self):
        """Save sessions to disk"""
        try:
            data = {
                session_id: session.to_dict()
                for session_id, session in self.sessions.items()
            }
            
            with open(self.sessions_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.sessions)} sessions to disk")
        
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for session in self.sessions.values()
            if not session.is_expired(self.default_timeout)
        )
        expired_sessions = total_sessions - active_sessions
        
        # Group by endpoint
        endpoint_counts = {}
        for session in self.sessions.values():
            if not session.is_expired(self.default_timeout):
                endpoint_counts[session.endpoint_id] = endpoint_counts.get(session.endpoint_id, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "sessions_by_endpoint": endpoint_counts
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop()
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
                await asyncio.sleep(30)
