from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "SwarmVault SaaS"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    cors_origins: list[str] = ["*"]


settings = Settings()
