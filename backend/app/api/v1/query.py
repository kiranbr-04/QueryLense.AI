import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.connection import DatabaseConnection
from app.models.schema_metadata import SchemaMetadata
from app.models.query_history import QueryHistory
from app.models.user import User
from app.schemas.query import (
    QueryGenerateRequest,
    QueryGenerateResponse,
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryCorrectRequest,
    QueryExplainRequest,
    ConversationalPipelineRequest,
)
from app.api.deps import get_current_user
from app.database.connection_manager import get_engine_for_connection
from app.database.query_executor import execute_raw_sql
from app.ai.sql_generator import generate_sql_from_question
from app.ai.sql_validator import validate_sql
from app.ai.error_corrector import correct_failing_sql
from app.ai.result_explainer import explain_query_results
from app.ai.conversational_memory import get_conversation_history
from app.agents.agent_manager import agent_manager
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/query", tags=["Conversational AI Engine"])

def _fetch_table_dicts(db: Session, connection_id: str) -> List[Dict[str, Any]]:
    records = db.query(SchemaMetadata).filter(SchemaMetadata.connection_id == connection_id).all()
    tables = []
    for r in records:
        tables.append({
            "table_name": r.table_name,
            "table_type": r.table_type,
            "columns_json": r.columns_json,
            "primary_keys_json": r.primary_keys_json,
            "foreign_keys_json": r.foreign_keys_json,
            "indexes_json": r.indexes_json,
            "business_description": r.business_description,
        })
    return tables

@router.post("/generate", response_model=QueryGenerateResponse)
async def generate_sql(
    data: QueryGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Transform natural language question into validated dialect-aware SQL."""
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == data.connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    all_tables = _fetch_table_dicts(db, conn.id)
    if not all_tables:
        raise HTTPException(
            status_code=400,
            detail="No schema metadata discovered for this database yet. Please click 'Refresh Schema' in Database Connections.",
        )

    # Conversational memory
    conv_turns = get_conversation_history(
        db,
        conversation_id=data.conversation_id,
        organization_id=current_user.organization_id,
    )

    sql, is_valid, err = await generate_sql_from_question(
        question=data.question,
        all_tables=all_tables,
        dialect=conn.dialect,
        conversation_turns=conv_turns,
        provider_name=data.llm_provider,
        api_key=data.api_key,
        model_name=data.model_name,
    )

    return QueryGenerateResponse(
        generated_sql=sql,
        is_valid=is_valid,
        validation_error=err,
        dialect=conn.dialect,
    )

@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    data: QueryExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate and execute SQL query against the real target database or connector agent.
    Never fabricates records; returns exact database records.
    """
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == data.connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    # 1. SQL Validation Layer
    all_tables = _fetch_table_dicts(db, conn.id)
    allowed_table_names = [t["table_name"] for t in all_tables]
    is_valid, val_err, safe_sql = validate_sql(data.sql, allowed_tables=allowed_table_names)

    if not is_valid:
        # Record failed validation attempt in history and audit log
        history_entry = QueryHistory(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            connection_id=conn.id,
            conversation_id=data.conversation_id,
            question=data.question or "Manual SQL Execution",
            generated_sql=data.sql,
            executed_sql=data.sql,
            status="error",
            error_message=val_err,
            row_count=0,
            execution_time_ms=0.0,
        )
        db.add(history_entry)
        db.commit()

        return QueryExecuteResponse(
            success=False,
            executed_sql=data.sql,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            error=val_err,
        )

    # 2. Execute on target (Direct or Agent)
    exec_res = {}
    if conn.connection_type == "direct":
        try:
            engine = get_engine_for_connection(conn)
            exec_res = execute_raw_sql(engine, safe_sql, limit=data.limit)
        except Exception as e:
            exec_res = {
                "success": False,
                "executed_sql": safe_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": str(e),
            }
    elif conn.connection_type == "agent":
        if not conn.agent_id:
            raise HTTPException(status_code=400, detail="No agent configured for this connection.")
        try:
            agent_res = await agent_manager.dispatch_command(
                agent_id=conn.agent_id,
                command_type="execute_sql",
                payload={"sql": safe_sql, "limit": data.limit or 500},
                timeout=35.0,
            )
            exec_res = agent_res
        except Exception as e:
            exec_res = {
                "success": False,
                "executed_sql": safe_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": f"Agent error: {str(e)}",
            }

    # 3. Explain results if requested and query succeeded
    explanation = None
    chart_suggestion = None
    if exec_res.get("success") and data.auto_explain:
        explain_res = await explain_query_results(
            question=data.question or "Display records",
            executed_sql=safe_sql,
            columns=exec_res.get("columns", []),
            rows=exec_res.get("rows", []),
            row_count=exec_res.get("row_count", 0),
            execution_time_ms=exec_res.get("execution_time_ms", 0.0),
        )
        explanation = explain_res.get("explanation")
        chart_suggestion = explain_res.get("visualization")

    # 4. Save Query History
    sample_for_history = exec_res.get("rows", [])[:50]
    history_entry = QueryHistory(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        connection_id=conn.id,
        conversation_id=data.conversation_id,
        question=data.question or "SQL Execution",
        generated_sql=data.sql,
        executed_sql=safe_sql,
        status="success" if exec_res.get("success") else "error",
        error_message=exec_res.get("error"),
        row_count=exec_res.get("row_count", 0),
        execution_time_ms=exec_res.get("execution_time_ms", 0.0),
        columns_json=json.dumps(exec_res.get("columns", [])),
        result_data_json=json.dumps(sample_for_history, default=str),
        ai_explanation=explanation,
        chart_suggestion_json=json.dumps(chart_suggestion) if chart_suggestion else None,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    # 5. Log audit event
    log_audit_event(
        db,
        organization_id=current_user.organization_id,
        action="QUERY_EXECUTE",
        resource_type="query",
        resource_id=history_entry.id,
        details={
            "sql": safe_sql[:200],
            "success": exec_res.get("success"),
            "row_count": exec_res.get("row_count", 0),
        },
        user_id=current_user.id,
        user_email=current_user.email,
    )

    return QueryExecuteResponse(
        success=exec_res.get("success", False),
        query_id=history_entry.id,
        executed_sql=safe_sql,
        columns=exec_res.get("columns", []),
        rows=exec_res.get("rows", []),
        row_count=exec_res.get("row_count", 0),
        execution_time_ms=exec_res.get("execution_time_ms", 0.0),
        error=exec_res.get("error"),
        truncated=exec_res.get("truncated", False),
        ai_explanation=explanation,
        chart_suggestion=chart_suggestion,
    )

@router.post("/correct")
async def correct_query(
    data: QueryCorrectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Automatic error correction loop for failing queries."""
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == data.connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    all_tables = _fetch_table_dicts(db, conn.id)
    corrected_sql, is_valid, val_err = await correct_failing_sql(
        failing_sql=data.failing_sql,
        db_error_message=data.error_message,
        all_tables=all_tables,
        dialect=conn.dialect,
        original_question=data.original_question,
    )

    return {
        "corrected_sql": corrected_sql,
        "is_valid": is_valid,
        "validation_error": val_err,
    }

@router.post("/explain")
async def explain_results(
    data: QueryExplainRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate business intelligence explanation grounded in actual returned records."""
    res = await explain_query_results(
        question=data.question,
        executed_sql=data.executed_sql,
        columns=data.columns,
        rows=data.rows,
        row_count=data.row_count,
        execution_time_ms=data.execution_time_ms,
        provider_name=data.llm_provider,
        api_key=data.api_key,
    )
    return res

@router.post("/pipeline", response_model=QueryExecuteResponse)
async def execute_conversational_pipeline(
    data: ConversationalPipelineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    End-to-end conversational intelligence pipeline:
    1. Retrieve conversation context & schema
    2. Generate SQL for target dialect
    3. Validate SQL
    4. Execute against database
    5. If execution fails and auto_correct is enabled, trigger automatic SQL error correction (up to 2 retries)
    6. Grounded AI result explanation + Chart recommendation
    """
    # Generate initial SQL
    gen_req = QueryGenerateRequest(
        connection_id=data.connection_id,
        question=data.question,
        conversation_id=data.conversation_id,
        llm_provider=data.llm_provider,
        api_key=data.api_key,
        model_name=data.model_name,
    )
    gen_res = await generate_sql(gen_req, current_user, db)

    # Initial execution
    exec_req = QueryExecuteRequest(
        connection_id=data.connection_id,
        sql=gen_res.generated_sql,
        question=data.question,
        conversation_id=data.conversation_id,
        auto_explain=True,
    )
    exec_res = await execute_query(exec_req, current_user, db)

    # Check if execution failed and auto_correct requested
    retry_count = 0
    max_retries = 2
    current_sql = gen_res.generated_sql

    while not exec_res.success and data.auto_correct and retry_count < max_retries:
        retry_count += 1
        correct_req = QueryCorrectRequest(
            connection_id=data.connection_id,
            failing_sql=current_sql,
            error_message=exec_res.error or "Unknown execution failure",
            original_question=data.question,
        )
        corr_res = await correct_query(correct_req, current_user, db)
        if not corr_res.get("is_valid"):
            break

        current_sql = corr_res.get("corrected_sql")
        exec_req.sql = current_sql
        exec_res = await execute_query(exec_req, current_user, db)
        if exec_res.success:
            # Mark history entry as corrected
            if exec_res.query_id:
                h = db.query(QueryHistory).filter(QueryHistory.id == exec_res.query_id).first()
                if h:
                    h.status = "corrected"
                    h.correction_count = retry_count
                    db.commit()
            break

    return exec_res

@router.post("/ask", response_model=QueryExecuteResponse)
async def ask_query(
    data: ConversationalPipelineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convenience alias for execute_conversational_pipeline."""
    return await execute_conversational_pipeline(data, current_user, db)

@router.post("/conversations")
def create_conversation_thread(current_user: User = Depends(get_current_user)):
    """Generate a clean new conversation thread ID."""
    import uuid
    new_id = f"conv_{uuid.uuid4().hex[:12]}"
    return {"conversation_id": new_id, "message": "New conversation thread initialized."}

@router.get("/conversations")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List conversation threads with their initial questions and query counts."""
    from sqlalchemy import func
    rows = (
        db.query(
            QueryHistory.conversation_id,
            func.min(QueryHistory.question).label("first_question"),
            func.max(QueryHistory.created_at).label("last_activity"),
            func.count(QueryHistory.id).label("total_queries"),
        )
        .filter(
            QueryHistory.organization_id == current_user.organization_id,
            QueryHistory.conversation_id.isnot(None),
        )
        .group_by(QueryHistory.conversation_id)
        .order_by(func.max(QueryHistory.created_at).desc())
        .limit(30)
        .all()
    )

    return [
        {
            "conversation_id": r.conversation_id,
            "title": r.first_question,
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "total_queries": r.total_queries,
        }
        for r in rows
    ]

@router.get("/conversations/{conversation_id}")
def get_conversation_thread(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all query turns belonging to a specific conversation thread."""
    records = (
        db.query(QueryHistory)
        .filter(
            QueryHistory.conversation_id == conversation_id,
            QueryHistory.organization_id == current_user.organization_id,
        )
        .order_by(QueryHistory.created_at.asc())
        .all()
    )

    return [
        {
            "id": r.id,
            "question": r.question,
            "executed_sql": r.executed_sql,
            "status": r.status,
            "row_count": r.row_count,
            "execution_time_ms": r.execution_time_ms,
            "ai_explanation": r.ai_explanation,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
