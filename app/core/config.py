from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Explicitly load .env file
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "NL2SQL Pipeline"
    API_V1_STR: str = "/api/v1"
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_NAME: str = "gemini-3-flash-preview"
    OPENAI_API_KEY: Optional[str] = None
    # stage-specific models
    INTENT_MODEL: str = os.getenv("INTENT_MODEL", "gemini-3-flash-preview")
    SQL_MODEL: str = os.getenv("SQL_MODEL", "gemini-3-flash-preview")
    CLARIFICATION_MODEL: str = os.getenv("CLARIFICATION_MODEL", "gemini-2.5-flash-lite")
    DISCOVERY_MODEL: str = os.getenv("DISCOVERY_MODEL", "gemini-2.5-flash-lite")
    EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "gemini-2.5-flash-lite")
    RETRIEVAL_MODEL: str = os.getenv("RETRIEVAL_MODEL", "gemini-2.5-flash-lite")
    
    # Database Settings (Target DB to query)
    DATABASE_URL: str = "sqlite:///./derivinsightnew.db"
    SCHEMA_PATH: str = "app/files/derivinsight_schema.sql"
    MOCK_DATA_SCRIPT_PATH: str = "app/files/generate_mock_data.py"
    
    # Cache Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App Settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
