import json
import httpx
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.api_connector import ApiConnector
from app.models.user import User
from app.schemas.api_connector import ApiConnectorCreate, ApiConnectorResponse, ApiExecuteRequest
from app.api.deps import get_current_user
from app.security.encryption import encrypt_secret, decrypt_secret
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/api-connectors", tags=["Business API Connectors"])

@router.post("", response_model=ApiConnectorResponse)
def create_api_connector(
    data: ApiConnectorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a business REST API connector."""
    enc_auth = encrypt_secret(data.auth_value) if data.auth_value else None
    headers_str = json.dumps(data.headers) if data.headers else None
    endpoints_str = json.dumps(data.endpoints) if data.endpoints else None

    connector = ApiConnector(
        organization_id=current_user.organization_id,
        name=data.name,
        base_url=data.base_url.rstrip("/"),
        auth_type=data.auth_type,
        auth_header_name=data.auth_header_name,
        encrypted_auth_value=enc_auth,
        headers_json=headers_str,
        endpoints_json=endpoints_str,
        status="active",
    )
    db.add(connector)
    db.commit()
    db.refresh(connector)

    log_audit_event(
        db,
        organization_id=current_user.organization_id,
        action="API_CONNECTOR_CREATE",
        resource_type="api_connector",
        resource_id=connector.id,
        details={"name": connector.name, "base_url": connector.base_url},
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiConnectorResponse(
        id=connector.id,
        organization_id=connector.organization_id,
        name=connector.name,
        base_url=connector.base_url,
        auth_type=connector.auth_type,
        auth_header_name=connector.auth_header_name,
        headers=data.headers,
        endpoints=data.endpoints,
        status=connector.status,
        created_at=connector.created_at,
        updated_at=connector.updated_at,
    )

@router.get("", response_model=List[ApiConnectorResponse])
def list_api_connectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connectors = db.query(ApiConnector).filter(ApiConnector.organization_id == current_user.organization_id).all()
    results = []
    for c in connectors:
        results.append(
            ApiConnectorResponse(
                id=c.id,
                organization_id=c.organization_id,
                name=c.name,
                base_url=c.base_url,
                auth_type=c.auth_type,
                auth_header_name=c.auth_header_name,
                headers=json.loads(c.headers_json) if c.headers_json else None,
                endpoints=json.loads(c.endpoints_json) if c.endpoints_json else None,
                status=c.status,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return results

@router.post("/{connector_id}/execute")
async def execute_api_call(
    connector_id: str,
    data: ApiExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute authenticated REST API call and return structured tabular response."""
    connector = (
        db.query(ApiConnector)
        .filter(
            ApiConnector.id == connector_id,
            ApiConnector.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not connector:
        raise HTTPException(status_code=404, detail="API Connector not found.")

    url = f"{connector.base_url}/{data.endpoint_path.lstrip('/')}"
    headers = json.loads(connector.headers_json) if connector.headers_json else {}

    # Apply authentication
    if connector.encrypted_auth_value:
        raw_auth = decrypt_secret(connector.encrypted_auth_value)
        if connector.auth_type == "bearer":
            headers[connector.auth_header_name] = f"Bearer {raw_auth}"
        elif connector.auth_type == "api_key":
            headers[connector.auth_header_name] = raw_auth

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            if data.method.upper() == "POST":
                resp = await client.post(url, headers=headers, params=data.params, json=data.payload)
            else:
                resp = await client.get(url, headers=headers, params=data.params)

        if resp.status_code >= 400:
            return {
                "success": False,
                "status_code": resp.status_code,
                "error": f"Upstream API returned HTTP {resp.status_code}: {resp.text[:300]}",
            }

        body = resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text
        return {
            "success": True,
            "status_code": resp.status_code,
            "data": body,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}",
        }
