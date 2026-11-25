# QueryLens AI – Multi-Database Conversational Intelligence Platform

QueryLens AI is an enterprise-grade, full-stack Generative AI application that allows non-technical business users and data analysts to interact with enterprise databases using natural language.

QueryLens AI goes far beyond a basic Text-to-SQL chatbot:
1. **Generates SQL** using target dialect semantics (PostgreSQL, MySQL, Oracle, SQL Server, SQLite).
2. **Strictly Validates SQL** through a dedicated security parsing layer (enforcing read-only `SELECT`, preventing destructive operations or multi-statement injections).
3. **Executes Against Real Databases**, measuring execution times, column types, and retrieving exact database rows.
4. **Captures and Auto-Corrects SQL Errors** through a closed-loop recovery mechanism.
5. **Generates Grounded AI Explanations** and interactive data visualizations (Bar, Line, Pie, Metric Cards).

---

## 🏛️ System Architecture

```
                  ┌───────────────────────────────────────────────┐
                  │          QueryLens Web Application            │
                  │   (React + JavaScript + Monaco + Recharts)    │
                  └───────────────────────┬───────────────────────┘
                                          │ REST & WebSocket
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │             FastAPI Backend Hub               │
                  │  ┌─────────────────┐    ┌──────────────────┐  │
                  │  │ Auth & Tenants  │    │ SQL Validator    │  │
                  │  ├─────────────────┤    ├──────────────────┤  │
                  │  │ RAG & Schema    │    │ Error Corrector  │  │
                  │  ├─────────────────┤    ├──────────────────┤  │
                  │  │ LLM Factory     │    │ Query Executor   │  │
                  │  └─────────────────┘    └──────────────────┘  │
                  └───────────┬───────────────┬───────────────────┘
                              │               │
        ┌─────────────────────┼───────────────┴──────────────────────┐
        │ Method 1: Direct    │ Method 2: On-Prem Agent              │ Method 3: REST API
        ▼                     ▼                                      ▼
┌───────────────┐   ┌───────────────────────────────┐    ┌───────────────────────┐
│ Cloud / VPC   │   │ Outbound WebSocket Connection │    │ Business REST API     │
│ Databases     │   │               ▼               │    │ (OpenAPI / JSON Proxy)│
│ (PostgreSQL,  │   │  QueryLens Connector Agent    │    └───────────────────────┘
│  MySQL,       │   │   (Local Company Server)      │
│  Oracle,      │   │               ▼               │
│  MSSQL,       │   │    Local Company Database     │
│  SQLite)      │   └───────────────────────────────┘
└───────────────┘
```

---

## 🚀 Key Capabilities

### 1. Multi-Database Dialect Awareness
- **PostgreSQL**: `LIMIT n`, `ILIKE`, `DATE_TRUNC('month', col)`.
- **MySQL**: `LIMIT n`, `DATE_FORMAT(col, '%Y-%m')`, backtick escaping.
- **Oracle**: `FETCH FIRST n ROWS ONLY`, `DUAL` table compatibility, `TO_CHAR(col, 'YYYY-MM')`.
- **Microsoft SQL Server**: `SELECT TOP n`, `DATEPART`, `FORMAT(col, 'yyyy-MM')`.
- **SQLite**: Built-in support for zero-friction local development and offline testing.

### 2. Three Connectivity Methods
1. **Direct Database Connection**: Safe connection pooling via SQLAlchemy, Fernet symmetric credential encryption at rest, SSRF protection against cloud metadata hosts.
2. **Secure On-Premise Database Agent**: Independent Python daemon (`connector-agent/`) that connects outbound to QueryLens Cloud via secure WebSockets. Internal databases never expose public IP addresses. Local policy enforces read-only query safety before execution.
3. **Business API Integration**: REST connector with configurable endpoints, headers, and Bearer / API Key authentication.

### 3. Dedicated SQL Validation & Security Layer
- Rejects non-read-only commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `CREATE`, `REPLACE`, `GRANT`, `REVOKE`, `EXEC`, `SHUTDOWN`, etc.).
- Prohibits multiple-statement query injection (semicolons separating queries).
- Enforces execution timeouts and query row limits.
- Audits every execution in immutable security logs.

### 4. Automatic SQL Error Recovery Loop
If a generated query fails against the database (e.g. column typo or dialect mismatch):
1. Error code and schema details are passed to the correction engine.
2. The AI generates a corrected query.
3. The query passes re-validation.
4. The system executes the corrected query (max 2 automatic retries).

### 5. Multi-Tenant Organization Isolation
- Complete logical separation: Users, Connections, Schema Metadata, Query History, Agents, and Audit Logs are strictly isolated by `organization_id`.
- Role-Based Access Control: `Admin`, `Member`, and `Viewer`.

---

## 🛠️ Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Navigate to project root
cd d:\QueryLens.AI

# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend\requirements.txt

# Seed sample business database (E-Commerce demo database)
python sample-databases\init_sample_db.py

# Launch FastAPI backend
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Backend API and Swagger UI will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
# In a new terminal:
cd d:\QueryLens.AI\frontend

# Install dependencies (already completed)
npm install

# Start Vite React development server
npm run dev
```
Frontend application will be live at: `http://localhost:3000`

---

## 🧪 Running the Automated Test Suite

QueryLens AI includes a complete pytest test suite covering encryption, dialect URL generation, SSRF prevention, SQL validation, schema discovery, exact query execution, and multi-tenant isolation:

```bash
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest tests\ -v
```

All 8 integration and unit tests pass with 0 errors.

---

## 🐳 Docker Compose Deployment

To deploy the entire production stack (PostgreSQL database, FastAPI backend, Nginx React frontend, sample MySQL database):

```bash
docker compose up --build -d
```

- **Frontend Application**: `http://localhost:80`
- **Backend API**: `http://localhost:8000/docs`
- **Application Database**: PostgreSQL on port `5432`
- **Sample MySQL Database**: MySQL on port `3306`

---

## 🔒 Security Best Practices
- **Never Log Secrets**: Passwords and connection secrets are encrypted using Fernet cryptography before saving to disk.
- **Dialect Isolation**: Connection strings use strict URL encoding to prevent injection in connection parameters.
- **SSRF Hardening**: Private internal cloud metadata IPs (e.g. `169.254.169.254`) are systematically rejected.
- **Zero Hallucination Guarantee**: AI result explanations are grounded exclusively in retrieved database rows.
