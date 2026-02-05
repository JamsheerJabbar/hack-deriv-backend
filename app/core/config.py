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
    INTENT_MODEL: str = os.getenv("INTENT_MODEL", "gemini-2.5-flash-lite")
    SQL_MODEL: str = os.getenv("SQL_MODEL", "gemini-2.5-flash-lite")
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
    
    # ECS worker tasks (optional; if set, API can start/stop engine/generator via ECS)
    ECS_CLUSTER: Optional[str] = None
    ECS_TASK_DEFINITION: Optional[str] = None # single task def; command overridden per run
    ECS_ENGINE_TASK_DEFINITION: Optional[str] = None  # fallback if ECS_TASK_DEFINITION not set
    ECS_GENERATOR_TASK_DEFINITION: Optional[str] = None
    ECS_ENGINE_WORKER_CONTAINER_NAME: str = "alerting-worker-container"  # MUST match container name in task definition
    ECS_GENERATOR_WORKER_CONTAINER_NAME: str = "event-generator-worker-container"
    
    ECS_SUBNETS: Optional[str] = None  # comma-separated subnet IDs
    ECS_SECURITY_GROUPS: Optional[str] = None  # comma-separated security group IDs
    ECS_LAUNCH_TYPE: str = "FARGATE"
    
    # App Settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
