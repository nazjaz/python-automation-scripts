# Customer Review Processor

Automated customer review processing system that extracts key themes, calculates sentiment scores, identifies product issues, and generates actionable improvement recommendations.

## Project Description

This automation system processes customer reviews to provide comprehensive insights for product teams. The system analyzes review text to extract themes, determine sentiment, identify product issues, and generate prioritized recommendations for product improvements.

### Target Audience

- Product managers analyzing customer feedback
- Quality assurance teams identifying product issues
- Customer success teams tracking sentiment trends
- Business analysts generating insights from review data
- Development teams prioritizing improvements

## Features

- **Sentiment Analysis**: Calculates sentiment scores and classifies reviews as positive, negative, or neutral
- **Theme Extraction**: Identifies key themes and topics from reviews using natural language processing
- **Issue Identification**: Automatically detects product issues with severity classification
- **Recommendation Generation**: Generates prioritized improvement recommendations based on identified issues
- **Comprehensive Reporting**: Creates HTML and CSV reports with visualizations and detailed metrics
- **Database Persistence**: Stores all review data, themes, issues, and recommendations in SQLite database
- **Batch Processing**: Processes multiple reviews efficiently with configurable limits
- **Flexible Import**: Supports importing reviews from text files or programmatic addition

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd customer-review-processor
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
DATABASE_URL=sqlite:///customer_reviews.db
APP_NAME=Customer Review Processor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize sentiment analysis, theme extraction, issue identification, and recommendation settings:

```yaml
sentiment:
  positive_threshold: 0.1
  negative_threshold: -0.1

themes:
  min_theme_length: 2
  max_themes_per_review: 5
  theme_categories:
    quality:
      - "quality"
      - "durable"
      - "broken"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///customer_reviews.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **sentiment**: Sentiment analysis thresholds and parameters
- **themes**: Theme extraction settings including categories and keywords
- **issues**: Issue identification settings including keywords and severity classification
- **recommendations**: Recommendation generation settings including priority weights and templates
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Import Reviews from File

Import reviews from a text file (one review per line):

```bash
python src/main.py --import reviews.txt --source amazon
```

### Process Reviews

Process imported reviews to extract themes, analyze sentiment, and identify issues:

```bash
python src/main.py --process --limit 100
```

### Generate Reports

Generate HTML and CSV reports with analysis results:

```bash
python src/main.py --report
```

### Complete Workflow

Run the complete workflow (import, process, and report):

```bash
python src/main.py --import reviews.txt --process --report
```

### Product-Specific Analysis

Filter operations by specific product ID:

```bash
python src/main.py --process --product-id prod123
python src/main.py --report --product-id prod123
```

### Command-Line Arguments

```
--process              Process customer reviews
--report              Generate analysis reports
--import FILE         Import reviews from text file
--product-id ID       Filter by specific product ID
--limit LIMIT         Maximum number of reviews to process
--source SOURCE       Review source identifier (default: file)
--config PATH         Path to configuration file (default: config.yaml)
```

## Project Structure

```
customer-review-processor/
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
│   ├── sentiment_analyzer.py # Sentiment analysis
│   ├── theme_extractor.py    # Theme extraction
│   ├── issue_identifier.py   # Issue identification
│   ├── recommendation_generator.py # Recommendation generation
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── review_report.html    # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates review import, processing, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for reviews, themes, issues, and recommendations
- **src/sentiment_analyzer.py**: Calculates sentiment scores using TextBlob
- **src/theme_extractor.py**: Extracts key themes using NLTK and frequency analysis
- **src/issue_identifier.py**: Identifies product issues with severity classification
- **src/recommendation_generator.py**: Generates prioritized improvement recommendations
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

- Sentiment analysis functionality
- Theme extraction algorithms
- Issue identification logic
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

### No Reviews to Process

**Problem**: "No unprocessed reviews found" message.

**Solutions**:
- Run `--import` command first to add reviews to database
- Verify reviews were successfully imported (check database)
- Ensure reviews meet minimum length requirements
- Check logs for import errors

### Sentiment Analysis Issues

**Problem**: All reviews showing neutral sentiment.

**Solutions**:
- Verify review text is not empty or too short
- Check sentiment thresholds in `config.yaml`
- Review logs for sentiment analysis errors
- Ensure TextBlob is properly installed and NLTK data is downloaded

### Theme Extraction Not Working

**Problem**: No themes extracted from reviews.

**Solutions**:
- Verify NLTK data is downloaded (punkt, stopwords)
- Check theme extraction settings in `config.yaml`
- Ensure reviews contain sufficient text (minimum length)
- Review theme category keywords configuration

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient review data has been processed
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Review file not found`: Verify the file path provided to `--import` is correct
- `Template not found`: HTML template file missing, system will use default template
- `NLTK data not found`: Run Python and execute `nltk.download('punkt')` and `nltk.download('stopwords')`

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

## Natural Language Processing

### NLTK Data Requirements

The system uses NLTK for text processing. Required NLTK data is automatically downloaded on first use:

- `punkt`: Sentence tokenization
- `stopwords`: Stop word filtering

If automatic download fails, manually download:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### TextBlob Sentiment Analysis

The system uses TextBlob for sentiment analysis, which provides polarity scores ranging from -1.0 (negative) to 1.0 (positive). The system classifies reviews based on configurable thresholds.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
