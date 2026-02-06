# Gift Recommender

Automated gift recommendation system that generates personalized gift suggestions by analyzing recipient preferences, purchase history, and special occasions with price range filtering.

## Project Description

This automation system helps users find the perfect gift by analyzing multiple data points including recipient preferences, historical purchase patterns, special occasions, and budget constraints. The system uses a sophisticated scoring algorithm to rank gift recommendations and provides detailed reasoning for each suggestion.

### Target Audience

- Individuals looking for personalized gift ideas
- Retailers offering gift recommendation services
- E-commerce platforms with gift suggestion features
- Customer service teams providing gift consultation

## Features

- **Recipient Management**: Store and manage recipient profiles with preferences and purchase history
- **Preference Analysis**: Analyzes recipient preferences by category with priority weighting
- **Purchase History Analysis**: Learns from past purchases to identify preferred categories and price ranges
- **Occasion Handling**: Considers special occasions (birthday, anniversary, wedding, etc.) with occasion-specific multipliers
- **Price Range Filtering**: Filters recommendations by budget, low, medium, high, premium, or luxury price ranges
- **Intelligent Scoring**: Multi-factor scoring algorithm combining preferences, purchase history, occasion, and price matching
- **Diversity Algorithm**: Ensures recommendations span multiple categories for variety
- **Report Generation**: Creates HTML and CSV reports with detailed recommendations and reasoning
- **Database Persistence**: Stores all data in SQLite database for historical tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd gift-recommender
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
DATABASE_URL=sqlite:///gift_recommender.db
APP_NAME=Gift Recommender
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize recommendation parameters, price ranges, and occasion settings:

```yaml
recommendations:
  max_recommendations: 10
  min_score_threshold: 0.3
  preference_weight: 0.4
  purchase_history_weight: 0.3
  occasion_weight: 0.2
  price_weight: 0.1

price_ranges:
  budget: 0.0
  low: 25.0
  medium: 100.0
  high: 500.0
  premium: 1000.0
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///gift_recommender.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **recipients**: Default recipient preferences and settings
- **gift_catalog**: Gift catalog categories and default items
- **recommendations**: Recommendation algorithm weights and thresholds
- **occasions**: Occasion types and multipliers
- **price_ranges**: Price range category definitions
- **logging**: Log file location, rotation, and format settings

## Usage

### Add a Recipient

Add a new recipient to the system:

```bash
python src/main.py --add-recipient --name "John Doe" --email "john@example.com" --age 30 --relationship "friend"
```

### Add Preferences

Add preferences for a recipient:

```bash
python src/main.py --add-preference --recipient-id 1 --category "electronics" --interest "gadgets" --priority 5
```

### Generate Recommendations

Generate gift recommendations for a recipient:

```bash
python src/main.py --recommend --recipient-id 1 --occasion "birthday" --price-range "medium" --max-recommendations 10
```

### Filter by Price Range

Generate recommendations within a specific price range:

```bash
python src/main.py --recommend --recipient-id 1 --min-price 50.0 --max-price 200.0
```

### Filter by Categories

Generate recommendations for specific categories:

```bash
python src/main.py --recommend --recipient-id 1 --categories electronics books
```

### Command-Line Arguments

```
--add-recipient          Add a new recipient
--name NAME              Recipient name (required for --add-recipient)
--email EMAIL            Recipient email address
--age AGE                Recipient age
--relationship REL       Relationship type
--add-preference         Add preference for recipient
--recipient-id ID        Recipient ID (required for --add-preference and --recommend)
--category CATEGORY      Preference category (required for --add-preference)
--interest INTEREST      Interest description
--priority PRIORITY      Priority level 1-10 (default: 1)
--recommend              Generate gift recommendations
--occasion OCCASION      Occasion type (birthday, anniversary, wedding, etc.)
--min-price PRICE        Minimum price filter
--max-price PRICE        Maximum price filter
--price-range RANGE      Price range category (budget, low, medium, high, premium)
--categories CATS        Category filters (space-separated)
--max-recommendations N  Maximum number of recommendations
--config PATH            Path to configuration file (default: config.yaml)
```

## Project Structure

```
gift-recommender/
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
│   ├── preference_analyzer.py # Preference analysis
│   ├── purchase_analyzer.py   # Purchase history analysis
│   ├── occasion_handler.py    # Occasion handling
│   ├── price_filter.py        # Price range filtering
│   ├── recommendation_engine.py # Recommendation engine
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── gift_recommendations.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for managing recipients and generating recommendations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for recipients, preferences, purchase history, gift items, and recommendations
- **src/preference_analyzer.py**: Analyzes recipient preferences and calculates category scores
- **src/purchase_analyzer.py**: Analyzes purchase history to identify preferred categories and price patterns
- **src/occasion_handler.py**: Handles special occasions and applies occasion-specific multipliers
- **src/price_filter.py**: Filters and categorizes items by price range
- **src/recommendation_engine.py**: Core recommendation engine with multi-factor scoring algorithm
- **src/report_generator.py**: Generates HTML and CSV reports with recommendations
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
- Preference analysis and scoring
- Purchase history analysis
- Occasion handling
- Price filtering
- Recommendation engine scoring
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

### No Recommendations Generated

**Problem**: System returns no recommendations or very few results.

**Solutions**:
- Ensure recipient has preferences or purchase history
- Lower the `min_score_threshold` in `config.yaml`
- Add more gift items to the catalog
- Check that price filters are not too restrictive
- Verify gift items match recipient's preferred categories

### Low Recommendation Scores

**Problem**: All recommendations have low scores.

**Solutions**:
- Add more preferences for the recipient
- Add purchase history to improve category matching
- Adjust scoring weights in `config.yaml`
- Ensure gift catalog items match recipient interests
- Check that occasion multipliers are being applied

### Price Range Issues

**Problem**: Recommendations don't match expected price range.

**Solutions**:
- Verify price range definitions in `config.yaml`
- Check that gift items have correct price values
- Ensure price filters are applied correctly
- Review price score calculation in recommendation engine

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Recipient not found`: Verify recipient ID exists in database
- `No gift items found`: Add gift items to catalog using database operations
- `Invalid occasion type`: Check that occasion is in configured occasion types

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

## Recommendation Algorithm

The recommendation engine uses a multi-factor scoring system:

1. **Preference Score** (40% weight): Based on recipient's stated preferences by category
2. **Purchase History Score** (30% weight): Based on frequency of purchases in each category
3. **Price Score** (10% weight): How well the item price matches target price or range
4. **Occasion Multiplier** (20% weight): Multiplier applied based on special occasion type

Final scores are normalized to 0.0-1.0 range, and items below the minimum threshold are filtered out. The system also applies diversity to ensure recommendations span multiple categories.

## Gift Catalog Management

To add gift items to the catalog, use the database manager directly or extend the CLI:

```python
from src.database import DatabaseManager
from src.config import get_settings

settings = get_settings()
db_manager = DatabaseManager(settings.database.url)
db_manager.create_tables()

item = db_manager.add_gift_item(
    name="Wireless Headphones",
    category="electronics",
    price=99.99,
    description="High-quality wireless headphones",
    brand="TechBrand",
)
```

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
