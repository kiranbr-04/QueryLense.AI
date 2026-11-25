from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

def gen_uuid():
    return str(uuid.uuid4())

class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    connection_id = Column(String(36), ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    conversation_id = Column(String(36), nullable=True, index=True)  # For conversational thread grouping
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    executed_sql = Column(Text, nullable=False)
    status = Column(String(50), default="success", nullable=False)  # success, error, corrected
    error_message = Column(Text, nullable=True)
    correction_count = Column(Integer, default=0)
    
    execution_time_ms = Column(Float, nullable=True)
    row_count = Column(Integer, default=0)
    columns_json = Column(Text, nullable=True)  # JSON list of column names & types
    result_data_json = Column(Text, nullable=True)  # JSON sample of returned rows
    ai_explanation = Column(Text, nullable=True)
    chart_suggestion_json = Column(Text, nullable=True)  # JSON config for visualization
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    organization = relationship("Organization", back_populates="query_histories")
    user = relationship("User", back_populates="queries")
    connection = relationship("DatabaseConnection", back_populates="query_histories")
