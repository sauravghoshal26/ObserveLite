from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "ObserveLite"
    log_level: str = "INFO"
    otel_service_name: str = "observelite-app"
    otel_exporter_otlp_endpoint: str = "http://jaeger:4317"
    enable_tracing: bool = True

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()

