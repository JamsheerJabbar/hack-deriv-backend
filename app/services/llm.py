import time
import google.generativeai as genai
from app.core.config import settings
from app.core.logger import logger

# Optional import of OpenAI – will be available if the package is installed
try:
    import openai
except ImportError:
    openai = None

class LLMService:
    def __init__(self):
        # Prefer OpenAI if an API key is provided
        if getattr(settings, "OPENAI_API_KEY", None):
            if openai is None:
                raise ImportError("openai package is required for OPENAI_API_KEY usage.")
            openai.api_key = settings.OPENAI_API_KEY
            self.provider = "openai"
            self.model_name = getattr(settings, "OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        elif settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.provider = "gemini"
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        else:
            print("Warning: No LLM API key found in settings.")
            self.provider = None
            self.model = None

    async def _call_openai(self, prompt: str) -> str:
        # Simple wrapper for OpenAI ChatCompletion
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content

    async def generate_response(self, prompt: str) -> str:
        if not self.provider:
            logger.error("LLM Service not configured (no API key found).")
            return "LLM Service not configured."

        logger.info(f"LLM [{self.provider}] generating response for prompt snippet: {prompt[:50]}...")
        # Retry logic for rate‑limit (429) – up to 3 attempts
        attempts = 0
        while attempts < 3:
            try:
                if self.provider == "openai":
                    res = await self._call_openai(prompt)
                else:  # gemini
                    response = self.model.generate_content(prompt)
                    res = response.text
                
                logger.info(f"LLM response received. Snippet: {res[:50]}...")
                return res
            except Exception as e:
                # Detect rate‑limit / quota errors
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg or "quota" in err_msg:
                    attempts += 1
                    wait = 2 ** attempts
                    logger.warning(f"LLM rate limit encountered, retrying in {wait}s (attempt {attempts})")
                    time.sleep(wait)
                    continue
                logger.error(f"LLM Error: {str(e)}")
                return f"Error generating response: {str(e)}"
        logger.error("LLM service rate limit exceeded after multiple retries.")
        return "Error: LLM service rate limit exceeded after multiple retries."

llm_service = LLMService()
