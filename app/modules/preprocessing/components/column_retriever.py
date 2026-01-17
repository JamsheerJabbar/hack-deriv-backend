from typing import List
from app.services.vector_store import VectorStoreFactory

class ColumnRetriever:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_store("column_descriptions")

    async def retrieve(self, query: str, top_k: int = 10) -> List[str]:
        """
        Identifies relevant columns using semantic search.
        """
        results = await self.vector_store.search(query, top_k=top_k)
        
        if not results:
            # Fallback mock
            return [
                "users.user_id", "users.full_name", "users.email", "users.country", "users.risk_level", "users.kyc_status",
                "transactions.txn_id", "transactions.amount_usd", "transactions.status", "transactions.txn_type",
                "login_events.ip_address", "login_events.status", "login_events.country",
                "alerts.severity", "alerts.rule_name"
            ]
            
        return [res["content"] for res in results]
