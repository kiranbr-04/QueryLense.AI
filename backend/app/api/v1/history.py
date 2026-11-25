import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.query_history import QueryHistory
from app.models.user import User
from app.schemas.history import QueryHistoryResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/query/history", tags=["Query History"])

@router.get("", response_model=List[QueryHistoryResponse])
def get_query_history(
    connection_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of executed queries for current organization."""
    query = (
        db.query(QueryHistory)
        .filter(QueryHistory.organization_id == current_user.organization_id)
    )

    if connection_id:
        query = query.filter(QueryHistory.connection_id == connection_id)
    if status:
        query = query.filter(QueryHistory.status == status)

    records = (
        query.order_by(QueryHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for r in records:
        cols = json.loads(r.columns_json) if r.columns_json else None
        res_data = json.loads(r.result_data_json) if r.result_data_json else None
        chart = json.loads(r.chart_suggestion_json) if r.chart_suggestion_json else None

        results.append(
            QueryHistoryResponse(
                id=r.id,
                organization_id=r.organization_id,
                user_id=r.user_id,
                connection_id=r.connection_id,
                conversation_id=r.conversation_id,
                question=r.question,
                generated_sql=r.generated_sql,
                executed_sql=r.executed_sql,
                status=r.status,
                error_message=r.error_message,
                correction_count=r.correction_count,
                execution_time_ms=r.execution_time_ms,
                row_count=r.row_count,
                columns=cols,
                result_data=res_data,
                ai_explanation=r.ai_explanation,
                chart_suggestion=chart,
                created_at=r.created_at,
            )
        )
    return results

@router.get("/{history_id}", response_model=QueryHistoryResponse)
def get_history_detail(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = (
        db.query(QueryHistory)
        .filter(
            QueryHistory.id == history_id,
            QueryHistory.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Query history item not found.")

    cols = json.loads(r.columns_json) if r.columns_json else None
    res_data = json.loads(r.result_data_json) if r.result_data_json else None
    chart = json.loads(r.chart_suggestion_json) if r.chart_suggestion_json else None

    return QueryHistoryResponse(
        id=r.id,
        organization_id=r.organization_id,
        user_id=r.user_id,
        connection_id=r.connection_id,
        conversation_id=r.conversation_id,
        question=r.question,
        generated_sql=r.generated_sql,
        executed_sql=r.executed_sql,
        status=r.status,
        error_message=r.error_message,
        correction_count=r.correction_count,
        execution_time_ms=r.execution_time_ms,
        row_count=r.row_count,
        columns=cols,
        result_data=res_data,
        ai_explanation=r.ai_explanation,
        chart_suggestion=chart,
        created_at=r.created_at,
    )
