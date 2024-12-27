from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    discord_token: str
    discord_guild_id: Optional[int] = None
    discord_log_channel_id: Optional[int] = None
    discord_command_prefix: str = "!"

    gcp_project_id: str = "gen-lang-client-0469845991"
    gcp_region: str = "us-central1"

    xai_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    use_connection_pooling: Optional[str] = None
    log_level: Optional[str] = None
    log_dir: Optional[str] = None
    services__cohere__enabled: Optional[str] = None
    services__cohere__options__api_key: Optional[str] = None
    services__cohere__options__model: Optional[str] = None
    services__cohere__options__max_tokens: Optional[str] = None
    services__cohere__options__batch_size: Optional[str] = None


# Create a global settings instance
settings = Settings()
