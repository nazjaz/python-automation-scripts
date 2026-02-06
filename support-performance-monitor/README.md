# Support Performance Monitor

Automated support performance monitoring system that monitors customer support response times, tracks resolution rates, identifies bottlenecks, and generates performance dashboards for management.

## Project Description

This automation system provides comprehensive monitoring and analysis of customer support operations. It tracks response times, calculates resolution rates, identifies performance bottlenecks, and generates detailed dashboards to help management make data-driven decisions about support operations.

### Target Audience

- Support managers monitoring team performance
- Operations teams optimizing support workflows
- Management teams reviewing support metrics
- Quality assurance teams tracking SLA compliance

## Features

- **Response Time Tracking**: Monitors first response times and calculates average response times
- **Resolution Rate Analysis**: Tracks resolution rates by category, agent, and overall
- **Bottleneck Identification**: Automatically identifies bottlenecks by category, agent, and time period
- **Performance Dashboards**: Generates HTML and CSV dashboards with comprehensive metrics
- **SLA Compliance Monitoring**: Tracks SLA compliance rates and identifies breaches
- **Multi-Dimensional Analysis**: Analyzes performance by category, agent, priority, and time period
- **Database Persistence**: Stores all ticket data, metrics, and bottlenecks in SQLite database
- **Real-Time Metrics**: Calculates metrics in real-time from ticket data

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd support-performance-monitor
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
DATABASE_URL=sqlite:///support_performance.db
APP_NAME=Support Performance Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize thresholds, categories, and dashboard settings:

```yaml
support:
  response_time_thresholds:
    first_response_minutes: 60
    resolution_hours: 24
    sla_target_percentage: 95.0

performance:
  resolution_rate_target: 0.85
  bottleneck_threshold_percentage: 20.0
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///support_performance.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **support**: Support ticket categories, priorities, statuses, and response time thresholds
- **monitoring**: Monitoring intervals and tracking options
- **performance**: Performance targets and metrics window
- **bottleneck_detection**: Bottleneck detection settings and thresholds
- **dashboard**: Dashboard generation settings and output directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Add a Support Ticket

Add a support ticket to the system:

```bash
python src/main.py --add-ticket --ticket-number "TICKET-001" --title "Login Issue" --category "technical" --priority "high" --customer-email "customer@example.com" --assigned-agent "agent1@example.com"
```

### Track Response Times

Track response times for all tickets:

```bash
python src/main.py --track-response-times --days 30
```

### Analyze Resolution Rates

Analyze resolution rates:

```bash
python src/main.py --analyze-resolution --days 30
```

Analyze by category:

```bash
python src/main.py --analyze-resolution --days 30 --category "technical"
```

### Identify Bottlenecks

Identify bottlenecks in support operations:

```bash
python src/main.py --identify-bottlenecks --days 30
```

### Generate Performance Dashboard

Generate performance dashboard:

```bash
python src/main.py --dashboard --days 30
```

### Complete Workflow

Run complete monitoring workflow:

```bash
python src/main.py --track-response-times --analyze-resolution --identify-bottlenecks --dashboard --days 30
```

### Command-Line Arguments

```
--add-ticket              Add a support ticket
--ticket-number NUMBER    Ticket number (required for --add-ticket)
--title TITLE             Ticket title (required)
--category CATEGORY       Ticket category (required)
--priority PRIORITY       Priority level (required)
--customer-email EMAIL    Customer email (required)
--description DESC        Ticket description
--assigned-agent AGENT    Assigned agent

--track-response-times    Track response times for tickets
--analyze-resolution     Analyze resolution rates
--identify-bottlenecks    Identify bottlenecks
--dashboard               Generate performance dashboard
--days DAYS               Number of days to analyze (default: 30)
--config PATH             Path to configuration file (default: config.yaml)
```

## Project Structure

```
support-performance-monitor/
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
│   ├── response_time_tracker.py # Response time tracking
│   ├── resolution_rate_analyzer.py # Resolution rate analysis
│   ├── bottleneck_identifier.py # Bottleneck identification
│   └── dashboard_generator.py # Dashboard generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Dashboard templates
│   └── dashboard.html        # HTML dashboard template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for tickets, responses, metrics, and bottlenecks
- **src/response_time_tracker.py**: Tracks and calculates response times and SLA compliance
- **src/resolution_rate_analyzer.py**: Analyzes resolution rates by various dimensions
- **src/bottleneck_identifier.py**: Identifies bottlenecks by category, agent, and time period
- **src/dashboard_generator.py**: Generates HTML and CSV performance dashboards
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
- Response time tracking and calculation
- Resolution rate analysis
- Bottleneck identification algorithms
- Dashboard generation
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

### No Metrics Generated

**Problem**: Dashboard shows no metrics or zero values.

**Solutions**:
- Ensure tickets have been added to the system
- Verify tickets have appropriate statuses (resolved, closed)
- Check that response times are being tracked
- Review date range filters (may need to adjust --days parameter)
- Ensure tickets have first_response_at and resolved_at timestamps

### Bottlenecks Not Identified

**Problem**: No bottlenecks are being identified.

**Solutions**:
- Verify bottleneck detection is enabled in `config.yaml`
- Check that minimum ticket threshold is met
- Ensure tickets have appropriate statuses for analysis
- Review bottleneck threshold percentage settings
- Check that categories and agents are properly assigned

### Response Times Not Tracking

**Problem**: Response times are not being calculated.

**Solutions**:
- Ensure tickets have first_response_at timestamps set
- Verify response records are being created
- Check that ticket statuses are being updated correctly
- Review response time tracking configuration
- Ensure tickets have created_at timestamps

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Ticket not found`: Verify ticket ID or ticket number exists in database
- `No tickets found for analysis`: Ensure tickets exist in the specified time period
- `Invalid date format`: Check date format matches expected format

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

## Performance Metrics

The system tracks the following metrics:

### Response Time Metrics

- **First Response Time**: Time from ticket creation to first agent response
- **Average Response Time**: Average first response time across all tickets
- **SLA Compliance Rate**: Percentage of tickets meeting response time SLA

### Resolution Metrics

- **Resolution Rate**: Percentage of tickets resolved
- **Average Resolution Time**: Average time to resolve tickets
- **Resolution Rate by Category**: Resolution rates broken down by ticket category
- **Resolution Rate by Agent**: Resolution rates broken down by assigned agent

### Bottleneck Detection

Bottlenecks are identified when:

- **Category Bottlenecks**: Category has >20% open tickets (configurable)
- **Agent Bottlenecks**: Agent has >20% open tickets (configurable)
- **Time Period Bottlenecks**: Specific time periods have >20% of open tickets

Severity levels:
- **Critical**: >=50% impact
- **High**: >=30% impact
- **Medium**: >=20% impact
- **Low**: <20% impact

## Dashboard Features

The performance dashboard includes:

- **Overall Metrics**: Total tickets, resolved tickets, resolution rate, response times, SLA compliance
- **Category Breakdown**: Resolution rates by ticket category
- **Agent Performance**: Resolution rates by assigned agent
- **Bottleneck Alerts**: List of identified bottlenecks with severity and impact
- **Ticket Volume**: Breakdown by ticket status

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
