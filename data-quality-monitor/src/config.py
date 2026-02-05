"""Configuration management for data quality monitoring."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    name: str = Field(..., description="Database identifier")
    type: str = Field(..., description="Database type (postgresql, mysql, sqlite)")
    connection_string: str = Field(..., description="Database connection string")
    enabled: bool = Field(default=True, description="Whether database is enabled")


class CompletenessConfig(BaseModel):
    """Completeness check configuration."""

    enabled: bool = Field(default=True, description="Whether check is enabled")
    threshold: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Minimum acceptable score"
    )
    check_null_percentage: bool = Field(
        default=True, description="Check for NULL values"
    )
    check_empty_strings: bool = Field(
        default=True, description="Check for empty strings"
    )


class ConsistencyConfig(BaseModel):
    """Consistency check configuration."""

    enabled: bool = Field(default=True, description="Whether check is enabled")
    threshold: float = Field(
        default=0.90, ge=0.0, le=1.0, description="Minimum acceptable score"
    )
    check_foreign_keys: bool = Field(
        default=True, description="Check foreign key constraints"
    )
    check_referential_integrity: bool = Field(
        default=True, description="Check referential integrity"
    )
    check_data_types: bool = Field(default=True, description="Check data type consistency")


class AccuracyConfig(BaseModel):
    """Accuracy check configuration."""

    enabled: bool = Field(default=True, description="Whether check is enabled")
    threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Minimum acceptable score"
    )
    check_format_validation: bool = Field(
        default=True, description="Check format validation"
    )
    check_range_validation: bool = Field(
        default=True, description="Check range validation"
    )
    check_pattern_matching: bool = Field(
        default=True, description="Check pattern matching"
    )


class UniquenessConfig(BaseModel):
    """Uniqueness check configuration."""

    enabled: bool = Field(default=True, description="Whether check is enabled")
    threshold: float = Field(
        default=0.98, ge=0.0, le=1.0, description="Minimum acceptable score"
    )
    check_primary_keys: bool = Field(
        default=True, description="Check primary key constraints"
    )
    check_unique_constraints: bool = Field(
        default=True, description="Check unique constraints"
    )
    check_duplicate_records: bool = Field(
        default=True, description="Check for duplicate records"
    )


class TimelinessConfig(BaseModel):
    """Timeliness check configuration."""

    enabled: bool = Field(default=True, description="Whether check is enabled")
    threshold: float = Field(
        default=0.80, ge=0.0, le=1.0, description="Minimum acceptable score"
    )
    check_data_freshness_days: int = Field(
        default=7, description="Maximum days for data freshness"
    )
    check_update_frequency: bool = Field(
        default=True, description="Check update frequency"
    )


class QualityChecksConfig(BaseModel):
    """Quality checks configuration."""

    completeness: CompletenessConfig = Field(
        default_factory=CompletenessConfig, description="Completeness checks"
    )
    consistency: ConsistencyConfig = Field(
        default_factory=ConsistencyConfig, description="Consistency checks"
    )
    accuracy: AccuracyConfig = Field(
        default_factory=AccuracyConfig, description="Accuracy checks"
    )
    uniqueness: UniquenessConfig = Field(
        default_factory=UniquenessConfig, description="Uniqueness checks"
    )
    timeliness: TimelinessConfig = Field(
        default_factory=TimelinessConfig, description="Timeliness checks"
    )


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    output_format: list[str] = Field(
        default=["html", "json"], description="Output formats"
    )
    output_directory: str = Field(
        default="reports", description="Output directory for reports"
    )
    include_remediation: bool = Field(
        default=True, description="Include remediation plans in reports"
    )
    scorecard_template: str = Field(
        default="templates/scorecard.html", description="Scorecard template path"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file: str = Field(default="logs/data_quality.log", description="Log file path")
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

    primary_db_url: str = Field(..., alias="PRIMARY_DB_URL")
    secondary_db_url: Optional[str] = Field(default=None, alias="SECONDARY_DB_URL")
    app_name: str = Field(default="Data Quality Monitor", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")

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
