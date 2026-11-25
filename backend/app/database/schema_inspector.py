import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from app.models.schema_metadata import SchemaMetadata

logger = logging.getLogger("querylens.schema")

def discover_database_schema(engine: Engine, connection_id: str) -> List[Dict[str, Any]]:
    """
    Introspect database schema using SQLAlchemy inspector.
    Extracts tables, views, columns, PKs, FKs, and indexes.
    Returns a list of table metadata dictionaries.
    """
    inspector = inspect(engine)
    discovered_tables = []

    try:
        # Schema names (default to None for standard schemas like SQLite/MySQL, or get all available)
        schema_names = inspector.get_schema_names()
    except Exception:
        schema_names = [None]

    # Focus on public / default schema to avoid system catalogs
    candidate_schemas = []
    for s in schema_names:
        if s is None or s.lower() in ("public", "dbo", "main", ""):
            candidate_schemas.append(s)
    if not candidate_schemas:
        candidate_schemas = [None]

    for schema in candidate_schemas:
        try:
            table_names = inspector.get_table_names(schema=schema)
        except Exception as e:
            logger.warning(f"Failed to list tables for schema '{schema}': {e}")
            continue

        try:
            view_names = inspector.get_view_names(schema=schema)
        except Exception:
            view_names = []

        all_items = [(t, "table") for t in table_names] + [(v, "view") for v in view_names]

        for item_name, item_type in all_items:
            try:
                # Columns
                columns_raw = inspector.get_columns(item_name, schema=schema)
                columns = []
                for col in columns_raw:
                    col_info = {
                        "name": str(col.get("name")),
                        "type": str(col.get("type")),
                        "nullable": bool(col.get("nullable", True)),
                        "default": str(col.get("default")) if col.get("default") is not None else None,
                        "primary_key": bool(col.get("primary_key", False)),
                    }
                    columns.append(col_info)

                # Primary Keys
                try:
                    pk_info = inspector.get_pk_constraint(item_name, schema=schema)
                    primary_keys = pk_info.get("constrained_columns", [])
                except Exception:
                    primary_keys = [c["name"] for c in columns if c.get("primary_key")]

                # Foreign Keys
                foreign_keys = []
                try:
                    fks_raw = inspector.get_foreign_keys(item_name, schema=schema)
                    for fk in fks_raw:
                        foreign_keys.append({
                            "constrained_columns": fk.get("constrained_columns", []),
                            "referred_schema": fk.get("referred_schema"),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", []),
                        })
                except Exception:
                    pass

                # Indexes
                indexes = []
                try:
                    idx_raw = inspector.get_indexes(item_name, schema=schema)
                    for idx in idx_raw:
                        indexes.append({
                            "name": idx.get("name"),
                            "column_names": idx.get("column_names", []),
                            "unique": idx.get("unique", False),
                        })
                except Exception:
                    pass

                # Estimate row count
                row_count = None
                try:
                    qualified_table = f'"{schema}"."{item_name}"' if schema else f'"{item_name}"'
                    with engine.connect() as conn:
                        res = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_table}"))
                        row_count = res.scalar()
                except Exception:
                    # Ignore count errors (e.g. permission or special views)
                    pass

                table_entry = {
                    "connection_id": connection_id,
                    "schema_name": schema or "public",
                    "table_name": item_name,
                    "table_type": item_type,
                    "columns_json": json.dumps(columns),
                    "primary_keys_json": json.dumps(primary_keys),
                    "foreign_keys_json": json.dumps(foreign_keys),
                    "indexes_json": json.dumps(indexes),
                    "row_count_estimate": row_count,
                    "business_description": "",
                }
                discovered_tables.append(table_entry)

            except Exception as item_err:
                logger.error(f"Error inspecting table {item_name}: {item_err}")
                continue

    return discovered_tables

def format_schema_for_prompt(tables: List[Dict[str, Any]], dialect: str) -> str:
    """Format schema into clear, dialect-aware DDL-like or structural markdown for the LLM."""
    lines = [f"### Target Database Dialect: {dialect.upper()}", "### Available Database Schema:"]

    for t in tables:
        t_name = t["table_name"]
        t_type = t.get("table_type", "table").upper()
        cols = json.loads(t["columns_json"]) if isinstance(t["columns_json"], str) else t["columns_json"]
        pks = json.loads(t.get("primary_keys_json") or "[]")
        fks = json.loads(t.get("foreign_keys_json") or "[]")
        desc = t.get("business_description")

        lines.append(f"\n{t_type} `{t_name}`:")
        if desc:
            lines.append(f"  -- Description: {desc}")

        col_strs = []
        for c in cols:
            pk_mark = " [PRIMARY KEY]" if c["name"] in pks else ""
            null_mark = "" if c.get("nullable", True) else " NOT NULL"
            col_strs.append(f"  - {c['name']} ({c['type']}){pk_mark}{null_mark}")
        lines.extend(col_strs)

        if fks:
            lines.append("  -- Relationships / Foreign Keys:")
            for fk in fks:
                lines.append(f"    * {', '.join(fk.get('constrained_columns', []))} -> {fk.get('referred_table')}({', '.join(fk.get('referred_columns', []))})")

    return "\n".join(lines)
