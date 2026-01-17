from typing import List
from app.services.vector_store import VectorStoreFactory

class TableRetriever:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_store("table_descriptions")

    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """
        Identifies relevant tables using semantic search.
        """
        results = await self.vector_store.search(query, top_k=top_k)
        
        # Mocking results if vector store returns empty (since it's a mock)
        if not results:
            # Simple keyword matching fallback for demo
            all_tables = [
                "users", "transactions", "login_events", "alerts", 
                "alert_rules", "audit_logs", "dashboards", "query_history"
            ]
            # If query mentions specific keywords, prioritize those tables
            relevant = []
            q = query.lower()
            if "user" in q or "customer" in q or "kyc" in q or "risk" in q:
                relevant.append("users")
            if "transaction" in q or "deposit" in q or "withdrawal" in q or "trade" in q or "amount" in q:
                relevant.append("transactions")
            if "login" in q or "auth" in q or "ip" in q:
                relevant.append("login_events")
            if "alert" in q or "rule" in q or "flag" in q:
                relevant.extend(["alerts", "alert_rules"])
            if "audit" in q or "log" in q:
                relevant.append("audit_logs")
                
            return list(set(relevant)) or all_tables
            
        return [res["content"] for res in results]
