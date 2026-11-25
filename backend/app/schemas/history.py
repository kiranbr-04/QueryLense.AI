from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class QueryHistoryResponse(BaseModel):
    id: str
    organization_id: str
    user_id: Optional[str] = None
    connection_id: str
    conversation_id: Optional[str] = None
    question: str
    generated_sql: str
    executed_sql: str
    status: str
    error_message: Optional[str] = None
    correction_count: int
    execution_time_ms: Optional[float] = None
    row_count: int
    columns: Optional[List[Dict[str, Any]]] = None
    result_data: Optional[List[Dict[str, Any]]] = None
    ai_explanation: Optional[str] = None
    chart_suggestion: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
