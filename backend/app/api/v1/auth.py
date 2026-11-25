import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import Token, UserRegister, UserLogin, UserResponse, OrganizationMemberCreate
from app.api.deps import get_current_user, get_current_admin
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", s)

@router.post("/register", response_model=Token)
def register_organization_and_admin(data: UserRegister, db: Session = Depends(get_db)):
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Create Organization
    slug_base = slugify(data.organization_name)
    slug = slug_base
    count = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{slug_base}-{count}"
        count += 1

    org = Organization(name=data.organization_name, slug=slug)
    db.add(org)
    db.flush()

    # Create Admin User
    hashed_pass = get_password_hash(data.password)
    user = User(
        organization_id=org.id,
        email=data.email.lower(),
        hashed_password=hashed_pass,
        full_name=data.full_name,
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log audit event
    log_audit_event(
        db,
        organization_id=org.id,
        action="USER_REGISTER",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "org_name": org.name},
        user_id=user.id,
        user_email=user.email,
    )

    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=org.id,
        organization_name=org.name,
    )

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    token = create_access_token(subject=user.id)

    log_audit_event(
        db,
        organization_id=user.organization_id,
        action="USER_LOGIN",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        user_email=user.email,
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "Default",
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/members", response_model=UserResponse)
def add_organization_member(
    data: OrganizationMemberCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        organization_id=current_admin.organization_id,
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db,
        organization_id=current_admin.organization_id,
        action="USER_INVITE",
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role},
        user_id=current_admin.id,
        user_email=current_admin.email,
    )
    return new_user

@router.get("/members", response_model=List[UserResponse])
def list_organization_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(User.organization_id == current_user.organization_id).all()
