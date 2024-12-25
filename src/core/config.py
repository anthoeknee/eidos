from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DiscordSettings(BaseSettings):
    token: str
    secret: str
    owner_id: int
    command_prefix: str = "n!"

    model_config = SettingsConfigDict(env_prefix="DISCORD_")


class AISettings(BaseSettings):
    xai_api_key: str = Field(alias="XAI_API_KEY")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    groq_api_key: str = Field(alias="GROQ_API_KEY")
    cohere_api_key: str = Field(alias="COHERE_API_KEY")
    fal_api_key: str = Field(alias="FAL_API_KEY")
    google_api_key: str = Field(alias="GOOGLE_API_KEY")


class DatabaseSettings(BaseSettings):
    session_url: str
    transaction_url: str
    direct_url: str
    use_connection_pooling: bool = True
    pool_size: int = 20
    pool_timeout: int = 30

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    conversation_ttl: int = 5400

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class LoggingSettings(BaseSettings):
    level: str = "INFO"
    log_dir: str = "logs"

    model_config = SettingsConfigDict(env_prefix="LOG_")


class CohereServiceSettings(BaseSettings):
    enabled: bool = True
    api_key: str
    model: str = "embed-english-v3.0"
    max_tokens: int = 2048
    batch_size: int = 48

    model_config = SettingsConfigDict(env_prefix="SERVICES__COHERE__OPTIONS__")


class Settings(BaseSettings):
    discord: DiscordSettings = Field(default_factory=DiscordSettings)
    ai: AISettings = Field(default_factory=AISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cohere_service: CohereServiceSettings = Field(default_factory=CohereServiceSettings)


# Create a global settings instance
settings = Settings()
