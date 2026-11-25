import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.connection import DatabaseConnection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.api.deps import get_current_user
from app.database.connection_manager import (
    test_connection_params,
    get_engine_for_connection,
)
from app.database.schema_inspector import discover_database_schema
from app.models.schema_metadata import SchemaMetadata
from app.security.encryption import encrypt_secret
from app.security.audit_logger import log_audit_event
from app.services.example_generator import generate_dynamic_examples_from_schema

router = APIRouter(prefix="/connections", tags=["Database Connections"])

@router.post("/test", response_model=ConnectionTestResponse)
def test_new_connection(data: ConnectionTestRequest, current_user: User = Depends(get_current_user)):
    """Test raw database connection parameters before saving."""
    res = test_connection_params(
        dialect=data.dialect,
        host=data.host,
        port=data.port,
        database_name=data.database_name,
        username=data.username,
        password=data.password,
        ssl_enabled=data.ssl_enabled,
        extra_params=data.extra_params,
    )
    return ConnectionTestResponse(**res)

@router.post("", response_model=ConnectionResponse)
def create_connection(
    data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register and connect a database, encrypt credentials, and trigger initial schema discovery."""
    encrypted_pass = encrypt_secret(data.password) if data.password else None
    extra_str = json.dumps(data.extra_params) if data.extra_params else None

    conn = DatabaseConnection(
        organization_id=current_user.organization_id,
        name=data.name,
        connection_type=data.connection_type,
        dialect=data.dialect,
        host=data.host,
        port=data.port,
        database_name=data.database_name,
        username=data.username,
        encrypted_password=encrypted_pass,
        ssl_enabled=data.ssl_enabled,
        agent_id=data.agent_id,
        extra_params=extra_str,
        status="disconnected",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    # Automatically test direct connection and discover schema
    if conn.connection_type == "direct":
        test_res = test_connection_params(
            dialect=conn.dialect,
            host=conn.host,
            port=conn.port,
            database_name=conn.database_name,
            username=conn.username,
            password=data.password,
            ssl_enabled=conn.ssl_enabled,
            extra_params=data.extra_params,
        )
        conn.last_tested_at = datetime.now(timezone.utc)
        if test_res["success"]:
            conn.status = "connected"
            conn.error_message = None
            try:
                engine = get_engine_for_connection(conn)
                tables = discover_database_schema(engine, conn.id)
                for t in tables:
                    meta = SchemaMetadata(
                        connection_id=conn.id,
                        schema_name=t["schema_name"],
                        table_name=t["table_name"],
                        table_type=t["table_type"],
                        columns_json=t["columns_json"],
                        primary_keys_json=t["primary_keys_json"],
                        foreign_keys_json=t["foreign_keys_json"],
                        indexes_json=t["indexes_json"],
                        row_count_estimate=t["row_count_estimate"],
                    )
                    db.add(meta)
                conn.schema_discovered_at = datetime.now(timezone.utc)
            except Exception as sch_err:
                conn.error_message = f"Connected but schema discovery failed: {str(sch_err)}"
        else:
            conn.status = "error"
            conn.error_message = test_res.get("message")
        db.commit()
        db.refresh(conn)

    log_audit_event(
        db,
        organization_id=current_user.organization_id,
        action="CONNECTION_CREATE",
        resource_type="connection",
        resource_id=conn.id,
        details={"name": conn.name, "dialect": conn.dialect, "status": conn.status},
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return conn

@router.get("", response_model=List[ConnectionResponse])
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all connections belonging strictly to the current user's organization."""
    return (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.organization_id == current_user.organization_id)
        .order_by(DatabaseConnection.created_at.desc())
        .all()
    )

@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")
    return conn

@router.get("/{connection_id}/examples", response_model=List[str])
def get_connection_examples(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dynamically generate schema-driven example queries for the connected database."""
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    records = db.query(SchemaMetadata).filter(SchemaMetadata.connection_id == connection_id).all()
    tables = [
        {
            "table_name": r.table_name,
            "columns_json": r.columns_json,
            "business_description": r.business_description,
        }
        for r in records
    ]
    return generate_dynamic_examples_from_schema(tables)

@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
def test_existing_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    from app.security.encryption import decrypt_secret
    password = decrypt_secret(conn.encrypted_password) if conn.encrypted_password else None
    extra = json.loads(conn.extra_params) if conn.extra_params else None

    res = test_connection_params(
        dialect=conn.dialect,
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        password=password,
        ssl_enabled=conn.ssl_enabled,
        extra_params=extra,
    )

    conn.last_tested_at = datetime.now(timezone.utc)
    if res["success"]:
        conn.status = "connected"
        conn.error_message = None
    else:
        conn.status = "error"
        conn.error_message = res.get("message")
    db.commit()

    return ConnectionTestResponse(**res)

@router.delete("/{connection_id}")
def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    db.delete(conn)
    db.commit()

    log_audit_event(
        db,
        organization_id=current_user.organization_id,
        action="CONNECTION_DELETE",
        resource_type="connection",
        resource_id=connection_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return {"message": "Connection deleted successfully."}
