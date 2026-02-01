import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from app.alert_system.metric_workflow import metric_app_graph

async def test_metric_logic():
    print("Testing Metric Generation Logic directly (skipping server)...")
    
    test_queries = [
        "Alert me if there are more than 3 failed transactions in 60 seconds",
        "Notify me if a user from Singapore has a blocked login",
        "I need a metric for average transaction amount over $1000 every 5 minutes"
    ]
    
    for query in test_queries:
        print(f"\nQUERY: {query}")
        initial_state = {
            "user_query": query,
            "domain": "general",
            "metric": {},
            "status": "pending",
            "explanation": ""
        }
        
        try:
            result = await metric_app_graph.ainvoke(initial_state)
            print("RESULT:")
            print(json.dumps(result.get("metric"), indent=2))
            print(f"STATUS: {result.get('status')}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_metric_logic())
