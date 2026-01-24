from typing import Dict, Any, Tuple
from app.services.llm import llm_service

class IntentClassificationModule:
    """
    HLD 3.3: Intent Classification Module
    Determines query type, complexity, confidence level, and if clarification is needed.
    """
    
    async def classify(self, query: str, conversation_history: list = None) -> Tuple[str, float, str, bool]:
        """
        Returns (intent, confidence, complexity, needs_clarification)
        """
        history_context = ""
        if conversation_history:
            history_context = "\n\nConversation History:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                history_context += f"- {msg.get('role', 'user')}: {msg.get('content', '')}\n"
        
        prompt = f"""
You are analyzing a natural language database query to determine if it's ready for SQL generation.

{history_context}

Current Query: "{query}"

Analyze the query and return a JSON object with:
- "intent": "SELECT", "UPDATE", "DELETE", "INSERT", or "UNKNOWN"
- "confidence": float between 0.0 and 1.0 (how confident you are about the intent)
- "complexity": "Simple", "Medium", "Complex"
- "needs_clarification": boolean - true if the query is:
  * Too vague or ambiguous
  * Missing critical information (date ranges, thresholds, specific entities)
  * Contains compliance rules that need to be broken down
  * Requires multiple steps or clarification
- "clarity_score": float between 0.0 and 1.0 (how clear and specific the query is)

Examples of queries needing clarification:
- "Show me suspicious users" → needs threshold/criteria
- "Find compliance violations" → needs specific rule type
- "Check recent activity" → needs time range (unless "recent" serves as default limit)
- "Users need to have verified KYC and no flagged transactions in last 30 days" → complex rule, may need confirmation

Examples of clear queries (DO NOT ASK FOR CLARIFICATION):
- "Show high-risk users from UAE"
- "Show me 5 users" (Implicitly means any 5 users)
- "List transactions over $50,000 with status FLAGGED"
- "Count failed login attempts in last 24 hours"
- "Show all users" (Implicitly means top N or all)

IMPORTANT: Do NOT ask for clarification for simple queries like "Show me users" or "List transactions". Assume reasonable defaults (LIMIT 5, Order by date desc) in the SQL generation phase instead. Only ask if the intent is truly ambiguous or unexecutable.

Return ONLY the JSON object.
"""
        
        try:
            response_text = await llm_service.generate_response(prompt)
            # Simple cleanup to handle potential markdown
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            import json
            data = json.loads(response_text)
            
            intent = data.get("intent", "SELECT")
            confidence = data.get("confidence", 0.9)
            complexity = data.get("complexity", "Simple")
            needs_clarification = data.get("needs_clarification", False)
            clarity_score = data.get("clarity_score", 0.9)
            
            # Override needs_clarification if clarity is too low
            if clarity_score < 0.6:
                needs_clarification = True
                
            return intent, confidence, complexity, needs_clarification
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            # Fallback if LLM fails or returns bad JSON
            return "SELECT", 0.9, "Simple", False

intent_module = IntentClassificationModule()
