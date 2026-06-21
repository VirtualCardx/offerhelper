from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Offer Compensation Decision Engine"
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./offer_engine.db"
    celery_broker_url: str = "memory://"
    celery_result_backend: str = "cache+memory://"
    celery_task_always_eager: bool = True
    celery_task_store_eager_result: bool = True
    market_sync_schedule_minutes: int = 30
    model_rollback_max_candidate_versions: int = 3
    high_risk_rollback_requires_approval: bool = True
    governance_pending_review_ttl_hours: int = 24
    governance_pending_review_sweep_minutes: int = 15
    governance_pending_review_alert_window_minutes: int = 120
    governance_notification_default_channel: str = "log"
    cors_allow_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
