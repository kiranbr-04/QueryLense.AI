import time
import decimal
import datetime
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from app.core.config import settings

def _json_serializable(val: Any) -> Any:
    """Convert DB types (Decimal, datetime, date, bytes, UUID) to JSON primitives."""
    if val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val

def execute_raw_sql(
    engine: Engine,
    sql: str,
    limit: Optional[int] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Safely execute a validated read-only SQL query against the target database engine.
    Captures exact records, columns, types, execution duration, and row counts.
    """
    max_limit = limit or settings.DEFAULT_ROW_LIMIT
    timeout = timeout_seconds or settings.QUERY_TIMEOUT_SECONDS

    # Clean query
    clean_sql = sql.strip().rstrip(";")

    start_time = time.perf_counter()
    rows = []
    columns = []

    try:
        # Enforce execution timeout via connection execution options where supported
        with engine.connect().execution_options(timeout=timeout) as conn:
            result = conn.execute(text(clean_sql))
            
            # Fetch column metadata
            if result.returns_rows:
                keys = list(result.keys())
                raw_rows = result.fetchmany(max_limit)
                
                # Determine column names and approximate types from first non-null values
                sample = raw_rows[0] if raw_rows else None
                for idx, col_name in enumerate(keys):
                    inferred_type = "string"
                    if sample and sample[idx] is not None:
                        val = sample[idx]
                        if isinstance(val, (int, float, decimal.Decimal)):
                            inferred_type = "number"
                        elif isinstance(val, (datetime.date, datetime.datetime)):
                            inferred_type = "datetime"
                        elif isinstance(val, bool):
                            inferred_type = "boolean"
                    columns.append({"name": col_name, "type": inferred_type})

                for row in raw_rows:
                    row_dict = {}
                    for col_name, val in zip(keys, row):
                        row_dict[col_name] = _json_serializable(val)
                    rows.append(row_dict)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "success": True,
            "executed_sql": clean_sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": duration_ms,
            "truncated": len(rows) == max_limit,
            "error": None,
        }

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "executed_sql": clean_sql,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": duration_ms,
            "truncated": False,
            "error": str(e),
        }
