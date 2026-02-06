# Cloud Resource Monitor

Automated cloud resource monitoring system that monitors cloud resource utilization, identifies idle resources, recommends right-sizing, and automatically scales resources based on demand patterns.

## Project Description

This automation system provides comprehensive cloud resource monitoring and optimization capabilities. It continuously monitors resource utilization metrics, identifies underutilized or idle resources, generates right-sizing recommendations to optimize costs, and automatically scales resources based on demand patterns and utilization thresholds.

### Target Audience

- Cloud infrastructure teams managing resource optimization
- DevOps engineers monitoring cloud costs
- System administrators tracking resource utilization
- Organizations optimizing cloud spending

## Features

- **Resource Monitoring**: Continuously monitors CPU, memory, disk, and network utilization
- **Idle Detection**: Identifies idle resources based on configurable thresholds
- **Right-Sizing Recommendations**: Analyzes utilization patterns and recommends instance type changes
- **Auto-Scaling**: Automatically scales resources based on demand patterns and utilization thresholds
- **Demand Pattern Analysis**: Detects daily, weekly, and seasonal usage patterns
- **Cost Analysis**: Estimates cost savings from right-sizing recommendations
- **HTML Reports**: Generates comprehensive resource utilization reports
- **Multi-Cloud Support**: Supports AWS, Azure, and GCP resources

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd cloud-resource-monitor
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
DATABASE_URL=sqlite:///cloud_resource_monitor.db
APP_NAME=Cloud Resource Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize monitoring intervals, idle thresholds, scaling policies, and reporting options:

```yaml
monitoring:
  check_interval_minutes: 15
  metrics_collection_window_hours: 24

idle_detection:
  idle_thresholds:
    cpu_utilization: 5.0
    memory_utilization: 10.0

auto_scaling:
  scale_up_threshold: 75.0
  scale_down_threshold: 25.0
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///cloud_resource_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **monitoring**: Check intervals, metrics collection, resource types, metrics to track
- **idle_detection**: Idle thresholds, duration requirements, minimum samples
- **right_sizing**: Analysis window, utilization thresholds, recommendation types, cost awareness
- **auto_scaling**: Scaling policies, thresholds, cooldown periods, instance limits
- **resources**: Cloud providers, resource states, cost tracking
- **demand_patterns**: Pattern detection, prediction windows, minimum data points
- **reporting**: Output formats, directory, analytics inclusion
- **logging**: Log file location, rotation, and format settings

## Usage

### Add Resource

Add a cloud resource to monitor:

```bash
python src/main.py --add-resource --resource-id "i-1234567890abcdef0" --resource-name "Web Server" --resource-type "compute" --cloud-provider "aws" --instance-type "t2.micro" --cost-per-hour 0.01
```

### Collect Metrics

Collect utilization metrics for a resource:

```bash
python src/main.py --collect-metrics --resource-id "i-1234567890abcdef0" --cpu-utilization 45.0 --memory-utilization 60.0 --disk-utilization 30.0
```

### Detect Idle Resources

Detect idle resources:

```bash
python src/main.py --detect-idle
```

Or for a specific resource:

```bash
python src/main.py --detect-idle --resource-id "i-1234567890abcdef0"
```

### Recommend Right-Sizing

Generate right-sizing recommendations:

```bash
python src/main.py --recommend-right-sizing
```

Or for a specific resource:

```bash
python src/main.py --recommend-right-sizing --resource-id "i-1234567890abcdef0"
```

### Check Scaling Needs

Check if a resource needs scaling:

```bash
python src/main.py --check-scaling --resource-id "i-1234567890abcdef0"
```

### Analyze Demand Patterns

Analyze demand patterns for a resource:

```bash
python src/main.py --analyze-patterns --resource-id "i-1234567890abcdef0"
```

### Generate Report

Generate resource monitoring report:

```bash
python src/main.py --generate-report --format html
```

### Complete Workflow

Run complete resource monitoring workflow:

```bash
# Add resources
python src/main.py --add-resource --resource-id "i-001" --resource-name "Web Server 1" --resource-type "compute" --cloud-provider "aws" --instance-type "t2.micro" --cost-per-hour 0.01
python src/main.py --add-resource --resource-id "i-002" --resource-name "Web Server 2" --resource-type "compute" --cloud-provider "aws" --instance-type "t2.small" --cost-per-hour 0.02

# Collect metrics
python src/main.py --collect-metrics --resource-id "i-001" --cpu-utilization 20.0 --memory-utilization 15.0
python src/main.py --collect-metrics --resource-id "i-002" --cpu-utilization 85.0 --memory-utilization 90.0

# Detect idle resources
python src/main.py --detect-idle

# Generate recommendations
python src/main.py --recommend-right-sizing

# Check scaling
python src/main.py --check-scaling --resource-id "i-002"

# Generate report
python src/main.py --generate-report
```

### Command-Line Arguments

```
--add-resource              Add a cloud resource
--resource-id ID            Resource ID (required)
--resource-name NAME         Resource name (required)
--resource-type TYPE         Resource type: compute, storage, database, network, container (required)
--cloud-provider PROVIDER    Cloud provider: aws, azure, gcp (required)
--instance-type TYPE         Instance type
--cost-per-hour COST         Cost per hour

--collect-metrics            Collect metrics for resource
--resource-id ID             Resource ID (required)
--cpu-utilization PERCENT    CPU utilization percentage
--memory-utilization PERCENT  Memory utilization percentage
--disk-utilization PERCENT   Disk utilization percentage

--detect-idle                Detect idle resources
--resource-id ID             Optional resource ID filter

--recommend-right-sizing     Recommend right-sizing
--resource-id ID             Optional resource ID filter

--check-scaling              Check if resource needs scaling
--resource-id ID             Resource ID (required)

--analyze-patterns           Analyze demand patterns
--resource-id ID             Resource ID (required)

--generate-report            Generate resource monitoring report
--format FORMAT              Report format: html (default: html)

--config PATH                Path to configuration file (default: config.yaml)
```

## Project Structure

```
cloud-resource-monitor/
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
│   ├── resource_monitor.py   # Resource utilization monitoring
│   ├── idle_detector.py      # Idle resource detection
│   ├── right_sizing_analyzer.py # Right-sizing recommendations
│   ├── auto_scaler.py        # Auto-scaling logic
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── resource_report.html  # HTML report template
├── docs/                     # Documentation
├── reports/                  # Generated reports
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for resources, metrics, recommendations, scaling actions, idle resources, demand patterns
- **src/resource_monitor.py**: Monitors resource utilization and collects metrics
- **src/idle_detector.py**: Detects idle resources based on utilization thresholds
- **src/right_sizing_analyzer.py**: Analyzes utilization and generates right-sizing recommendations
- **src/auto_scaler.py**: Automatically scales resources based on demand patterns
- **src/report_generator.py**: Generates HTML reports with resource utilization and recommendations
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
- Resource monitoring functionality
- Idle detection algorithms
- Right-sizing analysis logic
- Auto-scaling evaluation
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

### Metrics Collection Issues

**Problem**: Metrics not being collected or stored.

**Solutions**:
- Verify resource exists in database
- Check metric values are within valid ranges (0-100 for percentages)
- Ensure resource ID is correct
- Review logs for metric collection errors
- Check database connection and permissions

### Idle Detection Not Working

**Problem**: Idle resources not being detected.

**Solutions**:
- Verify idle detection is enabled in `config.yaml`
- Check idle thresholds are appropriate for your resources
- Ensure sufficient metrics have been collected (minimum samples)
- Review idle duration requirements
- Check that resources are in "running" state

### Right-Sizing Recommendations Missing

**Problem**: No right-sizing recommendations generated.

**Solutions**:
- Verify right-sizing is enabled in configuration
- Ensure sufficient metrics collected (minimum samples requirement)
- Check utilization thresholds are appropriate
- Review analysis window settings
- Verify resources have utilization metrics

### Auto-Scaling Not Triggering

**Problem**: Auto-scaling not being triggered when expected.

**Solutions**:
- Verify auto-scaling is enabled in configuration
- Check scaling thresholds are appropriate
- Ensure cooldown period has elapsed since last action
- Verify resources have recent metrics
- Review scaling policies configuration
- Check min/max instance limits

### Report Generation Failures

**Problem**: Reports not being generated or incomplete.

**Solutions**:
- Verify output directory exists and is writable
- Check template file exists at configured path
- Ensure database has data to report
- Review template syntax is valid Jinja2
- Check logs for template rendering errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Resource not found`: Verify resource ID exists in database
- `Insufficient metrics`: Collect more metrics before analysis
- `Invalid metric value`: Ensure metric values are within valid ranges
- `Scaling not enabled`: Enable auto-scaling in configuration

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

## Resource Monitoring

The system monitors the following metrics:

- **CPU Utilization**: Percentage of CPU usage
- **Memory Utilization**: Percentage of memory usage
- **Disk Utilization**: Percentage of disk usage
- **Network I/O**: Network input/output metrics
- **Request Count**: Number of requests per time period

## Idle Detection

Resources are considered idle when:

- Utilization metrics fall below configured thresholds
- Idle condition persists for minimum duration
- Minimum number of samples collected
- All or specific metrics meet idle criteria

## Right-Sizing Recommendations

Recommendations are generated based on:

- **Underutilized Resources**: Average utilization below threshold → Downsize recommendation
- **Overutilized Resources**: P95 utilization above threshold → Upsize recommendation
- **Cost Analysis**: Estimated cost savings or increases
- **Priority Levels**: High, medium, low based on utilization extremes

## Auto-Scaling

Auto-scaling features:

- **CPU-Based Scaling**: Scale based on CPU utilization
- **Memory-Based Scaling**: Scale based on memory utilization
- **Request-Based Scaling**: Scale based on request count
- **Cooldown Periods**: Prevent rapid scaling changes
- **Instance Limits**: Min/max instance constraints
- **Approval Requirements**: Optional approval before scaling

## Demand Pattern Analysis

Pattern detection includes:

- **Daily Cycles**: Hourly usage patterns
- **Weekly Cycles**: Day-of-week patterns
- **Seasonal Patterns**: Long-term trends
- **Spike Detection**: Unusual usage spikes
- **Prediction**: Forecasted demand based on patterns

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
