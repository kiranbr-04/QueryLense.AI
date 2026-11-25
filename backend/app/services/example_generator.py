import json
from typing import List, Dict, Any

def generate_dynamic_examples_from_schema(tables: List[Dict[str, Any]]) -> List[str]:
    """
    Generate realistic, schema-driven natural language query suggestions
    based on the actual tables, columns, and data types in the connected database.
    """
    if not tables:
        return [
            "Show all records from the database",
            "Count total entries in each table",
        ]

    examples = []
    
    # Analyze tables and their columns
    for table in tables:
        t_name = table.get("table_name", "")
        cols_raw = table.get("columns_json", "[]")
        cols = json.loads(cols_raw) if isinstance(cols_raw, str) else (cols_raw or [])
        
        col_names = [c["name"].lower() for c in cols]
        num_cols = [c["name"] for c in cols if any(t in str(c.get("type", "")).lower() for t in ["int", "float", "double", "decimal", "numeric", "real", "money"])]
        str_cols = [c["name"] for c in cols if any(t in str(c.get("type", "")).lower() for t in ["char", "text", "varchar", "string"])]
        date_cols = [c["name"] for c in cols if any(t in str(c.get("type", "")).lower() for t in ["date", "time", "timestamp"])]

        # Specific pattern 1: Employees table
        if "employee" in t_name.lower():
            if "salary" in col_names:
                examples.append("Find employees whose salary is 50000")
                examples.append("Show employees earning more than 60000")
                examples.append("Find the highest-paid employee")
                examples.append("Calculate the average salary of employees")
                examples.append("Show the top three highest-paid employees")
            if any("dept" in c or "department" in c for c in col_names):
                examples.append("Count employees by department")
                examples.append("Show all IT department employees")
            continue

        # Specific pattern 2: Products / Catalog table
        if any(p in t_name.lower() for p in ["product", "item", "catalog"]):
            price_col = next((c for c in num_cols if "price" in c.lower() or "cost" in c.lower()), None)
            stock_col = next((c for c in num_cols if "stock" in c.lower() or "qty" in c.lower() or "quantity" in c.lower()), None)
            
            if price_col:
                examples.append(f"Show {t_name} with {price_col.replace('_', ' ')} less than 100")
                examples.append(f"Find the top 5 most expensive {t_name}")
                examples.append(f"Calculate average {price_col.replace('_', ' ')} of {t_name}")
            if stock_col:
                examples.append(f"Which {t_name} have the lowest {stock_col.replace('_', ' ')}?")
            continue

        # Specific pattern 3: Orders / Sales table
        if any(o in t_name.lower() for o in ["order", "sale", "invoice", "transaction"]):
            amt_col = next((c for c in num_cols if any(a in c.lower() for a in ["amount", "total", "price", "revenue", "sum"])), None)
            date_col = next((c for c in date_cols if any(d in c.lower() for d in ["date", "time", "created"])), None)
            
            if amt_col:
                examples.append(f"Show total revenue from {t_name}")
                examples.append(f"Find {t_name} with {amt_col.replace('_', ' ')} greater than 1000")
            if date_col:
                examples.append(f"Show monthly sales for this year")
            if any("status" in c for c in col_names):
                examples.append(f"Count of {t_name} grouped by status")
            continue

        # Generic pattern for any other table
        readable_name = t_name.replace("_", " ")
        if num_cols and str_cols:
            cat_col = str_cols[0].replace("_", " ")
            metric_col = num_cols[0].replace("_", " ")
            examples.append(f"Show {readable_name} ordered by {metric_col} descending")
            examples.append(f"Calculate total {metric_col} by {cat_col}")
            examples.append(f"Show top 5 {readable_name}")
        elif str_cols:
            examples.append(f"List all unique {str_cols[0].replace('_', ' ')} in {readable_name}")
        else:
            examples.append(f"Show all records from {readable_name}")

    # Remove duplicates preserving order and cap to 6-8 relevant suggestions
    seen = set()
    deduped = []
    for ex in examples:
        if ex.lower() not in seen:
            seen.add(ex.lower())
            deduped.append(ex)
            if len(deduped) >= 8:
                break

    return deduped or [
        "Show all records from the database",
        "Show top 10 records",
    ]
