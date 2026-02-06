"""Configuration management for research data processor system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    url: str = Field(default="sqlite:///research_data_processor.db")


class AppSettings(BaseModel):
    """Application settings."""

    name: str = Field(default="Research Data Processor")
    log_level: str = Field(default="INFO")


class Settings(BaseModel):
    """Application settings container."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    app: AppSettings = Field(default_factory=AppSettings)


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Optional path to configuration file.
            Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If configuration file does not exist.
        yaml.YAMLError: If configuration file is invalid YAML.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_settings() -> Settings:
    """Load application settings from environment variables.

    Returns:
        Settings object with configuration values.
    """
    load_dotenv()

    return Settings(
        database=DatabaseSettings(url=os.getenv("DATABASE_URL", "sqlite:///research_data_processor.db")),
        app=AppSettings(
            name=os.getenv("APP_NAME", "Research Data Processor"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        ),
    )
