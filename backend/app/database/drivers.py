import urllib.parse
from typing import Dict, Any, Optional

SUPPORTED_DIALECTS = {
    "postgresql": {
        "name": "PostgreSQL",
        "default_port": 5432,
        "driver": "psycopg",
        "url_scheme": "postgresql+psycopg",
    },
    "mysql": {
        "name": "MySQL",
        "default_port": 3306,
        "driver": "pymysql",
        "url_scheme": "mysql+pymysql",
    },
    "oracle": {
        "name": "Oracle Database",
        "default_port": 1521,
        "driver": "oracledb",
        "url_scheme": "oracle+oracledb",
    },
    "mssql": {
        "name": "Microsoft SQL Server",
        "default_port": 1433,
        "driver": "pyodbc",
        "url_scheme": "mssql+pyodbc",
    },
    "sqlite": {
        "name": "SQLite (Local/Testing)",
        "default_port": 0,
        "driver": "sqlite",
        "url_scheme": "sqlite",
    },
}

def build_connection_url(
    dialect: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database_name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    ssl_enabled: bool = False,
    extra_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Construct a secure and properly-escaped SQLAlchemy connection URL for the target dialect.
    """
    dialect = dialect.lower().strip()
    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(f"Unsupported database dialect: '{dialect}'. Supported dialects are: {list(SUPPORTED_DIALECTS.keys())}")

    if dialect == "sqlite":
        # SQLite uses local file path or :memory:
        db_path = database_name or ":memory:"
        return f"sqlite:///{db_path}"

    config = SUPPORTED_DIALECTS[dialect]
    resolved_port = port or config["default_port"]
    encoded_user = urllib.parse.quote_plus(username) if username else ""
    encoded_pass = urllib.parse.quote_plus(password) if password else ""
    auth_part = f"{encoded_user}:{encoded_pass}@" if (encoded_user or encoded_pass) else ""
    host_part = f"{host}:{resolved_port}" if host else f"localhost:{resolved_port}"

    query_params = {}
    if extra_params:
        query_params.update(extra_params)

    if dialect == "postgresql":
        if ssl_enabled:
            query_params["sslmode"] = "require"
        query_string = f"?{urllib.parse.urlencode(query_params)}" if query_params else ""
        return f"postgresql+psycopg://{auth_part}{host_part}/{database_name or ''}{query_string}"

    elif dialect == "mysql":
        query_params["charset"] = "utf8mb4"
        if ssl_enabled:
            query_params["ssl"] = "true"
        query_string = f"?{urllib.parse.urlencode(query_params)}" if query_params else ""
        return f"mysql+pymysql://{auth_part}{host_part}/{database_name or ''}{query_string}"

    elif dialect == "oracle":
        # Oracle standard service name format
        query_string = f"?{urllib.parse.urlencode(query_params)}" if query_params else ""
        return f"oracle+oracledb://{auth_part}{host_part}/?service_name={database_name or 'ORCL'}{('&' + urllib.parse.urlencode(query_params)) if query_params else ''}"

    elif dialect == "mssql":
        query_params.setdefault("driver", "ODBC Driver 17 for SQL Server")
        if ssl_enabled:
            query_params["Encrypt"] = "yes"
        query_string = f"?{urllib.parse.urlencode(query_params)}"
        return f"mssql+pyodbc://{auth_part}{host_part}/{database_name or ''}{query_string}"

    raise ValueError(f"Unimplemented dialect builder for '{dialect}'")
