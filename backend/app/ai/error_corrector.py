import logging
from typing import List, Dict, Any, Optional, Tuple
from app.ai.provider_factory import get_llm_provider
from app.ai.prompt_templates import ERROR_CORRECTION_SYSTEM_PROMPT
from app.ai.sql_validator import validate_sql
from app.database.schema_inspector import format_schema_for_prompt

logger = logging.getLogger("querylens.error_corrector")

async def correct_failing_sql(
    failing_sql: str,
    db_error_message: str,
    all_tables: List[Dict[str, Any]],
    dialect: str,
    original_question: str,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[str, bool, Optional[str]]:
    """
    Takes a failing SQL query and the actual database error message,
    prompts the LLM for a corrected query, and validates the result.
    Returns (corrected_sql, is_valid, validation_error).
    """
    schema_text = format_schema_for_prompt(all_tables, dialect)

    user_prompt = f"""Target Dialect: {dialect}
Original User Question: {original_question}
Failing SQL Query:
{failing_sql}

Database Execution Error:
{db_error_message}

{schema_text}

Provide ONLY the corrected, executable read-only SQL query for {dialect.upper()}:"""

    llm = get_llm_provider(provider_name=provider_name, api_key=api_key, model_name=model_name)
    try:
        raw_output = await llm.generate_text(ERROR_CORRECTION_SYSTEM_PROMPT, user_prompt, temperature=0.0)
    except Exception as e:
        logger.error(f"Correction generation failed: {e}")
        return failing_sql, False, f"Correction generation failed: {str(e)}"

    allowed_table_names = [t["table_name"] for t in all_tables]
    is_valid, val_err, safe_sql = validate_sql(raw_output, allowed_tables=allowed_table_names)
    return safe_sql, is_valid, val_err
