from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Settings for the Discord bot."""

    # Discord Configuration
    discord_token: str
    discord_secret: str
    discord_owner_id: int
    discord_command_prefix: str = "n!"
    discord_guild_id: int
    discord_log_channel_id: int
    discord_bot_id: int

    # AI Provider Configurations
    xai_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    google_api_key: str

    # Database Configuration
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    postgres_host: str
    instance_connection_name: str

    # Redis Configuration
    redis_url: str
    redis_password: str
    redis_conversation_ttl: int

    # Logging Configuration
    log_level: str = "INFO"
    log_dir: str = "logs"

    sqlite_path: str = "data/eidos.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
