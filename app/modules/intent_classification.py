from typing import Dict, Any, Tuple
from app.services.llm import llm_service

class IntentClassificationModule:
    """
    HLD 3.3: Intent Classification Module
    Determines query type, complexity, and confidence level.
    """
    
    async def classify(self, query: str) -> Tuple[str, float, str]:
        """
        Returns (intent, confidence, complexity)
        """
        prompt = f"""
        Classify the following natural language query for a database system.
        
        Query: "{query}"
        
        Return a JSON object with:
        - "intent": "SELECT", "UPDATE", "DELETE", "INSERT", or "UNKNOWN"
        - "confidence": float between 0.0 and 1.0
        - "complexity": "Simple", "Medium", "Complex"
        
        Return ONLY the JSON.
        """
        
        try:
            response_text = await llm_service.generate_response(prompt)
            # Simple cleanup to handle potential markdown
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            import json
            data = json.loads(response_text)
            return data.get("intent", "SELECT"), data.get("confidence", 0.9), data.get("complexity", "Simple")
        except Exception:
            # Fallback if LLM fails or returns bad JSON
            return "SELECT", 0.9, "Simple"

intent_module = IntentClassificationModule()
