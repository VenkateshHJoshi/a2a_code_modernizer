from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: Optional[str] = None
    
    # Ollama Configuration (Default local host)
    ollama_host: str = "http://localhost:11434"
    
    # Model Preferences
    # We default to 'codellama:instruct' as requested, or 'deepseek-coder' if available
    preferred_local_model: str = "codellama:instruct" 
    fallback_model: str = "gemini-1.5-flash" # Using flash for speed/cost efficiency
    
    # Agent Settings
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()