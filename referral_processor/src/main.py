"""Referral Processor.

Automatically processes customer referrals by tracking referral sources,
calculating rewards, sending thank-you messages, and generating referral
program analytics.
"""

import json
import logging
import smtplib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReferralDataConfig(BaseModel):
    """Configuration for referral data source."""

    file_path: str = Field(..., description="Path to referral data file")
    format: str = Field(default="csv", description="File format: csv or json")
    referral_id_column: str = Field(
        default="referral_id", description="Column name for referral ID"
    )
    referrer_id_column: str = Field(
        default="referrer_id", description="Column name for referrer ID"
    )
    referee_id_column: str = Field(
        default="referee_id", description="Column name for referee ID"
    )
    referral_date_column: str = Field(
        default="referral_date", description="Column name for referral date"
    )
    referral_source_column: Optional[str] = Field(
        default=None, description="Column name for referral source"
    )
    conversion_status_column: Optional[str] = Field(
        default=None, description="Column name for conversion status"
    )
    conversion_date_column: Optional[str] = Field(
        default=None, description="Column name for conversion date"
    )


class RewardConfig(BaseModel):
    """Configuration for reward calculation."""

    base_reward_amount: float = Field(
        default=10.0, description="Base reward amount for successful referral"
    )
    conversion_bonus: float = Field(
        default=25.0, description="Additional bonus for converted referrals"
    )
    reward_currency: str = Field(
        default="USD", description="Reward currency code"
    )
    min_referrals_for_bonus: int = Field(
        default=5, description="Minimum referrals for bonus tier"
    )
    bonus_multiplier: float = Field(
        default=1.5, description="Multiplier for bonus tier rewards"
    )
    require_conversion: bool = Field(
        default=True, description="Require conversion for reward eligibility"
    )


class NotificationConfig(BaseModel):
    """Configuration for thank-you messages."""

    enabled: bool = Field(
        default=True, description="Enable thank-you message notifications"
    )
    smtp_server: Optional[str] = Field(
        default=None, description="SMTP server address"
    )
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(
        default=None, description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None, description="SMTP password"
    )
    from_email: Optional[str] = Field(
        default=None, description="Sender email address"
    )
    message_template: str = Field(
        default="Thank you for your referral! You have earned {reward_amount} {currency}.",
        description="Thank-you message template",
    )


class AnalyticsConfig(BaseModel):
    """Configuration for analytics generation."""

    output_format: str = Field(
        default="markdown", description="Analytics report format"
    )
    output_path: str = Field(
        default="logs/referral_analytics.md",
        description="Path for analytics report",
    )
    include_top_referrers: int = Field(
        default=10, description="Number of top referrers to include"
    )


class Config(BaseModel):
    """Main configuration model."""

    referral_data: ReferralDataConfig = Field(
        ..., description="Referral data source configuration"
    )
    customer_data_file: Optional[str] = Field(
        default=None, description="Path to customer data file for email lookup"
    )
    reward: RewardConfig = Field(
        default_factory=RewardConfig, description="Reward calculation settings"
    )
    notification: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification settings",
    )
    analytics: AnalyticsConfig = Field(
        default_factory=AnalyticsConfig,
        description="Analytics generation settings",
    )
    rewards_output_file: str = Field(
        default="logs/rewards.json",
        description="Path to save calculated rewards",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"
    smtp_username: Optional[str] = Field(
        default=None, description="SMTP username from environment"
    )
    smtp_password: Optional[str] = Field(
        default=None, description="SMTP password from environment"
    )


@dataclass
class ReferralRecord:
    """Represents a single referral record."""

    referral_id: str
    referrer_id: str
    referee_id: str
    referral_date: datetime
    referral_source: Optional[str] = None
    conversion_status: Optional[str] = None
    conversion_date: Optional[datetime] = None


@dataclass
class RewardCalculation:
    """Reward calculation for a referrer."""

    referrer_id: str
    total_referrals: int
    converted_referrals: int
    base_reward: float
    conversion_bonus: float
    tier_bonus: float
    total_reward: float
    currency: str


@dataclass
class ReferralAnalytics:
    """Analytics data for referral program."""

    total_referrals: int
    total_referrers: int
    total_conversions: int
    conversion_rate: float
    total_rewards_paid: float
    avg_referrals_per_referrer: float
    top_referrers: List[Dict[str, any]]
    source_breakdown: Dict[str, int]
    monthly_trends: Dict[str, int]
    generated_at: datetime


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def load_referral_data(
    config: ReferralDataConfig, project_root: Path
) -> List[ReferralRecord]:
    """Load referral data from CSV or JSON file.

    Args:
        config: Referral data configuration
        project_root: Project root directory

    Returns:
        List of ReferralRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Referral data file not found: {data_path}")

    referrals = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.referral_id_column,
            config.referrer_id_column,
            config.referee_id_column,
            config.referral_date_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.referral_date_column] = pd.to_datetime(
            df[config.referral_date_column]
        )

        if (
            config.conversion_date_column
            and config.conversion_date_column in df.columns
        ):
            df[config.conversion_date_column] = pd.to_datetime(
                df[config.conversion_date_column], errors="coerce"
            )

        for _, row in df.iterrows():
            referral = ReferralRecord(
                referral_id=str(row[config.referral_id_column]),
                referrer_id=str(row[config.referrer_id_column]),
                referee_id=str(row[config.referee_id_column]),
                referral_date=row[config.referral_date_column],
                referral_source=(
                    str(row[config.referral_source_column])
                    if config.referral_source_column
                    and config.referral_source_column in df.columns
                    and pd.notna(row[config.referral_source_column])
                    else None
                ),
                conversion_status=(
                    str(row[config.conversion_status_column])
                    if config.conversion_status_column
                    and config.conversion_status_column in df.columns
                    and pd.notna(row[config.conversion_status_column])
                    else None
                ),
                conversion_date=(
                    row[config.conversion_date_column]
                    if config.conversion_date_column
                    and config.conversion_date_column in df.columns
                    and pd.notna(row[config.conversion_date_column])
                    else None
                ),
            )
            referrals.append(referral)

        logger.info(f"Loaded {len(referrals)} referrals from {data_path}")
        return referrals

    except pd.errors.EmptyDataError:
        logger.warning(f"Data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load referral data: {e}")
        raise


def load_customer_emails(
    customer_file: Optional[Path],
) -> Dict[str, str]:
    """Load customer email addresses.

    Args:
        customer_file: Path to customer data file (optional)

    Returns:
        Dictionary mapping customer_id to email address
    """
    if not customer_file or not customer_file.exists():
        return {}

    try:
        if customer_file.suffix.lower() == ".csv":
            df = pd.read_csv(customer_file)
            if "customer_id" not in df.columns or "email" not in df.columns:
                logger.warning(
                    "customer_id or email column not found in customer file"
                )
                return {}

            return {
                str(row["customer_id"]): str(row["email"])
                for _, row in df.iterrows()
                if pd.notna(row.get("email"))
            }
        elif customer_file.suffix.lower() == ".json":
            with open(customer_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return {
                    str(item.get("customer_id", "")): str(item.get("email", ""))
                    for item in data
                    if item.get("email")
                }
            elif isinstance(data, dict):
                return {
                    str(customer_id): str(email)
                    for customer_id, email in data.items()
                    if email
                }

    except Exception as e:
        logger.warning(f"Failed to load customer emails: {e}")

    return {}


def is_converted(referral: ReferralRecord, config: RewardConfig) -> bool:
    """Check if referral is considered converted.

    Args:
        referral: Referral record to check
        config: Reward configuration

    Returns:
        True if referral is converted, False otherwise
    """
    if not config.require_conversion:
        return True

    if referral.conversion_status:
        return referral.conversion_status.lower() in [
            "converted",
            "completed",
            "success",
            "yes",
            "true",
        ]

    return referral.conversion_date is not None


def calculate_rewards(
    referrals: List[ReferralRecord], config: RewardConfig
) -> Dict[str, RewardCalculation]:
    """Calculate rewards for all referrers.

    Args:
        referrals: List of referral records
        config: Reward configuration

    Returns:
        Dictionary mapping referrer_id to RewardCalculation
    """
    referrer_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "converted": 0}
    )

    for referral in referrals:
        referrer_stats[referral.referrer_id]["total"] += 1
        if is_converted(referral, config):
            referrer_stats[referral.referrer_id]["converted"] += 1

    rewards = {}

    for referrer_id, stats in referrer_stats.items():
        total_referrals = stats["total"]
        converted_referrals = stats["converted"]

        base_reward = (
            converted_referrals * config.base_reward_amount
            if config.require_conversion
            else total_referrals * config.base_reward_amount
        )

        conversion_bonus = (
            converted_referrals * config.conversion_bonus
            if converted_referrals > 0
            else 0.0
        )

        tier_bonus = 0.0
        if total_referrals >= config.min_referrals_for_bonus:
            tier_bonus = (
                base_reward * (config.bonus_multiplier - 1.0)
            )

        total_reward = base_reward + conversion_bonus + tier_bonus

        rewards[referrer_id] = RewardCalculation(
            referrer_id=referrer_id,
            total_referrals=total_referrals,
            converted_referrals=converted_referrals,
            base_reward=base_reward,
            conversion_bonus=conversion_bonus,
            tier_bonus=tier_bonus,
            total_reward=total_reward,
            currency=config.reward_currency,
        )

    logger.info(f"Calculated rewards for {len(rewards)} referrers")
    return rewards


def send_thank_you_message(
    referrer_id: str,
    reward: RewardCalculation,
    email: str,
    config: NotificationConfig,
) -> bool:
    """Send thank-you message to referrer.

    Args:
        referrer_id: Referrer identifier
        reward: Calculated reward
        email: Referrer email address
        config: Notification configuration

    Returns:
        True if message sent successfully, False otherwise
    """
    if not config.enabled or not config.smtp_server:
        logger.debug("Notifications disabled or SMTP not configured")
        return False

    message_body = config.message_template.format(
        reward_amount=f"{reward.total_reward:.2f}",
        currency=reward.currency,
    )

    message_body += f"\n\nTotal Referrals: {reward.total_referrals}\n"
    message_body += f"Converted Referrals: {reward.converted_referrals}\n"
    message_body += f"Base Reward: {reward.currency} {reward.base_reward:.2f}\n"

    if reward.conversion_bonus > 0:
        message_body += (
            f"Conversion Bonus: {reward.currency} "
            f"{reward.conversion_bonus:.2f}\n"
        )

    if reward.tier_bonus > 0:
        message_body += (
            f"Tier Bonus: {reward.currency} {reward.tier_bonus:.2f}\n"
        )

    subject = f"Thank You for Your Referrals - {reward.currency} {reward.total_reward:.2f} Reward"

    try:
        msg = MIMEText(message_body)
        msg["Subject"] = subject
        msg["From"] = config.from_email or config.smtp_username
        msg["To"] = email

        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)
            server.send_message(msg)

        logger.info(f"Thank-you message sent to {email} for referrer {referrer_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send thank-you message to {email}: {e}")
        return False


def generate_analytics(
    referrals: List[ReferralRecord],
    rewards: Dict[str, RewardCalculation],
    config: AnalyticsConfig,
) -> ReferralAnalytics:
    """Generate referral program analytics.

    Args:
        referrals: List of referral records
        rewards: Dictionary of reward calculations
        config: Analytics configuration

    Returns:
        ReferralAnalytics object with analytics data
    """
    total_referrals = len(referrals)
    total_referrers = len(rewards)

    converted_count = sum(
        1
        for r in referrals
        if is_converted(r, RewardConfig())
    )
    conversion_rate = (
        converted_count / total_referrals if total_referrals > 0 else 0.0
    )

    total_rewards_paid = sum(r.total_reward for r in rewards.values())
    avg_referrals_per_referrer = (
        total_referrals / total_referrers if total_referrers > 0 else 0.0
    )

    top_referrers_list = sorted(
        rewards.values(),
        key=lambda x: x.total_referrals,
        reverse=True,
    )[: config.include_top_referrers]

    top_referrers = [
        {
            "referrer_id": r.referrer_id,
            "total_referrals": r.total_referrals,
            "converted_referrals": r.converted_referrals,
            "total_reward": r.total_reward,
        }
        for r in top_referrers_list
    ]

    source_breakdown = defaultdict(int)
    for referral in referrals:
        source = referral.referral_source or "unknown"
        source_breakdown[source] += 1

    monthly_trends = defaultdict(int)
    for referral in referrals:
        month_key = referral.referral_date.strftime("%Y-%m")
        monthly_trends[month_key] += 1

    return ReferralAnalytics(
        total_referrals=total_referrals,
        total_referrers=total_referrers,
        total_conversions=converted_count,
        conversion_rate=conversion_rate,
        total_rewards_paid=total_rewards_paid,
        avg_referrals_per_referrer=avg_referrals_per_referrer,
        top_referrers=top_referrers,
        source_breakdown=dict(source_breakdown),
        monthly_trends=dict(monthly_trends),
        generated_at=datetime.now(),
    )


def write_analytics_report(
    analytics: ReferralAnalytics, output_path: Path
) -> None:
    """Write analytics report to markdown file.

    Args:
        analytics: Analytics data to report
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Referral Program Analytics Report\n\n")
        f.write(
            f"**Generated:** {analytics.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Summary\n\n")
        f.write(f"- **Total Referrals:** {analytics.total_referrals}\n")
        f.write(f"- **Total Referrers:** {analytics.total_referrers}\n")
        f.write(f"- **Total Conversions:** {analytics.total_conversions}\n")
        f.write(
            f"- **Conversion Rate:** {analytics.conversion_rate:.1%}\n"
        )
        f.write(
            f"- **Total Rewards Paid:** ${analytics.total_rewards_paid:,.2f}\n"
        )
        f.write(
            f"- **Avg Referrals per Referrer:** "
            f"{analytics.avg_referrals_per_referrer:.2f}\n"
        )
        f.write("\n")

        f.write("## Top Referrers\n\n")
        if analytics.top_referrers:
            f.write(
                "| Referrer ID | Total Referrals | Converted | "
                "Total Reward |\n"
            )
            f.write("|-------------|------------------|-----------|-------------|\n")
            for ref in analytics.top_referrers:
                f.write(
                    f"| {ref['referrer_id']} | {ref['total_referrals']} | "
                    f"{ref['converted_referrals']} | "
                    f"${ref['total_reward']:.2f} |\n"
                )
            f.write("\n")

        f.write("## Referral Source Breakdown\n\n")
        if analytics.source_breakdown:
            f.write("| Source | Count |\n")
            f.write("|--------|-------|\n")
            for source, count in sorted(
                analytics.source_breakdown.items(),
                key=lambda x: -x[1],
            ):
                f.write(f"| {source} | {count} |\n")
            f.write("\n")

        f.write("## Monthly Trends\n\n")
        if analytics.monthly_trends:
            f.write("| Month | Referrals |\n")
            f.write("|-------|-----------|\n")
            for month, count in sorted(analytics.monthly_trends.items()):
                f.write(f"| {month} | {count} |\n")

    logger.info(f"Analytics report written to {output_path}")


def process_referrals(config_path: Path) -> Dict[str, RewardCalculation]:
    """Process referrals and calculate rewards.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary of reward calculations

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    referrals = load_referral_data(config.referral_data, project_root)

    if not referrals:
        logger.warning("No referrals found to process")
        return {}

    rewards = calculate_rewards(referrals, config.reward)

    customer_emails = {}
    if config.customer_data_file:
        customer_file = Path(config.customer_data_file)
        if not customer_file.is_absolute():
            customer_file = project_root / customer_file
        customer_emails = load_customer_emails(customer_file)

    notification_config = config.notification
    settings = AppSettings()
    if settings.smtp_username:
        notification_config.smtp_username = settings.smtp_username
    if settings.smtp_password:
        notification_config.smtp_password = settings.smtp_password

    for referrer_id, reward in rewards.items():
        if referrer_id in customer_emails:
            send_thank_you_message(
                referrer_id, reward, customer_emails[referrer_id], notification_config
            )

    analytics = generate_analytics(referrals, rewards, config.analytics)

    analytics_path = Path(config.analytics.output_path)
    if not analytics_path.is_absolute():
        analytics_path = project_root / analytics_path

    write_analytics_report(analytics, analytics_path)

    rewards_output = Path(config.rewards_output_file)
    if not rewards_output.is_absolute():
        rewards_output = project_root / rewards_output

    rewards_output.parent.mkdir(parents=True, exist_ok=True)
    rewards_data = {
        referrer_id: {
            "referrer_id": reward.referrer_id,
            "total_referrals": reward.total_referrals,
            "converted_referrals": reward.converted_referrals,
            "base_reward": reward.base_reward,
            "conversion_bonus": reward.conversion_bonus,
            "tier_bonus": reward.tier_bonus,
            "total_reward": reward.total_reward,
            "currency": reward.currency,
        }
        for referrer_id, reward in rewards.items()
    }

    with open(rewards_output, "w", encoding="utf-8") as f:
        json.dump(rewards_data, f, indent=2)

    logger.info(f"Rewards data saved to {rewards_output}")

    return rewards


def main() -> None:
    """Main entry point for the referral processor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting referral processing")
        rewards = process_referrals(config_path)
        logger.info(
            f"Processing complete. Calculated rewards for {len(rewards)} referrers."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
