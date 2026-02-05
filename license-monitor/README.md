# License Monitor

Automated software license monitoring system that tracks license usage, monitors compliance, identifies unused licenses, and generates optimization reports for cost reduction.

## Project Description

This automation system provides comprehensive software license management by monitoring license usage across multiple sources, tracking compliance status, identifying unused and over-licensed scenarios, and generating detailed optimization reports with cost-saving recommendations.

### Target Audience

- IT asset managers tracking software licenses
- Finance teams optimizing software costs
- Compliance officers ensuring license compliance
- IT administrators managing license inventory

## Features

- **Multi-Source License Collection**: Collects license data from LDAP/Active Directory, APIs (ServiceNow), and CSV files
- **Usage Tracking**: Tracks license usage over time with detailed statistics
- **Compliance Monitoring**: Monitors compliance status with configurable thresholds
- **Unused License Detection**: Identifies licenses unused for specified periods
- **Optimization Recommendations**: Generates cost-saving recommendations for unused and over-licensed scenarios
- **Comprehensive Reporting**: Creates HTML, JSON, and Excel reports with compliance status and optimization recommendations
- **Cost Analysis**: Calculates potential annual savings from optimization recommendations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to license data sources (LDAP, APIs, or CSV files)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd license-monitor
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
AD_CONNECTION_STRING=ldap://ad.example.com:389
SNOW_API_URL=https://your-instance.service-now.com/api
SNOW_API_KEY=your-snow-api-key
```

### Step 5: Configure Application Settings

Edit `config.yaml` to configure license sources, types, and monitoring settings:

```yaml
license_sources:
  - name: "active_directory"
    type: "ldap"
    enabled: true
    connection_string: "${AD_CONNECTION_STRING}"

license_types:
  - name: "Microsoft Office"
    category: "productivity"
    cost_per_license: 150.00
    compliance_required: true
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AD_CONNECTION_STRING` | Active Directory LDAP connection string | No |
| `SNOW_API_URL` | ServiceNow API URL | No |
| `SNOW_API_KEY` | ServiceNow API key | No |
| `SMTP_HOST` | SMTP server hostname (for email notifications) | No |
| `SMTP_PORT` | SMTP server port | No |
| `SMTP_USERNAME` | SMTP username | No |
| `SMTP_PASSWORD` | SMTP password | No |
| `SMTP_FROM_EMAIL` | Sender email address | No |

### Configuration File (config.yaml)

The `config.yaml` file contains:

- **license_sources**: List of sources to collect license data from (LDAP, API, CSV)
- **monitoring**: Compliance check intervals, usage tracking, and thresholds
- **license_types**: License type definitions with costs and compliance requirements
- **optimization**: Settings for identifying unused licenses and over-licensed scenarios
- **reporting**: Output formats, directory, and notification settings
- **database**: Database connection URL
- **logging**: Log file configuration

## Usage

### Collect Licenses

Collect licenses from all configured sources:

```bash
python src/main.py --collect
```

### Check Compliance

Check compliance status for all license types:

```bash
python src/main.py --compliance
```

### Generate Optimization Report

Generate comprehensive optimization report:

```bash
python src/main.py --report
```

### Command-Line Arguments

```
--collect          Collect licenses from all configured sources
--compliance       Check compliance status for all license types
--report           Generate optimization report with recommendations
--config PATH      Path to configuration file (optional)
```

## Project Structure

```
license-monitor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Application configuration
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and operations
│   ├── license_collector.py # License data collection
│   ├── usage_tracker.py     # License usage tracking
│   ├── compliance_checker.py # Compliance checking
│   ├── optimizer.py         # Optimization recommendations
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                 # Report templates
│   └── license_report.html   # HTML report template
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main orchestrator that coordinates license collection, compliance checking, and report generation
- **src/config.py**: Configuration loading with environment variable substitution
- **src/database.py**: SQLAlchemy models for storing licenses, usage, compliance, and recommendations
- **src/license_collector.py**: Collects license data from LDAP, APIs, and CSV files
- **src/usage_tracker.py**: Tracks and records license usage over time
- **src/compliance_checker.py**: Checks compliance status against thresholds
- **src/optimizer.py**: Identifies unused licenses and generates optimization recommendations
- **src/report_generator.py**: Generates HTML, JSON, and Excel reports

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

- License collection from various sources
- Compliance checking logic
- Optimization recommendation generation
- Usage tracking functionality
- Report generation

## Troubleshooting

### License Collection Failures

**Problem**: Licenses are not being collected from sources.

**Solutions**:
- Verify source configuration in `config.yaml`
- Check connection strings and API credentials in `.env`
- Ensure source is enabled in configuration
- Review logs in `logs/license_monitor.log` for detailed error messages
- Test LDAP/API connectivity using external tools

### Compliance Check Errors

**Problem**: Compliance checks are failing or returning incorrect results.

**Solutions**:
- Verify license types are configured in `config.yaml`
- Check that licenses have been collected from sources
- Review compliance threshold settings
- Ensure database contains license data
- Check logs for specific error messages

### Report Generation Issues

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Verify output directory exists and is writable
- Check disk space availability
- Ensure required dependencies are installed (openpyxl for Excel)
- Review template file paths in configuration
- Check logs for template rendering errors

### Database Errors

**Problem**: Database connection or operation errors.

**Solutions**:
- Ensure SQLite is available (included with Python)
- Check file permissions for database file location
- Verify `DATABASE_URL` in `config.yaml` is correctly formatted
- Delete existing database file to recreate schema if needed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that required environment variables are set in `.env`
- `Source not configured`: Verify license source configuration in `config.yaml`
- `No licenses found`: Run `--collect` to gather license data first
- `Compliance check failed`: Review license type configuration and collected data

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

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
