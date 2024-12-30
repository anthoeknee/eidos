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

    # AI Provider Configurations
    xai_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Database Configuration
    database_session_url: str
    database_transaction_url: str
    database_direct_url: str
    use_connection_pooling: bool = True
    database_pool_size: int = 20
    database_pool_timeout: int = 30

    # Redis Configuration
    valkey_url: str = "valkey://10.188.0.2:6379"
    valkey_password: str
    valkey_conversation_ttl: int = 5400

    # Logging Configuration
    log_level: str = "INFO"
    log_dir: str = "logs"

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()

if __name__ == "__main__":
    print(f"Discord Token: {settings.discord_token}")
    print(f"Log Level: {settings.log_level}")
    print(f"Redis URL: {settings.valkey_url}")
