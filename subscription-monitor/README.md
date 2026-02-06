# Subscription Monitor

Automated subscription monitoring system that monitors customer subscription renewals, identifies churn risks, triggers retention campaigns, and tracks subscription lifecycle metrics.

## Project Description

This automation system provides comprehensive subscription management and monitoring capabilities. It continuously monitors subscription renewals, analyzes customer behavior to identify churn risks, automatically triggers retention campaigns for at-risk customers, and tracks key subscription metrics to help businesses maintain healthy customer relationships and reduce churn.

### Target Audience

- SaaS companies managing subscription-based services
- Subscription businesses monitoring customer retention
- Customer success teams tracking subscription health
- Business analysts monitoring subscription metrics

## Features

- **Renewal Monitoring**: Continuously monitors subscription renewals with configurable look-ahead windows
- **Churn Risk Detection**: Identifies customers at risk of churning based on multiple factors
- **Retention Campaigns**: Automatically triggers retention campaigns for at-risk customers
- **Lifecycle Metrics**: Tracks key subscription metrics (MRR, ARR, churn rate, renewal rate, LTV)
- **Payment Failure Tracking**: Monitors and tracks payment failures
- **Multi-Campaign Support**: Supports multiple campaign types (email discount, engagement, phone call, loyalty rewards)
- **Risk Scoring**: Calculates churn risk scores with detailed factor analysis
- **Multi-Format Reports**: Generates HTML and CSV subscription monitoring reports

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd subscription-monitor
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=sqlite:///subscription_monitor.db
APP_NAME=Subscription Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize monitoring intervals, churn detection thresholds, and campaign settings:

```yaml
monitoring:
  check_interval_hours: 24
  renewal_check_days_ahead: 30

churn_detection:
  risk_factors:
    payment_failures: 2
    engagement_score_threshold: 0.3
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///subscription_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **monitoring**: Check intervals, renewal look-ahead windows, batch sizes
- **churn_detection**: Risk factors, thresholds, risk level definitions
- **retention**: Campaign types, trigger conditions, email templates
- **subscription**: Status values, billing cycles, auto-renewal settings
- **metrics**: Metrics to track, calculation windows, cohort analysis
- **reporting**: Output formats, directory, inclusion options
- **logging**: Log file location, rotation, and format settings

## Usage

### Check Renewals

Check subscriptions due for renewal:

```bash
python src/main.py --check-renewals --days-ahead 30
```

### Detect Churn Risks

Detect churn risks for all customers:

```bash
python src/main.py --detect-churn
```

Detect churn risk for specific customer:

```bash
python src/main.py --detect-churn --customer-id 1
```

### Trigger Retention Campaigns

Trigger retention campaigns:

```bash
python src/main.py --trigger-campaigns
```

### Track Metrics

Track subscription lifecycle metrics:

```bash
python src/main.py --track-metrics
```

### Generate Report

Generate subscription monitoring report:

```bash
python src/main.py --generate-report --format html
```

### Complete Workflow

Run complete monitoring workflow:

```bash
# Check renewals
python src/main.py --check-renewals

# Detect churn risks
python src/main.py --detect-churn

# Trigger campaigns for at-risk customers
python src/main.py --trigger-campaigns

# Track metrics
python src/main.py --track-metrics

# Generate report
python src/main.py --generate-report
```

### Command-Line Arguments

```
--check-renewals          Check subscriptions due for renewal
--days-ahead DAYS         Days ahead to check (default: 30)

--detect-churn            Detect churn risks
--customer-id ID          Optional customer ID filter

--trigger-campaigns       Trigger retention campaigns
--customer-id ID          Optional customer ID filter

--track-metrics           Track subscription lifecycle metrics

--generate-report         Generate subscription monitoring report
--format FORMAT           Report format: html or csv (default: html)

--config PATH             Path to configuration file (default: config.yaml)
```

## Project Structure

```
subscription-monitor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Application configuration
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # Database models and operations
│   ├── renewal_monitor.py    # Renewal monitoring
│   ├── churn_detector.py     # Churn risk detection
│   ├── campaign_trigger.py   # Retention campaign triggering
│   ├── metrics_tracker.py    # Subscription metrics tracking
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── subscription_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for customers, subscriptions, renewals, churn risks, campaigns, metrics
- **src/renewal_monitor.py**: Monitors subscription renewals and identifies upcoming renewals
- **src/churn_detector.py**: Analyzes customer behavior to detect churn risks
- **src/campaign_trigger.py**: Triggers retention campaigns based on risk factors
- **src/metrics_tracker.py**: Tracks subscription lifecycle metrics (MRR, ARR, churn rate, etc.)
- **src/report_generator.py**: Generates HTML and CSV subscription monitoring reports
- **tests/test_main.py**: Comprehensive unit tests with mocking

## Testing

### Run Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage and includes:

- Database operations and models
- Renewal monitoring functionality
- Churn risk detection algorithms
- Campaign triggering logic
- Metrics calculation
- Report generation
- Configuration loading and validation

## Troubleshooting

### Database Errors

**Problem**: Database connection or operation errors.

**Solutions**:
- Ensure SQLite is available (included with Python)
- Check file permissions for database file location
- Verify `DATABASE_URL` in `.env` is correctly formatted
- Delete existing database file to recreate schema if needed

### Configuration Errors

**Problem**: Configuration file not found or invalid.

**Solutions**:
- Ensure `config.yaml` exists in project root directory
- Validate YAML syntax using an online YAML validator
- Check that all required configuration sections are present
- Review error messages in logs for specific validation issues

### Renewal Monitoring Issues

**Problem**: Renewals not being detected or processed.

**Solutions**:
- Verify subscription renewal dates are set correctly
- Check date range settings in `config.yaml`
- Ensure subscriptions have valid status values
- Review logs for specific error messages

### Churn Detection Not Working

**Problem**: Churn risks not being identified.

**Solutions**:
- Verify churn detection is enabled in `config.yaml`
- Check risk factor thresholds are appropriate
- Ensure customer data is complete (subscriptions, payment history)
- Review risk level definitions in configuration
- Check logs for detection errors

### Campaigns Not Triggering

**Problem**: Retention campaigns not being triggered.

**Solutions**:
- Verify campaigns are enabled in `config.yaml`
- Check trigger conditions are configured correctly
- Ensure churn risks are being detected first
- Review campaign type definitions
- Check logs for trigger evaluation

### Metrics Calculation Errors

**Problem**: Metrics showing incorrect values.

**Solutions**:
- Verify calculation window settings
- Ensure subscription data is complete
- Check date ranges for metric calculations
- Review metric calculation logic in logs
- Verify subscription status values are correct

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Customer not found`: Verify customer ID exists in database
- `Subscription not found`: Verify subscription ID exists in database
- `Invalid campaign type`: Use one of the configured campaign types
- `Invalid risk level`: Use one of: low, medium, high, critical

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes following PEP 8 and project standards
4. Write tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Commit with conventional commit messages
7. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Use type hints for all function signatures
- Write comprehensive docstrings (Google style)
- Keep functions focused and under 50 lines
- Use meaningful variable and function names
- Include error handling and logging

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Write clear commit messages following conventional format
4. Provide description of changes and testing performed

## Churn Risk Factors

The system evaluates multiple factors to assess churn risk:

### Payment Failures

- **Threshold**: Configurable (default: 2 failures)
- **Impact**: High risk indicator
- **Action**: Triggers discount campaigns

### Engagement Score

- **Threshold**: Configurable (default: < 0.3)
- **Impact**: Medium risk indicator
- **Action**: Triggers engagement campaigns

### Days Since Last Activity

- **Threshold**: Configurable (default: > 30 days)
- **Impact**: Medium risk indicator
- **Action**: Triggers engagement campaigns

### Subscription Status

- **No Active Subscriptions**: High risk
- **Auto-Renewal Disabled**: Medium risk
- **Upcoming Renewal**: Low to medium risk

## Retention Campaigns

Supported campaign types:

- **email_discount**: Discount offers for at-risk customers
- **email_engagement**: Engagement emails to re-engage customers
- **phone_call**: Phone call campaigns (requires external integration)
- **loyalty_reward**: Loyalty rewards for retention

Campaigns are triggered by:

- **High Risk Churn**: Critical or high churn risk detected
- **Payment Failure**: Payment failures detected
- **Engagement Drop**: Low engagement score
- **Renewal Reminder**: Upcoming renewals (7-14 days)

## Subscription Metrics

The system tracks the following metrics:

### Monthly Recurring Revenue (MRR)

- Calculated from all active subscriptions
- Accounts for different billing cycles
- Tracked daily

### Annual Recurring Revenue (ARR)

- Calculated as MRR × 12
- Provides annual revenue projection
- Tracked daily

### Churn Rate

- Percentage of customers who cancelled
- Calculated over configurable window (default: 30 days)
- Tracked daily

### Renewal Rate

- Percentage of successful renewals
- Calculated over configurable window
- Tracked daily

### Customer Lifetime Value (LTV)

- Total revenue from customer over lifetime
- Calculated per customer
- Based on subscription history

## Report Features

Subscription reports include:

- **Key Metrics**: MRR, ARR, churn rate, renewal rate, active subscriptions
- **High-Risk Customers**: List of customers with high churn risk
- **Pending Campaigns**: Retention campaigns awaiting execution
- **Risk Analysis**: Detailed churn risk factors
- **Time-based Trends**: Metrics over time

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
