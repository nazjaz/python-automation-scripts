"""Configuration management for refund processing."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class RefundPolicyConfig(BaseModel):
    """Refund policy configuration."""

    max_refund_days: int = Field(
        default=90, description="Maximum days after purchase for refund"
    )
    min_refund_amount: float = Field(
        default=1.00, description="Minimum refund amount"
    )
    max_refund_amount: float = Field(
        default=10000.00, description="Maximum refund amount"
    )
    auto_approve_threshold: float = Field(
        default=50.00, description="Auto-approve refunds below this amount"
    )
    require_approval_above: float = Field(
        default=500.00, description="Require approval for refunds above this amount"
    )
    refund_reasons: list[str] = Field(
        default_factory=list, description="Allowed refund reasons"
    )
    partial_refund_allowed: bool = Field(
        default=True, description="Allow partial refunds"
    )
    restocking_fee_percentage: float = Field(
        default=0.10, description="Restocking fee percentage"
    )
    restocking_fee_minimum: float = Field(
        default=5.00, description="Minimum restocking fee"
    )


class PaymentSystemConfig(BaseModel):
    """Payment system configuration."""

    provider: str = Field(..., description="Payment provider name")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    enabled: bool = Field(default=True, description="Whether provider is enabled")


class ValidationConfig(BaseModel):
    """Validation configuration."""

    require_order_id: bool = Field(
        default=True, description="Require order ID in refund request"
    )
    require_customer_email: bool = Field(
        default=True, description="Require customer email"
    )
    validate_order_exists: bool = Field(
        default=True, description="Validate order exists"
    )
    validate_customer_match: bool = Field(
        default=True, description="Validate customer matches order"
    )
    check_duplicate_refunds: bool = Field(
        default=True, description="Check for duplicate refund requests"
    )
    max_refunds_per_order: int = Field(
        default=3, description="Maximum refunds allowed per order"
    )


class EmailConfig(BaseModel):
    """Email configuration."""

    confirmation_template: str = Field(
        default="templates/refund_confirmation.html",
        description="Refund confirmation email template",
    )
    subject: str = Field(
        default="Refund Confirmation - Order {{order_id}}",
        description="Email subject template",
    )
    from_email: str = Field(..., description="Sender email address")
    from_name: str = Field(
        default="Refund Processing Team", description="Sender display name"
    )
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay_seconds: int = Field(
        default=5, description="Delay between retries in seconds"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file: str = Field(
        default="logs/refund_processor.log", description="Log file path"
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

    stripe_api_key: str = Field(..., alias="STRIPE_API_KEY")
    stripe_secret_key: str = Field(..., alias="STRIPE_SECRET_KEY")
    paypal_client_id: Optional[str] = Field(default=None, alias="PAYPAL_CLIENT_ID")
    paypal_secret: Optional[str] = Field(default=None, alias="PAYPAL_SECRET")
    smtp_host: str = Field(..., alias="SMTP_HOST")
    smtp_port: int = Field(..., alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(..., alias="SMTP_FROM_EMAIL")
    app_name: str = Field(default="Refund Processor", alias="APP_NAME")
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
