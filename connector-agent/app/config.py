import os
from pydantic_settings import BaseSettings
from pydantic import Field

class AgentSettings(BaseSettings):
    AGENT_NAME: str = Field(default_factory=lambda: os.getenv("AGENT_NAME", "OnPrem-Connector-01"))
    AGENT_TOKEN: str = Field(default_factory=lambda: os.getenv("AGENT_TOKEN", "qlagent_sample_token"))
    CLOUD_WS_URL: str = Field(
        default_factory=lambda: os.getenv("CLOUD_WS_URL", "ws://127.0.0.1:8000/ws/agents/connect")
    )

    # Local Database Connection to be bridged
    LOCAL_DB_DIALECT: str = Field(default_factory=lambda: os.getenv("LOCAL_DB_DIALECT", "sqlite"))
    LOCAL_DB_HOST: str = Field(default_factory=lambda: os.getenv("LOCAL_DB_HOST", "localhost"))
    LOCAL_DB_PORT: int = Field(default_factory=lambda: int(os.getenv("LOCAL_DB_PORT", "5432")))
    LOCAL_DB_NAME: str = Field(default_factory=lambda: os.getenv("LOCAL_DB_NAME", "company_local.db"))
    LOCAL_DB_USER: str = Field(default_factory=lambda: os.getenv("LOCAL_DB_USER", "postgres"))
    LOCAL_DB_PASSWORD: str = Field(default_factory=lambda: os.getenv("LOCAL_DB_PASSWORD", ""))

    HEARTBEAT_INTERVAL_SECONDS: int = 15
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_ROWS_LIMIT: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True

agent_settings = AgentSettings()
