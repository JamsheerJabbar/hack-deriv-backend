import json
import os
from typing import Dict, List, Any, Optional

class DomainAdapterModule:
    """
    Independent module to manage domain-specific configurations (Prompts, Schema, Few-Shots).
    Allows 'teaching' the system new domains without code changes.
    """
    
    def __init__(self, storage_path: str = "app/data/domains"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
    def _get_file_path(self, domain: str) -> str:
        return os.path.join(self.storage_path, f"{domain.lower()}.json")

    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Load configuration for a specific domain."""
        file_path = self._get_file_path(domain)
        if not os.path.exists(file_path):
            return self._get_default_config(domain)
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading domain config for {domain}: {e}")
            return self._get_default_config(domain)

    def update_domain_config(self, domain: str, 
                           description: str = None,
                           schema_context: str = None,
                           intent_prompt: str = None,
                           sql_prompt: str = None,
                           few_shots: List[Dict] = None) -> bool:
        """
        Update specific fields of a domain configuration.
        """
        config = self.get_domain_config(domain)
        
        if description: config["description"] = description
        if schema_context: config["schema_context"] = schema_context
        if intent_prompt: config["prompts"]["intent"] = intent_prompt
        if sql_prompt: config["prompts"]["sql"] = sql_prompt
        if few_shots is not None: config["few_shots"] = few_shots
        
        return self._save_config(domain, config)

    def add_few_shot_example(self, domain: str, question: str, sql: str, explanation: str = ""):
        """Add a new training example to the domain."""
        config = self.get_domain_config(domain)
        
        new_example = {
            "question": question,
            "sql": sql,
            "explanation": explanation
        }
        
        # Avoid duplicates
        if new_example not in config["few_shots"]:
            config["few_shots"].append(new_example)
            self._save_config(domain, config)

    async def refine_domain(self, domain: str, sample_queries: List[str], existing_sql_pairs: Dict[str, str] = None):
        """
        AI-Powered refinement: Analyzes sample queries to improve domain configuration.
        - Updates Schema Context (understanding of tables/columns).
        - Suggests and adds Few-Shot examples.
        - Tunes the System Prompts.
        """
        from app.services.llm import llm_service
        
        config = self.get_domain_config(domain)
        current_context = config.get("schema_context", "")
        
        # 1. Analyze Schema & Intent
        # We ask the LLM to look at the queries and the current schema context, and improve the context.
        queries_str = "\n".join([f"- {q}" for q in sample_queries])
        
        analysis_prompt = f"""
You are a Domain Knowledge Optimizer for an NL2SQL system.
Domain: {domain}

Current Schema Context:
"{current_context}"

Sample User Queries:
{queries_str}

Task:
1. Analyze the queries to understand the specific terminology and potential ambiguity in this domain.
2. Rewrite the "Schema Context" to be more helpful. Explicitly map user terms to potential DB concepts.
3. If you see patterns, suggest 2 new logical Few-Shot examples (Question + generic logical SQL).

Return JSON:
{{
  "improved_schema_context": "The improved string...",
  "suggested_few_shots": [
      {{"question": "...", "sql": "SELECT ...", "explanation": "..."}}
  ],
  "intent_prompt_suggestion": "Optional suggestion for system prompt... or null"
}}
"""
        try:
            response = await llm_service.generate_response(analysis_prompt)
            data = json.loads(response.replace("```json", "").replace("```", "").strip())
            
            # Application Logic
            if data.get("improved_schema_context"):
                print(f"Refining Schema Context for {domain}...")
                config["schema_context"] = data["improved_schema_context"]
                
            if data.get("suggested_few_shots"):
                print(f"Adding {len(data['suggested_few_shots'])} few-shot suggestions...")
                for fs in data["suggested_few_shots"]:
                    # check for duplicates
                    if fs not in config["few_shots"]:
                        config["few_shots"].append(fs)
                        
            # Save the refined config
            self._save_config(domain, config)
            return True, "Domain refined successfully!"
            
        except Exception as e:
            print(f"Refinement failed: {e}")
            return False, str(e)

    async def discover_and_learn(self, domain: str):
        """
        Autonomous Discovery Agent:
        1. Scans database for actual data patterns (Values, Distributions).
        2. Generates synthetic 'User Questions' based on real data.
        3. Refines the domain configuration (Prompts, Schema Context, Few-Shots) using these insights.
        """
        from app.services.llm import llm_service
        from app.services.database import db_service
        
        print(f"🕵️ Starting discovery for domain: {domain}...")
        
        # Step 1: Profile the Database (Get real sample data)
        # We assume we can query the DB. We'll get generic info first.
        # This query works for SQLite. For Postgres/MySQL, it might differ slightly.
        try:
            # Get list of tables
            tables_res = db_service.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row['name'] for row in tables_res]
            
            db_profile = {}
            
            for table in tables:
                # Get columns
                cols_res = db_service.execute(f"PRAGMA table_info({table});")
                columns = [row['name'] for row in cols_res]
                
                table_data = {"columns": columns, "samples": {}}
                
                # Sample distinctive values for text columns to understand entities
                for col in columns:
                    try:
                        # Get 5 distinctive non-null values
                        sample_res = db_service.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT 5")
                        vals = [list(row.values())[0] for row in sample_res]
                        table_data["samples"][col] = vals
                    except:
                        pass
                
                db_profile[table] = table_data
                
        except Exception as e:
            print(f"Profiling failed: {e}")
            return False, f"Database profiling failed: {e}"

        print(f"📊 Profiled {len(db_profile)} tables. Generating insights...")
        
        # Step 2: LLM Analysis & Generation
        profile_str = json.dumps(db_profile, indent=2)
        
        learning_prompt = f"""
You are an expert Data Scientist and System Architect.
You are tasked with "Teaching" an NL2SQL system about a specific database domain: "{domain}".

Here is the ACTUAL DATA extracted from the database (Tables, Columns, and Sample Values):
{profile_str}

Your Task:
1. Analyze the sample values to understand the "Entities" (e.g., if you see "US", "UK", "IN" in 'country', note that).
2. Generate 5 REALISTIC user questions that someone would ask based on this data. 
   - Use the actual values found (e.g. "Show me users from 'IN'" instead of "Show me users from X").
3. Determine the best "Schema Context" description to help an AI understand these tables.
4. Suggest a specific "Intent Classification" prompt that highlights specific jargon found in this data.

Return JSON:
{{
  "refined_schema_context": "Detailed description of tables and what the columns represent based on data...",
  "synthetic_few_shots": [
      {{"question": "Generated question 1", "sql": "Logical SQL for Q1", "explanation": "Why this query?"}},
      {{"question": "Generated question 2", "sql": "Logical SQL for Q2", "explanation": "..."}}
  ],
  "intent_prompt_tuning": "Add this instruction to the system prompt: ..."
}}
"""
        try:
            response = await llm_service.generate_response(learning_prompt)
            data = json.loads(response.replace("```json", "").replace("```", "").strip())
            
            # Step 3: Apply Learning
            config = self.get_domain_config(domain)
            
            # Update Schema Context
            if data.get("refined_schema_context"):
                config["schema_context"] = data["refined_schema_context"]
                
            # Add Synthetic Few-Shots
            if data.get("synthetic_few_shots"):
                current_qs = [fs["question"] for fs in config["few_shots"]]
                for fs in data["synthetic_few_shots"]:
                    if fs["question"] not in current_qs:
                        config["few_shots"].append(fs)
            
            # Update Intent Prompt (Append suggestion)
            suggestion = data.get("intent_prompt_tuning")
            if suggestion:
                # We append the specific instruction to the default if custom is empty, or append to custom
                base_prompt = config["prompts"].get("intent") or "You are an AI assistant..."
                if suggestion not in base_prompt:
                    config["prompts"]["intent"] = base_prompt + "\n\nDOMAIN SPECIFIC INSTRUCTION:\n" + suggestion
            
            self._save_config(domain, config)
            return True, f"Discovery complete! Added {len(data.get('synthetic_few_shots', []))} examples and refined schema context."
            
        except Exception as e:
            print(f"Learning failed: {e}")
            return False, str(e)

    def _save_config(self, domain: str, config: Dict) -> bool:
        try:
            with open(self._get_file_path(domain), 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save domain config: {e}")
            return False

    def _get_default_config(self, domain: str) -> Dict[str, Any]:
        """Return a default structure for new domains."""
        return {
            "domain": domain,
            "description": f"Configuration for {domain} domain",
            "schema_context": "Standard database tables.",
            "prompts": {
                "intent": None, # Use system default if None
                "sql": None     # Use system default if None
            },
            "few_shots": []
        }

domain_adapter = DomainAdapterModule()
