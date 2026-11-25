from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
