import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.database.drivers import build_connection_url
from app.database.ssrf_protection import validate_host_safety
from app.security.encryption import decrypt_secret
from app.models.connection import DatabaseConnection

logger = logging.getLogger("querylens.database")

# In-memory pool of connection engines keyed by connection ID or config hash
_engine_cache: Dict[str, Engine] = {}

def get_engine_for_connection(connection: DatabaseConnection) -> Engine:
    """Get or create an SQLAlchemy Engine for a DatabaseConnection record."""
    cache_key = f"{connection.id}_{connection.updated_at.isoformat() if connection.updated_at else 'init'}"
    if cache_key in _engine_cache:
        return _engine_cache[cache_key]

    # Decrypt password
    decrypted_password = decrypt_secret(connection.encrypted_password) if connection.encrypted_password else None

    # Parse extra params
    extra = {}
    if connection.extra_params:
        try:
            extra = json.loads(connection.extra_params)
        except Exception:
            extra = {}

    engine = create_direct_engine(
        dialect=connection.dialect,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        username=connection.username,
        password=decrypted_password,
        ssl_enabled=connection.ssl_enabled,
        extra_params=extra,
    )

    _engine_cache[cache_key] = engine
    return engine

def create_direct_engine(
    dialect: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database_name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    ssl_enabled: bool = False,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Engine:
    """Validate host and instantiate a new SQLAlchemy Engine."""
    if dialect != "sqlite" and host:
        validate_host_safety(host)

    url = build_connection_url(
        dialect=dialect,
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        password=password,
        ssl_enabled=ssl_enabled,
        extra_params=extra_params,
    )

    connect_args = {}
    if dialect == "sqlite":
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )
    return engine

def test_connection_params(
    dialect: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database_name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    ssl_enabled: bool = False,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Test raw connection credentials by executing a lightweight ping query."""
    engine = None
    try:
        engine = create_direct_engine(
            dialect=dialect,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            extra_params=extra_params,
        )

        test_query = "SELECT 1"
        if dialect == "oracle":
            test_query = "SELECT 1 FROM DUAL"

        with engine.connect() as conn:
            result = conn.execute(text(test_query))
            val = result.scalar()

        return {
            "success": True,
            "message": f"Successfully connected to {dialect.upper()} database '{database_name or 'default'}'.",
            "server_version": "Connected",
        }
    except Exception as e:
        logger.error(f"Connection test failed for {dialect} on host {host}: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "error_detail": type(e).__name__,
        }
    finally:
        if engine and dialect == "sqlite":
            pass  # keep SQLite or let gc clean
        elif engine:
            engine.dispose()
