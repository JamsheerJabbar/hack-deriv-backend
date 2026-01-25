from typing import Dict, Any, List
import json
import asyncio
from app.services.llm import llm_service
from app.services.vector_store import VectorStoreFactory
from app.modules.preprocessing.assets.prompts import ENTITY_EXTRACTION_PROMPT

class EntityExtractor:
    """
    Handles extraction and normalization of entities (dates, names, categories).
    Uses Domain Context to resolve values to actual database entries.
    """
    def __init__(self):
        pass

    async def extract(self, query: str, domain: str = "general") -> Dict[str, Any]:
        """
        Extracts entities and resolves them against database values using LLM reasoning 
        informed by the domain schema context.
        """
        from app.modules.domain_adapter import domain_adapter
        from app.services.llm import llm_service
        
        # 1. Get learned domain knowledge (contains sample values and entity info)
        config = domain_adapter.get_domain_config(domain)
        schema_context = config.get("schema_context", "")
        
        # 2. Build a prompt that asks the LLM to extract AND resolve
        prompt = f"""
You are a Precise Entity Extractor and Resolver.
Your goal is to extract filters from the user query and map them to ACTUAL database values.

Database Data Insights:
{schema_context}

User Query: "{query}"

Task:
1. Extract filtering entities (Names, Categories, Statuses, Dates, Numbers).
2. RESOLVE them to the exact values found in the "Database Data Insights".
   - If user says "verified", and the data shows 'VERIFIED', resolve it to 'VERIFIED'.
   - If user says "Germany", and data shows 'DE', resolve it to 'DE'.
   - If user says "failed", and data shows 'FAILED', resolve it to 'FAILED'.
3. Output the result in JSON format.

Output JSON Format:
{{
  "resolved_entities": {{
    "column_name_1": "actual_db_value",
    "column_name_2": "actual_db_value"
  }},
  "metadata": {{
    "dates": [],
    "numbers": []
  }}
}}

Example:
Query: "Users from Germany with verified status"
Output:
{{
  "resolved_entities": {{
    "country": "DE",
    "kyc_status": "VERIFIED"
  }},
  "metadata": {{ ... }}
}}

IMPORTANT: Only resolve if you are high confidence based on the "Database Data Insights". If not found, put in raw 'names' or 'categories' list.

Return ONLY the JSON.
"""
        try:
            response = await llm_service.generate_response(prompt)
            # Cleanup
            response = response.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(response)
            
            # Log for transparency (using the logger if possible, but keeping it simple)
            from app.core.logger import logger
            logger.info(f"Entities Extracted/Resolved: {data.get('resolved_entities')}")
            
            return data
            
        except Exception as e:
            from app.core.logger import logger
            logger.error(f"Entity Extraction Error: {e}")
            return {"resolved_entities": {}, "metadata": {}}
