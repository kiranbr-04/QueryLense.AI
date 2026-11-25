import json
import logging
from typing import List, Dict, Any, Optional
from app.ai.provider_factory import get_llm_provider
from app.ai.prompt_templates import RESULT_EXPLANATION_SYSTEM_PROMPT

logger = logging.getLogger("querylens.explainer")

def _auto_detect_visualization(columns: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback heuristic to suggest the best visualization given column types and row count."""
    if not rows or not columns:
        return {"type": "table"}

    if len(rows) == 1 and len(columns) == 1:
        col = columns[0]["name"]
        return {"type": "metric", "y_axis": col, "title": col.replace("_", " ").title()}

    num_cols = [c["name"] for c in columns if c["type"] == "number"]
    str_cols = [c["name"] for c in columns if c["type"] == "string"]
    date_cols = [c["name"] for c in columns if c["type"] == "datetime"]

    # If date column and number column -> line chart
    if date_cols and num_cols:
        return {
            "type": "line",
            "x_axis": date_cols[0],
            "y_axis": num_cols[0],
            "title": f"{num_cols[0].replace('_', ' ').title()} over Time",
        }

    # If categorical string and number column and <= 15 rows -> bar or pie chart
    if str_cols and num_cols:
        if len(rows) <= 6:
            return {
                "type": "pie",
                "x_axis": str_cols[0],
                "y_axis": num_cols[0],
                "title": f"Distribution by {str_cols[0].replace('_', ' ').title()}",
            }
        return {
            "type": "bar",
            "x_axis": str_cols[0],
            "y_axis": num_cols[0],
            "title": f"{num_cols[0].replace('_', ' ').title()} by {str_cols[0].replace('_', ' ').title()}",
        }

    return {"type": "table"}

async def explain_query_results(
    question: str,
    executed_sql: str,
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    row_count: int,
    execution_time_ms: float,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an AI business intelligence explanation grounded strictly in the returned records.
    Also returns suggested chart configuration for the frontend visualizer.
    """
    if row_count == 0:
        return {
            "explanation": f"The query '{executed_sql}' was executed successfully against the database in {execution_time_ms:.1f}ms, but returned 0 records matching the given criteria.",
            "visualization": {"type": "table"},
        }

    # Prepare sample rows for prompt (limit to first 10 rows to keep tokens minimal and fast)
    sample_rows = rows[:10]
    user_prompt = f"""User Question: {question}
Executed SQL: {executed_sql}
Execution Time: {execution_time_ms:.1f} ms
Total Rows Returned: {row_count}
Columns: {json.dumps(columns)}
Sample Returned Data:
{json.dumps(sample_rows, default=str)}"""

    llm = get_llm_provider(provider_name=provider_name, api_key=api_key, model_name=model_name)
    try:
        raw_output = await llm.generate_text(RESULT_EXPLANATION_SYSTEM_PROMPT, user_prompt, temperature=0.1)
        # Try parsing JSON output
        cleaned = raw_output.strip()
        if "{" in cleaned and "}" in cleaned:
            json_str = cleaned[cleaned.find("{"):cleaned.rfind("}") + 1]
            data = json.loads(json_str)
            explanation = data.get("explanation")
            viz = data.get("visualization") or _auto_detect_visualization(columns, rows)
            return {
                "explanation": explanation or "Query executed successfully.",
                "visualization": viz,
            }
    except Exception as e:
        logger.warning(f"AI explanation JSON parse failed or provider error: {e}")

    # Fallback grounded explanation
    auto_viz = _auto_detect_visualization(columns, rows)
    first_row_keys = list(rows[0].keys()) if rows else []
    summary = (
        f"Query executed successfully in {execution_time_ms:.1f}ms and returned {row_count} record(s). "
        f"Fields retrieved include {', '.join(first_row_keys[:5])}. "
        f"The data is organized and displayed in the table below."
    )
    return {
        "explanation": summary,
        "visualization": auto_viz,
    }
