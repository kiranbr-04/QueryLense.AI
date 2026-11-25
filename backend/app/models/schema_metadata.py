from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

def gen_uuid():
    return str(uuid.uuid4())

class SchemaMetadata(Base):
    __tablename__ = "schema_metadata"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    connection_id = Column(String(36), ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    schema_name = Column(String(255), default="public", nullable=False)
    table_name = Column(String(255), nullable=False, index=True)
    table_type = Column(String(50), default="table")  # table, view
    columns_json = Column(Text, nullable=False)  # JSON list of columns with types, nullability, default
    primary_keys_json = Column(Text, nullable=True)  # JSON list of PK columns
    foreign_keys_json = Column(Text, nullable=True)  # JSON list of FK relationships
    indexes_json = Column(Text, nullable=True)  # JSON list of indexes
    business_description = Column(Text, nullable=True)  # User or AI enriched business description
    row_count_estimate = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    connection = relationship("DatabaseConnection", back_populates="schema_metadata")
