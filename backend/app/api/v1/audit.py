import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve security and activity audit logs for the organization."""
    query = db.query(AuditLog).filter(AuditLog.organization_id == current_user.organization_id)

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    records = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for r in records:
        details = json.loads(r.details_json) if r.details_json else None
        results.append(
            AuditLogResponse(
                id=r.id,
                organization_id=r.organization_id,
                user_id=r.user_id,
                user_email=r.user_email,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                details=details,
                ip_address=r.ip_address,
                created_at=r.created_at,
            )
        )
    return results
