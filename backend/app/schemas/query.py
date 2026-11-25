from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QueryGenerateRequest(BaseModel):
    connection_id: str
    question: str
    conversation_id: Optional[str] = None
    llm_provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None

class QueryGenerateResponse(BaseModel):
    generated_sql: str
    is_valid: bool
    validation_error: Optional[str] = None
    dialect: str

class QueryExecuteRequest(BaseModel):
    connection_id: str
    sql: str
    question: Optional[str] = None
    conversation_id: Optional[str] = None
    limit: Optional[int] = None
    auto_explain: bool = True

class QueryExecuteResponse(BaseModel):
    success: bool
    query_id: Optional[str] = None
    executed_sql: str
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None
    truncated: bool = False
    ai_explanation: Optional[str] = None
    chart_suggestion: Optional[Dict[str, Any]] = None

class QueryCorrectRequest(BaseModel):
    connection_id: str
    failing_sql: str
    error_message: str
    original_question: str

class QueryExplainRequest(BaseModel):
    question: str
    executed_sql: str
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    llm_provider: Optional[str] = None
    api_key: Optional[str] = None

class ConversationalPipelineRequest(BaseModel):
    connection_id: str
    question: str
    conversation_id: Optional[str] = None
    auto_correct: bool = True
    llm_provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None

class ConversationThreadSummary(BaseModel):
    conversation_id: str
    title: str
    last_query_at: Optional[str] = None
    query_count: int

class ConversationCreateResponse(BaseModel):
    conversation_id: str
    message: str
