import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from app.alert_system.metric_workflow import metric_app_graph

async def test_metric_conversation():
    print("Testing Conversational Metric Logic...")
    
    # 1. Test case: Missing info (should trigger clarification)
    print("\n--- TEST: MISSING INFO ---")
    state1 = {
        "user_query": "Alert me on failed transactions",
        "domain": "risk",
        "conversation_history": [],
        "metric": {},
        "status": "pending",
        "explanation": ""
    }
    res1 = await metric_app_graph.ainvoke(state1)
    print(f"Status: {res1['status']}")
    print(f"Clarification Needed: {res1.get('needs_clarification')}")
    print(f"Question: {res1.get('clarification_question')}")

    # 2. Test case: Full info (should succeed)
    print("\n--- TEST: FULL INFO ---")
    state2 = {
        "user_query": "Alert me if failed transactions > 5 in 1 minute",
        "domain": "risk",
        "conversation_history": [],
        "metric": {},
        "status": "pending",
        "explanation": ""
    }
    res2 = await metric_app_graph.ainvoke(state2)
    print(f"Status: {res2['status']}")
    print("Metric:")
    print(json.dumps(res2.get("metric"), indent=2))

    # 3. Test case: Conversation history (referencing previous)
    print("\n--- TEST: CONVERSATION CONTEXT ---")
    state3 = {
        "user_query": "Actually, change the threshold to 10",
        "domain": "risk",
        "conversation_history": [
            {"role": "user", "content": "Alert me if failed transactions > 5 in 1 minute"},
            {"role": "assistant", "content": "Metric created with threshold 5."}
        ],
        "metric": {},
        "status": "pending",
        "explanation": ""
    }
    res3 = await metric_app_graph.ainvoke(state3)
    print(f"Status: {res3['status']}")
    print("Metric (After Update):")
    print(json.dumps(res3.get("metric"), indent=2))

if __name__ == "__main__":
    asyncio.run(test_metric_conversation())
