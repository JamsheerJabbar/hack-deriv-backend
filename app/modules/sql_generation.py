from typing import List, Dict, Any
from app.services.llm import llm_service
from app.modules.schema_understanding import schema_module

class SQLGenerationModule:
    """
    HLD 3.4: SQL Generation Module
    Leverages LLMs with schema-aware prompting to produce SQL.
    """
    
    async def generate(self, query: str, context: Dict[str, Any]) -> str:
        """
        Generates SQL based on query and context (schema, few-shot, etc.)
        """
        # Load the full schema for context
        try:
            from app.core.config import settings
            with open(settings.SCHEMA_PATH, 'r') as f:
                schema_str = f.read()
        except Exception:
            # Fallback if file read fails
            schema_str = schema_module.get_schema_string(context.get("relevant_columns", []))

        examples = context.get("few_shot_examples", [])
        
        prompt = f"""
        You are a SQL expert for the DerivInsight platform. 
        Generate a valid SQLite SQL query for the following natural language request.
        
        Database Schema:
        {schema_str}
        
        Guidelines:
        1. Use SQLite syntax.
        2. Return ONLY the SQL query. Do not include markdown formatting (```sql ... ```) or explanations.
        3. Current date is available via datetime('now').
        4. Use the provided Views (v_high_risk_users, v_flagged_transactions, etc.) when appropriate as they simplify complex logic.
        
        Request: {query}
        
        SQL Query:
        """
        
        response = await llm_service.generate_response(prompt)
        
        # Clean up response
        cleaned_sql = response.replace("```sql", "").replace("```", "").strip()
        return cleaned_sql

sql_generation_module = SQLGenerationModule()
