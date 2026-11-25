import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
import httpx
from app.core.config import settings

logger = logging.getLogger("querylens.ai")

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        pass

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser Request: {user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No generation candidate returned by Gemini.")
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join([p.get("text", "") for p in parts]).strip()

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 2048,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["content"][0]["text"].strip()

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama API error ({resp.status_code}): {resp.text}")
            return resp.json().get("response", "").strip()

class IntelligentMockProvider(BaseLLMProvider):
    """
    Schema-driven semantic SQL generator and grounded BI result explainer.
    Dynamically analyzes database schema structure (tables, columns, types, foreign keys),
    conversational turn memory, filtering predicates, aggregations, groupings, rankings,
    and dialect-specific syntax without requiring external API keys.
    """
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        sys_lower = system_prompt.lower()
        prompt_lower = user_prompt.lower()

        # Explanation task
        if "business intelligence analyst" in sys_lower or "explain the following query results" in sys_lower or "explain the query results" in sys_lower:
            return self._explain_results(user_prompt)

        # Error correction task
        if "database recovery engineer" in sys_lower or "the previous query failed" in prompt_lower:
            return self._correct_query(user_prompt)

        # Text-to-SQL generation task
        return self._generate_sql(user_prompt)

    def _parse_schema_from_prompt(self, prompt: str) -> Dict[str, Dict[str, Any]]:
        """Extract structured tables, columns, and foreign keys from the prompt context."""
        tables = {}
        current_table = None

        lines = prompt.split("\n")
        for line in lines:
            line_str = line.strip()
            # Match TABLE or VIEW definition (e.g. TABLE `employees`:, Table: employees, etc.)
            table_match = re.match(r"^(?:TABLE|VIEW|Table):?\s*`?([a-zA-Z0-9_]+)`?:?", line_str, re.IGNORECASE)
            if table_match and table_match.group(1).lower() not in ["the", "database", "dialect", "schema", "structure", "available"]:
                current_table = table_match.group(1)
                if current_table not in tables:
                    tables[current_table] = {"columns": {}, "fks": []}
                continue

            if current_table and line_str.startswith("- "):
                # Column line: "- name (type) [PRIMARY KEY] NOT NULL"
                col_match = re.match(r"^-\s+([a-zA-Z0-9_]+)\s*\(([^)]+)\)", line_str)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2).lower()
                    tables[current_table]["columns"][col_name] = col_type

            if current_table and line_str.startswith("* ") and "->" in line_str:
                # FK line: "* department_id -> departments(department_id)"
                fk_match = re.match(r"^\*\s+([a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_]+)\(([^)]+)\)", line_str)
                if fk_match:
                    tables[current_table]["fks"].append({
                        "from_col": fk_match.group(1),
                        "to_table": fk_match.group(2),
                        "to_col": fk_match.group(3),
                    })

        return tables

    def _parse_conversation_history(self, prompt: str) -> List[Dict[str, str]]:
        """Extract previous turn SQL and questions from the prompt context."""
        history = []
        hist_section = re.search(r"### Conversation History Context:(.*?)(?:###|$)", prompt, re.DOTALL)
        if hist_section:
            turns = hist_section.group(1)
            user_questions = re.findall(r"User:\s*(.*?)(?:\n|$)", turns)
            executed_sqls = re.findall(r"Executed SQL:\s*(SELECT.*?)(?:\n|$)", turns, re.IGNORECASE)
            for q, sql in zip(user_questions, executed_sqls):
                history.append({"question": q.strip(), "sql": sql.strip()})
        return history

    def _generate_sql(self, user_prompt: str) -> str:
        # Detect dialect
        dialect = "postgresql"
        for d in ["mysql", "oracle", "mssql", "sqlite"]:
            if f"dialect: {d}" in user_prompt.lower() or f"for {d.upper()}" in user_prompt:
                dialect = d
                break

        # Extract the user's current question
        q_match = re.search(r"User Question:\s*(.*?)(?:\n|$)", user_prompt, re.IGNORECASE)
        question = q_match.group(1).strip() if q_match else user_prompt.strip()
        q_lower = question.lower()

        # Parse available schema
        schema_tables = self._parse_schema_from_prompt(user_prompt)

        # Parse conversation history for follow-ups
        conv_history = self._parse_conversation_history(user_prompt)

        # Check if question is a conversational follow-up
        if conv_history:
            last_turn = conv_history[-1]
            last_sql = last_turn["sql"].rstrip(";")
            followup_sql = self._handle_conversational_followup(question, last_sql, schema_tables, dialect)
            if followup_sql:
                return followup_sql

        # 1. Determine Target Table
        target_table, target_cols = self._identify_target_table(q_lower, schema_tables)

        # 2. Check for Specific Subqueries (e.g. above average salary)
        if "above average" in q_lower or "greater than average" in q_lower or "higher than average" in q_lower:
            num_col = self._find_column_by_types(target_cols, ["int", "float", "double", "decimal", "real", "numeric"]) or "salary"
            return f"SELECT * FROM {target_table} WHERE {num_col} > (SELECT AVG({num_col}) FROM {target_table});"

        # 3. Check for Distinct / Unique
        if "unique" in q_lower or "distinct" in q_lower:
            target_col = self._match_any_column(q_lower, target_cols) or "department_id"
            return f"SELECT DISTINCT {target_col} FROM {target_table};"

        # 4. Check for Aggregations (Average, Sum, Count, Min, Max)
        agg_sql = self._handle_aggregations(q_lower, target_table, target_cols, schema_tables, dialect)
        if agg_sql:
            return agg_sql

        # 5. Check for Ranking (Second highest, 2nd highest, etc.)
        ranking_sql = self._handle_ranking(q_lower, target_table, target_cols, dialect)
        if ranking_sql:
            return ranking_sql

        # 6. Check for Joins (e.g. employees with their department details)
        join_sql = self._handle_joins(q_lower, target_table, schema_tables, dialect)
        if join_sql:
            return join_sql

        # 7. Build Standard SELECT Query with Filters, Sorting, and Limits
        return self._build_filtered_query(q_lower, target_table, target_cols, dialect)

    def _handle_conversational_followup(
        self,
        question: str,
        last_sql: str,
        schema: Dict[str, Dict[str, Any]],
        dialect: str,
    ) -> Optional[str]:
        """
        Handle conversational follow-ups by modifying or extending the previous turn's query.
        Example follow-ups:
          - "Only IT employees" / "Only in department 1"
          - "Sort them by salary in descending order"
          - "Show only the top two"
          - "Who has the highest salary?"
        """
        q_lower = question.lower()

        # Extract table from previous SQL
        table_match = re.search(r"FROM\s+([a-zA-Z0-9_]+)", last_sql, re.IGNORECASE)
        if not table_match:
            return None
        table_name = table_match.group(1)
        table_cols = schema.get(table_name, {}).get("columns", {})

        # Follow-up: Sorting modifier
        if ("sort" in q_lower or "order" in q_lower) and any(w in q_lower for w in ["desc", "asc", "highest", "lowest"]):
            sort_col = self._match_any_column(q_lower, table_cols) or "salary"
            is_desc = any(w in q_lower for w in ["desc", "highest", "descending"])
            base_sql = re.sub(r"\s+ORDER\s+BY.*$", "", last_sql, flags=re.IGNORECASE).rstrip(";")
            base_sql = re.sub(r"\s+LIMIT.*$", "", base_sql, flags=re.IGNORECASE).rstrip(";")
            order_clause = f"ORDER BY {sort_col} {'DESC' if is_desc else 'ASC'}"
            return f"{base_sql} {order_clause};"

        # Follow-up: Limit modifier ("Show only the top two", "first 5", "limit 3", "top 2")
        limit_match = re.search(r"\b(?:top|first|limit|only\s+top)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", q_lower)
        if limit_match:
            num_val = self._word_to_number(limit_match.group(1))
            if num_val:
                base_sql = re.sub(r"\s+LIMIT\s+\d+.*$", "", last_sql, flags=re.IGNORECASE).rstrip(";")
                base_sql = re.sub(r"\s+FETCH\s+FIRST.*$", "", base_sql, flags=re.IGNORECASE).rstrip(";")
                if dialect == "oracle":
                    return f"{base_sql} FETCH FIRST {num_val} ROWS ONLY;"
                elif dialect == "mssql":
                    base_sql = re.sub(r"^SELECT\s+", f"SELECT TOP {num_val} ", base_sql, flags=re.IGNORECASE)
                    return f"{base_sql};"
                else:
                    return f"{base_sql} LIMIT {num_val};"

        # Follow-up: Department filter ("Only IT employees", "Only in department 1", "department 1")
        if "department" in q_lower or "dept" in q_lower or "it employees" in q_lower or "it department" in q_lower:
            cond = self._extract_where_condition(q_lower, table_cols)
            if cond:
                return self._append_where_condition(last_sql, cond)

        if "only" in q_lower or "now show" in q_lower or "whose" in q_lower or "earning" in q_lower:
            cond = self._extract_where_condition(q_lower, table_cols)
            if cond:
                return self._append_where_condition(last_sql, cond)

        # Follow-up: "Who has the highest salary?" / "Which one is highest?"
        if "highest" in q_lower or "top" in q_lower:
            num_col = self._match_any_column(q_lower, table_cols) or "salary"
            base_sql = re.sub(r"\s+ORDER\s+BY.*$", "", last_sql, flags=re.IGNORECASE).rstrip(";")
            base_sql = re.sub(r"\s+LIMIT.*$", "", base_sql, flags=re.IGNORECASE).rstrip(";")
            return f"{base_sql} ORDER BY {num_col} DESC LIMIT 1;"

        return None

    def _append_where_condition(self, sql: str, condition: str) -> str:
        """Helper to append or expand WHERE condition onto an existing SQL statement."""
        sql_clean = sql.rstrip(";")
        limit_match = re.search(r"(\s+LIMIT\s+\d+.*$)", sql_clean, re.IGNORECASE)
        limit_part = limit_match.group(1) if limit_match else ""
        sql_no_limit = re.sub(r"\s+LIMIT\s+\d+.*$", "", sql_clean, flags=re.IGNORECASE)

        order_match = re.search(r"(\s+ORDER\s+BY\s+.*$)", sql_no_limit, re.IGNORECASE)
        order_part = order_match.group(1) if order_match else ""
        sql_core = re.sub(r"\s+ORDER\s+BY\s+.*$", "", sql_no_limit, flags=re.IGNORECASE)

        if "WHERE" in sql_core.upper():
            new_sql = f"{sql_core} AND {condition}{order_part}{limit_part};"
        else:
            new_sql = f"{sql_core} WHERE {condition}{order_part}{limit_part};"
        return new_sql

    def _identify_target_table(self, q_lower: str, schema: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, str]]:
        """Identify which table best matches the question using semantic scoring."""
        if not schema:
            return "employees", {}

        scores = {}
        for t_name, t_meta in schema.items():
            score = 0
            t_lower = t_name.lower()
            t_base = t_lower.rstrip("s")
            cols = t_meta.get("columns", {})

            # Table name / stem match
            if re.search(rf"\b{t_lower}\b", q_lower):
                score += 10
            elif len(t_base) > 2 and re.search(rf"\b{t_base}\b", q_lower):
                score += 8

            # Column matches:
            for c in cols.keys():
                c_lower = c.lower()
                c_clean = c_lower.replace("_", " ")
                if re.search(rf"\b{c_lower}\b", q_lower) or re.search(rf"\b{c_clean}\b", q_lower):
                    score += 4
                if "salary" in c_lower and any(w in q_lower for w in ["salary", "earning", "compensation", "wage", "pay"]):
                    score += 5
                if "price" in c_lower and any(w in q_lower for w in ["price", "cost", "pricing"]):
                    score += 5
                if "stock" in c_lower and any(w in q_lower for w in ["stock", "inventory", "quantity"]):
                    score += 5
                if "amount" in c_lower and any(w in q_lower for w in ["total amount", "amount", "revenue"]):
                    score += 5

            scores[t_name] = score

        best_table = max(scores, key=scores.get)
        if scores[best_table] > 0:
            return best_table, schema[best_table].get("columns", {})

        first_table = list(schema.keys())[0]
        return first_table, schema[first_table].get("columns", {})

    def _match_any_column(self, q_lower: str, columns: Dict[str, str]) -> Optional[str]:
        """Find if any column in the table is mentioned in the question."""
        for col in columns.keys():
            col_clean = col.lower().replace("_", " ")
            if col.lower() in q_lower or col_clean in q_lower:
                return col
        return None

    def _find_column_by_types(self, columns: Dict[str, str], type_keywords: List[str]) -> Optional[str]:
        for col, col_type in columns.items():
            if any(kw in col_type.lower() for kw in type_keywords):
                return col
        return None

    def _word_to_number(self, word: str) -> Optional[int]:
        mapping = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        }
        if word.isdigit():
            return int(word)
        return mapping.get(word.lower())

    def _handle_aggregations(
        self,
        q_lower: str,
        table: str,
        columns: Dict[str, str],
        schema: Dict[str, Dict[str, Any]],
        dialect: str,
    ) -> Optional[str]:
        """Handle average, count, sum, min, max, with optional GROUP BY."""
        # Queries with explicit comparison operators are WHERE filters, not pure aggregations
        has_comparison = any(w in q_lower for w in ["greater than", "more than", "above", "less than", "below", "exceeding", ">", "<"])
        if has_comparison:
            return None

        is_avg = any(w in q_lower for w in ["average", "avg", "mean"])
        is_sum = any(w in q_lower for w in ["total salary", "sum of", "sum "]) or q_lower.startswith("total ") or ("total " in q_lower and "by " in q_lower)
        is_count = any(w in q_lower for w in ["count", "how many", "number of"])
        is_min = any(w in q_lower for w in ["minimum", "lowest", "min "])
        is_max = any(w in q_lower for w in ["maximum", "max "])

        if not (is_avg or is_sum or is_count or is_min or is_max):
            return None

        # Check for GROUP BY
        group_col = None
        group_match = re.search(r"(?:by|in each|per)\s+([a-zA-Z0-9_]+)", q_lower)
        if group_match:
            potential_group = group_match.group(1).lower()
            for c in columns.keys():
                if potential_group in c.lower() or potential_group.rstrip("s") in c.lower():
                    group_col = c
                    break

        num_col = self._match_any_column(q_lower, columns) or self._find_column_by_types(columns, ["int", "float", "decimal", "real"]) or "salary"

        if is_avg:
            if group_col:
                return f"SELECT {group_col}, AVG({num_col}) AS average_{num_col} FROM {table} GROUP BY {group_col};"
            return f"SELECT AVG({num_col}) AS average_{num_col} FROM {table};"

        if is_sum:
            if group_col:
                return f"SELECT {group_col}, SUM({num_col}) AS total_{num_col} FROM {table} GROUP BY {group_col};"
            return f"SELECT SUM({num_col}) AS total_{num_col} FROM {table};"

        if is_count:
            if group_col:
                return f"SELECT {group_col}, COUNT(*) AS total_count FROM {table} GROUP BY {group_col};"
            # Count with condition?
            cond = self._extract_where_condition(q_lower, columns)
            where_clause = f" WHERE {cond}" if cond else ""
            return f"SELECT COUNT(*) AS total_count FROM {table}{where_clause};"

        if is_min:
            if group_col:
                return f"SELECT {group_col}, MIN({num_col}) AS min_{num_col} FROM {table} GROUP BY {group_col};"
            return f"SELECT MIN({num_col}) AS min_{num_col} FROM {table};"

        if is_max:
            if group_col:
                return f"SELECT {group_col}, MAX({num_col}) AS max_{num_col} FROM {table} GROUP BY {group_col};"
            return f"SELECT MAX({num_col}) AS max_{num_col} FROM {table};"

        return None

    def _handle_ranking(self, q_lower: str, table: str, columns: Dict[str, str], dialect: str) -> Optional[str]:
        """Handle 2nd highest, second highest, 3rd highest."""
        second_match = re.search(r"\b(?:second|2nd)\s+highest\b", q_lower)
        if second_match:
            sort_col = self._match_any_column(q_lower, columns) or "salary"
            if dialect == "oracle":
                return f"SELECT * FROM {table} ORDER BY {sort_col} DESC OFFSET 1 ROWS FETCH NEXT 1 ROWS ONLY;"
            return f"SELECT * FROM {table} ORDER BY {sort_col} DESC LIMIT 1 OFFSET 1;"

        third_match = re.search(r"\b(?:third|3rd)\s+highest\b", q_lower)
        if third_match:
            sort_col = self._match_any_column(q_lower, columns) or "salary"
            if dialect == "oracle":
                return f"SELECT * FROM {table} ORDER BY {sort_col} DESC OFFSET 2 ROWS FETCH NEXT 1 ROWS ONLY;"
            return f"SELECT * FROM {table} ORDER BY {sort_col} DESC LIMIT 1 OFFSET 2;"

        return None

    def _handle_joins(self, q_lower: str, target_table: str, schema: Dict[str, Dict[str, Any]], dialect: str) -> Optional[str]:
        """Handle multi-table questions requiring relational joins."""
        fks = schema.get(target_table, {}).get("fks", [])
        if not fks:
            return None

        # Only join when relational intent is present (join, details, with their)
        is_join_intent = any(w in q_lower for w in ["join", "with their", "along with", "together with", "details", "department name", "category name"])
        if not is_join_intent:
            return None

        # Check if question mentions any referred table
        for fk in fks:
            ref_table = fk["to_table"]
            if ref_table.lower() in q_lower or ref_table.lower().rstrip("s") in q_lower or "detail" in q_lower:
                from_col = fk["from_col"]
                to_col = fk["to_col"]
                return f"SELECT {target_table}.*, {ref_table}.name AS {ref_table}_name FROM {target_table} JOIN {ref_table} ON {target_table}.{from_col} = {ref_table}.{to_col} LIMIT 50;"

        return None

    def _extract_where_condition(self, q_lower: str, columns: Dict[str, str]) -> Optional[str]:
        """
        Dynamically extracts WHERE filter condition from natural language.
        Supports:
          - Exact numeric: salary is 50000, salary = 50000, price equal to 100
          - Comparisons: greater than 60000, above 60000, less than 50000, >= 50000
          - Department filters: department 1, IT employees
          - String search: names contain 'a', LIKE '%a%'
          - Null checks: missing department, is null
          - Multiple conditions: IT employees earning more than 50000
        """
        conditions = []

        # Find relevant numeric column (salary, price, amount, stock, budget)
        num_col = None
        for c in columns.keys():
            if any(term in c.lower() for term in ["salary", "price", "amount", "budget", "quantity", "stock"]):
                num_col = c
                break

        # 1. Exact numeric equality (e.g. "salary is 50000", "salary = 50000", "whose salary is 50000", "earning 50000")
        eq_match = re.search(r"(?:salary|price|amount|budget|is|equal to|=|earning|worth)\s+(?:is\s+|equal\s+to\s+|of\s+)?(\d+(?:\.\d+)?)", q_lower)
        if eq_match and not any(w in q_lower for w in ["more than", "greater", "above", "higher than", "less than", "below", "under", "highest", "lowest", "top"]):
            val = eq_match.group(1)
            target_col = num_col or "salary"
            conditions.append(f"{target_col} = {val}")

        # 2. Greater than / Above / More than / Exceeding (e.g. "earning more than 60000", "greater than 60000")
        gt_match = re.search(r"(?:more than|greater than|above|higher than|exceeding|>|over)\s+(\d+(?:\.\d+)?)", q_lower)
        if gt_match:
            val = gt_match.group(1)
            target_col = num_col or "salary"
            conditions.append(f"{target_col} > {val}")

        # 3. Less than / Below / Under
        lt_match = re.search(r"(?:less than|below|under|fewer than|<)\s+(\d+(?:\.\d+)?)", q_lower)
        if lt_match:
            val = lt_match.group(1)
            target_col = num_col or "salary"
            conditions.append(f"{target_col} < {val}")

        # 4. Between X and Y
        between_match = re.search(r"between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)", q_lower)
        if between_match:
            v1, v2 = between_match.group(1), between_match.group(2)
            target_col = num_col or "salary"
            conditions.append(f"{target_col} BETWEEN {v1} AND {v2}")

        # 5. Department filter (e.g. "IT employees", "department 10", "department 1")
        dept_col = next((c for c in columns.keys() if "dept" in c.lower() or "department" in c.lower()), None)
        if dept_col:
            dept_num_match = re.search(r"department\s+(?:id\s+)?['\"]?(\d+)['\"]?", q_lower)
            if dept_num_match:
                dept_id = dept_num_match.group(1)
                conditions.append(f"{dept_col} = {dept_id}")
            elif "it employees" in q_lower or "it department" in q_lower or "whose department is it" in q_lower:
                if dept_col.endswith("_id"):
                    conditions.append(f"{dept_col} = 1")
                else:
                    conditions.append(f"{dept_col} = 'IT'")
            elif "engineering" in q_lower:
                conditions.append(f"{dept_col} = 1" if dept_col.endswith("_id") else f"{dept_col} = 'Engineering'")
            elif "sales" in q_lower:
                conditions.append(f"{dept_col} = 2" if dept_col.endswith("_id") else f"{dept_col} = 'Sales'")

        # 6. String Search: name contains 'a' / starts with 'x'
        name_col = next((c for c in columns.keys() if "name" in c.lower() or "title" in c.lower()), None)
        if name_col:
            contain_match = re.search(r"(?:contain|contains|having|like)\s+['\"]?([a-zA-Z0-9]+)['\"]?", q_lower)
            if contain_match:
                term = contain_match.group(1)
                conditions.append(f"{name_col} LIKE '%{term}%'")

        # 7. Null Checks: missing / is null / without
        if "missing" in q_lower or "is null" in q_lower or "without" in q_lower:
            null_target = self._match_any_column(q_lower, columns) or dept_col or list(columns.keys())[-1]
            conditions.append(f"{null_target} IS NULL")
        elif "not null" in q_lower:
            not_null_target = self._match_any_column(q_lower, columns) or dept_col or list(columns.keys())[-1]
            conditions.append(f"{not_null_target} IS NOT NULL")

        if conditions:
            return " AND ".join(conditions)
        return None

    def _build_filtered_query(self, q_lower: str, table: str, columns: Dict[str, str], dialect: str) -> str:
        """Construct full SELECT query with extracted filters, order by, and limit."""
        # Check if specific columns requested
        proj_cols = "*"
        if "id, name, salary, department" in q_lower or "id, name, salary" in q_lower:
            # Map to actual columns in table
            matched = []
            for wanted in ["id", "name", "salary", "department"]:
                for c in columns.keys():
                    if wanted in c.lower():
                        matched.append(c)
                        break
            if matched:
                proj_cols = ", ".join(matched)

        # WHERE condition
        where_cond = self._extract_where_condition(q_lower, columns)
        where_clause = f" WHERE {where_cond}" if where_cond else ""

        # ORDER BY
        order_clause = ""
        sort_col = self._match_any_column(q_lower, columns) or next((c for c in columns.keys() if any(term in c.lower() for term in ["salary", "price", "amount", "date", "created"])), None)

        if "highest" in q_lower or "desc" in q_lower or "descending" in q_lower:
            if sort_col:
                order_clause = f" ORDER BY {sort_col} DESC"
        elif "lowest" in q_lower or "asc" in q_lower or "ascending" in q_lower:
            if sort_col:
                order_clause = f" ORDER BY {sort_col} ASC"

        # LIMIT
        limit_num = None
        limit_match = re.search(r"\b(?:top|first|limit)\s+(\w+)\b", q_lower)
        if limit_match:
            limit_num = self._word_to_number(limit_match.group(1))

        if not limit_num:
            if "top three" in q_lower or "top 3" in q_lower:
                limit_num = 3
            elif "top five" in q_lower or "top 5" in q_lower:
                limit_num = 5
            elif "highest" in q_lower and not order_clause and not where_clause:
                limit_num = 5

        # Format dialect limit
        if dialect == "oracle":
            fetch_clause = f" FETCH FIRST {limit_num} ROWS ONLY" if limit_num else ""
            return f"SELECT {proj_cols} FROM {table}{where_clause}{order_clause}{fetch_clause};"
        elif dialect == "mssql":
            top_clause = f"TOP {limit_num} " if limit_num else ""
            return f"SELECT {top_clause}{proj_cols} FROM {table}{where_clause}{order_clause};"
        else:
            limit_clause = f" LIMIT {limit_num}" if limit_num else ""
            return f"SELECT {proj_cols} FROM {table}{where_clause}{order_clause}{limit_clause};"

    def _correct_query(self, user_prompt: str) -> str:
        """Analyze database execution error and return corrected SQL."""
        prev_query_match = re.search(r"Query:\s*(SELECT.*?)(?:\n|$)", user_prompt, re.IGNORECASE | re.DOTALL)
        prev_sql = prev_query_match.group(1).strip().rstrip(";") if prev_query_match else "SELECT * FROM records"

        schema_tables = self._parse_schema_from_prompt(user_prompt)
        error_match = re.search(r"Error:\s*(.*?)(?:\n|$)", user_prompt, re.IGNORECASE)
        error_text = error_match.group(1).lower() if error_match else ""

        # Case 1: Unknown column error (e.g. no such column: name -> full_name)
        col_err_match = re.search(r"no such column:\s*([a-zA-Z0-9_.]+)", error_text)
        if col_err_match:
            bad_col = col_err_match.group(1).split(".")[-1]
            # Find closest valid column in schema
            for t_name, t_meta in schema_tables.items():
                for real_col in t_meta.get("columns", {}).keys():
                    if bad_col in real_col or real_col in bad_col:
                        return re.sub(rf"\b{bad_col}\b", real_col, prev_sql) + ";"

        # Case 2: Unknown table error
        tbl_err_match = re.search(r"no such table:\s*([a-zA-Z0-9_]+)", error_text)
        if tbl_err_match and schema_tables:
            real_table = list(schema_tables.keys())[0]
            return re.sub(r"FROM\s+[a-zA-Z0-9_]+", f"FROM {real_table}", prev_sql, flags=re.IGNORECASE) + ";"

        return prev_sql + ";"

    def _explain_results(self, user_prompt: str) -> str:
        """Grounded explanation of actual database records."""
        # Extract row count and sample rows
        count_match = re.search(r"Total Rows Returned:\s*(\d+)", user_prompt)
        count = int(count_match.group(1)) if count_match else 0

        time_match = re.search(r"Execution Time:\s*([0-9.]+)\s*ms", user_prompt)
        time_ms = time_match.group(1) if time_match else "0"

        q_match = re.search(r"User Question:\s*(.*?)(?:\n|$)", user_prompt)
        q_text = q_match.group(1) if q_match else ""

        if count == 0:
            return json.dumps({
                "explanation": f"No records were found matching your criteria for: '{q_text}'. The database query completed cleanly in {time_ms}ms with 0 matching rows.",
                "visualization": {"type": "table"}
            })

        # Extract sample returned data
        data_match = re.search(r"Sample Returned Data:\s*(\[.*?\])", user_prompt, re.DOTALL)
        sample_rows = []
        if data_match:
            try:
                sample_rows = json.loads(data_match.group(1))
            except Exception:
                pass

        if count == 1 and sample_rows:
            first_row = sample_rows[0]
            details = ", ".join([f"{k}: {v}" for k, v in first_row.items() if v is not None][:4])
            return json.dumps({
                "explanation": f"One record matched your query in {time_ms}ms ({details}).",
                "visualization": {"type": "table"}
            })

        # If aggregate result (e.g. average, total, count)
        if count == 1 and sample_rows and len(sample_rows[0]) == 1:
            key, val = list(sample_rows[0].items())[0]
            formatted_val = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}" if isinstance(val, int) else str(val)
            return json.dumps({
                "explanation": f"The calculated {key.replace('_', ' ')} is {formatted_val}.",
                "visualization": {"type": "metric", "y_axis": key, "title": key.replace("_", " ").title()}
            })

        summary = f"Retrieved {count} records in {time_ms}ms matching your query '{q_text}'."
        return json.dumps({
            "explanation": summary,
            "visualization": {"type": "table"}
        })

def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> BaseLLMProvider:
    provider = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

    if provider == "gemini":
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            return IntelligentMockProvider()
        return GeminiProvider(api_key=key, model_name=model_name or "gemini-1.5-flash")

    elif provider == "openai":
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            return IntelligentMockProvider()
        return OpenAIProvider(api_key=key, model_name=model_name or settings.AI_MODEL_NAME)

    elif provider == "anthropic":
        key = api_key or settings.ANTHROPIC_API_KEY
        if not key:
            return IntelligentMockProvider()
        return AnthropicProvider(api_key=key, model_name=model_name or "claude-3-haiku-20240307")

    elif provider == "ollama":
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model_name=model_name or "llama3")

    return IntelligentMockProvider()
