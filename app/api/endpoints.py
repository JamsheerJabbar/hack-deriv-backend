from fastapi import APIRouter, HTTPException
from app.models.state import QueryRequest, QueryResponse, AlertRequest, AlertResponse
from app.orchestration.workflow import app_graph

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Process a natural language query through the NL2SQL pipeline.
    Supports conversational clarification flow.
    """
    initial_state = {
        "user_question": request.query,
        "domain": request.domain,
        "conversation_history": request.conversation_history,
        "retry_count": 0
    }
    
    # Run the graph
    result = await app_graph.ainvoke(initial_state)
    
    # Check if clarification is needed
    if result.get("status") == "needs_clarification":
        return QueryResponse(
            sql=None,
            results=None,
            status="needs_clarification",
            clarification_question=result.get("clarification_question"),
            is_final=False
        )
    
    # Check for validation errors
    if result.get("validation_error") and not result.get("query_result"):
        return QueryResponse(
            sql=result.get("generated_sql"),
            results=None,
            status="failed",
            error=result["validation_error"],
            is_final=True
        )
    
    # Success - SQL generated and executed
    return QueryResponse(
        sql=result.get("generated_sql"),
        results=result.get("query_result"),
        visualization_config=result.get("visualization_config"),
        status="success",
        is_final=True
    )

@router.post("/alert", response_model=AlertResponse)
async def create_alert(request: AlertRequest):
    """
    Process a request to create a data alert based on a previous query.
    """
    from app.modules.alert_generation import alert_module
    
    status, message, sql, config = await alert_module.process_alert_request(
        request.base_sql,
        request.user_message,
        request.conversation_history
    )
    
    return AlertResponse(
        status=status,
        response_message=message,
        alert_sql=sql,
        alert_config=config,
        clarification_question=message if status == "needs_clarification" else None
    )
