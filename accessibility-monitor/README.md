# Accessibility Monitor

Automated website accessibility monitoring system that monitors website accessibility compliance, identifies WCAG violations, generates remediation reports, and tracks improvement progress over time.

## Project Description

This automation system provides comprehensive monitoring and analysis of website accessibility compliance. It scans websites for WCAG violations, generates detailed remediation reports, creates actionable tasks, and tracks improvement progress over time to help organizations achieve and maintain accessibility standards.

### Target Audience

- Web developers ensuring accessibility compliance
- QA teams monitoring accessibility standards
- Compliance officers tracking WCAG adherence
- Project managers overseeing accessibility improvements

## Features

- **Website Scanning**: Automatically scans websites for accessibility issues
- **WCAG Compliance Checking**: Validates pages against WCAG 2.1 guidelines (A, AA, AAA levels)
- **Violation Detection**: Identifies violations across multiple categories (images, forms, navigation, keyboard, color contrast, ARIA, headings, links)
- **Remediation Reports**: Generates detailed remediation reports with code examples and recommendations
- **Task Generation**: Automatically creates remediation tasks from violations
- **Progress Tracking**: Tracks accessibility improvement over time with trend analysis
- **Multi-Format Reports**: Generates HTML and CSV reports
- **Database Persistence**: Stores all scan data, violations, and progress metrics

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Internet connection (for scanning websites)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd accessibility-monitor
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
DATABASE_URL=sqlite:///accessibility_monitor.db
APP_NAME=Accessibility Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize scanning options, WCAG levels, and reporting:

```yaml
accessibility:
  wcag_version: "2.1"
  target_level: "AA"
  max_pages: 50
  timeout_seconds: 30

scanning:
  check_images: true
  check_forms: true
  check_color_contrast: true
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///accessibility_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **accessibility**: WCAG version, compliance levels, scan depth, timeout settings
- **violations**: Severity levels, auto-categorization, suggestions
- **scanning**: Check options for images, forms, navigation, keyboard, color contrast, ARIA, headings, links
- **remediation**: Report generation, code examples, prioritization
- **progress_tracking**: Tracking intervals, improvement thresholds
- **reporting**: Output formats, directory, inclusion options
- **logging**: Log file location, rotation, and format settings

## Usage

### Add a Website

Add a website to monitor:

```bash
python src/main.py --add-website --url "https://example.com" --name "Example Website"
```

### Scan Website

Scan website for accessibility issues:

```bash
python src/main.py --scan --website-id 1 --max-pages 10
```

### Generate Remediation Tasks

Generate remediation tasks from violations:

```bash
python src/main.py --generate-tasks --website-id 1 --severity high
```

### Track Progress

Track accessibility improvement progress:

```bash
python src/main.py --track-progress --website-id 1 --progress-days 30
```

### Generate Report

Generate accessibility compliance report:

```bash
python src/main.py --generate-report --website-id 1 --format html
```

### Complete Workflow

Run complete monitoring workflow:

```bash
python src/main.py --scan --website-id 1 && \
python src/main.py --generate-tasks --website-id 1 && \
python src/main.py --generate-report --website-id 1
```

### Command-Line Arguments

```
--add-website          Add a website to monitor
--url URL              Website URL (required)
--name NAME            Website name

--scan                 Scan website for accessibility issues
--website-id ID        Website ID (required)
--start-url URL        Starting URL for scan
--max-pages N          Maximum pages to scan

--generate-tasks       Generate remediation tasks
--website-id ID        Website ID filter
--scan-id ID           Scan ID filter
--severity LEVEL       Filter by severity (critical, high, medium, low)

--track-progress       Track accessibility improvement progress
--website-id ID        Website ID (required)
--progress-days DAYS   Days to analyze (default: 30)

--generate-report      Generate accessibility compliance report
--website-id ID        Website ID filter
--scan-id ID           Scan ID filter
--format FORMAT        Report format (html or csv, default: html)

--config PATH          Path to configuration file (default: config.yaml)
```

## Project Structure

```
accessibility-monitor/
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
│   ├── accessibility_scanner.py # Website scanning
│   ├── wcag_validator.py     # WCAG compliance validation
│   ├── remediation_generator.py # Remediation report generation
│   ├── progress_tracker.py    # Progress tracking
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── accessibility_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for websites, scans, violations, tasks, and progress
- **src/accessibility_scanner.py**: Scans websites and extracts pages for analysis
- **src/wcag_validator.py**: Validates pages against WCAG guidelines
- **src/remediation_generator.py**: Generates remediation tasks and reports
- **src/progress_tracker.py**: Tracks accessibility improvement over time
- **src/report_generator.py**: Generates HTML and CSV accessibility reports
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
- WCAG validation algorithms
- Website scanning functionality
- Remediation task generation
- Progress tracking calculations
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

### Website Scanning Failures

**Problem**: Website scanning fails or returns no results.

**Solutions**:
- Verify website URL is accessible and correct
- Check internet connection
- Review timeout settings in `config.yaml`
- Ensure website doesn't block automated scanners
- Check logs for specific error messages
- Try with a different starting URL

### No Violations Detected

**Problem**: Scans complete but no violations are detected.

**Solutions**:
- Verify scanning options are enabled in `config.yaml`
- Check that pages contain actual content (not just redirects)
- Review WCAG validation criteria
- Ensure HTML content is being parsed correctly
- Check logs for parsing errors

### Progress Tracking Not Working

**Problem**: Progress tracking shows insufficient data.

**Solutions**:
- Ensure multiple scans have been performed over time
- Verify scans have compliance scores calculated
- Check that minimum scan threshold is met
- Review progress tracking configuration
- Ensure scans are associated with the correct website

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Website not found`: Verify website ID exists in database
- `Connection timeout`: Increase timeout_seconds in `config.yaml` or check network
- `Invalid URL`: Verify URL format is correct (include http:// or https://)

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

## WCAG Compliance Checking

The system checks for violations in the following areas:

### Images
- Missing alt text attributes
- Empty alt text without decorative marking

### Forms
- Missing form labels
- Missing ARIA labels

### Navigation
- Missing navigation elements
- Unlabeled navigation

### Keyboard
- Keyboard traps (negative tabindex)
- Keyboard navigation issues

### Color Contrast
- Potential contrast issues
- Background color specification

### ARIA
- Missing error descriptions
- ARIA attribute usage

### Headings
- Missing h1 headings
- Multiple h1 headings
- Heading hierarchy skips

### Links
- Empty link text
- Generic link text ("click here", "read more")

## Remediation Reports

Remediation reports include:

- **Violation Details**: WCAG criterion, severity, type, description
- **Element Information**: Element type, CSS selector, line numbers
- **Recommendations**: Specific remediation steps
- **Code Examples**: Before/after code examples where applicable
- **Priority**: Task priority based on violation severity

## Progress Tracking

The system tracks:

- **Compliance Scores**: Overall accessibility compliance scores over time
- **Violation Counts**: Total violations by severity level
- **Trend Analysis**: Improving, stable, or declining trends
- **Improvement Metrics**: Score changes and violation reductions
- **Baseline Comparison**: Comparison to initial scan results

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
