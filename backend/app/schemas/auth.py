from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    organization_id: str
    organization_name: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "member"
