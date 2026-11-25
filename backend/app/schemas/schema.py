from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

class ForeignKeyInfo(BaseModel):
    constrained_columns: List[str]
    referred_schema: Optional[str] = None
    referred_table: str
    referred_columns: List[str]

class IndexInfo(BaseModel):
    name: Optional[str] = None
    column_names: List[str]
    unique: bool = False

class TableSchemaResponse(BaseModel):
    id: str
    connection_id: str
    schema_name: str
    table_name: str
    table_type: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    business_description: Optional[str] = None
    row_count_estimate: Optional[int] = None
    updated_at: datetime

class TableDescriptionUpdate(BaseModel):
    business_description: str
