from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.models.state import GraphState
from app.modules.intent_classification import intent_module
from app.modules.preprocessing import preprocessing_service
from app.modules.sql_generation import sql_generation_module
from app.modules.validation import validation_module
from app.services.database import db_service

# Node Definitions

async def classify_intent_node(state: GraphState) -> Dict[str, Any]:
    query = state["user_question"]
    intent, confidence, complexity = await intent_module.classify(query)
    
    # Also run preprocessing here or in a separate node. 
    # HLD says parallel preprocessing happens before routing, but for simplicity in graph:
    preproc_data = await preprocessing_service.process(query)
    
    return {
        "intent": intent,
        "confidence": confidence,
        "relevant_columns": preproc_data["relevant_columns"],
        "few_shot_examples": preproc_data["few_shot_examples"]
    }

async def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    query = state["user_question"]
    context = {
        "relevant_columns": state["relevant_columns"],
        "few_shot_examples": state["few_shot_examples"]
    }
    sql = await sql_generation_module.generate(query, context)
    return {"generated_sql": sql}

async def validate_sql_node(state: GraphState) -> Dict[str, Any]:
    sql = state["generated_sql"]
    is_valid, error = validation_module.validate(sql)
    return {"validation_error": error}

async def repair_sql_node(state: GraphState) -> Dict[str, Any]:
    # Mock repair: just return a valid SQL
    return {
        "generated_sql": "SELECT * FROM users;", 
        "validation_error": None,
        "retry_count": state.get("retry_count", 0) + 1
    }

async def execute_query_node(state: GraphState) -> Dict[str, Any]:
    sql = state["generated_sql"]
    results = db_service.execute(sql)
    return {"query_result": results, "status": "success"}

async def format_response_node(state: GraphState) -> Dict[str, Any]:
    # Format results if needed
    return {}

# Conditional Edges

def route_after_intent(state: GraphState):
    if state["confidence"] < 0.6:
        return "human_clarification" # Not implemented in this demo
    return "generate_sql"

def route_after_validation(state: GraphState):
    if state["validation_error"]:
        if state.get("retry_count", 0) < 3:
            return "repair_sql"
        else:
            return "format_response" # Or failure node
    return "execute_query"

# Graph Construction

workflow = StateGraph(GraphState)

workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("validate_sql", validate_sql_node)
workflow.add_node("repair_sql", repair_sql_node)
workflow.add_node("execute_query", execute_query_node)
workflow.add_node("format_response", format_response_node)

workflow.set_entry_point("classify_intent")

workflow.add_conditional_edges(
    "classify_intent",
    route_after_intent,
    {
        "generate_sql": "generate_sql",
        "human_clarification": END # Placeholder
    }
)

workflow.add_edge("generate_sql", "validate_sql")

workflow.add_conditional_edges(
    "validate_sql",
    route_after_validation,
    {
        "execute_query": "execute_query",
        "repair_sql": "repair_sql",
        "format_response": "format_response"
    }
)

workflow.add_edge("repair_sql", "validate_sql")
workflow.add_edge("execute_query", "format_response")
workflow.add_edge("format_response", END)

app_graph = workflow.compile()
