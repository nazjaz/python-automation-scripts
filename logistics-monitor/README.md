# Logistics Monitor

Automated supply chain logistics monitoring system that monitors supply chain logistics, tracks shipments, predicts delays, and generates logistics reports with route optimization recommendations.

## Project Description

This automation system provides comprehensive logistics monitoring and optimization for supply chains. The system tracks shipments in real-time, predicts potential delays, optimizes routes for efficiency, monitors overall logistics performance, and generates detailed reports with actionable recommendations. This helps logistics managers, supply chain coordinators, and operations teams maintain efficient supply chains and respond quickly to issues.

### Target Audience

- Logistics managers monitoring supply chain operations
- Supply chain coordinators tracking shipments
- Operations teams optimizing routes and deliveries
- Warehouse managers coordinating shipments
- Transportation managers managing fleet operations

## Features

- **Shipment Tracking**: Real-time tracking of shipments with location updates and status monitoring
- **Delay Prediction**: Predicts potential delays based on various factors (weather, traffic, customs, etc.) with severity assessment
- **Route Optimization**: Optimizes shipment routes to reduce time, distance, and cost with savings calculations
- **Logistics Monitoring**: Monitors overall logistics performance including on-time delivery rates and trends
- **Performance Metrics**: Tracks key performance indicators including on-time percentage, average delays, and delivery trends
- **Optimization Recommendations**: Generates actionable route optimization recommendations with expected savings
- **Comprehensive Reporting**: Generates HTML and CSV reports with logistics metrics, trends, active shipments, and recommendations
- **Database Persistence**: Stores all suppliers, shipments, routes, tracking events, delays, and recommendations in SQLite database
- **Flexible Configuration**: Customizable tracking settings, delay factors, optimization parameters, and reporting options
- **Multi-Supplier Support**: Supports multiple suppliers with individual shipment tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd logistics-monitor
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
DATABASE_URL=sqlite:///logistics_monitor.db
APP_NAME=Logistics Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize tracking, delay prediction, route optimization, and monitoring settings:

```yaml
delay_prediction:
  delay_factors:
    weather: 0.3
    traffic: 0.2

route_optimization:
  optimization_factors:
    distance: 0.4
    time: 0.4
    cost: 0.2
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///logistics_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **tracking**: Shipment tracking configuration
- **delay_prediction**: Delay prediction settings including delay factors
- **route_optimization**: Route optimization settings including optimization factors
- **monitoring**: Logistics monitoring configuration
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Track Shipment

Track shipment status and location:

```bash
python src/main.py --track shipment1
```

### Predict Delay

Predict delay for a shipment:

```bash
python src/main.py --predict-delay shipment1 weather --delay-reason "Heavy rain"
python src/main.py --predict-delay shipment1 traffic --delay-reason "Road closure"
```

### Optimize Route

Optimize route for a shipment:

```bash
python src/main.py --optimize-route shipment1
```

### Monitor Logistics

Monitor logistics performance:

```bash
python src/main.py --monitor --days 7
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --shipment-id shipment1
```

### Complete Workflow

Run complete logistics monitoring workflow:

```bash
# Track shipments
python src/main.py --track shipment1

# Predict delays
python src/main.py --predict-delay shipment1 weather

# Optimize routes
python src/main.py --optimize-route shipment1

# Monitor performance
python src/main.py --monitor --days 7

# Generate reports
python src/main.py --report
```

### Command-Line Arguments

```
--track SHIPMENT_ID              Track shipment
--predict-delay SHIPMENT_ID TYPE Predict delay for shipment
--optimize-route SHIPMENT_ID    Optimize route for shipment
--monitor                       Monitor logistics performance
--report                        Generate logistics reports
--shipment-id ID                Filter by shipment ID
--days DAYS                     Number of days to analyze
--delay-reason REASON           Delay reason
--config PATH                   Path to configuration file (default: config.yaml)
```

## Project Structure

```
logistics-monitor/
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
│   ├── shipment_tracker.py   # Shipment tracking
│   ├── delay_predictor.py    # Delay prediction
│   ├── route_optimizer.py    # Route optimization
│   ├── logistics_monitor.py # Logistics monitoring
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── logistics_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates shipment tracking, delay prediction, route optimization, logistics monitoring, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for suppliers, shipments, routes, tracking events, delays, optimization recommendations, and logistics metrics
- **src/shipment_tracker.py**: Tracks shipments and updates status with location tracking
- **src/delay_predictor.py**: Predicts delays based on various factors with risk analysis
- **src/route_optimizer.py**: Optimizes routes to reduce time, distance, and cost
- **src/logistics_monitor.py**: Monitors logistics performance and trends
- **src/report_generator.py**: Generates HTML and CSV reports with logistics data
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

- Shipment tracking functionality
- Delay prediction algorithms
- Route optimization logic
- Logistics monitoring
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

### Shipment Not Found

**Problem**: Shipment tracking returns "Shipment not found".

**Solutions**:
- Verify shipment ID is correct
- Ensure shipment exists in database
- Check that supplier and shipment were created properly
- Review shipment creation process

### Delay Prediction Issues

**Problem**: Delay predictions are inaccurate or not working.

**Solutions**:
- Verify delay factors are configured correctly in `config.yaml`
- Check that shipment has route information
- Ensure delay type is valid (weather, traffic, customs, etc.)
- Review delay prediction algorithm settings

### Route Optimization Not Working

**Problem**: Route optimization returns no savings or errors.

**Solutions**:
- Verify shipment has existing route to optimize
- Check that origin and destination are set correctly
- Ensure optimization factors are configured
- Review route calculation logic

### No Reports Generated

**Problem**: Reports are not being generated.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient shipment data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Shipment not found`: Verify shipment ID is correct and shipment exists
- `Supplier not found`: Ensure supplier exists before creating shipments
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

## Delay Types

The system supports various delay types:

- **weather**: Weather-related delays (rain, snow, storms)
- **traffic**: Traffic congestion delays
- **customs**: Customs clearance delays
- **mechanical**: Vehicle/equipment mechanical issues
- **other**: Other types of delays

Delay predictions are based on configured delay factors and shipment characteristics.

## Route Optimization

Route optimization considers multiple factors:

- **distance**: Minimize total distance traveled
- **time**: Minimize total travel time
- **cost**: Minimize transportation costs

Optimization recommendations include expected time and cost savings.

## Shipment Statuses

The system tracks various shipment statuses:

- **pending**: Shipment created but not yet shipped
- **in_transit**: Shipment is in transit
- **shipped**: Shipment has been shipped
- **delivered**: Shipment has been delivered

Status updates are tracked through tracking events.

## Priority Levels

Shipments can have different priority levels:

- **low**: Low priority shipments
- **normal**: Normal priority (default)
- **high**: High priority shipments
- **urgent**: Urgent priority shipments

Priority affects delay calculations and route optimization.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
