from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AgentRegisterRequest(BaseModel):
    name: str

class AgentResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    agent_token: str
    status: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    version: str
    last_heartbeat: Optional[datetime] = None
    is_revoked: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    is_online: bool
    last_heartbeat: Optional[datetime] = None
