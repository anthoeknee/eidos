from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse


class Settings(BaseSettings):
    # Discord Configuration
    DISCORD_TOKEN: str
    DISCORD_OWNER_ID: int
    DISCORD_COMMAND_PREFIX: str = "n!"

    # AI Provider API Keys - all optional
    XAI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    FAL_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Database Configuration
    POSTGRES_URL: str

    # Redis Configuration
    REDIS_URL: str
    REDIS_CONVERSATION_TTL: int = 5400

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("LOG_DIR")
    @classmethod
    def validate_log_dir(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @field_validator("POSTGRES_URL")
    @classmethod
    def validate_postgres_url(cls, v: str) -> str:
        if not v.startswith(("postgres://", "postgresql://")):
            raise ValueError("Invalid POSTGRES_URL format")

        # Replace postgres:// with postgresql+psycopg2:// but preserve any query parameters
        base_url = v.split("?")[0]
        query_params = v.split("?")[1] if "?" in v else ""

        new_base = base_url.replace("postgres://", "postgresql+psycopg2://", 1).replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )

        return f"{new_base}{'?' + query_params if query_params else ''}"

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str):
        parsed_url = urlparse(v)
        if parsed_url.scheme not in ["redis", "rediss"]:
            raise ValueError(
                "Invalid REDIS_URL scheme. Must be 'redis://' or 'rediss://'"
            )

        # Reconstruct the URL with proper formatting
        auth_part = ""
        if parsed_url.username and parsed_url.password:
            auth_part = f"{parsed_url.username}:{parsed_url.password}@"
        elif parsed_url.password:
            auth_part = f":{parsed_url.password}@"

        # Use default port if not specified
        port = parsed_url.port or 6379

        # Keep the original scheme (redis://) since we're not using SSL
        return f"redis://{auth_part}{parsed_url.hostname}:{port}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# Create a global config instance
config = Settings()


def get_config() -> Settings:
    return config
