# Security Monitor

Automated application security monitoring system that monitors security scans, tracks vulnerabilities, prioritizes fixes, and generates security compliance reports with remediation timelines.

## Project Description

This automation system provides comprehensive security monitoring for applications. The system automatically monitors security scans, tracks vulnerabilities by severity and status, prioritizes fixes based on severity and CVSS scores, generates compliance reports, and creates remediation timelines with target fix dates. This helps security teams, DevOps engineers, and compliance officers efficiently manage security vulnerabilities and maintain security posture.

### Target Audience

- Security teams monitoring application security
- DevOps engineers managing security vulnerabilities
- Compliance officers ensuring security compliance
- Development teams prioritizing security fixes
- Security managers tracking remediation progress

## Features

- **Security Scan Monitoring**: Monitors application security scans (static, dynamic, dependency) with status tracking and vulnerability counting
- **Vulnerability Tracking**: Tracks vulnerabilities by severity (critical, high, medium, low), CVSS scores, CVE IDs, and status with discovery and fix timestamps
- **Fix Prioritization**: Automatically prioritizes fixes based on severity weights, CVSS scores, days open, and CVE presence with priority scoring
- **Compliance Reporting**: Generates security compliance reports with compliance status (compliant, at_risk, non_compliant) and compliance scores
- **Remediation Timelines**: Generates remediation timelines with target fix dates based on severity, remediation steps, and estimated completion dates
- **Performance Metrics**: Tracks key performance indicators including vulnerability counts, fix rates, average fix times, and compliance trends
- **Comprehensive Reporting**: Generates HTML and CSV reports with vulnerability statistics, critical vulnerabilities, prioritized fixes, compliance trends, and timeline summaries
- **Database Persistence**: Stores all applications, security scans, vulnerabilities, fixes, remediation timelines, compliance reports, and metrics in SQLite database
- **Flexible Configuration**: Customizable severity weights, CVSS thresholds, compliance thresholds, timeline parameters, and monitoring settings
- **Multi-Application Support**: Supports multiple applications with individual vulnerability tracking and compliance reporting

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd security-monitor
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
DATABASE_URL=sqlite:///security_monitor.db
APP_NAME=Security Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize severity weights, compliance thresholds, and timeline parameters:

```yaml
fix_prioritization:
  severity_weights:
    critical: 10.0
    high: 7.0

compliance:
  compliance_thresholds:
    critical: 0
    high: 5
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///security_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **scan_monitoring**: Security scan monitoring configuration
- **vulnerability_tracking**: Vulnerability tracking settings
- **fix_prioritization**: Fix prioritization settings including severity weights and CVSS thresholds
- **compliance**: Compliance reporting settings including compliance thresholds
- **remediation**: Remediation timeline settings including timeline parameters by severity
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Monitor Security Scan

Monitor a security scan:

```bash
python src/main.py --monitor-scan "SCAN001"
```

### Process Scan Results

Process scan results from JSON file:

```bash
python src/main.py --process-results "SCAN001" vulnerabilities.json
```

Example `vulnerabilities.json`:

```json
[
  {
    "vulnerability_id": "VULN001",
    "title": "SQL Injection Vulnerability",
    "severity": "critical",
    "cvss_score": 9.8,
    "cve_id": "CVE-2023-12345",
    "description": "SQL injection in login endpoint",
    "component": "auth-service",
    "affected_version": "1.0.0"
  }
]
```

### Track Vulnerability

Track a vulnerability:

```bash
python src/main.py --track "VULN001"
```

### Prioritize Fix

Prioritize fix for vulnerability:

```bash
python src/main.py --prioritize "VULN001"
```

### Generate Compliance Report

Generate compliance report:

```bash
python src/main.py --generate-compliance "APP001" --report-type "security"
```

### Generate Remediation Timeline

Generate remediation timeline:

```bash
python src/main.py --generate-timeline "VULN001"
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --application-id "APP001"
```

### Complete Workflow

Run complete security monitoring workflow:

```bash
# Monitor scan
python src/main.py --monitor-scan "SCAN001"

# Process scan results
python src/main.py --process-results "SCAN001" vulnerabilities.json

# Prioritize fixes
python src/main.py --prioritize "VULN001"

# Generate compliance report
python src/main.py --generate-compliance "APP001"

# Generate remediation timeline
python src/main.py --generate-timeline "VULN001"

# Generate reports
python src/main.py --report
```

### Command-Line Arguments

```
--monitor-scan SCAN_ID                    Monitor security scan
--process-results SCAN_ID FILE            Process scan results from JSON file
--track VULNERABILITY_ID                  Track vulnerability
--prioritize VULNERABILITY_ID             Prioritize fix for vulnerability
--generate-compliance APPLICATION_ID     Generate compliance report
--generate-timeline VULNERABILITY_ID      Generate remediation timeline
--report                                  Generate analysis reports
--application-id ID                        Filter by application ID
--report-type TYPE                        Report type (default: security)
--config PATH                             Path to configuration file (default: config.yaml)
```

## Project Structure

```
security-monitor/
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
│   ├── scan_monitor.py       # Security scan monitoring
│   ├── vulnerability_tracker.py # Vulnerability tracking
│   ├── fix_prioritizer.py    # Fix prioritization
│   ├── compliance_reporter.py # Compliance reporting
│   ├── remediation_timeline.py # Remediation timeline generation
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── security_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates scan monitoring, vulnerability tracking, fix prioritization, compliance reporting, remediation timeline generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for applications, security scans, vulnerabilities, fixes, remediation timelines, compliance reports, and metrics
- **src/scan_monitor.py**: Monitors security scans and processes scan results
- **src/vulnerability_tracker.py**: Tracks vulnerabilities with statistics and overdue identification
- **src/fix_prioritizer.py**: Prioritizes fixes based on severity, CVSS scores, and other factors
- **src/compliance_reporter.py**: Generates compliance reports with status and score calculation
- **src/remediation_timeline.py**: Generates remediation timelines with target fix dates
- **src/report_generator.py**: Generates HTML and CSV reports with security data
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

- Security scan monitoring functionality
- Vulnerability tracking algorithms
- Fix prioritization logic
- Compliance reporting
- Remediation timeline generation
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

### Scan Not Processed

**Problem**: Scan results are not being processed correctly.

**Solutions**:
- Verify scan exists in database
- Check JSON file format for vulnerabilities
- Ensure vulnerability data includes required fields
- Review scan status and completion time
- Check that application exists for scan

### Vulnerability Not Tracked

**Problem**: Vulnerability tracking not working correctly.

**Solutions**:
- Verify vulnerability exists in database
- Check that vulnerability has required fields (title, severity)
- Ensure vulnerability status is correct
- Review vulnerability tracking settings
- Check that scan is linked to vulnerability

### Fix Not Prioritized

**Problem**: Fix prioritization returns incorrect priority.

**Solutions**:
- Verify severity weights are configured correctly
- Check CVSS score is set for vulnerability
- Review priority calculation logic
- Ensure fix exists for vulnerability
- Check that estimated effort is calculated correctly

### Compliance Report Not Generated

**Problem**: Compliance report is not being generated or is incorrect.

**Solutions**:
- Verify application exists in database
- Check that vulnerabilities exist for application
- Ensure compliance thresholds are configured
- Review compliance score calculation
- Check that report type is valid

### Timeline Not Generated

**Problem**: Remediation timeline is not being generated.

**Solutions**:
- Verify vulnerability exists and is open
- Check that timeline parameters are configured
- Ensure target fix date is calculated correctly
- Review remediation steps generation
- Check that timeline is saved to database

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient security data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Scan not found`: Verify scan ID is correct and scan exists
- `Vulnerability not found`: Verify vulnerability ID is correct and vulnerability exists
- `Application not found`: Ensure application is created before running scans
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

## Vulnerability Severities

The system supports various vulnerability severities:

- **critical**: Critical severity vulnerabilities (CVSS 9.0+)
- **high**: High severity vulnerabilities (CVSS 7.0-8.9)
- **medium**: Medium severity vulnerabilities (CVSS 4.0-6.9)
- **low**: Low severity vulnerabilities (CVSS 0.0-3.9)

Severities are used for prioritization and compliance calculations.

## Vulnerability Statuses

The system tracks various vulnerability statuses:

- **open**: Vulnerability is open and needs to be fixed
- **in_progress**: Fix is in progress
- **fixed**: Vulnerability has been fixed
- **false_positive**: Vulnerability is a false positive
- **closed**: Vulnerability is closed

Status updates are tracked through vulnerability lifecycle.

## Priority Levels

Fixes can have different priority levels:

- **low**: Low priority fixes
- **medium**: Normal priority (default)
- **high**: High priority fixes
- **urgent**: Urgent priority fixes

Priority affects remediation timeline and resource allocation.

## Compliance Statuses

The system supports various compliance statuses:

- **compliant**: Application is compliant (score >= 90)
- **at_risk**: Application is at risk (score 70-89)
- **non_compliant**: Application is non-compliant (score < 70)

Compliance status is calculated based on vulnerability counts and thresholds.

## Scan Types

The system supports various security scan types:

- **static**: Static application security testing (SAST)
- **dynamic**: Dynamic application security testing (DAST)
- **dependency**: Dependency scanning
- **container**: Container image scanning
- **infrastructure**: Infrastructure as code scanning

Scan types help categorize and organize security scans.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
