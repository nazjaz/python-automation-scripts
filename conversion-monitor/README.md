# Conversion Monitor

Automated website conversion monitoring system that monitors conversion rates, tracks user journeys, identifies drop-off points, and generates optimization recommendations for improving conversions.

## Project Description

This automation system provides comprehensive conversion monitoring and optimization for websites. The system processes user events, monitors conversion rates over time, tracks user journeys through the website, identifies critical drop-off points, and generates actionable optimization recommendations. This helps marketing teams, product managers, and conversion optimization specialists improve website performance and increase conversion rates.

### Target Audience

- Marketing teams tracking conversion performance
- Product managers optimizing user experience
- Conversion optimization specialists identifying improvement opportunities
- E-commerce managers monitoring sales funnels
- Growth teams analyzing user behavior

## Features

- **Conversion Rate Monitoring**: Continuously monitors conversion rates with configurable time windows and trend analysis
- **User Journey Tracking**: Tracks user journeys through website pages and events with pattern identification
- **Drop-off Point Identification**: Automatically identifies drop-off points in user journeys with rate calculations
- **Optimization Recommendations**: Generates actionable recommendations for improving conversions with priority and impact scoring
- **Event Processing**: Processes user events from various sources (JSON, CSV) with automatic session management
- **Conversion Goal Management**: Supports multiple conversion goals per website with flexible target definitions
- **Comprehensive Reporting**: Generates HTML and CSV reports with conversion metrics, trends, drop-offs, and recommendations
- **Database Persistence**: Stores all events, sessions, conversion rates, journeys, drop-offs, and recommendations in SQLite database
- **Flexible Configuration**: Customizable monitoring windows, drop-off thresholds, and recommendation templates
- **Multi-Website Support**: Monitors multiple websites simultaneously with individual conversion tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd conversion-monitor
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
DATABASE_URL=sqlite:///conversion_monitor.db
APP_NAME=Conversion Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize monitoring windows, drop-off detection, and recommendation settings:

```yaml
monitoring:
  time_window_hours: 24

dropoff_detection:
  min_dropoff_rate: 0.1
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///conversion_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **monitoring**: Conversion monitoring settings including time windows
- **events**: Event processing configuration
- **journey_tracking**: User journey tracking settings
- **dropoff_detection**: Drop-off identification settings including minimum thresholds
- **recommendations**: Recommendation generation settings including templates
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Add Website

Add a new website to monitor:

```bash
python src/main.py --add-website "example.com" "Example Website"
```

### Add Conversion Goal

Add a conversion goal for a website:

```bash
python src/main.py --add-goal 1 "Purchase" "purchase" --target-url "/checkout/complete"
python src/main.py --add-goal 1 "Signup" "signup" --target-event "user_signup"
```

### Import Events

Import user events from JSON file:

```bash
python src/main.py --import-events 1 events.json --format json
```

Import user events from CSV file:

```bash
python src/main.py --import-events 1 events.csv --format csv
```

### Monitor Conversion Rates

Monitor conversion rates for a website:

```bash
python src/main.py --monitor 1 --hours 24
python src/main.py --monitor 1 --conversion-goal-id 1
```

### Track User Journeys

Track user journeys through website:

```bash
python src/main.py --track-journeys 1
```

### Identify Drop-off Points

Identify drop-off points in user journeys:

```bash
python src/main.py --identify-dropoffs 1
python src/main.py --identify-dropoffs 1 --conversion-goal-id 1
```

### Generate Recommendations

Generate optimization recommendations:

```bash
python src/main.py --generate-recommendations 1
python src/main.py --generate-recommendations 1 --conversion-goal-id 1
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --website-id 1
```

### Complete Workflow

Run complete conversion monitoring workflow:

```bash
# Add website and conversion goal
python src/main.py --add-website "example.com" "Example Website"
python src/main.py --add-goal 1 "Purchase" "purchase" --target-url "/checkout/complete"

# Import events
python src/main.py --import-events 1 events.json --format json

# Monitor and analyze
python src/main.py --monitor 1 --track-journeys 1 --identify-dropoffs 1 --generate-recommendations 1 --report
```

### Command-Line Arguments

```
--add-website DOMAIN NAME          Add a new website
--add-goal ID NAME TYPE            Add conversion goal
--import-events ID FILE            Import events from JSON or CSV file
--monitor ID                       Monitor conversion rates
--track-journeys ID                Track user journeys
--identify-dropoffs ID             Identify drop-off points
--generate-recommendations ID      Generate optimization recommendations
--report                           Generate analysis reports
--website-id ID                    Filter by website ID
--conversion-goal-id ID            Filter by conversion goal ID
--hours HOURS                       Number of hours to analyze
--target-url URL                   Target URL for conversion goal
--target-event EVENT               Target event for conversion goal
--format FORMAT                    File format for import (json or csv, default: json)
--config PATH                      Path to configuration file (default: config.yaml)
```

## Project Structure

```
conversion-monitor/
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
│   ├── event_processor.py    # Event processing and import
│   ├── conversion_monitor.py # Conversion rate monitoring
│   ├── journey_tracker.py     # User journey tracking
│   ├── dropoff_identifier.py # Drop-off point identification
│   ├── optimization_recommender.py # Optimization recommendations
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── conversion_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates website management, event import, conversion monitoring, journey tracking, drop-off identification, recommendation generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for websites, sessions, events, conversion goals, conversion rates, journey steps, drop-off points, and recommendations
- **src/event_processor.py**: Processes user events and imports from JSON/CSV files
- **src/conversion_monitor.py**: Monitors conversion rates and calculates trends
- **src/journey_tracker.py**: Tracks user journeys and identifies common patterns
- **src/dropoff_identifier.py**: Identifies drop-off points in user journeys
- **src/optimization_recommender.py**: Generates optimization recommendations based on drop-offs and conversion data
- **src/report_generator.py**: Generates HTML and CSV reports with conversion metrics
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

- Event processing functionality
- Conversion rate monitoring algorithms
- Journey tracking logic
- Drop-off identification
- Recommendation generation
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

### Event Import Errors

**Problem**: Event import fails or imports incorrect data.

**Solutions**:
- Verify JSON/CSV file format matches expected structure
- Check file encoding (should be UTF-8)
- Ensure file contains required fields (session_id, event_type, timestamp)
- Review file path is correct and file is readable
- Check that website ID exists before importing events

### No Conversion Rates Calculated

**Problem**: Conversion rates are not being calculated.

**Solutions**:
- Verify events have been imported for the website
- Ensure conversion goals are defined
- Check that time window (--hours) includes event data
- Verify sessions have been created from events
- Review conversion goal target URLs/events match event data

### No Drop-offs Identified

**Problem**: Drop-off identification returns no results.

**Solutions**:
- Verify journey steps are defined or sufficient event data exists
- Ensure minimum drop-off rate threshold is appropriate
- Check that sessions have multiple events
- Review drop-off detection settings in `config.yaml`
- Lower minimum drop-off rate threshold if needed

### Recommendations Not Generated

**Problem**: Optimization recommendations are not being generated.

**Solutions**:
- Ensure drop-offs have been identified first (run `--identify-dropoffs`)
- Verify conversion statistics are available
- Check that website has sufficient data
- Review recommendation generation settings
- Ensure conversion monitoring has been run

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient website data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Website not found`: Verify website ID is correct and website exists
- `Events file not found`: Verify the file path provided to `--import-events` is correct
- `No sessions found`: Ensure events have been imported and sessions created
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

## Event Import Formats

### JSON Format

```json
{
  "events": [
    {
      "session_id": "session1",
      "event_type": "pageview",
      "timestamp": "2024-01-01T10:00:00Z",
      "page_url": "/home",
      "page_title": "Home Page",
      "user_id": "user1"
    }
  ]
}
```

### CSV Format

```csv
session_id,event_type,timestamp,page_url,page_title,user_id
session1,pageview,2024-01-01T10:00:00Z,/home,Home Page,user1
```

## Conversion Goal Types

The system supports various conversion goal types:

- **purchase**: E-commerce purchase completions
- **signup**: User registration/signup
- **download**: File downloads
- **form_submit**: Form submissions
- **custom**: Custom conversion events

Conversion goals can be defined by target URL or target event name.

## Recommendation Types

The system generates various recommendation types:

- **dropoff_optimization**: Recommendations for reducing drop-offs at specific points
- **conversion_optimization**: Recommendations for improving overall conversion rates
- **engagement_optimization**: Recommendations for increasing user engagement
- **navigation_optimization**: Recommendations for improving site navigation

Recommendations are prioritized (low, medium, high, urgent) and include expected impact scores.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
