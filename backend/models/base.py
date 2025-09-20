"""
Base model classes for the Universal AI Endpoint Management System
"""

import uuid
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

if TYPE_CHECKING:
    from sqlalchemy.ext.declarative import DeclarativeMeta
    BaseType = DeclarativeMeta
else:
    BaseType = Base

class BaseModel(BaseType):  # type: ignore[misc]
    """Base model with common fields for all database models"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata for extensibility
    metadata_json = Column(JSON, default=dict, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
