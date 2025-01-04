from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, SecretStr
from typing import Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    # Discord Configuration
    DISCORD_TOKEN: str
    DISCORD_OWNER_ID: int
    DISCORD_COMMAND_PREFIX: str = "n!"

    # AI Provider API Keys
    XAI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    FAL_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Database Configuration
    POSTGRES_USER: str = "eidos"
    POSTGRES_PASSWORD: SecretStr = SecretStr("gPCZn3etyNEAn7Pgj5JEW4gz")
    POSTGRES_HOST: str = "34.59.232.41"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "db"
    POSTGRES_URL: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str
    REDIS_PASSWORD: str
    REDIS_CONVERSATION_TTL: int = 5400  # Default 90 minutes

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
    def validate_postgres_url(cls, v: Optional[str], values) -> str:
        if v:
            # If POSTGRES_URL is provided directly, validate and return it
            if v.startswith("postgres://"):
                v = "postgresql://" + v[len("postgres://") :]
            return v

        # Construct URL from components
        user = values.data.get("POSTGRES_USER")
        password = values.data.get("POSTGRES_PASSWORD").get_secret_value()
        host = values.data.get("POSTGRES_HOST")
        port = values.data.get("POSTGRES_PORT")
        db = values.data.get("POSTGRES_DB")

        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    def get_database_url(self) -> str:
        """
        Get database URL with priority:
        1. Environment variable DATABASE_URL
        2. Configured POSTGRES_URL
        3. Constructed URL from components
        """
        return os.getenv("DATABASE_URL") or self.POSTGRES_URL

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# Create a global config instance
config = Settings()


# Example of how to use typing hints with the config
def get_config() -> Settings:
    return config
