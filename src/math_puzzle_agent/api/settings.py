"""Environment-backed settings for the web service."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_name: str = "PhysicsForge API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://physicsforge:physicsforge@localhost:5433/physicsforge",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = 5
    database_pool_max_overflow: int = 10
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    planner_model: str = Field(default="gpt-4o-mini", validation_alias="PLANNER_MODEL")
    designer_model: str = Field(default="gpt-4o-mini", validation_alias="GENERATOR_MODEL")
    reviewer_model: str = Field(default="gpt-4o-mini", validation_alias="REVIEWER_MODEL")
    reviewer_vision_model: str = Field(default="gpt-4o", validation_alias="REVIEWER_VISION_MODEL")
    max_generation_attempts: int = Field(default=3, ge=1, le=5)
    workflow_timeout_seconds: float = Field(default=120.0, gt=0, le=600)
    cors_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    max_request_body_bytes: int = Field(default=16_384, ge=1, le=1_048_576)
    generation_rate_limit_requests: int = Field(default=10, ge=1, le=1000)
    generation_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    @property
    def allowed_origins(self) -> list[str]:
        """Return explicitly configured browser origins; wildcards are intentionally rejected."""

        origins = [item.strip().rstrip("/") for item in self.cors_allowed_origins.split(",")]
        return [item for item in origins if item and item != "*"]

    @property
    def model_generation_enabled(self) -> bool:
        if self.openai_api_key is None:
            return False
        value = self.openai_api_key.get_secret_value().strip()
        return bool(value and value != "your_openai_api_key_here")
