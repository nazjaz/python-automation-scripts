"""Configuration management for license monitoring."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LicenseSourceConfig(BaseModel):
    """License source configuration."""

    name: str = Field(..., description="Source identifier")
    type: str = Field(..., description="Source type (ldap, api, csv)")
    enabled: bool = Field(default=True, description="Whether source is enabled")
    connection_string: Optional[str] = Field(
        default=None, description="Connection string for source"
    )
    api_url: Optional[str] = Field(default=None, description="API URL")
    api_key: Optional[str] = Field(default=None, description="API key")
    file_path: Optional[str] = Field(default=None, description="File path for CSV")
    sync_interval_hours: int = Field(
        default=24, description="Sync interval in hours"
    )


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    compliance_check_interval_hours: int = Field(
        default=24, description="Compliance check interval"
    )
    usage_tracking_interval_hours: int = Field(
        default=6, description="Usage tracking interval"
    )
    unused_license_threshold_days: int = Field(
        default=90, description="Days of inactivity to mark as unused"
    )
    compliance_threshold_percentage: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Minimum compliance percentage"
    )


class LicenseTypeConfig(BaseModel):
    """License type configuration."""

    name: str = Field(..., description="License type name")
    category: str = Field(..., description="License category")
    cost_per_license: float = Field(..., description="Cost per license")
    currency: str = Field(default="USD", description="Currency")
    compliance_required: bool = Field(
        default=True, description="Whether compliance is required"
    )


class OptimizationConfig(BaseModel):
    """Optimization configuration."""

    identify_unused: bool = Field(
        default=True, description="Identify unused licenses"
    )
    identify_over_licensed: bool = Field(
        default=True, description="Identify over-licensed scenarios"
    )
    cost_savings_threshold: float = Field(
        default=100.00, description="Minimum cost savings to report"
    )
    recommend_downgrades: bool = Field(
        default=True, description="Recommend license downgrades"
    )


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    output_format: list[str] = Field(
        default=["html", "json"], description="Output formats"
    )
    output_directory: str = Field(
        default="reports", description="Output directory"
    )
    include_cost_analysis: bool = Field(
        default=True, description="Include cost analysis in reports"
    )
    include_compliance_status: bool = Field(
        default=True, description="Include compliance status"
    )
    include_optimization_recommendations: bool = Field(
        default=True, description="Include optimization recommendations"
    )
    report_template: str = Field(
        default="templates/license_report.html", description="Report template path"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file: str = Field(
        default="logs/license_monitor.log", description="Log file path"
    )
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

    ad_connection_string: Optional[str] = Field(
        default=None, alias="AD_CONNECTION_STRING"
    )
    snow_api_url: Optional[str] = Field(default=None, alias="SNOW_API_URL")
    snow_api_key: Optional[str] = Field(default=None, alias="SNOW_API_KEY")
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")
    app_name: str = Field(default="License Monitor", alias="APP_NAME")
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
