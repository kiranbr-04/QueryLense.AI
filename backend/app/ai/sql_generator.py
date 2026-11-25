import logging
from typing import List, Dict, Any, Optional, Tuple
from app.ai.provider_factory import get_llm_provider
from app.ai.prompt_templates import TEXT_TO_SQL_SYSTEM_PROMPT
from app.ai.sql_validator import validate_sql
from app.ai.rag_schema_retriever import retrieve_relevant_tables
from app.database.schema_inspector import format_schema_for_prompt
from app.ai.conversational_memory import format_conversation_context

logger = logging.getLogger("querylens.sql_generator")

async def generate_sql_from_question(
    question: str,
    all_tables: List[Dict[str, Any]],
    dialect: str,
    conversation_turns: Optional[List[Dict[str, str]]] = None,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[str, bool, Optional[str]]:
    """
    Generate dialect-aware SQL from user question with schema context & conversational memory.
    Validates the generated SQL before returning.
    Returns (generated_sql, is_valid, validation_error).
    """
    # 1. RAG retrieval of schema
    relevant_tables = retrieve_relevant_tables(all_tables, question)
    schema_text = format_schema_for_prompt(relevant_tables, dialect)

    # 2. Conversational context
    conv_context = format_conversation_context(conversation_turns or [])

    # 3. Construct user prompt
    user_prompt = f"""Target Dialect: {dialect}
{conv_context}
{schema_text}

User Question: {question}

Generate ONLY the executable read-only SQL query for {dialect.upper()}:"""

    # 4. Invoke LLM
    llm = get_llm_provider(provider_name=provider_name, api_key=api_key, model_name=model_name)
    try:
        raw_output = await llm.generate_text(TEXT_TO_SQL_SYSTEM_PROMPT, user_prompt, temperature=0.0)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return "", False, f"AI generation error: {str(e)}"

    # 5. Extract and validate SQL
    allowed_table_names = [t["table_name"] for t in all_tables]
    is_valid, val_err, safe_sql = validate_sql(raw_output, allowed_tables=allowed_table_names)

    return safe_sql, is_valid, val_err
