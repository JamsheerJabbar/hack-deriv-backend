import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from app.orchestration.workflow import app_graph

async def test_executive_insights():
    print("Testing CIO Insights & Recommendations Logic...")
    
    # Query that likely has data
    query = "Show me all users and their risk levels"
    
    print(f"\nQUERY: {query}")
    initial_state = {
        "user_question": query,
        "domain": "security",
        "conversation_history": [],
        "retry_count": 0
    }
    
    try:
        # Run the full pipeline
        result = await app_graph.ainvoke(initial_state)
        
        output = {
            "status": result.get("status"),
            "sql": result.get("generated_sql"),
            "insight": result.get("insight"),
            "recommendation": result.get("recommendation")
        }
        
        with open("test_output.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print("\nSUCCESS: Output saved to test_output.json")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_executive_insights())
