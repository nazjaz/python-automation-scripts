# Error Monitor

Automated application error monitoring system that monitors error rates, categorizes errors, identifies patterns, and generates bug reports with reproduction steps and priority rankings.

## Project Description

This automation system provides comprehensive error monitoring and analysis for applications. The system parses log files, categorizes errors, identifies recurring patterns, calculates error rates, and generates prioritized bug reports with detailed reproduction steps to help development teams quickly identify and resolve issues.

### Target Audience

- DevOps engineers monitoring application health
- Development teams tracking and resolving bugs
- QA teams analyzing error patterns and trends
- System administrators monitoring production systems
- Product managers prioritizing bug fixes

## Features

- **Log File Parsing**: Parses standard and JSON log formats to extract error information
- **Error Categorization**: Automatically categorizes errors into predefined categories (database, authentication, network, validation, etc.)
- **Pattern Identification**: Identifies recurring error patterns and calculates frequency and trends
- **Error Rate Monitoring**: Calculates error rates over time windows and tracks threshold violations
- **Bug Report Generation**: Automatically generates bug reports with reproduction steps, priority rankings, and severity classification
- **Comprehensive Reporting**: Creates HTML and CSV reports with visualizations and detailed metrics
- **Database Persistence**: Stores all error data, patterns, and bug reports in SQLite database for historical tracking
- **Flexible Filtering**: Filter analysis by application, environment, and time period
- **Trend Analysis**: Tracks error trends (increasing, decreasing, stable) to identify emerging issues

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Application log files in standard or JSON format

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd error-monitor
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
DATABASE_URL=sqlite:///error_monitor.db
APP_NAME=Error Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize error categorization, pattern identification, monitoring thresholds, and reporting options:

```yaml
categorization:
  categories:
    database:
      description: "Database connection or query errors"
      keywords:
        - "database"
        - "sql"
        - "connection"
      default_severity: "high"

monitoring:
  error_rate_threshold: 1.0
  time_window_minutes: 60
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///error_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **parsing**: Log file parsing settings including format and timestamp patterns
- **categorization**: Error categorization rules including categories, keywords, patterns, and severity rules
- **pattern_identification**: Pattern identification settings including minimum frequency and similarity thresholds
- **monitoring**: Error rate monitoring settings including time windows and thresholds
- **bug_reports**: Bug report generation settings including priority rules and reproduction templates
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Parse Log File

Parse a log file and import errors into the database:

```bash
python src/main.py --parse app.log --application myapp --environment production
```

### Analyze Errors

Analyze errors and identify patterns:

```bash
python src/main.py --analyze --hours 24
```

### Generate Bug Reports

Generate bug reports from identified error patterns:

```bash
python src/main.py --generate-bugs
```

### Generate Reports

Generate HTML and CSV reports with analysis results:

```bash
python src/main.py --report
```

### Complete Workflow

Run the complete workflow (parse, analyze, generate bugs, and report):

```bash
python src/main.py --parse app.log --analyze --generate-bugs --report --application myapp
```

### Filter by Application or Environment

Filter operations by specific application or environment:

```bash
python src/main.py --analyze --application myapp --environment production
python src/main.py --generate-bugs --environment staging
python src/main.py --report --application myapp
```

### Command-Line Arguments

```
--parse LOG_FILE        Parse log file and import errors
--analyze               Analyze errors and identify patterns
--generate-bugs         Generate bug reports from error patterns
--report                Generate analysis reports
--application APP       Filter by application name
--environment ENV       Filter by environment (production, staging, development)
--hours HOURS           Number of hours to analyze (default: 24)
--config PATH           Path to configuration file (default: config.yaml)
```

## Project Structure

```
error-monitor/
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
│   ├── log_parser.py         # Log file parsing
│   ├── error_categorizer.py  # Error categorization
│   ├── pattern_identifier.py # Pattern identification
│   ├── error_monitor.py      # Error rate monitoring
│   ├── bug_report_generator.py # Bug report generation
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── error_report.html     # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates log parsing, error analysis, pattern identification, bug report generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for errors, categories, patterns, bug reports, and error rates
- **src/log_parser.py**: Parses standard and JSON log formats to extract error information
- **src/error_categorizer.py**: Categorizes errors into predefined categories based on keywords and patterns
- **src/pattern_identifier.py**: Identifies recurring error patterns and calculates trends
- **src/error_monitor.py**: Monitors error rates and calculates metrics over time windows
- **src/bug_report_generator.py**: Generates bug reports with reproduction steps, priority, and severity
- **src/report_generator.py**: Generates HTML and CSV reports with analysis results
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

- Log file parsing functionality
- Error categorization logic
- Pattern identification algorithms
- Error rate monitoring
- Bug report generation
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

### Log Parsing Issues

**Problem**: No errors found in log file or parsing fails.

**Solutions**:
- Verify log file format matches configured format (standard or JSON)
- Check that log file contains error entries (ERROR, EXCEPTION, FATAL, etc.)
- Review timestamp format in `config.yaml` matches log file format
- Ensure log file is readable and not corrupted
- Check log file encoding (should be UTF-8)

### No Patterns Identified

**Problem**: Pattern identification returns no results.

**Solutions**:
- Verify minimum frequency threshold in `config.yaml` (default: 3)
- Ensure sufficient errors have been imported
- Check that errors have similar signatures
- Review pattern identification settings

### Error Rate Calculation Issues

**Problem**: Error rates seem incorrect or unrealistic.

**Solutions**:
- Verify total request estimation logic
- Check time window settings
- Review error count accuracy
- Ensure errors are properly timestamped
- Adjust error rate threshold if needed

### Bug Report Generation Failures

**Problem**: Bug reports are not being generated or are incomplete.

**Solutions**:
- Ensure error patterns have been identified first (run `--analyze`)
- Verify sufficient error data exists
- Check that patterns meet minimum frequency requirements
- Review bug report generation settings in `config.yaml`
- Ensure output directory exists and is writable

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient error data has been analyzed
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Log file not found`: Verify the file path provided to `--parse` is correct
- `No errors found in log file`: Check log file format and content
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

## Log File Formats

### Standard Format

The system supports standard log formats with timestamps and error messages:

```
2024-01-01 10:00:00 ERROR: Database connection failed
2024-01-01 10:01:00 EXCEPTION: NullPointerException at com.example.App.main
```

### JSON Format

The system also supports JSON log formats:

```json
{"timestamp": "2024-01-01T10:00:00Z", "level": "ERROR", "message": "Database connection failed", "application": "myapp", "environment": "production"}
```

### Custom Formats

To support custom log formats, modify the `log_parser.py` module to add new parsing logic or update the `log_format` setting in `config.yaml`.

## Error Categories

The system categorizes errors into the following default categories:

- **database**: Database connection or query errors
- **authentication**: Authentication and authorization errors
- **network**: Network and connectivity errors
- **validation**: Input validation errors
- **application**: Application logic errors
- **performance**: Performance and resource errors
- **unknown**: Uncategorized errors

Categories can be customized in `config.yaml` by adding keywords, patterns, and severity rules.

## Bug Report Priority

Bug reports are prioritized based on:

- Error rate percentage (urgent if > 10%, high if > 5%)
- Error frequency (high if >= 100, medium if >= 50)
- Error trend (high priority if increasing)
- Error severity (critical/high severity increases priority)

Priority levels: `low`, `medium`, `high`, `urgent`

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
