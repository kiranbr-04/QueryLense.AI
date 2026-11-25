import re
from typing import Tuple, Optional, Set, List
import sqlparse
from sqlparse.sql import Statement, Token, IdentifierList, Identifier
from sqlparse.tokens import DML, DDL, Keyword

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", 
    "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL", "MERGE", 
    "UPSERT", "ATTACH", "DETACH", "SHUTDOWN", "INTO OUTFILE", "LOAD DATA",
    "XP_CMDSHELL", "BENCHMARK", "PG_SLEEP", "SLEEP", "COPY", "VACUUM",
}

FORBIDDEN_PATTERNS = [
    re.compile(r";\s*\S+", re.IGNORECASE),  # multiple queries separated by semicolon
    re.compile(r"\binto\s+outfile\b", re.IGNORECASE),
    re.compile(r"\binto\s+dumpfile\b", re.IGNORECASE),
    re.compile(r"\bxp_cmdshell\b", re.IGNORECASE),
    re.compile(r"\bpg_sleep\b", re.IGNORECASE),
    re.compile(r"\b(truncate|drop|delete|alter|insert|update)\b", re.IGNORECASE),
]

def extract_table_names(sql: str) -> Set[str]:
    """Extract table names referenced in the query for schema validation."""
    tables = set()
    try:
        parsed = sqlparse.parse(sql)
        for stmt in parsed:
            from_seen = False
            for token in stmt.tokens:
                if from_seen:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.add(identifier.get_real_name())
                    elif isinstance(token, Identifier):
                        tables.add(token.get_real_name())
                    elif token.ttype is Keyword and token.value.upper() in ("JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"):
                        continue
                    elif token.ttype is Keyword and token.value.upper() not in ("AS", "ON"):
                        from_seen = False
                elif token.ttype is Keyword and token.value.upper() in ("FROM", "JOIN", "INTO"):
                    from_seen = True
    except Exception:
        pass
    return {t for t in tables if t}

def validate_sql(
    sql: str,
    allowed_tables: Optional[List[str]] = None,
    max_limit: int = 1000,
) -> Tuple[bool, Optional[str], str]:
    """
    Strict SQL validation layer.
    Ensures:
      1. Single statement only.
      2. Strictly read-only (SELECT / WITH ... SELECT).
      3. No DDL, DML modifications, or destructive functions.
      4. Safe comments / no comment trickery.
      5. Referenced tables match discovered database schema (if provided).
    Returns (is_valid, error_message, cleaned_sql).
    """
    if not sql or not sql.strip():
        return False, "Query cannot be empty.", ""

    # Clean markdown code blocks if the LLM wrapped it in ```sql ... ```
    cleaned_sql = sql.strip()
    if cleaned_sql.startswith("```"):
        cleaned_sql = re.sub(r"^```(?:sql)?\s*", "", cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r"\s*```$", "", cleaned_sql)
    cleaned_sql = cleaned_sql.strip().rstrip(";")

    # Parse statements
    parsed = sqlparse.parse(cleaned_sql)
    if not parsed:
        return False, "Failed to parse SQL statement.", ""

    if len(parsed) > 1:
        return False, "Multiple SQL statements are strictly forbidden for security.", ""

    stmt = parsed[0]

    # Verify statement begins with SELECT or WITH
    first_token = None
    for token in stmt.tokens:
        if not token.is_whitespace and token.ttype is not sqlparse.tokens.Comment:
            first_token = token
            break

    if not first_token or first_token.value.upper() not in ("SELECT", "WITH"):
        return False, f"Unauthorized statement type '{first_token.value if first_token else 'UNKNOWN'}'. Only read-only SELECT queries are permitted.", ""

    # Check for forbidden keywords across all tokens
    sql_upper = cleaned_sql.upper()
    for kw in FORBIDDEN_KEYWORDS:
        # Match whole word
        if re.search(rf"\b{kw}\b", sql_upper):
            return False, f"Forbidden SQL operation or keyword detected: '{kw}'. Query execution rejected.", ""

    # Check forbidden regex patterns (e.g. multiple statements, outfile, shell)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(cleaned_sql):
            match = pattern.search(cleaned_sql).group(0)
            return False, f"Potentially malicious or destructive pattern detected: '{match}'. Query execution rejected.", ""

    # Check if allowed_tables are specified, verify tables
    if allowed_tables:
        allowed_set = {t.lower() for t in allowed_tables}
        extracted = extract_table_names(cleaned_sql)
        for tbl in extracted:
            if tbl and tbl.lower() not in allowed_set:
                return False, f"Query references table '{tbl}' which is not in the authorized database schema.", ""

    return True, None, cleaned_sql
