# Backup Monitor

Automated backup monitoring system that monitors system backups, verifies backup integrity, tests restore procedures, and generates backup health reports with failure alerts.

## Project Description

This automation system provides comprehensive backup monitoring and health management. It continuously tracks backup files, verifies their integrity using multiple methods, tests restore procedures to ensure backups are recoverable, and generates detailed health reports. The system includes an alerting mechanism to notify administrators of backup failures and issues.

### Target Audience

- System administrators managing backup infrastructure
- DevOps teams ensuring backup reliability
- IT operations teams monitoring backup health
- Organizations requiring backup compliance and verification

## Features

- **Backup Monitoring**: Automatically scans backup locations and tracks all backup files
- **Integrity Verification**: Verifies backup integrity using checksums, size validation, and timestamp checks
- **Restore Testing**: Tests restore procedures to ensure backups are recoverable
- **Health Reporting**: Generates comprehensive HTML and CSV health reports with metrics and scores
- **Failure Alerts**: Sends alerts via email, Slack, or logs for backup failures and issues
- **Multi-Location Support**: Monitors multiple backup locations with different configurations
- **Database Tracking**: Stores all backup metadata, verification results, and test outcomes
- **Health Scoring**: Calculates health scores based on success rates, verification results, and restore tests

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Access to backup locations (read permissions required)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd backup-monitor
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
DATABASE_URL=sqlite:///backup_monitor.db
APP_NAME=Backup Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to configure backup locations, verification methods, and alerting:

```yaml
backups:
  locations:
    - name: "database_backup"
      path: "/backups/database"
      type: "database"
      schedule: "daily"
      retention_days: 30
      verify_integrity: true
      test_restore: true

monitoring:
  check_interval_minutes: 60
  alert_on_failure: true
  alert_on_verification_failure: true
  alert_on_restore_failure: true
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///backup_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **backups**: Backup location configurations, verification settings, and restore testing options
- **monitoring**: Monitoring intervals and alert thresholds
- **alerts**: Alert configuration for email, Slack, and logging
- **reporting**: Report generation settings including formats and output directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Monitor Backups

Monitor all backup locations and track backup files:

```bash
python src/main.py --monitor
```

Monitor specific location:

```bash
python src/main.py --monitor --location-name "database_backup"
```

### Verify Backup Integrity

Verify integrity of all backups:

```bash
python src/main.py --verify --days 7
```

Verify specific location:

```bash
python src/main.py --verify --location-id 1 --days 7
```

### Test Restore Procedures

Test restore procedures for backups:

```bash
python src/main.py --test-restore --days 7
```

### Generate Health Report

Generate backup health report:

```bash
python src/main.py --report --days 7
```

Generate report for specific location:

```bash
python src/main.py --report --location-id 1 --days 30
```

### Check and Send Alerts

Check for failures and send alerts:

```bash
python src/main.py --check-alerts
```

### Complete Workflow

Run complete monitoring workflow:

```bash
python src/main.py --monitor --verify --test-restore --report --check-alerts
```

### Command-Line Arguments

```
--monitor              Monitor backup locations and track backups
--verify               Verify backup integrity
--test-restore         Test restore procedures
--report               Generate backup health report
--check-alerts         Check for failures and send alerts
--location-id ID       Filter by location ID
--location-name NAME   Filter by location name
--days DAYS            Number of days to analyze (default: 7)
--config PATH          Path to configuration file (default: config.yaml)
```

## Project Structure

```
backup-monitor/
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
│   ├── backup_monitor.py     # Backup monitoring
│   ├── integrity_verifier.py # Integrity verification
│   ├── restore_tester.py     # Restore testing
│   ├── health_reporter.py    # Health reporting
│   └── alert_system.py       # Alert system
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── health_report.html    # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for backups, verifications, restore tests, health metrics, and alerts
- **src/backup_monitor.py**: Scans backup locations and tracks backup files
- **src/integrity_verifier.py**: Verifies backup integrity using checksums, size validation, and timestamps
- **src/restore_tester.py**: Tests restore procedures for file and database backups
- **src/health_reporter.py**: Generates HTML and CSV health reports with metrics
- **src/alert_system.py**: Sends alerts via email, Slack, or logs
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
- Backup monitoring and scanning
- Integrity verification methods
- Restore testing procedures
- Health report generation
- Alert system functionality
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

### Permission Errors

**Problem**: Cannot access backup locations or files.

**Solutions**:
- Verify read permissions for backup location paths
- Check that backup files are accessible
- Ensure test restore location is writable
- Review file system permissions for backup directories

### No Backups Found

**Problem**: Monitoring finds no backup files.

**Solutions**:
- Verify backup location paths in `config.yaml` are correct
- Check that backup locations exist and contain files
- Ensure backup files match expected naming patterns
- Review logs for permission or access errors

### Verification Failures

**Problem**: Backup verification consistently fails.

**Solutions**:
- Check that backup files are not corrupted
- Verify checksum algorithm matches backup creation method
- Ensure backup files are not being modified after creation
- Review verification error messages in logs

### Restore Test Failures

**Problem**: Restore tests fail.

**Solutions**:
- Verify backup file formats are supported
- Check that test restore location has sufficient space
- Ensure backup files are not corrupted
- Review restore test error messages for specific issues

### Alert Not Sending

**Problem**: Alerts are not being sent.

**Solutions**:
- Verify alert configuration in `config.yaml`
- Check email SMTP settings if using email alerts
- Verify Slack webhook URL if using Slack alerts
- Review logs for alert sending errors
- Ensure alert conditions are being met

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Backup location does not exist`: Verify backup paths in configuration
- `Permission denied`: Check file system permissions for backup locations
- `Backup file does not exist`: Backup may have been deleted or moved

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

## Backup Verification Methods

The system supports multiple verification methods:

1. **Checksum Verification**: Calculates and compares file checksums (SHA256, MD5, etc.)
2. **Size Validation**: Verifies backup file size matches stored size
3. **Timestamp Validation**: Checks backup file modification timestamp

## Restore Testing

Restore testing supports:

- **File Backups**: Extracts archives (ZIP, TAR, TAR.GZ) and validates contents
- **Database Backups**: Validates SQL files and database dump formats
- **Custom Formats**: Extensible for additional backup types

## Health Scoring

Health scores are calculated using:

- **Backup Success Rate** (50% weight): Percentage of successful backups
- **Verification Success Rate** (30% weight): Percentage of passed verifications
- **Restore Test Success Rate** (20% weight): Percentage of successful restore tests

Scores range from 0.0 to 1.0:
- **0.8-1.0**: Good (green)
- **0.5-0.8**: Warning (yellow)
- **0.0-0.5**: Critical (red)

## Alert Types

The system generates alerts for:

- **Backup Failures**: When backups fail to complete
- **Verification Failures**: When integrity verification fails
- **Restore Failures**: When restore tests fail
- **Health Degradation**: When health scores drop below thresholds

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
