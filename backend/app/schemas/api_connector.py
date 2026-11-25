from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class ApiConnectorCreate(BaseModel):
    name: str
    base_url: str
    auth_type: str = "none"  # none, bearer, api_key, basic
    auth_header_name: str = "Authorization"
    auth_value: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    endpoints: Optional[List[Dict[str, Any]]] = None

class ApiConnectorResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    base_url: str
    auth_type: str
    auth_header_name: str
    headers: Optional[Dict[str, str]] = None
    endpoints: Optional[List[Dict[str, Any]]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApiExecuteRequest(BaseModel):
    endpoint_path: str
    method: str = "GET"
    params: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
