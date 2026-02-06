"""Payment Processor Monitor.

Monitors customer payment processing, identifies failed payments, sends retry
reminders, and generates payment analytics with revenue forecasting.
"""

import json
import logging
import smtplib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from enum import Enum
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


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class FailureReason(str, Enum):
    """Common payment failure reasons."""

    INSUFFICIENT_FUNDS = "insufficient_funds"
    EXPIRED_CARD = "expired_card"
    DECLINED = "declined"
    NETWORK_ERROR = "network_error"
    INVALID_CARD = "invalid_card"
    FRAUD_DETECTED = "fraud_detected"
    UNKNOWN = "unknown"


class PaymentDataConfig(BaseModel):
    """Configuration for payment data source."""

    file_path: str = Field(..., description="Path to payment data file")
    format: str = Field(default="csv", description="File format: csv or json")
    payment_id_column: str = Field(
        default="payment_id", description="Column name for payment ID"
    )
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    amount_column: str = Field(
        default="amount", description="Column name for payment amount"
    )
    status_column: str = Field(
        default="status", description="Column name for payment status"
    )
    timestamp_column: str = Field(
        default="timestamp", description="Column name for payment timestamp"
    )
    failure_reason_column: Optional[str] = Field(
        default=None, description="Column name for failure reason"
    )
    retry_count_column: Optional[str] = Field(
        default=None, description="Column name for retry count"
    )


class RetryConfig(BaseModel):
    """Configuration for retry reminders."""

    enabled: bool = Field(
        default=True, description="Enable retry reminder notifications"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retry attempts"
    )
    retry_delay_days: int = Field(
        default=3, description="Days to wait before retry reminder"
    )
    reminder_template: str = Field(
        default="Your payment of {amount} {currency} failed. Please update your payment method.",
        description="Reminder message template",
    )


class NotificationConfig(BaseModel):
    """Configuration for email notifications."""

    enabled: bool = Field(
        default=True, description="Enable email notifications"
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
    customer_email_column: Optional[str] = Field(
        default=None, description="Column name for customer email in data"
    )


class ForecastingConfig(BaseModel):
    """Configuration for revenue forecasting."""

    forecast_days: int = Field(
        default=30, description="Number of days to forecast ahead"
    )
    lookback_days: int = Field(
        default=90, description="Days of historical data to use"
    )
    method: str = Field(
        default="moving_average",
        description="Forecasting method: moving_average or trend",
    )


class AnalyticsConfig(BaseModel):
    """Configuration for analytics generation."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    output_path: str = Field(
        default="logs/payment_analytics.md",
        description="Path for analytics report",
    )


class Config(BaseModel):
    """Main configuration model."""

    payment_data: PaymentDataConfig = Field(
        ..., description="Payment data source configuration"
    )
    customer_data_file: Optional[str] = Field(
        default=None, description="Path to customer data file for email lookup"
    )
    retry: RetryConfig = Field(
        default_factory=RetryConfig, description="Retry reminder settings"
    )
    notification: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification settings",
    )
    forecasting: ForecastingConfig = Field(
        default_factory=ForecastingConfig,
        description="Revenue forecasting settings",
    )
    analytics: AnalyticsConfig = Field(
        default_factory=AnalyticsConfig,
        description="Analytics generation settings",
    )
    failed_payments_output: str = Field(
        default="logs/failed_payments.json",
        description="Path to save failed payments list",
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
class PaymentRecord:
    """Represents a payment record."""

    payment_id: str
    customer_id: str
    amount: float
    status: PaymentStatus
    timestamp: datetime
    failure_reason: Optional[FailureReason] = None
    retry_count: int = 0
    currency: str = "USD"


@dataclass
class FailedPayment:
    """Represents a failed payment requiring attention."""

    payment_id: str
    customer_id: str
    amount: float
    failure_reason: Optional[FailureReason]
    timestamp: datetime
    retry_count: int
    days_since_failure: int
    requires_reminder: bool


@dataclass
class PaymentAnalytics:
    """Payment analytics summary."""

    total_payments: int
    successful_payments: int
    failed_payments: int
    success_rate: float
    total_revenue: float
    failed_revenue: float
    avg_payment_amount: float
    failure_reasons: Dict[str, int]
    daily_trends: Dict[str, Dict[str, float]]
    revenue_forecast: List[Dict[str, any]]


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


def load_payment_data(
    config: PaymentDataConfig, project_root: Path
) -> List[PaymentRecord]:
    """Load payment data from CSV or JSON file.

    Args:
        config: Payment data configuration
        project_root: Project root directory

    Returns:
        List of PaymentRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Payment data file not found: {data_path}")

    payments = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.payment_id_column,
            config.customer_id_column,
            config.amount_column,
            config.status_column,
            config.timestamp_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(df[config.timestamp_column])

        for _, row in df.iterrows():
            status_str = str(row[config.status_column]).lower()
            try:
                status = PaymentStatus(status_str)
            except ValueError:
                logger.warning(f"Unknown payment status: {status_str}")
                continue

            failure_reason = None
            if config.failure_reason_column and config.failure_reason_column in df.columns:
                if pd.notna(row[config.failure_reason_column]):
                    try:
                        failure_reason = FailureReason(
                            str(row[config.failure_reason_column]).lower()
                        )
                    except ValueError:
                        failure_reason = FailureReason.UNKNOWN

            retry_count = 0
            if config.retry_count_column and config.retry_count_column in df.columns:
                if pd.notna(row[config.retry_count_column]):
                    retry_count = int(row[config.retry_count_column])

            payment = PaymentRecord(
                payment_id=str(row[config.payment_id_column]),
                customer_id=str(row[config.customer_id_column]),
                amount=float(row[config.amount_column]),
                status=status,
                timestamp=row[config.timestamp_column],
                failure_reason=failure_reason,
                retry_count=retry_count,
            )
            payments.append(payment)

        logger.info(f"Loaded {len(payments)} payment records")
        return payments

    except pd.errors.EmptyDataError:
        logger.warning(f"Payment data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load payment data: {e}")
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


def identify_failed_payments(
    payments: List[PaymentRecord], retry_config: RetryConfig
) -> List[FailedPayment]:
    """Identify failed payments requiring attention.

    Args:
        payments: List of payment records
        config: Retry configuration

    Returns:
        List of failed payments requiring reminders
    """
    failed_payments = []
    now = datetime.now()

    for payment in payments:
        if payment.status != PaymentStatus.FAILED:
            continue

        days_since_failure = (now - payment.timestamp).days
        requires_reminder = (
            payment.retry_count < retry_config.max_retries
            and days_since_failure >= retry_config.retry_delay_days
        )

        failed_payment = FailedPayment(
            payment_id=payment.payment_id,
            customer_id=payment.customer_id,
            amount=payment.amount,
            failure_reason=payment.failure_reason,
            timestamp=payment.timestamp,
            retry_count=payment.retry_count,
            days_since_failure=days_since_failure,
            requires_reminder=requires_reminder,
        )
        failed_payments.append(failed_payment)

    logger.info(f"Identified {len(failed_payments)} failed payments")
    return failed_payments


def send_retry_reminder(
    failed_payment: FailedPayment,
    customer_email: str,
    config: NotificationConfig,
    retry_config: RetryConfig,
) -> bool:
    """Send retry reminder email to customer.

    Args:
        failed_payment: Failed payment record
        customer_email: Customer email address
        config: Notification configuration
        retry_config: Retry configuration

    Returns:
        True if email sent successfully, False otherwise
    """
    if not config.enabled or not config.smtp_server:
        logger.debug("Notifications disabled or SMTP not configured")
        return False

    message_body = retry_config.reminder_template.format(
        amount=f"{failed_payment.amount:.2f}",
        currency="USD",
    )

    message_body += f"\n\nPayment ID: {failed_payment.payment_id}\n"
    message_body += f"Failure Date: {failed_payment.timestamp.strftime('%Y-%m-%d')}\n"

    if failed_payment.failure_reason:
        reason_text = failed_payment.failure_reason.value.replace("_", " ").title()
        message_body += f"Reason: {reason_text}\n"

    message_body += "\nPlease update your payment method to continue service."

    subject = f"Payment Failed - Action Required (Payment ID: {failed_payment.payment_id})"

    try:
        msg = MIMEText(message_body)
        msg["Subject"] = subject
        msg["From"] = config.from_email or config.smtp_username
        msg["To"] = customer_email

        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            if config.smtp_username and config.smtp_password:
                server.login(config.smtp_username, config.smtp_password)
            server.send_message(msg)

        logger.info(
            f"Retry reminder sent to {customer_email} for payment {failed_payment.payment_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send reminder to {customer_email}: {e}")
        return False


def calculate_analytics(
    payments: List[PaymentRecord],
    forecasting_config: ForecastingConfig,
) -> PaymentAnalytics:
    """Calculate payment analytics and generate forecast.

    Args:
        payments: List of payment records
        forecasting_config: Forecasting configuration

    Returns:
        PaymentAnalytics object with analytics data
    """
    if not payments:
        return PaymentAnalytics(
            total_payments=0,
            successful_payments=0,
            failed_payments=0,
            success_rate=0.0,
            total_revenue=0.0,
            failed_revenue=0.0,
            avg_payment_amount=0.0,
            failure_reasons={},
            daily_trends={},
            revenue_forecast=[],
        )

    total_payments = len(payments)
    successful_payments = sum(
        1 for p in payments if p.status == PaymentStatus.SUCCESS
    )
    failed_payments = sum(
        1 for p in payments if p.status == PaymentStatus.FAILED
    )
    success_rate = (
        successful_payments / total_payments if total_payments > 0 else 0.0
    )

    total_revenue = sum(
        p.amount for p in payments if p.status == PaymentStatus.SUCCESS
    )
    failed_revenue = sum(
        p.amount for p in payments if p.status == PaymentStatus.FAILED
    )
    avg_payment_amount = (
        sum(p.amount for p in payments) / total_payments
        if total_payments > 0
        else 0.0
    )

    failure_reasons = defaultdict(int)
    for payment in payments:
        if payment.status == PaymentStatus.FAILED:
            reason = (
                payment.failure_reason.value
                if payment.failure_reason
                else FailureReason.UNKNOWN.value
            )
            failure_reasons[reason] += 1

    cutoff_date = datetime.now() - timedelta(days=forecasting_config.lookback_days)
    recent_payments = [
        p for p in payments if p.timestamp >= cutoff_date
    ]

    daily_revenue = defaultdict(float)
    daily_counts = defaultdict(int)
    for payment in recent_payments:
        date_key = payment.timestamp.strftime("%Y-%m-%d")
        if payment.status == PaymentStatus.SUCCESS:
            daily_revenue[date_key] += payment.amount
        daily_counts[date_key] += 1

    daily_trends = {}
    for date_key in sorted(daily_revenue.keys()):
        daily_trends[date_key] = {
            "revenue": daily_revenue[date_key],
            "payment_count": daily_counts[date_key],
        }

    revenue_forecast = []
    if daily_trends and forecasting_config.method == "moving_average":
        recent_revenues = list(daily_revenue.values())
        if recent_revenues:
            avg_daily_revenue = sum(recent_revenues[-7:]) / min(7, len(recent_revenues))

            forecast_date = datetime.now()
            for _ in range(forecasting_config.forecast_days):
                forecast_date += timedelta(days=1)
                revenue_forecast.append(
                    {
                        "date": forecast_date.strftime("%Y-%m-%d"),
                        "forecasted_revenue": avg_daily_revenue,
                        "method": "moving_average",
                    }
                )

    elif daily_trends and forecasting_config.method == "trend":
        sorted_dates = sorted(daily_revenue.keys())
        if len(sorted_dates) >= 2:
            recent_revenues = [daily_revenue[d] for d in sorted_dates[-7:]]
            if len(recent_revenues) >= 2:
                trend = (recent_revenues[-1] - recent_revenues[0]) / len(recent_revenues)

                forecast_date = datetime.now()
                base_revenue = recent_revenues[-1] if recent_revenues else 0.0
                for i in range(forecasting_config.forecast_days):
                    forecast_date += timedelta(days=1)
                    forecasted = base_revenue + (trend * (i + 1))
                    revenue_forecast.append(
                        {
                            "date": forecast_date.strftime("%Y-%m-%d"),
                            "forecasted_revenue": max(0.0, forecasted),
                            "method": "trend",
                        }
                    )

    return PaymentAnalytics(
        total_payments=total_payments,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        success_rate=success_rate,
        total_revenue=total_revenue,
        failed_revenue=failed_revenue,
        avg_payment_amount=avg_payment_amount,
        failure_reasons=dict(failure_reasons),
        daily_trends=daily_trends,
        revenue_forecast=revenue_forecast,
    )


def write_analytics_report(
    analytics: PaymentAnalytics, output_path: Path
) -> None:
    """Write payment analytics report to markdown file.

    Args:
        analytics: Payment analytics data
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Payment Processing Analytics Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total Payments:** {analytics.total_payments}\n")
        f.write(f"- **Successful Payments:** {analytics.successful_payments}\n")
        f.write(f"- **Failed Payments:** {analytics.failed_payments}\n")
        f.write(f"- **Success Rate:** {analytics.success_rate:.1%}\n")
        f.write(f"- **Total Revenue:** ${analytics.total_revenue:,.2f}\n")
        f.write(f"- **Failed Revenue:** ${analytics.failed_revenue:,.2f}\n")
        f.write(f"- **Average Payment Amount:** ${analytics.avg_payment_amount:.2f}\n")
        f.write("\n")

        f.write("## Failure Reasons Breakdown\n\n")
        if analytics.failure_reasons:
            f.write("| Reason | Count |\n")
            f.write("|--------|-------|\n")
            for reason, count in sorted(
                analytics.failure_reasons.items(), key=lambda x: -x[1]
            ):
                reason_display = reason.replace("_", " ").title()
                f.write(f"| {reason_display} | {count} |\n")
        else:
            f.write("No failed payments.\n")
        f.write("\n")

        f.write("## Revenue Forecast\n\n")
        if analytics.revenue_forecast:
            total_forecast = sum(
                f["forecasted_revenue"] for f in analytics.revenue_forecast
            )
            f.write(f"**Forecast Period:** {len(analytics.revenue_forecast)} days\n")
            f.write(f"**Total Forecasted Revenue:** ${total_forecast:,.2f}\n")
            f.write(f"**Average Daily Forecast:** ${total_forecast / len(analytics.revenue_forecast):,.2f}\n\n")

            f.write("| Date | Forecasted Revenue | Method |\n")
            f.write("|------|-------------------|--------|\n")
            for forecast in analytics.revenue_forecast[:30]:
                f.write(
                    f"| {forecast['date']} | "
                    f"${forecast['forecasted_revenue']:,.2f} | "
                    f"{forecast['method']} |\n"
                )
        else:
            f.write("Insufficient data for revenue forecasting.\n")

    logger.info(f"Analytics report written to {output_path}")


def process_payments(config_path: Path) -> Dict[str, any]:
    """Process payment data and generate analytics.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary with processing results

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    payments = load_payment_data(config.payment_data, project_root)

    if not payments:
        logger.warning("No payment data available for processing")
        return {
            "failed_payments": [],
            "reminders_sent": 0,
            "analytics": None,
        }

    failed_payments = identify_failed_payments(payments, config.retry)

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

    reminders_sent = 0
    for failed_payment in failed_payments:
        if failed_payment.requires_reminder:
            customer_id = failed_payment.customer_id
            if customer_id in customer_emails:
                if send_retry_reminder(
                    failed_payment,
                    customer_emails[customer_id],
                    notification_config,
                    config.retry,
                ):
                    reminders_sent += 1

    analytics = calculate_analytics(payments, config.forecasting)

    analytics_path = Path(config.analytics.output_path)
    if not analytics_path.is_absolute():
        analytics_path = project_root / analytics_path

    write_analytics_report(analytics, analytics_path)

    failed_output = Path(config.failed_payments_output)
    if not failed_output.is_absolute():
        failed_output = project_root / failed_output

    failed_output.parent.mkdir(parents=True, exist_ok=True)
    failed_data = [
        {
            "payment_id": fp.payment_id,
            "customer_id": fp.customer_id,
            "amount": fp.amount,
            "failure_reason": (
                fp.failure_reason.value if fp.failure_reason else None
            ),
            "timestamp": fp.timestamp.isoformat(),
            "retry_count": fp.retry_count,
            "days_since_failure": fp.days_since_failure,
            "requires_reminder": fp.requires_reminder,
        }
        for fp in failed_payments
    ]

    with open(failed_output, "w", encoding="utf-8") as f:
        json.dump(failed_data, f, indent=2)

    logger.info(f"Failed payments saved to {failed_output}")

    return {
        "failed_payments": failed_payments,
        "reminders_sent": reminders_sent,
        "analytics": analytics,
    }


def main() -> None:
    """Main entry point for the payment processor monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting payment processing monitor")
        results = process_payments(config_path)
        logger.info(
            f"Processing complete. Identified {len(results['failed_payments'])} "
            f"failed payments, sent {results['reminders_sent']} reminders."
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
