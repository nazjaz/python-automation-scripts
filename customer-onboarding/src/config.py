"""Configuration management for customer onboarding automation."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class EmailConfig(BaseModel):
    """Email configuration settings."""

    host: str = Field(..., description="SMTP server host")
    port: int = Field(..., description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    from_email: str = Field(..., description="Sender email address")
    from_name: str = Field(..., description="Sender display name")
    welcome_template: str = Field(
        default="templates/welcome_email.html",
        description="Path to welcome email template",
    )
    subject: str = Field(
        default="Welcome to {{company_name}}",
        description="Welcome email subject template",
    )
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay_seconds: int = Field(
        default=5, description="Delay between retries in seconds"
    )


class OnboardingStep(BaseModel):
    """Individual onboarding step configuration."""

    name: str = Field(..., description="Step identifier")
    required: bool = Field(default=True, description="Whether step is required")
    order: int = Field(..., description="Step execution order")


class OnboardingConfig(BaseModel):
    """Onboarding process configuration."""

    steps: list[OnboardingStep] = Field(..., description="List of onboarding steps")
    completion_threshold: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Completion percentage threshold"
    )
    tracking_interval_hours: int = Field(
        default=24, description="Progress tracking interval in hours"
    )


class ResourceAssignment(BaseModel):
    """Resource assignment configuration."""

    type: str = Field(..., description="Resource type")
    name: str = Field(..., description="Resource name")


class ResourcesConfig(BaseModel):
    """Resource assignment configuration."""

    default_assignments: list[ResourceAssignment] = Field(
        default_factory=list, description="Default resources to assign"
    )
    assignment_api_timeout: int = Field(
        default=30, description="API timeout in seconds"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file: str = Field(default="logs/onboarding.log", description="Log file path")
    max_bytes: int = Field(
        default=10485760, description="Maximum log file size in bytes"
    )
    backup_count: int = Field(default=5, description="Number of backup log files")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    smtp_host: str = Field(..., alias="SMTP_HOST")
    smtp_port: int = Field(..., alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(..., alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(..., alias="SMTP_FROM_NAME")
    database_url: str = Field(default="sqlite:///onboarding.db", alias="DATABASE_URL")
    app_name: str = Field(default="Customer Onboarding System", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    resource_api_url: Optional[str] = Field(default=None, alias="RESOURCE_API_URL")
    resource_api_key: Optional[str] = Field(default=None, alias="RESOURCE_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: Optional[Path] = None) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file. If None, uses default location.

    Returns:
        Dictionary containing configuration values.

    Raises:
        FileNotFoundError: If configuration file does not exist.
        yaml.YAMLError: If configuration file is invalid YAML.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_settings() -> Settings:
    """Load and return application settings from environment.

    Returns:
        Settings object with loaded configuration.

    Raises:
        ValueError: If required environment variables are missing.
    """
    load_dotenv()
    try:
        return Settings()
    except Exception as e:
        raise ValueError(f"Failed to load settings: {e}") from e
