import json
import re
from typing import List, Dict, Any, Set
import numpy as np

def create_table_document(table_meta: Dict[str, Any]) -> str:
    """Create a searchable text representation of a table and its fields."""
    table_name = table_meta["table_name"]
    desc = table_meta.get("business_description") or ""
    cols = json.loads(table_meta["columns_json"]) if isinstance(table_meta["columns_json"], str) else table_meta["columns_json"]
    col_names = " ".join([c["name"] for c in cols])
    return f"table {table_name} {desc} columns: {col_names}"

def simple_token_embedding(text: str, vocab_size: int = 128) -> np.ndarray:
    """
    Lightweight deterministic token embedding for fast local vector retrieval
    without needing heavy external embedding API calls or models.
    """
    vec = np.zeros(vocab_size, dtype=np.float32)
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        idx = hash(token) % vocab_size
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    return float(np.dot(v1, v2))

def retrieve_relevant_tables(
    tables: List[Dict[str, Any]],
    query: str,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    RAG-based schema retrieval:
    If database schema is small (<= 15 tables), return all tables.
    If database schema is large, find the most relevant tables and their foreign-key neighbors.
    """
    if len(tables) <= 15:
        return tables

    query_vec = simple_token_embedding(query)
    scores = []

    for t in tables:
        doc = create_table_document(t)
        doc_vec = simple_token_embedding(doc)
        sim = cosine_similarity(query_vec, doc_vec)
        scores.append((sim, t))

    # Sort descending by similarity
    scores.sort(key=lambda x: x[0], reverse=True)
    selected = [t for sim, t in scores[:top_k]]
    selected_names = {t["table_name"].lower() for t in selected}

    # Expand to include FK-related tables to ensure joins work
    table_map = {t["table_name"].lower(): t for t in tables}
    additional_tables: Set[str] = set()

    for t in selected:
        fks = json.loads(t.get("foreign_keys_json") or "[]")
        for fk in fks:
            ref = fk.get("referred_table")
            if ref and ref.lower() in table_map and ref.lower() not in selected_names:
                additional_tables.add(ref.lower())

    for ref_name in list(additional_tables)[:3]:
        selected.append(table_map[ref_name])

    return selected
