# src/core/config.py
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
from src.core.module_manager import module

load_dotenv()


@module(
    name="config",
    module_type="core",
    description="Application configuration",
)
class AppConfig(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Discord Configuration
    discord_token: str = Field(description="Discord bot token")
    discord_owner_id: int = Field(description="Discord owner ID")
    bot_prefix: str = Field(default="!", description="Discord command prefix")

    # AI Provider API Keys (all optional)
    xai_api_key: Optional[str] = Field(default=None, description="X.AI API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    cohere_api_key: Optional[str] = Field(default=None, description="Cohere API key")
    fal_api_key: Optional[str] = Field(default=None, description="FAL API key")
    google_api_key: str = Field(
        default=os.getenv("GOOGLE_API_KEY", ""), description="Google API key"
    )

    # Database Configuration
    postgres_url: str = Field(description="PostgreSQL database URL")

    # Redis Configuration
    redis_url: str = Field(description="Redis URL")
    redis_conversation_ttl: int = Field(
        default=5400, description="Redis conversation TTL in seconds"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default="logs", description="Logging directory")

    # Azure Quantum Configuration
    azure_subscription_id: Optional[str] = Field(
        default=None, description="Azure subscription ID"
    )
    azure_resource_group: Optional[str] = Field(
        default=None, description="Azure resource group"
    )
    azure_workspace_name: Optional[str] = Field(
        default=None, description="Azure workspace name"
    )
    azure_location: Optional[str] = Field(default=None, description="Azure location")

    # Neo4j Configuration
    neo4j_uri: str = Field(description="Neo4j connection URL")
    neo4j_username: str = Field(description="Neo4j username")
    neo4j_password: str = Field(description="Neo4j password")

    # SurrealDB Configuration
    surrealdb_host: str = Field(description="SurrealDB host")
    surrealdb_port: int = Field(default=443, description="SurrealDB port")
    surrealdb_username: str = Field(description="SurrealDB username")
    surrealdb_password: str = Field(description="SurrealDB password")
    surrealdb_namespace: str = Field(default="test", description="SurrealDB namespace")
    surrealdb_database: str = Field(default="test", description="SurrealDB database")

    # Base Directory
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent,
        description="Base directory of the project",
    )

    @field_validator("discord_owner_id")
    @classmethod
    def validate_discord_owner_id(cls, value):
        if not isinstance(value, int):
            raise ValueError("Discord owner ID must be an integer.")
        return value

    @field_validator("redis_conversation_ttl")
    @classmethod
    def validate_redis_conversation_ttl(cls, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Redis conversation TTL must be a positive integer.")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {', '.join(allowed_levels)}")
        return value.upper()

    @field_validator(
        "azure_subscription_id",
        "azure_resource_group",
        "azure_workspace_name",
        "azure_location",
        mode="before",
    )
    @classmethod
    def validate_azure_config(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Azure config values must be strings.")
        return value

    def __init__(self, **data: Dict[str, Any]):
        super().__init__(**data)

    def __repr__(self):
        return f"<AppConfig: {', '.join([f'{k}={v}' for k, v in self.model_dump().items()])}>"

    def __str__(self):
        return self.__repr__()


def load_config() -> AppConfig:
    """Load and return the application configuration."""
    return AppConfig()


# Create default instances
config = AppConfig()
settings = config

# Export the load_config function
__all__ = ["config", "settings", "load_config"]


if __name__ == "__main__":
    loaded_config = load_config()
    print(loaded_config)
    print(f"Discord Token: {loaded_config.discord_token}")
    print(f"Redis TTL: {loaded_config.redis_conversation_ttl}")
    print(f"Log Level: {loaded_config.log_level}")
    print(f"Azure Subscription ID: {loaded_config.azure_subscription_id}")
    print(f"Neo4j URL: {loaded_config.neo4j_uri}")
    print(f"Base Directory: {loaded_config.base_dir}")
