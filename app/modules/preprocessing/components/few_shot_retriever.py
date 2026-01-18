from typing import List, Dict, Any
from app.services.vector_store import VectorStoreFactory
from app.modules.preprocessing.assets.domain_config import get_domain_few_shots

class FewShotRetriever:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_store("few_shot_examples")

    async def retrieve(self, query: str, domain: str = "general", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves similar past query-SQL pairs, filtered by domain.
        """
        # Try vector store first
        results = await self.vector_store.search(query, top_k=top_k)
        
        if results:
            return [res["metadata"] for res in results]
        
        # Fallback to domain-specific static examples
        return get_domain_few_shots(domain)
