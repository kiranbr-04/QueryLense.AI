import time
import json
import decimal
import datetime
import uuid
import urllib.parse
from typing import Dict, Any, List
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from app.config import agent_settings
from app.security.validator import validate_agent_sql

def _json_serializable(val: Any) -> Any:
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

class LocalDatabaseExecutor:
    def __init__(self):
        self.engine: Engine = self._create_local_engine()

    def _create_local_engine(self) -> Engine:
        d = agent_settings.LOCAL_DB_DIALECT.lower()
        if d == "sqlite":
            url = f"sqlite:///{agent_settings.LOCAL_DB_NAME}"
            return create_engine(url, connect_args={"check_same_thread": False})

        user = urllib.parse.quote_plus(agent_settings.LOCAL_DB_USER)
        pwd = urllib.parse.quote_plus(agent_settings.LOCAL_DB_PASSWORD)
        host = f"{agent_settings.LOCAL_DB_HOST}:{agent_settings.LOCAL_DB_PORT}"
        dbname = agent_settings.LOCAL_DB_NAME

        if d == "postgresql":
            url = f"postgresql+psycopg://{user}:{pwd}@{host}/{dbname}"
        elif d == "mysql":
            url = f"mysql+pymysql://{user}:{pwd}@{host}/{dbname}?charset=utf8mb4"
        elif d == "oracle":
            url = f"oracle+oracledb://{user}:{pwd}@{host}/?service_name={dbname}"
        elif d == "mssql":
            url = f"mssql+pyodbc://{user}:{pwd}@{host}/{dbname}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported local dialect: {d}")

        return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)

    def execute_query(self, sql: str, limit: int = 500) -> Dict[str, Any]:
        is_valid, err, clean_sql = validate_agent_sql(sql)
        if not is_valid:
            return {
                "success": False,
                "executed_sql": sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": err,
            }

        start = time.perf_counter()
        rows = []
        columns = []
        cap_limit = min(limit, agent_settings.MAX_ROWS_LIMIT)

        try:
            with self.engine.connect().execution_options(timeout=agent_settings.QUERY_TIMEOUT_SECONDS) as conn:
                result = conn.execute(text(clean_sql))
                if result.returns_rows:
                    keys = list(result.keys())
                    raw_rows = result.fetchmany(cap_limit)
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
                        row_dict = {col: _json_serializable(val) for col, val in zip(keys, row)}
                        rows.append(row_dict)

            duration = round((time.perf_counter() - start) * 1000, 2)
            return {
                "success": True,
                "executed_sql": clean_sql,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": duration,
                "truncated": len(rows) == cap_limit,
                "error": None,
            }
        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 2)
            return {
                "success": False,
                "executed_sql": clean_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": duration,
                "truncated": False,
                "error": str(e),
            }

    def introspect_schema(self) -> Dict[str, Any]:
        inspector = inspect(self.engine)
        tables = []
        try:
            table_names = inspector.get_table_names()
        except Exception:
            table_names = []

        for t_name in table_names:
            try:
                cols_raw = inspector.get_columns(t_name)
                columns = [
                    {
                        "name": str(c.get("name")),
                        "type": str(c.get("type")),
                        "nullable": bool(c.get("nullable", True)),
                        "default": str(c.get("default")) if c.get("default") is not None else None,
                        "primary_key": bool(c.get("primary_key", False)),
                    }
                    for c in cols_raw
                ]

                try:
                    pk_info = inspector.get_pk_constraint(t_name)
                    pks = pk_info.get("constrained_columns", [])
                except Exception:
                    pks = []

                try:
                    fks_raw = inspector.get_foreign_keys(t_name)
                    fks = [
                        {
                            "constrained_columns": fk.get("constrained_columns", []),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", []),
                        }
                        for fk in fks_raw
                    ]
                except Exception:
                    fks = []

                tables.append({
                    "table_name": t_name,
                    "table_type": "table",
                    "columns_json": json.dumps(columns),
                    "primary_keys_json": json.dumps(pks),
                    "foreign_keys_json": json.dumps(fks),
                    "indexes_json": "[]",
                })
            except Exception:
                continue

        return {"tables": tables}
