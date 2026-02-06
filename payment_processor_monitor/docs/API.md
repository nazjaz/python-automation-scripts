# Payment Processor Monitor API Documentation

## Overview

This document describes the public API for the payment processor monitoring system.

## Configuration Models

### PaymentDataConfig

Configuration for payment data source.

**Fields:**
- `file_path` (str): Path to payment data file
- `format` (str): File format (`csv` or `json`)
- `payment_id_column` (str): Column name for payment ID
- `customer_id_column` (str): Column name for customer ID
- `amount_column` (str): Column name for payment amount
- `status_column` (str): Column name for payment status
- `timestamp_column` (str): Column name for payment timestamp
- `failure_reason_column` (Optional[str]): Column name for failure reason
- `retry_count_column` (Optional[str]): Column name for retry count

### RetryConfig

Configuration for retry reminders.

**Fields:**
- `enabled` (bool): Enable retry reminder notifications
- `max_retries` (int): Maximum number of retry attempts
- `retry_delay_days` (int): Days to wait before retry reminder
- `reminder_template` (str): Reminder message template

### NotificationConfig

Configuration for email notifications.

**Fields:**
- `enabled` (bool): Enable email notifications
- `smtp_server` (Optional[str]): SMTP server address
- `smtp_port` (int): SMTP server port
- `smtp_username` (Optional[str]): SMTP username
- `smtp_password` (Optional[str]): SMTP password
- `from_email` (Optional[str]): Sender email address
- `customer_email_column` (Optional[str]): Column name for customer email

### ForecastingConfig

Configuration for revenue forecasting.

**Fields:**
- `forecast_days` (int): Number of days to forecast ahead
- `lookback_days` (int): Days of historical data to use
- `method` (str): Forecasting method (`moving_average` or `trend`)

## Data Models

### PaymentRecord

Represents a payment record.

**Fields:**
- `payment_id` (str): Unique payment identifier
- `customer_id` (str): Customer identifier
- `amount` (float): Payment amount
- `status` (PaymentStatus): Payment status
- `timestamp` (datetime): Payment timestamp
- `failure_reason` (Optional[FailureReason]): Reason for failure if failed
- `retry_count` (int): Number of retry attempts
- `currency` (str): Currency code (default: "USD")

### FailedPayment

Represents a failed payment requiring attention.

**Fields:**
- `payment_id` (str): Payment identifier
- `customer_id` (str): Customer identifier
- `amount` (float): Payment amount
- `failure_reason` (Optional[FailureReason]): Reason for failure
- `timestamp` (datetime): Failure timestamp
- `retry_count` (int): Current retry count
- `days_since_failure` (int): Days since payment failed
- `requires_reminder` (bool): Whether reminder should be sent

### PaymentAnalytics

Payment analytics summary.

**Fields:**
- `total_payments` (int): Total number of payments
- `successful_payments` (int): Number of successful payments
- `failed_payments` (int): Number of failed payments
- `success_rate` (float): Success rate (0.0 to 1.0)
- `total_revenue` (float): Total revenue from successful payments
- `failed_revenue` (float): Total amount of failed payments
- `avg_payment_amount` (float): Average payment amount
- `failure_reasons` (Dict[str, int]): Breakdown of failure reasons
- `daily_trends` (Dict[str, Dict[str, float]]): Daily revenue and count trends
- `revenue_forecast` (List[Dict[str, any]]): Revenue forecast data

## Enumerations

### PaymentStatus

Payment status enumeration.

**Values:**
- `SUCCESS`: Payment succeeded
- `FAILED`: Payment failed
- `PENDING`: Payment pending
- `REFUNDED`: Payment refunded
- `CANCELLED`: Payment cancelled

### FailureReason

Common payment failure reasons.

**Values:**
- `INSUFFICIENT_FUNDS`: Insufficient funds
- `EXPIRED_CARD`: Expired card
- `DECLINED`: Card declined
- `NETWORK_ERROR`: Network error
- `INVALID_CARD`: Invalid card details
- `FRAUD_DETECTED`: Fraud detected
- `UNKNOWN`: Unknown reason

## Functions

### load_config(config_path: Path) -> Config

Load and validate configuration from YAML file.

**Parameters:**
- `config_path` (Path): Path to configuration YAML file

**Returns:**
- `Config`: Validated configuration object

**Raises:**
- `FileNotFoundError`: If config file does not exist
- `ValueError`: If configuration is invalid

### load_payment_data(config: PaymentDataConfig, project_root: Path) -> List[PaymentRecord]

Load payment data from CSV or JSON file.

**Parameters:**
- `config` (PaymentDataConfig): Payment data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[PaymentRecord]`: List of payment records

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### identify_failed_payments(payments: List[PaymentRecord], retry_config: RetryConfig) -> List[FailedPayment]

Identify failed payments requiring attention.

**Parameters:**
- `payments` (List[PaymentRecord]): List of payment records
- `retry_config` (RetryConfig): Retry configuration

**Returns:**
- `List[FailedPayment]`: List of failed payments

### calculate_analytics(payments: List[PaymentRecord], forecasting_config: ForecastingConfig) -> PaymentAnalytics

Calculate payment analytics and generate forecast.

**Parameters:**
- `payments` (List[PaymentRecord]): List of payment records
- `forecasting_config` (ForecastingConfig): Forecasting configuration

**Returns:**
- `PaymentAnalytics`: Payment analytics object

### send_retry_reminder(failed_payment: FailedPayment, customer_email: str, config: NotificationConfig, retry_config: RetryConfig) -> bool

Send retry reminder email to customer.

**Parameters:**
- `failed_payment` (FailedPayment): Failed payment record
- `customer_email` (str): Customer email address
- `config` (NotificationConfig): Notification configuration
- `retry_config` (RetryConfig): Retry configuration

**Returns:**
- `bool`: True if email sent successfully

### process_payments(config_path: Path) -> Dict[str, any]

Process payment data and generate analytics.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `Dict[str, any]`: Dictionary with processing results

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from payment_processor_monitor.src.main import process_payments

config_path = Path("config.yaml")
results = process_payments(config_path)

print(f"Failed payments: {len(results['failed_payments'])}")
print(f"Reminders sent: {results['reminders_sent']}")

analytics = results['analytics']
if analytics:
    print(f"Success rate: {analytics.success_rate:.1%}")
    print(f"Total revenue: ${analytics.total_revenue:,.2f}")
    print(f"Forecast days: {len(analytics.revenue_forecast)}")
```
