import os
import pytest
import sqlite3
from app.database.drivers import build_connection_url
from app.database.ssrf_protection import validate_host_safety
from app.ai.sql_validator import validate_sql
from app.database.connection_manager import create_direct_engine
from app.database.query_executor import execute_raw_sql
from app.database.schema_inspector import discover_database_schema
from app.security.encryption import encrypt_secret, decrypt_secret

SAMPLE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample-databases", "ecommerce_sample.db"))

def test_encryption_and_decryption():
    secret = "SuperSecretDbPassword123!@#"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret

def test_dialect_url_builders():
    # PostgreSQL
    pg_url = build_connection_url("postgresql", "pg.company.internal", 5432, "analytics", "admin", "p@ss:word")
    assert pg_url.startswith("postgresql+psycopg://")
    assert "admin:p%40ss%3Aword@pg.company.internal:5432/analytics" in pg_url

    # MySQL
    mysql_url = build_connection_url("mysql", "db.company.com", 3306, "shop", "user", "pass", ssl_enabled=True)
    assert mysql_url.startswith("mysql+pymysql://")
    assert "ssl=true" in mysql_url

    # Oracle
    oracle_url = build_connection_url("oracle", "oracle.prod", 1521, "ORCLPDB1", "system", "oracle_pass")
    assert oracle_url.startswith("oracle+oracledb://")
    assert "service_name=ORCLPDB1" in oracle_url

    # MSSQL
    mssql_url = build_connection_url("mssql", "sqlserver.cloud", 1433, "master", "sa", "MsSqlPass!")
    assert mssql_url.startswith("mssql+pyodbc://")

    # SQLite
    sqlite_url = build_connection_url("sqlite", database_name="test.db")
    assert sqlite_url == "sqlite:///test.db"

def test_ssrf_protection():
    # Cloud metadata ip should raise ValueError
    with pytest.raises(ValueError, match="Access to forbidden cloud metadata host"):
        validate_host_safety("169.254.169.254")

def test_sql_validator_accepts_valid_queries():
    valid_queries = [
        "SELECT * FROM employees WHERE salary > 50000 ORDER BY salary DESC LIMIT 5",
        "SELECT department_id, COUNT(*) AS cnt FROM employees GROUP BY department_id",
        "WITH high_earners AS (SELECT * FROM employees WHERE salary > 100000) SELECT * FROM high_earners",
    ]
    for q in valid_queries:
        is_valid, err, cleaned = validate_sql(q)
        assert is_valid, f"Query failed validation: {err}"
        assert cleaned

def test_sql_validator_rejects_destructive_queries():
    dangerous_queries = [
        "DROP TABLE employees;",
        "DELETE FROM employees WHERE id = 1;",
        "UPDATE employees SET salary = 999999;",
        "INSERT INTO employees (name) VALUES ('Hacker');",
        "ALTER TABLE employees ADD COLUMN leaked_data TEXT;",
        "TRUNCATE TABLE customers;",
        "SELECT 1; DROP TABLE employees;",
        "SELECT * FROM employees; UPDATE employees SET role = 'CEO';",
    ]
    for q in dangerous_queries:
        is_valid, err, _ = validate_sql(q)
        assert not is_valid, f"Dangerous query was wrongly allowed: {q}"
        assert err is not None

def test_schema_discovery_on_sample_database():
    engine = create_direct_engine(dialect="sqlite", database_name=SAMPLE_DB_PATH)
    tables = discover_database_schema(engine, connection_id="conn-test-01")
    table_names = [t["table_name"] for t in tables]
    
    assert "employees" in table_names
    assert "departments" in table_names
    assert "products" in table_names
    assert "orders" in table_names
    assert "order_items" in table_names
    assert "customers" in table_names
    assert "categories" in table_names

def test_actual_sql_execution_on_sample_database():
    engine = create_direct_engine(dialect="sqlite", database_name=SAMPLE_DB_PATH)
    sql = "SELECT full_name, salary, role FROM employees ORDER BY salary DESC LIMIT 3"
    result = execute_raw_sql(engine, sql)

    assert result["success"] is True
    assert result["row_count"] == 3
    assert result["execution_time_ms"] > 0
    assert len(result["columns"]) == 3
    assert result["columns"][0]["name"] == "full_name"
    assert result["columns"][1]["name"] == "salary"

    # Verify highest earner is Alice Chen
    top_earner = result["rows"][0]
    assert top_earner["full_name"] == "Alice Chen"
    assert top_earner["salary"] == 145000.0
