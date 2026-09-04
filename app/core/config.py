from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
import json
import logging

logger = logging.getLogger(__name__)

_DEV_DATABASE_URL = "postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault"
_DEV_SECRET = "dev-insecure-default-change-in-production-123"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "SwarmVault SaaS"
    environment: str = "development"

    @property
    def debug(self) -> bool:
        """Debug is true only in non-production environments."""
        return self.environment != "production"

    # Database — dev default for local use. MUST be overridden in production.
    database_url: str = _DEV_DATABASE_URL

    # Auth — dev default is insecure. MUST be overridden in production.
    secret_key: str = _DEV_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # CORS — comma-separated string (e.g. "https://app.example.com,https://admin.example.com")
    # or JSON list. Use cors_origins_safe for parsed list.
    cors_origins: str = "*"

    # LLM provider
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_retry_backoff: float = 1.0
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

    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        """Ensure SECRET_KEY has sufficient entropy.

        In production, rejects any dev default value.
        In development, warns but allows any value >= 32 chars.
        """
        is_prod = self.environment == "production"
        if len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Detect insecure defaults (known dev values)
        insecure_defaults = (
            "change-me-in-production",
            "changeme",
            "dev-secret",
            "development",
            "dev-insecure-default-change-in-production-123",
        )
        if self.secret_key.lower() in insecure_defaults:
            if is_prod:
                raise ValueError(
                    "SECRET_KEY is a known development placeholder. "
                    "Generate and set a cryptographically secure random value."
                )
            logger.warning(
                "SECURITY: Using insecure default SECRET_KEY. "
                "Set SECRET_KEY in .env for any deployment."
            )
        # In production, reject non-default secrets that look like dictionary words
        if is_prod:
            # Check for low entropy (repeating patterns, common words)
            lower = self.secret_key.lower()
            weak_patterns = ("password", "secret", "admin", "test", "123456")
            if any(p in lower for p in weak_patterns):
                raise ValueError(
                    "SECRET_KEY appears to be a weak value. "
                    "Use a cryptographically random value."
                )
        logger.debug("SECRET_KEY validated: %d chars", len(self.secret_key))
        return self

    @model_validator(mode="after")
    def _validate_database_url(self) -> "Settings":
        """In production, reject the development database URL."""
        if self.environment == "production":
            if "swarmvault:swarmvault@localhost" in self.database_url:
                raise ValueError(
                    "DATABASE_URL is the development default. "
                    "Set a production database URL via DATABASE_URL env var."
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string or JSON list."""
        raw = self.cors_origins
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw or raw == "*":
                return ["*"]
            if raw.startswith("["):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass
            return [o.strip() for o in raw.split(",") if o.strip()]
        return ["*"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins_safe(self) -> list[str]:
        """Never allow wildcard origins with credentials.

        In production, enforce explicit origin list (no wildcard).
        In development, restrict to localhost variants only.
        """
        origins = self.cors_origins_list
        # Always strip wildcard when allow_credentials=True (prevents reflected-origin attacks)
        origins = [o for o in origins if o != "*"]
        if not origins:
            if self.is_production:
                raise ValueError("CORS_ORIGINS must be set in production (comma-separated URLs)")
            # Dev fallback: only localhost
            origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
        return origins


settings = Settings()
