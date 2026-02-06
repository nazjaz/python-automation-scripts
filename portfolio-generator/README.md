# Portfolio Generator

Automated investment portfolio generation system that creates personalized investment portfolios based on risk tolerance, financial goals, and market conditions, with rebalancing recommendations.

## Project Description

This automation system provides comprehensive portfolio generation and management capabilities. It analyzes investor risk tolerance, calculates portfolio requirements based on financial goals, generates personalized asset allocations, and provides rebalancing recommendations to maintain optimal portfolio balance.

### Target Audience

- Individual investors seeking personalized portfolio recommendations
- Financial advisors managing client portfolios
- Investment platforms providing automated portfolio services
- Wealth management firms optimizing client allocations

## Features

- **Personalized Portfolio Generation**: Creates portfolios tailored to individual risk tolerance and financial goals
- **Risk Tolerance Analysis**: Analyzes investor characteristics to recommend appropriate risk levels
- **Goal-Based Planning**: Calculates portfolio requirements based on financial goals and time horizons
- **Asset Allocation**: Automatically allocates assets across stocks, bonds, and cash based on risk profile
- **Rebalancing Recommendations**: Identifies when portfolios need rebalancing and provides specific recommendations
- **Multi-Asset Class Support**: Supports stocks (large cap, mid cap, small cap, international), bonds (government, corporate, municipal), and alternatives
- **Market Condition Awareness**: Considers market conditions when generating recommendations
- **Performance Tracking**: Tracks portfolio performance and allocation drift
- **Multi-Format Reports**: Generates HTML and CSV portfolio reports

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd portfolio-generator
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
DATABASE_URL=sqlite:///portfolio_generator.db
APP_NAME=Portfolio Generator
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize portfolio settings, risk allocations, and rebalancing thresholds:

```yaml
portfolio:
  default_currency: "USD"
  rebalancing_threshold: 0.05

risk_tolerance:
  conservative_allocation:
    stocks: 0.30
    bonds: 0.50
    cash: 0.20
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///portfolio_generator.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **portfolio**: Default currency, minimum investment, rebalancing thresholds
- **risk_tolerance**: Risk levels and corresponding asset allocations
- **asset_classes**: Available asset classes and types
- **financial_goals**: Goal types and time horizons
- **market_conditions**: Market condition tracking settings
- **rebalancing**: Rebalancing frequency, thresholds, and tax awareness
- **optimization**: Portfolio optimization method and parameters
- **reporting**: Output formats and directory settings
- **logging**: Log file location, rotation, and format settings

## Usage

### Add an Investor

Add an investor to the system:

```bash
python src/main.py --add-investor --investor-id "INV001" --name "John Doe" --email "john@example.com" --risk-tolerance "moderate" --age 35 --horizon-years 20
```

### Add a Financial Goal

Add a financial goal for an investor:

```bash
python src/main.py --add-goal --investor-id "INV001" --goal-type "retirement" --target-amount 1000000 --target-date "2045-12-31" --priority "high"
```

### Generate Portfolio

Generate a personalized portfolio:

```bash
python src/main.py --generate-portfolio --investor-id "INV001" --portfolio-name "Retirement Portfolio" --initial-investment 50000
```

### Analyze Risk Tolerance

Analyze investor's risk tolerance:

```bash
python src/main.py --analyze-risk --investor-id "INV001"
```

### Calculate Goal Requirements

Calculate portfolio requirements for goals:

```bash
python src/main.py --calculate-goals --investor-id "INV001"
```

### Check Rebalancing

Check if portfolio needs rebalancing:

```bash
python src/main.py --check-rebalancing --portfolio-id 1
```

### Generate Report

Generate portfolio report:

```bash
python src/main.py --generate-report --portfolio-id 1 --format html
```

### Complete Workflow

Run complete portfolio generation workflow:

```bash
# Add investor
python src/main.py --add-investor --investor-id "INV001" --name "John Doe" --email "john@example.com" --risk-tolerance "moderate"

# Add goal
python src/main.py --add-goal --investor-id "INV001" --goal-type "retirement" --target-amount 1000000 --target-date "2045-12-31"

# Analyze risk
python src/main.py --analyze-risk --investor-id "INV001"

# Calculate requirements
python src/main.py --calculate-goals --investor-id "INV001"

# Generate portfolio
python src/main.py --generate-portfolio --investor-id "INV001" --portfolio-name "Retirement Portfolio" --initial-investment 50000

# Check rebalancing
python src/main.py --check-rebalancing --portfolio-id 1

# Generate report
python src/main.py --generate-report --portfolio-id 1
```

### Command-Line Arguments

```
--add-investor              Add an investor
--investor-id ID            Investor ID (required)
--name NAME                  Investor name (required)
--email EMAIL                Investor email (required)
--risk-tolerance LEVEL       Risk tolerance: conservative, moderate, aggressive (required)
--age AGE                    Investor age
--horizon-years YEARS        Investment horizon in years

--add-goal                   Add a financial goal
--investor-id ID             Investor ID (required)
--goal-type TYPE             Goal type: retirement, education, house_purchase, emergency_fund, wealth_building (required)
--target-amount AMOUNT        Target amount (required)
--target-date DATE           Target date YYYY-MM-DD (required)
--priority LEVEL             Priority: low, medium, high (default: medium)

--generate-portfolio         Generate personalized portfolio
--investor-id ID             Investor ID (required)
--portfolio-name NAME        Portfolio name (required)
--initial-investment AMOUNT  Initial investment amount (required)
--risk-tolerance LEVEL       Optional risk tolerance override

--analyze-risk               Analyze investor risk tolerance
--investor-id ID             Investor ID (required)

--calculate-goals            Calculate portfolio requirements for goals
--investor-id ID             Investor ID (required)

--check-rebalancing          Check if portfolio needs rebalancing
--portfolio-id ID             Portfolio ID (required)

--generate-report            Generate portfolio report
--portfolio-id ID            Portfolio ID (required)
--format FORMAT              Report format: html or csv (default: html)

--config PATH                Path to configuration file (default: config.yaml)
```

## Project Structure

```
portfolio-generator/
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
│   ├── portfolio_generator.py # Portfolio generation logic
│   ├── risk_analyzer.py      # Risk tolerance analysis
│   ├── goal_calculator.py    # Financial goal calculations
│   ├── rebalancing_engine.py # Rebalancing recommendations
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── portfolio_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for investors, portfolios, holdings, goals, market conditions, recommendations
- **src/portfolio_generator.py**: Generates personalized portfolios based on risk tolerance and goals
- **src/risk_analyzer.py**: Analyzes investor characteristics to determine risk tolerance
- **src/goal_calculator.py**: Calculates portfolio requirements based on financial goals
- **src/rebalancing_engine.py**: Identifies rebalancing needs and generates recommendations
- **src/report_generator.py**: Generates HTML and CSV portfolio reports
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
- Portfolio generation logic
- Risk tolerance analysis
- Goal requirement calculations
- Rebalancing detection and recommendations
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

### Portfolio Generation Failures

**Problem**: Portfolio generation fails or produces unexpected results.

**Solutions**:
- Verify investor exists in database
- Check risk tolerance is one of: conservative, moderate, aggressive
- Ensure initial investment amount is positive
- Review asset class configuration in `config.yaml`
- Check logs for specific error messages

### Rebalancing Not Detected

**Problem**: Rebalancing recommendations not generated when expected.

**Solutions**:
- Verify rebalancing is enabled in `config.yaml`
- Check drift threshold settings
- Ensure portfolio has holdings with market values
- Verify minimum rebalance amount threshold
- Check that sufficient time has passed since last rebalancing

### Goal Calculation Errors

**Problem**: Goal requirements calculation produces incorrect results.

**Solutions**:
- Verify target date is in the future
- Check that target amount is positive
- Ensure investor risk tolerance is set correctly
- Review expected return assumptions in configuration
- Check logs for calculation details

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Investor not found`: Verify investor ID exists in database
- `Invalid risk tolerance`: Use one of: conservative, moderate, aggressive
- `Invalid date format`: Use YYYY-MM-DD format for dates
- `Portfolio not found`: Verify portfolio ID exists in database

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

## Risk Tolerance Levels

The system supports three risk tolerance levels:

### Conservative

- **Stocks**: 30%
- **Bonds**: 50%
- **Cash**: 20%
- **Expected Return**: ~4% annually
- **Suitable for**: Risk-averse investors, short-term goals, retirees

### Moderate

- **Stocks**: 60%
- **Bonds**: 30%
- **Cash**: 10%
- **Expected Return**: ~7% annually
- **Suitable for**: Balanced investors, medium-term goals, mid-career professionals

### Aggressive

- **Stocks**: 80%
- **Bonds**: 15%
- **Cash**: 5%
- **Expected Return**: ~10% annually
- **Suitable for**: Risk-tolerant investors, long-term goals, young professionals

## Financial Goals

Supported goal types:

- **Retirement**: Long-term retirement savings
- **Education**: Education fund for children or self
- **House Purchase**: Down payment and home purchase
- **Emergency Fund**: Short-term emergency savings
- **Wealth Building**: General wealth accumulation

## Rebalancing

The system automatically:

- Monitors portfolio allocation drift
- Identifies when allocations deviate from targets
- Generates specific buy/sell recommendations
- Considers minimum rebalance amounts
- Tracks rebalancing frequency

Rebalancing is recommended when:
- Allocation drift exceeds threshold (default: 5%)
- Minimum rebalance amount is met (default: $100)
- Sufficient time has passed since last rebalance (default: 90 days)

## Portfolio Reports

Reports include:

- **Portfolio Summary**: Total value, number of holdings
- **Holdings Table**: Asset details, allocations, drift analysis
- **Rebalancing Recommendations**: Specific actions to rebalance portfolio
- **Performance Metrics**: Allocation percentages, target vs. current

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
