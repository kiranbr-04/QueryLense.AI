import os
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base
from app.database.session import init_db, engine
from app.database.connection_manager import create_direct_engine
from app.database.query_executor import execute_raw_sql
from app.database.schema_inspector import discover_database_schema, format_schema_for_prompt
from app.ai.conversational_memory import format_conversation_context
from app.ai.sql_validator import validate_sql
from app.ai.provider_factory import IntelligentMockProvider
from app.ai.prompt_templates import (
    TEXT_TO_SQL_SYSTEM_PROMPT, 
    ERROR_CORRECTION_SYSTEM_PROMPT,
    RESULT_EXPLANATION_SYSTEM_PROMPT,
)

SAMPLE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample-databases", "ecommerce_sample.db"))

@pytest.fixture(scope="module")
def sample_engine():
    return create_direct_engine(dialect="sqlite", database_name=SAMPLE_DB_PATH)

@pytest.fixture(scope="module")
def sample_schema(sample_engine):
    return discover_database_schema(sample_engine, connection_id="test-accuracy-conn")

@pytest.fixture(scope="module")
def mock_provider():
    return IntelligentMockProvider()

@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    init_db()
    c = TestClient(app)
    yield c
    Base.metadata.drop_all(bind=engine)

def _build_prompt(question: str, schema_tables: list, dialect: str = "sqlite", history: list = None) -> str:
    schema_text = format_schema_for_prompt(schema_tables, dialect)
    conv_turns = []
    if history:
        for turn in history:
            conv_turns.append({"role": "user", "content": turn["question"]})
            conv_turns.append({"role": "assistant", "content": f"Executed SQL: {turn['sql']}\nResult Summary: Retrieved rows."})
    conv_text = format_conversation_context(conv_turns)
    return f"""Target Dialect: {dialect}
{conv_text}
{schema_text}

User Question: {question}

Generate ONLY the executable read-only SQL query for {dialect.upper()}:"""

# ==============================================================================
# SCENARIO 1: Exact Filtering (WHERE salary = ...)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_01_exact_filtering(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Find employees whose salary is 110000", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)
    
    assert "where" in sql.lower()
    assert "salary = 110000" in sql.lower() or "salary = 110000.0" in sql.lower()

    # Execute on sample DB
    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 1
    assert res["rows"][0]["full_name"] == "David Ross"
    assert float(res["rows"][0]["salary"]) == 110000.0

# ==============================================================================
# SCENARIO 2: Comparison (WHERE salary > 100000)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_02_comparison_filter(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Show employees earning more than 100000", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "where" in sql.lower()
    assert "salary > 100000" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 4  # Alice, Marcus, Sarah, David
    for row in res["rows"]:
        assert float(row["salary"]) > 100000.0

# ==============================================================================
# SCENARIO 3: Multiple Conditions (Department + Salary)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_03_multiple_conditions(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Employees in department 1 with salary greater than 90000", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "where" in sql.lower()
    assert "department_id = 1" in sql.lower()
    assert "salary > 90000" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 3  # Alice Chen (145k), Marcus Vance (132k), Elena Rostova (98k)
    for row in res["rows"]:
        assert row["department_id"] == 1
        assert float(row["salary"]) > 90000.0

# ==============================================================================
# SCENARIO 4: Sorting (ORDER BY salary DESC)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_04_sorting(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Show employees ordered by highest salary", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "order by salary desc" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    salaries = [float(r["salary"]) for r in res["rows"]]
    assert salaries == sorted(salaries, reverse=True)

# ==============================================================================
# SCENARIO 5: Top N (ORDER BY salary DESC LIMIT 3)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_05_top_n(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Top three highest-paid employees", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "limit 3" in sql.lower()
    assert "order by salary desc" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 3
    assert res["rows"][0]["full_name"] == "Alice Chen"
    assert res["rows"][1]["full_name"] == "Marcus Vance"
    assert res["rows"][2]["full_name"] == "Sarah Jenkins"

# ==============================================================================
# SCENARIO 6: Aggregation (AVG salary)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_06_aggregation_avg(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("What is the average salary of employees?", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "avg(salary)" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 1
    avg_val = list(res["rows"][0].values())[0]
    assert 90000 <= float(avg_val) <= 100000  # Actual average is ~96,000

# ==============================================================================
# SCENARIO 7: Counting (COUNT employees)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_07_count(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Count how many employees we have", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "count(*)" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 1
    cnt = list(res["rows"][0].values())[0]
    assert cnt == 10

# ==============================================================================
# SCENARIO 8: Grouping (GROUP BY department)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_08_group_by(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Total salary by department", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "group by department_id" in sql.lower()
    assert "sum(salary)" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] >= 4  # 5 departments in sample db

# ==============================================================================
# SCENARIO 9: Zero Matching Records (Grounded 0-row handling)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_09_zero_matching_records(mock_provider, sample_schema, sample_engine):
    prompt = _build_prompt("Find employees whose salary is 99999999", sample_schema)
    sql = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt)

    assert "salary = 99999999" in sql.lower()

    res = execute_raw_sql(sample_engine, sql)
    assert res["success"] is True
    assert res["row_count"] == 0
    assert len(res["rows"]) == 0

    # Test explanation on 0 records
    explain_prompt = f"User Question: Find employees whose salary is 99999999\nExecuted SQL: {sql}\nTotal Rows Returned: 0\nExecution Time: 1.2 ms\nSample Returned Data: []"
    explanation_json = await mock_provider.generate_text(system_prompt=RESULT_EXPLANATION_SYSTEM_PROMPT, user_prompt=explain_prompt)
    parsed = json.loads(explanation_json)
    assert "No records were found" in parsed["explanation"]

# ==============================================================================
# SCENARIO 10: Automatic SQL Error Correction
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_10_sql_error_correction(mock_provider, sample_schema, sample_engine):
    # Failing SQL references non-existent column 'name' instead of 'full_name'
    failing_sql = "SELECT name, salary FROM employees WHERE salary > 100000;"
    error_message = "no such column: name"

    correction_prompt = f"Original User Question: Employees with salary > 100000\nFailing SQL Query: {failing_sql}\nDatabase Error: {error_message}\n\nAvailable Database Schema:\nTable: employees\n- id (INTEGER)\n- full_name (VARCHAR)\n- salary (FLOAT)\n- role (VARCHAR)"
    corrected_sql = await mock_provider.generate_text(system_prompt=ERROR_CORRECTION_SYSTEM_PROMPT, user_prompt=correction_prompt)

    assert "full_name" in corrected_sql.lower()

    # Verify corrected SQL runs cleanly on database
    res = execute_raw_sql(sample_engine, corrected_sql)
    assert res["success"] is True
    assert res["row_count"] == 4

# ==============================================================================
# SCENARIO 11: SQL Injection Rejection
# ==============================================================================
def test_scenario_11_sql_injection_protection():
    injection_payloads = [
        "SELECT * FROM employees; DROP TABLE employees;",
        "SELECT * FROM employees; UPDATE employees SET salary = 0;",
        "'; EXEC xp_cmdshell('dir'); --",
        "SELECT * FROM employees WHERE 1=1; DELETE FROM employees WHERE 1=1;",
    ]
    for injection in injection_payloads:
        is_valid, err, _ = validate_sql(injection)
        assert not is_valid, f"Injection passed validation unexpectedly: {injection}"
        assert err is not None

# ==============================================================================
# SCENARIO 12: Write & DDL Operations Rejection
# ==============================================================================
def test_scenario_12_write_ddl_rejection():
    forbidden = [
        "INSERT INTO employees (full_name, salary) VALUES ('Infiltrator', 999999);",
        "UPDATE employees SET salary = salary * 2;",
        "DELETE FROM employees WHERE id = 1;",
        "ALTER TABLE employees ADD COLUMN hacked TEXT;",
        "TRUNCATE TABLE employees;",
        "CREATE TABLE backdoor (id INT);",
    ]
    for write_stmt in forbidden:
        is_valid, err, _ = validate_sql(write_stmt)
        assert not is_valid, f"Write/DDL statement was permitted: {write_stmt}"
        assert any(term in err.lower() for term in ["read-only", "forbidden", "not allowed", "unauthorized"])

# ==============================================================================
# SCENARIO 13: Conversational Multi-Turn Follow-Ups
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_13_conversational_followups(mock_provider, sample_schema, sample_engine):
    # Turn 1: Show all employees
    turn1_prompt = _build_prompt("Show all employees", sample_schema)
    sql1 = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=turn1_prompt)
    assert "from employees" in sql1.lower()
    res1 = execute_raw_sql(sample_engine, sql1)
    assert res1["success"] is True
    assert res1["row_count"] == 10

    # Turn 2: Follow-up -> "Only in department 1"
    history_turn2 = [{"question": "Show all employees", "sql": sql1}]
    turn2_prompt = _build_prompt("Only in department 1", sample_schema, history=history_turn2)
    sql2 = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=turn2_prompt)
    assert "department_id = 1" in sql2.lower()
    res2 = execute_raw_sql(sample_engine, sql2)
    assert res2["success"] is True
    assert res2["row_count"] == 4

    # Turn 3: Follow-up -> "Sort them by salary in descending order"
    history_turn3 = [
        {"question": "Show all employees", "sql": sql1},
        {"question": "Only in department 1", "sql": sql2},
    ]
    turn3_prompt = _build_prompt("Sort them by salary in descending order", sample_schema, history=history_turn3)
    sql3 = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=turn3_prompt)
    assert "department_id = 1" in sql3.lower()
    assert "order by salary desc" in sql3.lower()
    res3 = execute_raw_sql(sample_engine, sql3)
    assert res3["success"] is True
    assert res3["row_count"] == 4
    salaries = [float(r["salary"]) for r in res3["rows"]]
    assert salaries == sorted(salaries, reverse=True)

    # Turn 4: Follow-up -> "Show only the top two"
    history_turn4 = [
        {"question": "Show all employees", "sql": sql1},
        {"question": "Only in department 1", "sql": sql2},
        {"question": "Sort them by salary in descending order", "sql": sql3},
    ]
    turn4_prompt = _build_prompt("Show only the top two", sample_schema, history=history_turn4)
    sql4 = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=turn4_prompt)
    assert "limit 2" in sql4.lower()
    assert "department_id = 1" in sql4.lower()
    assert "order by salary desc" in sql4.lower()
    res4 = execute_raw_sql(sample_engine, sql4)
    assert res4["success"] is True
    assert res4["row_count"] == 2
    assert res4["rows"][0]["full_name"] == "Alice Chen"
    assert res4["rows"][1]["full_name"] == "Marcus Vance"

# ==============================================================================
# SCENARIO 14: SQL Execution Pipeline with Error Recovery
# ==============================================================================
def test_scenario_14_api_pipeline_auto_recovery(client):
    # Register & connect to sample DB
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "pipeline_tester@corp.com",
        "password": "Password123!",
        "full_name": "Pipeline Tester",
        "organization_name": "Pipeline Org",
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conn_res = client.post("/api/v1/connections", json={
        "name": "Pipeline Test DB",
        "connection_type": "direct",
        "dialect": "sqlite",
        "database_name": SAMPLE_DB_PATH,
    }, headers=headers)
    assert conn_res.status_code == 200
    conn_id = conn_res.json()["id"]

    # Run pipeline with auto_correct enabled
    pipe_res = client.post("/api/v1/query/pipeline", json={
        "connection_id": conn_id,
        "question": "Show top three highest-paid employees",
        "auto_correct": True,
    }, headers=headers)

    assert pipe_res.status_code == 200
    pdata = pipe_res.json()
    assert pdata["success"] is True
    assert pdata["row_count"] == 3
    assert pdata["ai_explanation"] is not None
    assert len(pdata["rows"]) == 3

# ==============================================================================
# SCENARIO 15: Multi-Schema Adaptation (Products & Orders)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_15_multi_schema_adaptation(mock_provider, sample_schema, sample_engine):
    # Query against products table
    prompt_prod = _build_prompt("Show products with price greater than 500", sample_schema)
    sql_prod = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt_prod)
    assert "products" in sql_prod.lower()
    assert "price > 500" in sql_prod.lower()
    res_prod = execute_raw_sql(sample_engine, sql_prod)
    assert res_prod["success"] is True
    assert res_prod["row_count"] > 0
    for row in res_prod["rows"]:
        assert float(row["price"]) > 500.0

    # Query against orders table
    prompt_orders = _build_prompt("Show orders with total amount greater than 1000", sample_schema)
    sql_orders = await mock_provider.generate_text(system_prompt=TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt=prompt_orders)
    assert "orders" in sql_orders.lower()
    assert "total_amount > 1000" in sql_orders.lower()
    res_orders = execute_raw_sql(sample_engine, sql_orders)
    assert res_orders["success"] is True
    assert res_orders["row_count"] > 0
    for row in res_orders["rows"]:
        assert float(row["total_amount"]) > 1000.0
