# QueryLens Connector Agent (On-Premise)

The **QueryLens Connector Agent** is a secure, lightweight Python service designed to be deployed within an organization's private network or on-premise infrastructure.

It bridges private, firewalled databases (PostgreSQL, MySQL, Oracle, MSSQL, SQLite) to the **QueryLens AI** platform without exposing the database to the public internet or requiring open inbound ports.

---

## 🔒 Security Architecture

```
QueryLens Cloud
      │
      ▲  (Outbound Encrypted WebSocket over TLS)
      │
QueryLens Connector Agent (Internal Server)
      │
      ▼  (Local Database Connection)
Internal Company Database
```

- **Outbound-only connection**: No inbound firewall ports required.
- **Organization-specific token**: Authenticated with cryptographically generated agent tokens.
- **Local Defense-in-Depth**: Agent independently verifies that every incoming query is strictly a read-only `SELECT` query. Prohibits any `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, or multi-statement injections before touching the database.
- **Configurable query limits & timeouts**: Protects internal databases from query overload.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file or export environment variables:

```bash
# QueryLens Cloud Configuration
CLOUD_WS_URL=ws://127.0.0.1:8000/ws/agents/connect
AGENT_TOKEN=qlagent_your_generated_token_from_querylens_dashboard
AGENT_NAME=HQ-Production-Agent-01

# Internal Local Database Configuration
LOCAL_DB_DIALECT=postgresql # postgresql, mysql, oracle, mssql, sqlite
LOCAL_DB_HOST=127.0.0.1
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=company_erp
LOCAL_DB_USER=readonly_user
LOCAL_DB_PASSWORD=your_secure_password
```

### 3. Run the Agent
```bash
python -m app.main
```
