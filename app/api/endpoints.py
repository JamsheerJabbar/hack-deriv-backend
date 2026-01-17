from fastapi import APIRouter, HTTPException
from app.models.state import QueryRequest, QueryResponse
from app.orchestration.workflow import app_graph

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Process a natural language query through the NL2SQL pipeline.
    """
    initial_state = {
        "user_question": request.query,
        "conversation_history": [],
        "retry_count": 0
    }
    
    # Run the graph
    result = await app_graph.ainvoke(initial_state)
    
    if result.get("validation_error") and not result.get("query_result"):
        return QueryResponse(
            sql=result.get("generated_sql"),
            results=None,
            status="failed",
            error=result["validation_error"]
        )
        
    return QueryResponse(
        sql=result.get("generated_sql"),
        results=result.get("query_result"),
        status="success"
    )
