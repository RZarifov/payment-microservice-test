from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    rabbitmq_url: str
    api_key: str

    outbox_poll_interval: float = 1.0
    webhook_retry_attempts: int = 5
    webhook_retry_base_delay: float = 1.0


settings = Settings()
