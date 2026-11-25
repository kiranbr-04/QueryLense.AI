import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "QueryLens AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # App Database (PostgreSQL recommended; SQLite supported for local dev)
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./querylens_app.db")
    )
    
    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "querylens-super-secret-key-change-in-production-32bytes!")
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Encryption at rest (Fernet key for connection passwords)
    # Default 32-byte url-safe base64 key for development
    ENCRYPTION_KEY: str = Field(
        default_factory=lambda: os.getenv("ENCRYPTION_KEY", "uK23k_Oq96ZcZ_bHnI8K_bN_6uV3mR7p8G1s_0oJk9Y=")
    )
    
    # SSRF Protection
    ALLOW_PRIVATE_IPS: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_PRIVATE_IPS", "true").lower() in ("true", "1")
    )
    
    # Query Execution Limits
    QUERY_TIMEOUT_SECONDS: int = 30
    DEFAULT_ROW_LIMIT: int = 500
    MAX_ROW_LIMIT: int = 5000
    
    # AI Provider: "mock", "gemini", "openai", "anthropic", "ollama"
    DEFAULT_LLM_PROVIDER: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    )
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    OPENAI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    ANTHROPIC_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    OLLAMA_BASE_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    AI_MODEL_NAME: str = Field(default_factory=lambda: os.getenv("AI_MODEL_NAME", "gpt-4o-mini"))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }

settings = Settings()
