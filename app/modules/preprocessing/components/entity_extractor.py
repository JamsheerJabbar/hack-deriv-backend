from typing import Dict, Any, List
import json
import asyncio
from app.services.llm import llm_service
from app.services.vector_store import VectorStoreFactory
from app.modules.preprocessing.assets.prompts import ENTITY_EXTRACTION_PROMPT

class EntityExtractor:
    def __init__(self):
        # Index containing unique values from the database (e.g. product names, cities, status codes)
        self.value_store = VectorStoreFactory.get_store("database_unique_values")

    async def extract(self, query: str) -> Dict[str, Any]:
        """
        Extracts entities and resolves them against database values using semantic search.
        """
        # 1. Extract raw entities using LLM/Heuristics
        raw_entities = await self._extract_raw_entities(query)
        
        # 2. Resolve entities against DB values in parallel
        resolved_entities = await self._resolve_entities(raw_entities)
        
        return resolved_entities

    async def _extract_raw_entities(self, query: str) -> Dict[str, List[str]]:
        prompt = ENTITY_EXTRACTION_PROMPT.format(query=query)
        
        # In a real scenario, we would parse the JSON response from LLM
        # response = await llm_service.generate_response(prompt)
        # return json.loads(response)
        
        # Mock logic for demonstration
        entities = {"dates": [], "numbers": [], "names": [], "categories": []}
        
        # Simple heuristic mocks
        if "2023" in query:
            entities["dates"].append("2023")
        
        words = query.split()
        for word in words:
            clean_word = word.strip(".,?!")
            if clean_word.lower() in ["pending", "shipped", "delivered", "active", "inactive"]:
                entities["categories"].append(clean_word)
            elif clean_word[0].isupper() and clean_word.isalpha() and clean_word.lower() not in ["show", "list", "select", "from", "where"]:
                 # Naive proper noun detector
                 entities["names"].append(clean_word)
                 
        return entities

    async def _resolve_entities(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Matches extracted string entities with actual database values using semantic search.
        """
        resolved = entities.copy()
        
        tasks = []
        
        # Prepare tasks for names
        for i, name in enumerate(entities.get("names", [])):
            tasks.append(self._match_value(name, "names", i))
            
        # Prepare tasks for categories
        for i, category in enumerate(entities.get("categories", [])):
            tasks.append(self._match_value(category, "categories", i))
            
        # Run all semantic searches in parallel
        if tasks:
            results = await asyncio.gather(*tasks)
            
            # Apply results
            for original_value, matched_value, score, category_key, index in results:
                if score > 0.85: # High confidence threshold
                    resolved[category_key][index] = {
                        "original": original_value,
                        "matched": matched_value,
                        "confidence": score,
                        "source": "vector_db"
                    }
                else:
                     resolved[category_key][index] = {
                        "original": original_value,
                        "matched": None,
                        "confidence": score,
                        "source": "raw"
                    }
        
        return resolved

    async def _match_value(self, value: str, category_key: str, index: int):
        """
        Helper to search vector store for a single value.
        """
        # Search in the unique values index
        results = await self.value_store.search(value, top_k=1)
        
        if results:
            best_match = results[0]
            # Mocking score if not present
            score = best_match.get("score", 0.95) 
            return value, best_match.get("content"), score, category_key, index
        
        return value, None, 0.0, category_key, index
