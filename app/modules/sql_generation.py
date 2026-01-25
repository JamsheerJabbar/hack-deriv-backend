from typing import List, Dict, Any
from app.services.llm import llm_service
from app.modules.schema_understanding import schema_module
from app.core.logger import logger
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
        from app.modules.domain_adapter import domain_adapter
        
        # Get domain from context
        domain = context.get("domain", "general")
        logger.info(f"Generating SQL for domain: {domain} | Query: {query}")
        
        # 1. Get Schema Context from Domain Adapter (via Schema Module)
        schema_str = schema_module.get_schema_string(domain=domain)
        
        # 2. Get Domain Prompt (SQL Specific) from Domain Adapter
        domain_config = domain_adapter.get_domain_config(domain)
        custom_sql_prompt = domain_config.get("prompts", {}).get("sql")
        
        if custom_sql_prompt:
            logger.info(f"Using custom SQL prompt for domain: {domain}")
            
        domain_prompt = custom_sql_prompt or f"You are an expert SQL assistant for the {domain} domain."
        
        # Format few-shot examples
        examples = context.get("few_shot_examples", [])
        few_shot_str = format_few_shots_for_prompt(examples) if examples else ""
        
        # 3. Get Resolved Entities from context
        entities = context.get("entities", {})
        resolved_vals = entities.get("resolved_entities", {})
        entity_str = ""
        if resolved_vals:
            entity_str = "Resolved Entity Mappings (Use these EXACT values in your filters):\n"
            for col, val in resolved_vals.items():
                entity_str += f"- {col}: {val}\n"

        prompt = f"""
{domain_prompt}

Database Schema & Entities:
{schema_str}

{entity_str}

{f"Example Queries for {domain.upper()} domain:" if few_shot_str else ""}
{few_shot_str}

Guidelines:
1. Use SQLite syntax ONLY.
2. Return ONLY the SQL query. Do not include markdown formatting (```sql ... ```) or explanations.
3. Current date is available via datetime('now').
4. Respect the schema relations described above. Favor querying the actual business tables (e.g., users, transactions, alerts) instead of system metadata (like sqlite_master).
5. If the user asks for "column names" or "schema", provide a query that selects a few rows from that table instead, or return an Error guidance explaining the table structure.
6. If the query CANNOT be answered with the given schema (e.g. asking for "Weather", "Stock Prices" not in DB), return "Error: <Explanation>. Try asking about: <List relevant tables/columns>".

User Request: {query}

SQL Query:
"""
        
        response = await llm_service.generate_response(prompt)
        
        # If the LLM explicitly returns an Error/Guidance message, return it as is.
        if response.startswith("Error"):
            logger.warning(f"SQL Generation guidance response for query: {query} | Msg: {response[:50]}...")
            return response

        # Clean up response
        cleaned_sql = response.replace("```sql", "").replace("```", "").strip()
        
        # Double check if cleaned result is an Error
        if cleaned_sql.startswith("Error"):
            logger.warning(f"SQL Generation guidance response (cleaned) for query: {query}")
            return cleaned_sql
            
        logger.info(f"SQL Generated and cleaned: {cleaned_sql[:50]}...")
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
