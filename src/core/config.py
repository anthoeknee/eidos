from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Settings for the Discord bot."""

    # Discord Configuration
    discord_token: str
    discord_secret: str
    discord_owner_id: int
    discord_command_prefix: str
    discord_guild_id: int
    discord_log_channel_id: int
    discord_bot_id: int

    # AI Provider Configurations
    xai_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Database Configuration
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    postgres_host: str
    use_connection_pooling: bool = True
    database_pool_size: int = 20
    database_pool_timeout: int = 30
    postgres_url: Optional[str] = None

    # Redis Configuration
    valkey_url: str
    valkey_password: str
    valkey_conversation_ttl: int

    # Logging Configuration
    log_level: str
    log_dir: str

    # Storage Configuration
    storage_type: str = "valkey"

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )


settings = Settings()
if __name__ == "__main__":
    print(f"Discord Token: {settings.discord_token}")
    print(f"Log Level: {settings.log_level}")
    print(f"Redis URL: {settings.valkey_url}")
    print(f"Postgres URL: {settings.postgres_url}")
    print(f"Storage Type: {settings.storage_type}")
