from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.query_history import QueryHistory

def get_conversation_history(
    db: Session,
    conversation_id: str,
    organization_id: str,
    limit: int = 5,
) -> List[Dict[str, str]]:
    """
    Retrieve the last N turns of query history in this conversation thread.
    Returns a list of dicts with role and message content.
    """
    if not conversation_id:
        return []

    history = (
        db.query(QueryHistory)
        .filter(
            QueryHistory.conversation_id == conversation_id,
            QueryHistory.organization_id == organization_id,
            QueryHistory.status.in_(["success", "corrected"]),
        )
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    # Reverse so they are chronological
    history = list(reversed(history))

    turns = []
    for item in history:
        turns.append({"role": "user", "content": item.question})
        turns.append({
            "role": "assistant",
            "content": f"Executed SQL: {item.executed_sql}\nResult Summary: Retrieved {item.row_count} rows."
        })

    return turns

def format_conversation_context(turns: List[Dict[str, str]]) -> str:
    """Format conversation history turns into prompt text."""
    if not turns:
        return ""

    lines = ["### Conversation History Context:"]
    for turn in turns:
        prefix = "User:" if turn["role"] == "user" else "Assistant:"
        lines.append(f"{prefix} {turn['content']}")
    return "\n".join(lines) + "\n\n"
