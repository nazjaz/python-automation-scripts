# Data Pipeline Monitor

Automated data pipeline monitoring system that monitors pipeline health, detects failures, identifies data quality issues, and automatically triggers remediation workflows with alerting.

## Project Description

This automation system provides comprehensive monitoring and management for data pipelines. The system continuously monitors pipeline health, automatically detects failures, performs data quality checks, triggers remediation workflows, and sends alerts to notify teams of issues. This helps data engineering teams maintain reliable data pipelines and quickly respond to issues.

### Target Audience

- Data engineers monitoring ETL/ELT pipelines
- DevOps engineers managing data infrastructure
- Data quality teams ensuring data reliability
- Platform engineers maintaining data platforms
- Data operations teams managing pipeline reliability

## Features

- **Pipeline Health Monitoring**: Continuously monitors pipeline health status and calculates success rates
- **Failure Detection**: Automatically detects pipeline failures and categorizes them by type and severity
- **Data Quality Checks**: Performs comprehensive data quality checks including completeness, validity, consistency, and accuracy
- **Automatic Remediation**: Triggers remediation workflows automatically when failures are detected
- **Alerting System**: Sends alerts through multiple channels (email, Slack, webhooks) based on severity
- **Comprehensive Reporting**: Generates HTML and CSV reports with pipeline metrics, failures, and quality issues
- **Database Persistence**: Stores all pipeline data, runs, failures, quality checks, and alerts in SQLite database
- **Flexible Configuration**: Customizable monitoring thresholds, quality check rules, remediation workflows, and alerting channels
- **Multi-Pipeline Support**: Monitors multiple pipelines simultaneously with individual health tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd data-pipeline-monitor
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
DATABASE_URL=sqlite:///pipeline_monitor.db
APP_NAME=Data Pipeline Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize monitoring thresholds, quality checks, remediation workflows, and alerting:

```yaml
monitoring:
  degraded_threshold: 0.8
  unhealthy_threshold: 0.5

quality_checks:
  quality_checks:
    completeness:
      threshold: 0.95
      required_fields: ["id", "timestamp"]
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///pipeline_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **monitoring**: Health monitoring settings including thresholds and check intervals
- **failure_detection**: Failure detection patterns and severity rules
- **quality_checks**: Data quality check configurations including thresholds and validation rules
- **remediation**: Remediation workflow templates for different failure types
- **alerting**: Alert channel configurations and severity rules
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Monitor Pipeline Health

Monitor health of all pipelines or a specific pipeline:

```bash
python src/main.py --monitor
python src/main.py --monitor --pipeline-id 1
```

### Detect Failures

Detect failures in pipeline runs:

```bash
python src/main.py --detect-failures --hours 24
python src/main.py --detect-failures --pipeline-id 1 --hours 1
```

### Check Data Quality

Run data quality checks for a pipeline:

```bash
python src/main.py --check-quality 1
```

### Trigger Remediation

Trigger remediation workflow for a failure:

```bash
python src/main.py --remediate 1 --failure-id 5
```

Auto-remediate all open failures:

```bash
python src/main.py --auto-remediate --pipeline-id 1
```

### Send Alerts

Send alerts for detected issues:

```bash
python src/main.py --alert --pipeline-id 1
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --pipeline-id 1
```

### Complete Workflow

Run complete monitoring workflow:

```bash
python src/main.py --monitor --detect-failures --check-quality 1 --auto-remediate --alert --report
```

### Command-Line Arguments

```
--monitor              Monitor pipeline health
--detect-failures      Detect pipeline failures
--check-quality ID     Check data quality for pipeline
--remediate ID         Trigger remediation workflow
--auto-remediate       Auto-remediate all open failures
--alert                Send alerts for issues
--report               Generate analysis reports
--pipeline-id ID       Filter by pipeline ID
--failure-id ID        Failure ID for remediation
--hours HOURS           Number of hours to analyze (default: 1)
--config PATH          Path to configuration file (default: config.yaml)
```

## Project Structure

```
data-pipeline-monitor/
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
│   ├── pipeline_monitor.py   # Pipeline health monitoring
│   ├── failure_detector.py   # Failure detection
│   ├── data_quality_checker.py # Data quality checks
│   ├── remediation_workflow.py # Remediation workflows
│   ├── alerting.py           # Alerting system
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── pipeline_report.html  # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates monitoring, failure detection, quality checks, remediation, alerting, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for pipelines, runs, failures, quality checks, remediation workflows, alerts, and health metrics
- **src/pipeline_monitor.py**: Monitors pipeline health and calculates metrics
- **src/failure_detector.py**: Detects and categorizes pipeline failures
- **src/data_quality_checker.py**: Performs data quality checks with configurable rules
- **src/remediation_workflow.py**: Executes remediation workflows for failures
- **src/alerting.py**: Sends alerts through multiple channels based on severity
- **src/report_generator.py**: Generates HTML and CSV reports with monitoring data
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

- Pipeline health monitoring functionality
- Failure detection algorithms
- Data quality check logic
- Remediation workflow execution
- Alerting system
- Report generation (HTML and CSV)
- Database operations and models
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

### No Failures Detected

**Problem**: Failure detection returns no results even when failures exist.

**Solutions**:
- Verify pipeline runs have status "failed"
- Check that error messages are present in failed runs
- Review failure patterns in `config.yaml` match actual error messages
- Ensure time window (--hours) includes the failure time
- Check that pipeline runs are properly recorded in database

### Quality Checks Not Running

**Problem**: Quality checks are not executing or returning incorrect results.

**Solutions**:
- Verify quality check configuration in `config.yaml`
- Ensure data sample format matches expected structure
- Check that required fields are present in data sample
- Review quality check thresholds and validation rules
- Ensure pipeline ID is correct

### Remediation Not Triggering

**Problem**: Remediation workflows are not being triggered.

**Solutions**:
- Verify remediation workflow templates exist in `config.yaml`
- Check that failure types match workflow template keys
- Ensure pipeline ID and failure ID are correct
- Review remediation workflow steps configuration
- Check logs for remediation execution errors

### Alerts Not Sending

**Problem**: Alerts are not being sent to configured channels.

**Solutions**:
- Verify alert channel configuration in `config.yaml`
- Check that alert channels are enabled (email_enabled, slack_enabled, etc.)
- Ensure alert severity meets minimum threshold
- Review alert channel credentials and configuration
- Check logs for alert sending errors
- Note: Email, Slack, and webhook integrations require additional setup (not included by default)

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient pipeline data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Pipeline not found`: Verify pipeline ID is correct and pipeline exists
- `No failures detected`: Check that failed pipeline runs exist in the specified time window
- `Template not found`: HTML template file missing, system will use default template

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

## Failure Types

The system detects and categorizes various failure types:

- **timeout**: Pipeline execution timeouts
- **connection**: Connection and network errors
- **validation**: Data validation errors
- **data_error**: Data corruption or missing data errors

Failure types can be customized in `config.yaml` by adding new patterns and severity rules.

## Remediation Workflows

The system supports various remediation workflow types:

- **retry**: Retry failed pipeline execution
- **restart**: Restart pipeline service
- **rollback**: Rollback to previous pipeline state
- **skip**: Skip failed records and continue
- **notify**: Notify team about failure

Remediation workflows can be customized in `config.yaml` with custom steps and actions.

## Alert Channels

The system supports multiple alert channels:

- **email**: Email notifications (requires SMTP configuration)
- **slack**: Slack webhook notifications (requires Slack webhook URL)
- **webhook**: Generic webhook notifications (requires webhook URL)
- **log**: Log-based alerts (always enabled)

Alert channels can be configured per severity level in `config.yaml`.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
