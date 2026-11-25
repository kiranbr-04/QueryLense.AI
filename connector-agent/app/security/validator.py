import re
from typing import Tuple, Optional
import sqlparse

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", 
    "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL", "MERGE", 
    "UPSERT", "ATTACH", "DETACH", "SHUTDOWN", "INTO OUTFILE", "LOAD DATA",
    "XP_CMDSHELL", "BENCHMARK", "PG_SLEEP", "SLEEP", "COPY", "VACUUM",
}

def validate_agent_sql(sql: str) -> Tuple[bool, Optional[str], str]:
    """
    On-premise validation layer before executing any command received from QueryLens Cloud.
    Rejects any non-SELECT, destructive, or multiple-statement queries.
    """
    if not sql or not sql.strip():
        return False, "Query cannot be empty.", ""

    clean = sql.strip().rstrip(";")
    parsed = sqlparse.parse(clean)
    if not parsed or len(parsed) > 1:
        return False, "Multiple or unparseable queries rejected by on-premise security policy.", ""

    stmt = parsed[0]
    first_token = None
    for token in stmt.tokens:
        if not token.is_whitespace and token.ttype is not sqlparse.tokens.Comment:
            first_token = token
            break

    if not first_token or first_token.value.upper() not in ("SELECT", "WITH"):
        return False, f"Unauthorized operation '{first_token.value if first_token else 'UNKNOWN'}'. Agent executes strictly read-only SELECT queries.", ""

    clean_upper = clean.upper()
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", clean_upper):
            return False, f"Prohibited operation '{kw}' rejected by local agent policy.", ""

    return True, None, clean
