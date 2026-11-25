from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

def gen_uuid():
    return str(uuid.uuid4())

class ApiConnector(Base):
    __tablename__ = "api_connectors"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    base_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none")  # none, bearer, api_key, basic
    auth_header_name = Column(String(100), default="Authorization")
    encrypted_auth_value = Column(Text, nullable=True)  # Fernet encrypted token / API key
    headers_json = Column(Text, nullable=True)  # Additional default headers
    endpoints_json = Column(Text, nullable=True)  # List of defined endpoint routes & schemas
    openapi_spec_json = Column(Text, nullable=True)  # Raw OpenAPI specification
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
