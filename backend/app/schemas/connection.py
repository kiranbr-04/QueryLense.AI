from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ConnectionCreate(BaseModel):
    name: str
    connection_type: str = "direct"  # direct, agent, api
    dialect: str = "postgresql"  # postgresql, mysql, oracle, mssql, sqlite
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: bool = False
    agent_id: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None

class ConnectionTestRequest(BaseModel):
    dialect: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: bool = False
    extra_params: Optional[Dict[str, Any]] = None

class ConnectionResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    connection_type: str
    dialect: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    ssl_enabled: bool
    agent_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    schema_discovered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    server_version: Optional[str] = None
    error_detail: Optional[str] = None
