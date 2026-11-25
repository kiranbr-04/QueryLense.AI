import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.connection import DatabaseConnection
from app.models.schema_metadata import SchemaMetadata
from app.models.user import User
from app.schemas.schema import TableSchemaResponse, TableDescriptionUpdate
from app.api.deps import get_current_user
from app.database.connection_manager import get_engine_for_connection
from app.database.schema_inspector import discover_database_schema
from app.agents.agent_manager import agent_manager
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/connections/{connection_id}/schema", tags=["Schema Discovery"])

@router.get("", response_model=List[TableSchemaResponse])
def get_connection_schema(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all discovered tables and columns for the given connection."""
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    records = db.query(SchemaMetadata).filter(SchemaMetadata.connection_id == connection_id).all()
    results = []
    for r in records:
        results.append(
            TableSchemaResponse(
                id=r.id,
                connection_id=r.connection_id,
                schema_name=r.schema_name,
                table_name=r.table_name,
                table_type=r.table_type,
                columns=json.loads(r.columns_json),
                primary_keys=json.loads(r.primary_keys_json or "[]"),
                foreign_keys=json.loads(r.foreign_keys_json or "[]"),
                indexes=json.loads(r.indexes_json or "[]"),
                business_description=r.business_description,
                row_count_estimate=r.row_count_estimate,
                updated_at=r.updated_at,
            )
        )
    return results

@router.post("/refresh")
async def refresh_connection_schema(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-introspect target database and synchronize schema metadata."""
    conn = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    tables = []
    if conn.connection_type == "direct":
        try:
            engine = get_engine_for_connection(conn)
            tables = discover_database_schema(engine, conn.id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to inspect database schema: {str(e)}")

    elif conn.connection_type == "agent":
        if not conn.agent_id:
            raise HTTPException(status_code=400, detail="No agent configured for this connection.")
        try:
            agent_res = await agent_manager.dispatch_command(
                agent_id=conn.agent_id,
                command_type="introspect_schema",
                payload={"connection_id": conn.id},
                timeout=45.0,
            )
            tables = agent_res.get("tables", [])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Connector Agent error: {str(e)}")

    # Clear old schema entries
    db.query(SchemaMetadata).filter(SchemaMetadata.connection_id == connection_id).delete()

    for t in tables:
        meta = SchemaMetadata(
            connection_id=conn.id,
            schema_name=t.get("schema_name", "public"),
            table_name=t["table_name"],
            table_type=t.get("table_type", "table"),
            columns_json=t["columns_json"] if isinstance(t["columns_json"], str) else json.dumps(t["columns_json"]),
            primary_keys_json=t.get("primary_keys_json") if isinstance(t.get("primary_keys_json"), str) else json.dumps(t.get("primary_keys_json", [])),
            foreign_keys_json=t.get("foreign_keys_json") if isinstance(t.get("foreign_keys_json"), str) else json.dumps(t.get("foreign_keys_json", [])),
            indexes_json=t.get("indexes_json") if isinstance(t.get("indexes_json"), str) else json.dumps(t.get("indexes_json", [])),
            row_count_estimate=t.get("row_count_estimate"),
            business_description=t.get("business_description", ""),
        )
        db.add(meta)

    conn.schema_discovered_at = datetime.now(timezone.utc)
    conn.status = "connected"
    conn.error_message = None
    db.commit()

    log_audit_event(
        db,
        organization_id=current_user.organization_id,
        action="SCHEMA_REFRESH",
        resource_type="connection",
        resource_id=conn.id,
        details={"table_count": len(tables)},
        user_id=current_user.id,
        user_email=current_user.email,
    )

    return {"message": f"Successfully refreshed schema. {len(tables)} table(s) discovered."}

@router.put("/{table_id}/description")
def update_table_description(
    connection_id: str,
    table_id: str,
    data: TableDescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enrich table with business descriptions to enhance AI and RAG schema retrieval."""
    meta = (
        db.query(SchemaMetadata)
        .join(DatabaseConnection, SchemaMetadata.connection_id == DatabaseConnection.id)
        .filter(
            SchemaMetadata.id == table_id,
            DatabaseConnection.id == connection_id,
            DatabaseConnection.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not meta:
        raise HTTPException(status_code=404, detail="Table metadata entry not found.")

    meta.business_description = data.business_description
    db.commit()
    db.refresh(meta)
    return {"message": "Description updated successfully.", "table_name": meta.table_name}
