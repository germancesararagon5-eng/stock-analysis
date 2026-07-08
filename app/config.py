from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@db:5432/stockdb"
    database_url_sync: str = "postgresql://user:pass@db:5432/stockdb"
    redis_url: str = "redis://redis:6379/0"
    whatsapp_gateway_url: str = "http://whatsapp-gateway:3000"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
