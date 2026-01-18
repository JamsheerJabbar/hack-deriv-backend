from typing import List, Dict, Any
from app.services.llm import llm_service
from app.modules.schema_understanding import schema_module
from app.modules.preprocessing.assets.domain_config import (
    get_domain_prompt,
    format_few_shots_for_prompt
)

class SQLGenerationModule:
    """
    HLD 3.4: SQL Generation Module
    Leverages LLMs with schema-aware prompting to produce SQL.
    Now supports domain-specific prompts for security, compliance, risk, and operations.
    """
    
    async def generate(self, query: str, context: Dict[str, Any]) -> str:
        """
        Generates SQL based on query and context (schema, few-shot, domain, etc.)
        """
        # Get domain from context
        domain = context.get("domain", "general")
        
        # Load the full schema for context
        try:
            from app.core.config import settings
            with open(settings.SCHEMA_PATH, 'r') as f:
                schema_str = f.read()
        except Exception:
            # Fallback if file read fails
            schema_str = schema_module.get_schema_string(context.get("relevant_columns", []))

        # Get domain-specific system prompt
        domain_prompt = get_domain_prompt(domain)
        
        # Format few-shot examples
        examples = context.get("few_shot_examples", [])
        few_shot_str = format_few_shots_for_prompt(examples) if examples else ""
        
        prompt = f"""
{domain_prompt}

Database Schema:
{schema_str}

{f"Example Queries for {domain.upper()} domain:" if few_shot_str else ""}
{few_shot_str}

Guidelines:
1. Use SQLite syntax.
2. Return ONLY the SQL query. Do not include markdown formatting (```sql ... ```) or explanations.
3. Current date is available via datetime('now').
4. Use the provided Views (v_high_risk_users, v_flagged_transactions, v_open_alerts, v_daily_summary) when appropriate.

User Request: {query}

SQL Query:
"""
        
        response = await llm_service.generate_response(prompt)
        
        if response.startswith("Error"):
            return response

        # Clean up response
        cleaned_sql = response.replace("```sql", "").replace("```", "").strip()
        return cleaned_sql

    async def repair(self, query: str, invalid_sql: str, error: str) -> str:
        """
        Repairs invalid SQL based on the error message.
        """
        prompt = f"""
You are a SQL expert. The following SQLite query generated for the request "{query}" is invalid.

Invalid SQL: {invalid_sql}
Error: {error}

Please fix the SQL query to be valid SQLite syntax.
Return ONLY the corrected SQL query. No markdown, no explanations.
"""
        
        response = await llm_service.generate_response(prompt)
        
        # Clean up response
        cleaned_sql = response.replace("```sql", "").replace("```", "").strip()
        return cleaned_sql

sql_generation_module = SQLGenerationModule()
