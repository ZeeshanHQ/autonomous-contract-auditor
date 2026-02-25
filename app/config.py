import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # LLM Settings
    LLM_PROVIDER: str = "groq" 
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    
    # App Settings
    APP_NAME: str = "Contract Auditor"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RISK_PLAYBOOK_PATH: str = os.path.join(BASE_DIR, "data", "risk_standards.json")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
