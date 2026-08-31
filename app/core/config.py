from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "SwarmVault SaaS"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # CORS — production must set SWARMMAULT_CORS_ORIGINS explicitly
    cors_origins: list[str] = ["*"]

    # LLM provider
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # SwarmVault
    swarmvault_url: str = "http://localhost:8000"
    swarmvault_api_key: str = ""

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = False

    # Rate limiting (requests per minute per key)
    rate_limit_login: int = 10
    rate_limit_chat: int = 30
    rate_limit_ingest: int = 5
    rate_limit_search: int = 60
    rate_limit_api: int = 100

    # Object storage (None = filesystem)
    storage_backend: str = "filesystem"
    storage_path: str = "./storage"
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "swarmvault-uploads"
    s3_region: str = "us-east-1"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins_safe(self) -> list[str]:
        """In production, never allow wildcard origins with credentials."""
        if self.is_production:
            origins = [o for o in self.cors_origins if o != "*"]
            if not origins:
                raise ValueError("SWARMMAULT_CORS_ORIGINS must be set in production")
            return origins
        return self.cors_origins


settings = Settings()
