"""Configuration management module."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings."""
    
    app_name: str = "Automation Project"
    version: str = "1.0.0"


def load_config(config_path: Optional[Path] = None) -> Settings:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        Settings object.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        return Settings()
    
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f) or {}
    
    return Settings(**config_data)


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings object.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    return load_config()
