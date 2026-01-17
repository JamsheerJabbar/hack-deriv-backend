import google.generativeai as genai
from app.core.config import settings

class LLMService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.MODEL_NAME)
        else:
            print("Warning: GEMINI_API_KEY not found in settings.")
            self.model = None

    async def generate_response(self, prompt: str) -> str:
        if not self.model:
            return "LLM Service not configured."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

llm_service = LLMService()
