import os
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db, SessionLocal, engine
from app.models import Base

SAMPLE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample-databases", "ecommerce_sample.db"))

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_full_saas_lifecycle_and_tenant_isolation(client):
    # 1. Register Organization A
    res_a = client.post("/api/v1/auth/register", json={
        "email": "admin@orga.com",
        "password": "Password123!",
        "full_name": "Org A Admin",
        "organization_name": "Acme Health",
    })
    assert res_a.status_code == 200, res_a.text
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Organization B
    res_b = client.post("/api/v1/auth/register", json={
        "email": "admin@orgb.com",
        "password": "Password123!",
        "full_name": "Org B Admin",
        "organization_name": "Beta Ecom",
    })
    assert res_b.status_code == 200, res_b.text
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Org A connects to SQLite Sample DB
    conn_res = client.post("/api/v1/connections", json={
        "name": "Acme Production DB",
        "connection_type": "direct",
        "dialect": "sqlite",
        "database_name": SAMPLE_DB_PATH,
    }, headers=headers_a)
    assert conn_res.status_code == 200, conn_res.text
    conn_data = conn_res.json()
    conn_id_a = conn_data["id"]
    assert conn_data["status"] == "connected"

    # 4. Verify Tenant Isolation: Org B attempts to access Org A's connection -> MUST BE 404!
    leak_check = client.get(f"/api/v1/connections/{conn_id_a}", headers=headers_b)
    assert leak_check.status_code == 404, "Tenant isolation breach: Org B could access Org A's connection!"

    # 5. Schema Discovery for Org A
    schema_res = client.get(f"/api/v1/connections/{conn_id_a}/schema", headers=headers_a)
    assert schema_res.status_code == 200
    tables = schema_res.json()
    assert len(tables) >= 5
    table_names = [t["table_name"] for t in tables]
    assert "employees" in table_names

    # 6. Natural Language Text-to-SQL Generation
    gen_res = client.post("/api/v1/query/generate", json={
        "connection_id": conn_id_a,
        "question": "Show the top five employees with the highest salary",
    }, headers=headers_a)
    assert gen_res.status_code == 200, gen_res.text
    gen_data = gen_res.json()
    assert gen_data["is_valid"] is True
    assert "employees" in gen_data["generated_sql"].lower()

    # 7. Actual Query Execution & Exact Record Retrieval
    exec_res = client.post("/api/v1/query/execute", json={
        "connection_id": conn_id_a,
        "sql": gen_data["generated_sql"],
        "question": "Show the top five employees with the highest salary",
        "auto_explain": True,
    }, headers=headers_a)
    assert exec_res.status_code == 200, exec_res.text
    exec_data = exec_res.json()
    assert exec_data["success"] is True
    assert exec_data["row_count"] > 0
    assert exec_data["execution_time_ms"] > 0
    assert exec_data["ai_explanation"] is not None
    assert len(exec_data["rows"]) <= 5

    # 8. Check Query History & Isolation
    hist_a = client.get("/api/v1/query/history", headers=headers_a)
    assert hist_a.status_code == 200
    assert len(hist_a.json()) >= 1

    hist_b = client.get("/api/v1/query/history", headers=headers_b)
    assert hist_b.status_code == 200
    assert len(hist_b.json()) == 0  # Org B has zero history

    # 9. Audit Logs
    audit_res = client.get("/api/v1/audit/logs", headers=headers_a)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 2  # user register, connection create, query execute
