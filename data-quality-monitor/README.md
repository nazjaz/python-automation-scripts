# Data Quality Monitor

Automated data quality monitoring system that monitors data quality across databases, identifies inconsistencies, validates data integrity, and generates comprehensive scorecards with remediation plans.

## Project Description

This automation system provides comprehensive data quality monitoring across multiple databases. It performs various quality checks including completeness, consistency, accuracy, uniqueness, and timeliness. The system identifies data inconsistencies, validates referential integrity, and generates detailed scorecards with actionable remediation plans.

### Target Audience

- Data engineers managing data quality across multiple databases
- Database administrators monitoring data integrity
- Data analysts requiring data quality metrics and reports
- DevOps teams implementing data quality monitoring in pipelines

## Features

- **Multi-Database Support**: Monitor data quality across PostgreSQL, MySQL, and SQLite databases
- **Comprehensive Quality Checks**: Completeness, consistency, accuracy, uniqueness, and timeliness validation
- **Integrity Validation**: Foreign key constraint validation and referential integrity checks
- **Automated Scorecards**: Generate HTML, JSON, and Excel scorecards with detailed metrics
- **Remediation Plans**: Automated generation of remediation plans with SQL queries and manual steps
- **Configurable Thresholds**: Customizable quality thresholds for each check type
- **Table-Specific Configuration**: Configure quality checks per table and column
- **Detailed Reporting**: Comprehensive reports with issue tracking and recommendations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to databases (PostgreSQL, MySQL, or SQLite)
- Database credentials with read permissions

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd data-quality-monitor
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

Edit `.env` with your database connection strings:

```env
PRIMARY_DB_URL=postgresql://user:password@localhost:5432/dbname
SECONDARY_DB_URL=mysql+pymysql://user:password@localhost:3306/dbname

APP_NAME=Data Quality Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to configure databases, tables, and quality checks:

```yaml
databases:
  - name: "primary_db"
    type: "postgresql"
    connection_string: "${PRIMARY_DB_URL}"
    enabled: true

tables:
  - name: "users"
    database: "primary_db"
    checks:
      - type: "completeness"
        columns: ["email", "name", "created_at"]
      - type: "uniqueness"
        columns: ["email"]
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PRIMARY_DB_URL` | Primary database connection string | Yes |
| `SECONDARY_DB_URL` | Secondary database connection string | No |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains:

- **databases**: List of databases to monitor with connection strings
- **quality_checks**: Configuration for each quality check type with thresholds
- **tables**: Table-specific check configurations
- **reporting**: Output format and directory settings
- **logging**: Log file configuration

### Quality Check Types

1. **Completeness**: Checks for NULL values and empty strings
2. **Consistency**: Validates foreign keys and referential integrity
3. **Accuracy**: Validates data formats, patterns, and ranges
4. **Uniqueness**: Checks for duplicate values and unique constraints
5. **Timeliness**: Validates data freshness and update frequency

## Usage

### Basic Usage

Monitor all configured databases:

```bash
python src/main.py
```

### Monitor Specific Database

```bash
python src/main.py --database primary_db
```

### Custom Configuration File

```bash
python src/main.py --config /path/to/config.yaml
```

### Custom Output Directory

```bash
python src/main.py --output-dir /path/to/reports
```

### Command-Line Arguments

```
--config PATH       Path to configuration file (optional)
--database NAME     Specific database to monitor (optional)
--output-dir PATH   Output directory for reports (optional)
```

## Project Structure

```
data-quality-monitor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Application configuration
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── database_connector.py # Database connection management
│   ├── quality_checks.py     # Quality check implementations
│   ├── integrity_validator.py # Data integrity validation
│   ├── scorecard_generator.py # Scorecard and report generation
│   └── remediation_planner.py # Remediation plan generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                 # Report templates
│   └── scorecard.html        # HTML scorecard template
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main orchestrator that coordinates all components
- **src/config.py**: Configuration loading with environment variable substitution
- **src/database_connector.py**: Multi-database connection management
- **src/quality_checks.py**: Implementations of completeness, uniqueness, and accuracy checks
- **src/integrity_validator.py**: Foreign key and referential integrity validation
- **src/scorecard_generator.py**: Multi-format report generation (HTML, JSON, Excel)
- **src/remediation_planner.py**: Automated remediation plan generation
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

- Quality check functionality (completeness, uniqueness, accuracy)
- Integrity validation
- Scorecard generation
- Remediation planning
- Database connector operations

## Troubleshooting

### Database Connection Failures

**Problem**: Cannot connect to database.

**Solutions**:
- Verify database connection strings in `.env` file
- Check database server is running and accessible
- Verify user credentials and permissions
- Test connection using database client tools
- Review logs in `logs/data_quality.log` for detailed error messages

### Configuration Errors

**Problem**: Configuration file not found or invalid.

**Solutions**:
- Ensure `config.yaml` exists in project root directory
- Validate YAML syntax using an online YAML validator
- Check that all required configuration sections are present
- Verify environment variable substitution syntax (${VARIABLE_NAME})
- Review error messages in logs for specific validation issues

### Quality Check Failures

**Problem**: Quality checks are failing or returning incorrect results.

**Solutions**:
- Verify table and column names in configuration match database schema
- Check database user has SELECT permissions on configured tables
- Review quality check thresholds in `config.yaml`
- Examine detailed error messages in logs
- Test individual quality checks with sample queries

### Report Generation Issues

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Verify output directory exists and is writable
- Check disk space availability
- Ensure required dependencies are installed (openpyxl for Excel)
- Review template file paths in configuration
- Check logs for template rendering errors

### Performance Issues

**Problem**: Quality checks are running slowly.

**Solutions**:
- Limit number of tables checked per run
- Add database indexes on frequently checked columns
- Use `--database` flag to check specific databases
- Review query performance in database logs
- Consider running checks during off-peak hours

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Failed to connect to database`: Verify database connection string and credentials
- `Table not found`: Verify table names in configuration match database schema
- `Permission denied`: Ensure database user has required SELECT permissions

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
