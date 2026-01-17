from typing import List, Dict, Any
from app.services.vector_store import VectorStoreFactory

class FewShotRetriever:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_store("few_shot_examples")

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves similar past query-SQL pairs.
        """
        results = await self.vector_store.search(query, top_k=top_k)
        
        if not results:
            # Fallback mock with RELEVANT DerivInsight examples
            return [
                {
                    "question": "Show me all high risk users from the UAE",
                    "sql": "SELECT * FROM users WHERE risk_level = 'HIGH' AND country = 'AE';"
                },
                {
                    "question": "Count the number of flagged transactions over $50,000",
                    "sql": "SELECT COUNT(*) FROM transactions WHERE status = 'FLAGGED' AND amount_usd > 50000;"
                },
                {
                    "question": "List failed login attempts in the last 24 hours",
                    "sql": "SELECT * FROM login_events WHERE status = 'FAILED' AND created_at > datetime('now', '-24 hours');"
                },
                {
                    "question": "Who are the users with pending KYC?",
                    "sql": "SELECT user_id, full_name, email FROM users WHERE kyc_status = 'PENDING';"
                }
            ]
            
        return [res["metadata"] for res in results]
