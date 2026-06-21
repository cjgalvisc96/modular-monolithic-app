"""Application settings (Pydantic BaseSettings), sourced from .env / environment."""

from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    owner: str = "local"
    debug: bool = True
    log_level: str = "DEBUG"
    db_echo: bool = False

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "todo"
    db_user: str = "todo"
    db_password: str = "todo"
    db_pool_size: int = 10
    db_pool_max_overflow: int = 20

    cors_allow_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    cache_enable: bool = True
    cache_namespaces: str = "users,tasks,ai"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_domain: str = ""
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    otel_enable: bool = False
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "todo-app"

    @cached_property
    def database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @cached_property
    def redis_dsn(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cache_namespace_tuple(self) -> tuple[str, ...]:
        return tuple(n.strip() for n in self.cache_namespaces.split(",") if n.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    def as_provider_dict(self) -> dict:
        """Flat dict fed into the DI Configuration provider, including derived values."""
        data = self.model_dump()
        data["database_dsn"] = self.database_dsn
        data["redis_dsn"] = self.redis_dsn
        data["cache_namespace_tuple"] = list(self.cache_namespace_tuple)
        data["cors_origin_list"] = self.cors_origin_list
        return data


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
