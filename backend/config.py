from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field("sqlite+aiosqlite:///./resolveai.db", env="DATABASE_URL")
    environment: str = Field("development", env="ENVIRONMENT")
    vector_dim: int = Field(384, env="VECTOR_DIM")
    mistral_api_key: str | None = Field(None, env="MISTRAL_API_KEY")
    mistral_api_base_url: str = Field("https://api.mistral.ai/v1", env="MISTRAL_API_BASE_URL")
    mistral_chat_model: str = Field("mistral-7b-chat", env="MISTRAL_CHAT_MODEL")
    mistral_embedding_model: str = Field("mistral-7b-embeddings", env="MISTRAL_EMBEDDING_MODEL")
    mistral_request_timeout: int = Field(60, env="MISTRAL_REQUEST_TIMEOUT")

    class Config:
        env_file = ".env"


settings = Settings()
