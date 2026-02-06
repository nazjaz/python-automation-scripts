# Payment Processor Monitor

## Project Title and Description

The payment processor monitor analyzes customer payment processing data to identify
failed payments, send retry reminders, generate payment analytics, and forecast
revenue trends.

It is designed for finance teams, payment operations, and business analysts who need
to monitor payment health, reduce revenue leakage from failed payments, and forecast
future revenue based on historical payment patterns.

## Features

- **Payment Monitoring**: Track all payment transactions and their statuses.
- **Failed Payment Detection**: Automatically identify failed payments requiring
  attention.
- **Retry Reminders**: Send automated email reminders to customers with failed
  payments.
- **Payment Analytics**: Calculate success rates, revenue metrics, and failure
  reason breakdowns.
- **Revenue Forecasting**: Generate revenue forecasts using moving average or trend
  analysis methods.
- **Daily Trends**: Track daily revenue and payment count trends.
- **Markdown Reporting**: Generate comprehensive payment analytics reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to payment data files (CSV or JSON format).
  - SMTP server access for email notifications (optional).

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd payment_processor_monitor
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   - Copy `.env.example` to `.env`.
   - Configure SMTP credentials if using email notifications.

5. **Prepare data files**:

   - Ensure your payment data CSV or JSON file is available.
   - Optionally create a customer data file for email lookups.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).
  - `SMTP_USERNAME`: SMTP username for email notifications (optional).
  - `SMTP_PASSWORD`: SMTP password for email notifications (optional).

- **Config file (`config.yaml`)**:
  - `payment_data`: Configuration for payment data source:
    - `file_path`: Path to payment data file.
    - `format`: File format (`csv` or `json`).
    - `payment_id_column`: Column name for payment ID.
    - `customer_id_column`: Column name for customer ID.
    - `amount_column`: Column name for payment amount.
    - `status_column`: Column name for payment status.
    - `timestamp_column`: Column name for payment timestamp.
    - `failure_reason_column`: Column name for failure reason (optional).
    - `retry_count_column`: Column name for retry count (optional).
  - `customer_data_file`: Path to customer data file for email lookup (optional).
  - `retry`: Retry reminder settings:
    - `enabled`: Enable retry reminders.
    - `max_retries`: Maximum number of retry attempts.
    - `retry_delay_days`: Days to wait before sending reminder.
    - `reminder_template`: Email message template.
  - `notification`: Email notification settings:
    - `enabled`: Enable email notifications.
    - `smtp_server`: SMTP server address.
    - `smtp_port`: SMTP server port.
    - `smtp_username`: SMTP username.
    - `smtp_password`: SMTP password.
    - `from_email`: Sender email address.
  - `forecasting`: Revenue forecasting settings:
    - `forecast_days`: Number of days to forecast ahead.
    - `lookback_days`: Days of historical data to use.
    - `method`: Forecasting method (`moving_average` or `trend`).
  - `analytics`: Analytics report settings:
    - `output_format`: Report format (`markdown` or `html`).
    - `output_path`: Path for analytics report.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the monitor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m payment_processor_monitor.src.main
```

This will:

- Load payment data from the configured file.
- Identify failed payments requiring attention.
- Send retry reminder emails to customers (if enabled).
- Calculate payment analytics and metrics.
- Generate revenue forecasts.
- Write analytics report and failed payments list to output files.

## Project Structure

```
payment_processor_monitor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
└── logs/
    └── .gitkeep            # Placeholder for logs directory
```

## Testing

Run tests using pytest:

```bash
pytest tests/
```

Tests cover core functionality including payment loading, failed payment detection,
analytics calculation, and forecasting.

## Troubleshooting

### Common Issues

**Error: "Payment data file not found"**
- Ensure the `payment_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your payment data file contains the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**Email notifications not sending**
- Verify SMTP server settings in `config.yaml` or environment variables.
- Check that SMTP credentials are correct.
- Ensure customer email addresses are available in customer data file.

**No revenue forecast generated**
- Ensure sufficient historical data (at least 7 days recommended).
- Check that `lookback_days` in forecasting config is appropriate.
- Verify payment data includes successful payments for revenue calculation.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
