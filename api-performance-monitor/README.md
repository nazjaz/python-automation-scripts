# API Performance Monitor

Automated API performance monitoring system that monitors API endpoint performance, tracks response times, identifies slow endpoints, and generates optimization recommendations with bottleneck analysis.

## Project Description

This automation system provides comprehensive monitoring and analysis of API endpoint performance. It continuously monitors endpoints, tracks response times with percentile analysis, identifies performance bottlenecks, and generates actionable optimization recommendations to help improve API performance and reliability.

### Target Audience

- API developers monitoring endpoint performance
- DevOps teams tracking API health
- Performance engineers optimizing APIs
- Technical leads reviewing API metrics

## Features

- **Endpoint Monitoring**: Continuously monitors API endpoints with configurable intervals
- **Response Time Tracking**: Tracks response times with percentile analysis (P50, P75, P90, P95, P99)
- **Slow Endpoint Detection**: Automatically identifies slow and very slow endpoints based on thresholds
- **Bottleneck Analysis**: Identifies performance bottlenecks (response time, error rate, throughput)
- **Optimization Recommendations**: Generates actionable recommendations for performance improvements
- **Performance Metrics**: Calculates comprehensive metrics including error rates and throughput
- **Multi-Format Reports**: Generates HTML and CSV performance reports
- **Database Persistence**: Stores all monitoring data, metrics, and analysis results

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Internet connection (for monitoring APIs)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd api-performance-monitor
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
DATABASE_URL=sqlite:///api_performance.db
APP_NAME=API Performance Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize monitoring intervals, thresholds, and analysis options:

```yaml
monitoring:
  check_interval_seconds: 60
  timeout_seconds: 30

performance:
  slow_endpoint_threshold_ms: 1000
  very_slow_endpoint_threshold_ms: 5000

bottleneck_detection:
  enabled: true
  error_rate_threshold: 0.05
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///api_performance.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **monitoring**: Check intervals, timeouts, retries, SSL verification
- **performance**: Response time thresholds, percentile calculations, analysis windows
- **bottleneck_detection**: Bottleneck detection settings and thresholds
- **endpoints**: Default HTTP methods, headers, authentication, rate limiting
- **optimization**: Recommendation generation settings
- **reporting**: Output formats, directory, inclusion options
- **logging**: Log file location, rotation, and format settings

## Usage

### Add an Endpoint

Add an API endpoint to monitor:

```bash
python src/main.py --add-endpoint --base-url "https://api.example.com" --path "/users" --method "GET" --description "Get users endpoint"
```

### Monitor Endpoint

Monitor a single endpoint:

```bash
python src/main.py --monitor --endpoint-id 1
```

### Analyze Performance

Analyze endpoint performance:

```bash
python src/main.py --analyze --endpoint-id 1 --analyze-hours 24
```

### Identify Bottlenecks

Identify performance bottlenecks:

```bash
python src/main.py --identify-bottlenecks --endpoint-id 1 --bottleneck-hours 24
```

### Generate Recommendations

Generate optimization recommendations:

```bash
python src/main.py --generate-recommendations --endpoint-id 1
```

### Generate Report

Generate performance report:

```bash
python src/main.py --generate-report --endpoint-id 1 --format html
```

### Complete Workflow

Run complete monitoring workflow:

```bash
# Add endpoint and monitor
python src/main.py --add-endpoint --base-url "https://api.example.com" --path "/users"
python src/main.py --monitor --endpoint-id 1

# Analyze and generate report
python src/main.py --analyze --endpoint-id 1
python src/main.py --identify-bottlenecks --endpoint-id 1
python src/main.py --generate-recommendations --endpoint-id 1
python src/main.py --generate-report --endpoint-id 1
```

### Command-Line Arguments

```
--add-endpoint          Add an API endpoint to monitor
--base-url URL          Base URL of the API (required)
--path PATH             Endpoint path (required)
--method METHOD         HTTP method (GET, POST, PUT, DELETE, PATCH, default: GET)
--description DESC      Endpoint description

--monitor               Monitor an API endpoint
--endpoint-id ID        Endpoint ID (required)

--analyze               Analyze endpoint performance
--endpoint-id ID        Optional endpoint ID filter
--analyze-hours HOURS   Hours to analyze (default: 24)

--identify-bottlenecks   Identify performance bottlenecks
--endpoint-id ID        Optional endpoint ID filter
--bottleneck-hours HOURS Hours to analyze (default: 24)

--generate-recommendations  Generate optimization recommendations
--endpoint-id ID        Optional endpoint ID filter

--generate-report       Generate performance report
--endpoint-id ID        Optional endpoint ID filter
--format FORMAT         Report format (html or csv, default: html)

--config PATH           Path to configuration file (default: config.yaml)
```

## Project Structure

```
api-performance-monitor/
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
│   ├── api_monitor.py        # API endpoint monitoring
│   ├── response_time_tracker.py # Response time tracking and analysis
│   ├── bottleneck_analyzer.py  # Bottleneck detection
│   ├── recommendation_engine.py # Optimization recommendations
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── performance_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for endpoints, requests, metrics, bottlenecks, recommendations
- **src/api_monitor.py**: Monitors API endpoints and records request/response data
- **src/response_time_tracker.py**: Tracks response times and calculates percentile metrics
- **src/bottleneck_analyzer.py**: Analyzes performance data to identify bottlenecks
- **src/recommendation_engine.py**: Generates optimization recommendations
- **src/report_generator.py**: Generates HTML and CSV performance reports
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
- API monitoring functionality
- Response time tracking and percentile calculations
- Bottleneck detection algorithms
- Recommendation generation
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

### API Monitoring Failures

**Problem**: Endpoint monitoring fails or returns errors.

**Solutions**:
- Verify endpoint URL is correct and accessible
- Check internet connection
- Review timeout settings in `config.yaml`
- Ensure API doesn't block automated monitoring
- Check SSL certificate verification settings
- Review logs for specific error messages

### No Metrics Generated

**Problem**: Performance analysis shows no metrics.

**Solutions**:
- Ensure endpoints have been monitored (requests recorded)
- Verify minimum request threshold is met
- Check date/time filters for analysis window
- Review analysis window hours parameter
- Ensure requests have response times recorded

### Bottlenecks Not Identified

**Problem**: No bottlenecks are being identified.

**Solutions**:
- Verify bottleneck detection is enabled in `config.yaml`
- Check that minimum sample threshold is met
- Ensure sufficient monitoring data exists
- Review bottleneck thresholds (error rate, response time)
- Check logs for detection errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Endpoint not found`: Verify endpoint ID exists in database
- `Connection timeout`: Increase timeout_seconds in `config.yaml` or check network
- `Invalid URL`: Verify endpoint URL format is correct
- `Insufficient samples`: Ensure enough requests have been recorded for analysis

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

- **Average Response Time**: Mean response time across all requests
- **Percentile Response Times**: P50, P75, P90, P95, P99 response times
- **Min/Max Response Times**: Minimum and maximum observed response times

### Reliability Metrics

- **Request Count**: Total number of requests
- **Success Count**: Number of successful requests (2xx status codes)
- **Error Count**: Number of error requests (4xx, 5xx status codes)
- **Error Rate**: Percentage of requests that resulted in errors

### Throughput Metrics

- **Throughput per Second**: Requests per second based on time window

## Bottleneck Detection

Bottlenecks are identified in the following areas:

### Response Time Bottlenecks

- **Critical**: P99 response time exceeds very slow threshold (default: 5000ms)
- **High**: P95 response time exceeds slow threshold (default: 1000ms)

### Error Rate Bottlenecks

- **Critical**: Error rate >= 10%
- **High**: Error rate >= 5% (configurable threshold)

### Throughput Bottlenecks

- **Medium**: Throughput degradation >= 20% (configurable threshold)

## Optimization Recommendations

The system generates recommendations for:

- **Caching**: Suggests implementing response caching for GET endpoints with high response times
- **Compression**: Recommends enabling response compression for large responses
- **Pagination**: Suggests pagination for endpoints returning large datasets
- **Query Optimization**: Recommends database query optimization for slow endpoints

## Report Features

Performance reports include:

- **Endpoint Performance Table**: Comprehensive metrics for all endpoints
- **Slow Endpoints Section**: List of endpoints exceeding performance thresholds
- **Bottleneck Analysis**: Detailed bottleneck information with severity
- **Optimization Recommendations**: Actionable recommendations with priorities
- **Time-based Analysis**: Performance trends over specified time windows

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
