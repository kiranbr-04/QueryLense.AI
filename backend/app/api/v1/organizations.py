from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationCreate
from app.api.deps import get_current_user, get_current_admin
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/current", response_model=OrganizationResponse)
def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org

@router.put("/current", response_model=OrganizationResponse)
def update_current_organization(
    data: OrganizationCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == current_admin.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    org.name = data.name
    db.commit()
    db.refresh(org)

    log_audit_event(
        db,
        organization_id=org.id,
        action="ORGANIZATION_UPDATE",
        resource_type="organization",
        resource_id=org.id,
        details={"new_name": org.name},
        user_id=current_admin.id,
        user_email=current_admin.email,
    )
    return org
