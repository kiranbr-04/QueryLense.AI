from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

def gen_uuid():
    return str(uuid.uuid4())

class DatabaseConnection(Base):
    __tablename__ = "database_connections"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    connection_type = Column(String(50), default="direct", nullable=False)  # direct, agent, api
    dialect = Column(String(50), default="postgresql", nullable=False)  # postgresql, mysql, oracle, mssql, sqlite
    
    # Direct DB parameters
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    encrypted_password = Column(Text, nullable=True)  # Fernet encrypted
    ssl_enabled = Column(Boolean, default=False)
    extra_params = Column(Text, nullable=True)  # JSON-encoded extra connection options
    
    # Agent reference if connection_type == "agent"
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Status & Timestamps
    status = Column(String(50), default="disconnected")  # connected, disconnected, error
    error_message = Column(Text, nullable=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    schema_discovered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="connections")
    agent = relationship("Agent", back_populates="connections")
    schema_metadata = relationship("SchemaMetadata", back_populates="connection", cascade="all, delete-orphan")
    query_histories = relationship("QueryHistory", back_populates="connection", cascade="all, delete-orphan")
