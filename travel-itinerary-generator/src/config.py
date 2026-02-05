"""Configuration management for travel itinerary generator."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class FlightConfig(BaseModel):
    """Flight booking configuration."""

    api_provider: str = Field(default="amadeus", description="Flight API provider")
    api_key: str = Field(..., description="Flight API key")
    api_secret: str = Field(..., description="Flight API secret")
    default_currency: str = Field(default="USD", description="Default currency")
    check_in_reminder_hours: int = Field(
        default=24, description="Hours before flight to send check-in reminder"
    )
    gate_change_notification: bool = Field(
        default=True, description="Enable gate change notifications"
    )


class HotelConfig(BaseModel):
    """Hotel booking configuration."""

    api_provider: str = Field(default="booking", description="Hotel API provider")
    api_key: str = Field(..., description="Hotel API key")
    default_currency: str = Field(default="USD", description="Default currency")
    check_in_reminder_hours: int = Field(
        default=24, description="Hours before check-in to send reminder"
    )
    check_out_reminder_hours: int = Field(
        default=2, description="Hours before check-out to send reminder"
    )


class ActivityConfig(BaseModel):
    """Activity booking configuration."""

    api_provider: str = Field(
        default="tripadvisor", description="Activity API provider"
    )
    api_key: str = Field(..., description="Activity API key")
    default_currency: str = Field(default="USD", description="Default currency")
    reminder_hours_before: int = Field(
        default=2, description="Hours before activity to send reminder"
    )


class EmailNotificationConfig(BaseModel):
    """Email notification configuration."""

    enabled: bool = Field(default=True, description="Enable email notifications")
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(..., description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    from_email: str = Field(..., description="Sender email address")
    from_name: str = Field(
        default="Travel Itinerary Service", description="Sender display name"
    )


class SMSNotificationConfig(BaseModel):
    """SMS notification configuration."""

    enabled: bool = Field(default=False, description="Enable SMS notifications")
    provider: str = Field(default="twilio", description="SMS provider")
    api_key: str = Field(..., description="SMS API key")
    api_secret: str = Field(..., description="SMS API secret")
    from_number: str = Field(..., description="SMS sender number")


class NotificationConfig(BaseModel):
    """Notification configuration."""

    email: EmailNotificationConfig = Field(
        default_factory=EmailNotificationConfig, description="Email settings"
    )
    sms: SMSNotificationConfig = Field(
        default_factory=SMSNotificationConfig, description="SMS settings"
    )


class ItineraryConfig(BaseModel):
    """Itinerary generation configuration."""

    default_timezone: str = Field(default="UTC", description="Default timezone")
    reminder_hours_before: list[int] = Field(
        default=[72, 24, 2], description="Hours before trip to send reminders"
    )
    update_interval_minutes: int = Field(
        default=30, description="Interval for checking updates in minutes"
    )
    output_format: list[str] = Field(
        default=["html", "pdf"], description="Output formats"
    )
    output_directory: str = Field(
        default="itineraries", description="Output directory"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file: str = Field(default="logs/itinerary.log", description="Log file path")
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

    flight_api_key: str = Field(..., alias="FLIGHT_API_KEY")
    flight_api_secret: str = Field(..., alias="FLIGHT_API_SECRET")
    hotel_api_key: str = Field(..., alias="HOTEL_API_KEY")
    activity_api_key: str = Field(..., alias="ACTIVITY_API_KEY")
    smtp_host: str = Field(..., alias="SMTP_HOST")
    smtp_port: int = Field(..., alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(..., alias="SMTP_FROM_EMAIL")
    smtp_from_name: Optional[str] = Field(default=None, alias="SMTP_FROM_NAME")
    sms_api_key: Optional[str] = Field(default=None, alias="SMS_API_KEY")
    sms_api_secret: Optional[str] = Field(default=None, alias="SMS_API_SECRET")
    sms_from_number: Optional[str] = Field(default=None, alias="SMS_FROM_NUMBER")
    app_name: str = Field(default="Travel Itinerary Generator", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: Optional[Path] = None) -> dict:
    """Load configuration from YAML file with environment variable substitution.

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

    load_dotenv()

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
        content = os.path.expandvars(content)
        config = yaml.safe_load(content)

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
