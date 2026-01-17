from typing import List, Dict, Any, Optional, Union, TypedDict
from pydantic import BaseModel, Field

# HLD Section 4.2: Graph State Definition
class GraphState(TypedDict):
    user_question: str
    conversation_history: List[Dict[str, str]]
    intent: Optional[str]
    confidence: float
    relevant_columns: List[str]
    few_shot_examples: List[Dict[str, Any]]
    generated_sql: Optional[str]
    validation_error: Optional[str]
    retry_count: int
    query_result: Optional[List[Dict[str, Any]]]
    status: str  # success | failed | needs_clarification

# API Models
class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    sql: Optional[str]
    results: Optional[List[Dict[str, Any]]]
    status: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
