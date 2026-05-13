from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = Field("postgresql+asyncpg://user:password@localhost/resolveai", env="DATABASE_URL")
    environment: str = Field("development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"


settings = Settings()
