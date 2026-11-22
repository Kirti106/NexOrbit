from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://root:change-me-please@localhost:5432/nexorbit"
    )
    cors_origins: str = "http://localhost:5173"
    ml_api_url: str = "http://localhost:8001"
    admin_api_key: str = ""
    cache_ttl: int = 8
    scheduler_enabled: bool = False
    socrates_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
