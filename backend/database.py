"""
Database configuration and initialization for the Universal AI Endpoint Management System
Integrates with Khoj database architecture
"""

import os
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .models.base import Base
from .models.providers import EndpointProvider, EndpointInstance, ProviderType
from .models.endpoints import Endpoint, EndpointConfiguration, EndpointSession, EndpointStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for the Universal AI Endpoint Management System"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default SQLite"""
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        
        # Default to SQLite for development
        db_path = os.getenv('DB_PATH', 'endpoint_manager.db')
        return f'sqlite:///{db_path}'
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine with appropriate settings
            if self.database_url.startswith('sqlite'):
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"Database initialized successfully with URL: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_default_providers(self):
        """Create default providers (Codegen API and Z.ai Web UI)"""
        with self.get_session() as session:
            # Check if default providers already exist
            existing_providers = session.query(EndpointProvider).filter(
                EndpointProvider.is_default == True
            ).all()
            
            if existing_providers:
                logger.info("Default providers already exist")
                return
            
            # Create Codegen API provider
            codegen_provider = EndpointProvider(
                name="Codegen REST API",
                provider_type=ProviderType.REST_API,
                description="Default Codegen API endpoint for code generation",
                base_url=os.getenv('CODEGEN_BASE_URL', 'https://codegen-sh--rest-api.modal.run'),
                api_key=os.getenv('CODEGEN_TOKEN'),
                model_mapping={
                    "gpt-4": "codegen-advanced",
                    "gpt-3.5-turbo": "codegen-standard",
                    "claude-3-opus": "codegen-premium",
                    "claude-3-sonnet": "codegen-advanced",
                    "gemini-pro": "codegen-standard"
                },
                is_default=True,
                priority=1,
                max_requests_per_minute=100,
                max_concurrent_requests=10
            )
            
            # Create Z.ai Web UI provider
            zai_provider = EndpointProvider(
                name="Z.ai Web UI",
                provider_type=ProviderType.WEB_CHAT,
                description="Z.ai web chat interface with GLM-4.5 model",
                base_url="https://z.ai",
                login_url="https://z.ai/login",
                browser_config={
                    "headless": True,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "viewport": {"width": 1920, "height": 1080},
                    "timeout": 30000,
                    "wait_for_selector": ".chat-input",
                    "anti_detection": True
                },
                model_mapping={
                    "gpt-4": "glm-4.5",
                    "gpt-3.5-turbo": "glm-4.5",
                    "claude-3-opus": "glm-4.5",
                    "gemini-pro": "glm-4.5"
                },
                is_default=True,
                priority=2,
                max_requests_per_minute=30,
                max_concurrent_requests=3
            )
            
            session.add(codegen_provider)
            session.add(zai_provider)
            session.commit()
            
            logger.info("Created default providers: Codegen REST API and Z.ai Web UI")
    
    def get_provider_by_name(self, name: str) -> Optional[EndpointProvider]:
        """Get provider by name"""
        with self.get_session() as session:
            return session.query(EndpointProvider).filter(
                EndpointProvider.name == name
            ).first()
    
    def get_active_endpoints(self) -> List[Endpoint]:
        """Get all active endpoints"""
        with self.get_session() as session:
            return session.query(Endpoint).filter(
                Endpoint.status == EndpointStatus.ACTIVE
            ).all()
    
    def get_endpoint_by_model_name(self, model_name: str) -> Optional[Endpoint]:
        """Get endpoint by model name"""
        with self.get_session() as session:
            return session.query(Endpoint).filter(
                Endpoint.model_name == model_name,
                Endpoint.status == EndpointStatus.ACTIVE
            ).first()
    
    def create_endpoint_instance(self, provider_name: str, instance_name: str) -> Optional[EndpointInstance]:
        """Create a new endpoint instance"""
        with self.get_session() as session:
            provider = session.query(EndpointProvider).filter(
                EndpointProvider.name == provider_name
            ).first()
            
            if not provider:
                logger.error(f"Provider '{provider_name}' not found")
                return None
            
            instance = EndpointInstance(
                provider_id=provider.id,
                instance_name=instance_name,
                status='stopped'
            )
            
            session.add(instance)
            session.commit()
            session.refresh(instance)
            
            logger.info(f"Created endpoint instance: {instance_name}")
            return instance
    
    def update_instance_status(self, instance_id: str, status: str, **kwargs):
        """Update endpoint instance status and metrics"""
        with self.get_session() as session:
            instance = session.query(EndpointInstance).filter(
                EndpointInstance.id == instance_id
            ).first()
            
            if instance:
                instance.status = status
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                
                session.commit()
                logger.info(f"Updated instance {instance.instance_name} status to {status}")

# Global database manager instance
db_manager = DatabaseManager()

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager

def init_database():
    """Initialize database and create default providers"""
    try:
        db_manager.create_default_providers()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
