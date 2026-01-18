from typing import Dict, Any
from app.services.llm import llm_service

class ClarificationModule:
    """
    Generates clarifying questions when user query is ambiguous or incomplete.
    Helps refine compliance rules and complex queries.
    """
    
    async def generate_clarification(self, query: str, domain: str, conversation_history: list = None) -> str:
        """
        Generates a follow-up question to clarify the user's intent.
        """
        history_context = ""
        if conversation_history:
            history_context = "\n\nConversation so far:\n"
            for msg in conversation_history[-5:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_context += f"{role.upper()}: {content}\n"
        
        domain_context = {
            "security": "Focus on login patterns, IP addresses, device info, authentication failures, blocked accounts.",
            "compliance": "Focus on KYC status, PEP flags, document expiry, regulatory requirements, audit trails.",
            "risk": "Focus on transaction amounts, risk scores, flagged transactions, velocity patterns, high-risk countries.",
            "operations": "Focus on daily volumes, user growth, system metrics, time ranges, aggregations."
        }.get(domain, "Focus on database tables: users, transactions, login_events, alerts.")
        
        prompt = f"""
You are a helpful assistant helping clarify database queries in the {domain.upper()} domain.

{domain_context}

{history_context}

Current user query: "{query}"

The query is ambiguous or missing critical information. Generate ONE clarifying question to help the user be more specific.

Examples of good clarifying questions:
- "What time range would you like to analyze? (e.g., last 24 hours, last 7 days, last month)"
- "What threshold should I use to identify 'high-risk' users? (e.g., risk_score > 70)"
- "Which specific compliance rule are you interested in? (e.g., KYC pending, PEP status, expired documents)"
- "Do you want to see all transactions or only flagged/suspicious ones?"
- "Should I include active users only, or all account statuses?"

Return ONLY the clarifying question. Be conversational and helpful. Don't include JSON or markdown.
"""
        
        try:
            response = await llm_service.generate_response(prompt)
            return response.strip()
        except Exception as e:
            print(f"Clarification generation error: {e}")
            return "Could you please provide more details about what you're looking for?"

clarification_module = ClarificationModule()
