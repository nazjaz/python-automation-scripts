"""Configuration management for content calendar generator."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class PlatformConfig(BaseModel):
    """Configuration for a social media platform."""

    enabled: bool = True
    optimal_times: list[Dict[str, Any]] = Field(default_factory=list)
    posts_per_day: int = Field(ge=1, le=10)


class CalendarConfig(BaseModel):
    """Calendar generation configuration."""

    weeks_ahead: int = Field(ge=1, le=52, default=4)
    posts_per_day: int = Field(ge=1, le=10, default=2)
    content_types: list[str] = Field(default_factory=list)
    content_mix: Dict[str, int] = Field(default_factory=dict)

    @validator("content_mix")
    def validate_content_mix(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Validate that content mix percentages sum to 100."""
        total = sum(v.values())
        if total != 100:
            raise ValueError(
                f"Content mix percentages must sum to 100, got {total}"
            )
        return v


class EngagementConfig(BaseModel):
    """Audience engagement analysis configuration."""

    analysis_period_days: int = Field(ge=1, default=90)
    metrics: list[str] = Field(default_factory=list)
    metric_weights: Dict[str, float] = Field(default_factory=dict)
    min_engagement_threshold: int = Field(ge=0, default=10)

    @validator("metric_weights")
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate that metric weights sum to 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Metric weights must sum to 1.0, got {total}"
            )
        return v


class PerformanceConfig(BaseModel):
    """Content performance analysis configuration."""

    analysis_period_days: int = Field(ge=1, default=90)
    metrics: list[str] = Field(default_factory=list)
    thresholds: Dict[str, float] = Field(default_factory=dict)


class PostingTimesConfig(BaseModel):
    """Optimal posting time analysis configuration."""

    analysis_period_days: int = Field(ge=1, default=90)
    time_slots: list[int] = Field(default_factory=list)
    min_posts_per_slot: int = Field(ge=1, default=5)


class SchedulingConfig(BaseModel):
    """Scheduling configuration."""

    auto_schedule: bool = False
    buffer_minutes: int = Field(ge=0, default=15)
    retry_failed: bool = True
    max_retries: int = Field(ge=1, default=3)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/content_calendar.log"
    max_bytes: int = 10485760
    backup_count: int = 5


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "Content Calendar Generator"
    version: str = "1.0.0"
    timezone: str = "America/New_York"


class Settings(BaseModel):
    """Application settings container."""

    app: AppConfig = Field(default_factory=AppConfig)
    calendar: CalendarConfig = Field(default_factory=CalendarConfig)
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)
    engagement: EngagementConfig = Field(default_factory=EngagementConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    posting_times: PostingTimesConfig = Field(
        default_factory=PostingTimesConfig
    )
    scheduling: SchedulingConfig = Field(default_factory=SchedulingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Optional[Path] = None) -> Settings:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file. If None, uses default.

    Returns:
        Settings object with loaded configuration.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If configuration is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return Settings(**config_data)


def get_settings() -> Settings:
    """Get application settings.

    Loads environment variables and configuration file.

    Returns:
        Settings object with loaded configuration.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return load_config()


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable.

    Args:
        key: Environment variable key.
        default: Default value if not found.

    Returns:
        Environment variable value or default.
    """
    return os.getenv(key, default)
