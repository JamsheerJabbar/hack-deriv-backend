import asyncio
from app.orchestration.workflow import app_graph
from app.core.config import settings

async def test_query():
    print(f"Testing query with DB: {settings.DATABASE_URL}")
    query = "Show me the top 5 transactions by amount"
    
    initial_state = {
        "user_question": query,
        "conversation_history": [],
        "retry_count": 0
    }
    
    try:
        result = await app_graph.ainvoke(initial_state)
        print("\nGenerated SQL:", result.get("generated_sql"))
        print("Validation Error:", result.get("validation_error"))
        if result.get("query_result"):
            print(f"Rows returned: {len(result['query_result'])}")
            print("Sample row:", result["query_result"][0] if result["query_result"] else "None")
        else:
            print("No results returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())
