# Content Recommender

Automated personalized content recommendation system that generates recommendations by analyzing user preferences, viewing history, and engagement patterns across multiple content types.

## Project Description

This automation system provides comprehensive content recommendation for users. The system automatically analyzes user preferences from explicit preferences and viewing history, tracks viewing history with ratings and completion rates, analyzes engagement patterns across content types, and generates personalized recommendations using a hybrid approach combining preference matching, history similarity, and engagement scores. This helps content platforms, media services, and e-learning platforms improve user experience and content discovery.

### Target Audience

- Content platforms providing personalized recommendations
- Media services optimizing content discovery
- E-learning platforms personalizing learning content
- Streaming services improving user engagement
- Content managers analyzing user behavior

## Features

- **User Preference Analysis**: Analyzes user preferences by category, content type, and tags with weight-based scoring
- **Viewing History Analysis**: Analyzes viewing history with ratings, completion rates, watch time, and similar content identification
- **Engagement Pattern Analysis**: Analyzes engagement patterns across content types with views, watch time, completion rates, and ratings
- **Personalized Recommendations**: Generates personalized recommendations using hybrid approach combining preference matching, history similarity, and engagement scores
- **Multi-Content Type Support**: Supports multiple content types (video, article, podcast, etc.) with type-specific analysis
- **Recommendation Tracking**: Tracks recommendation performance with click-through rates, conversion rates, and engagement metrics
- **Comprehensive Reporting**: Generates HTML and CSV reports with user preferences, viewing history, engagement patterns, and recommendations
- **Database Persistence**: Stores all users, content, preferences, viewing history, engagement patterns, recommendations, and metrics in SQLite database
- **Flexible Configuration**: Customizable recommendation weights, analysis parameters, and reporting settings
- **Performance Metrics**: Tracks key performance indicators including recommendation scores, click-through rates, and conversion rates

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd content-recommender
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
DATABASE_URL=sqlite:///content_recommender.db
APP_NAME=Content Recommender
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize recommendation weights and analysis parameters:

```yaml
recommendation:
  recommendation_weights:
    preference: 0.3
    history: 0.4
    engagement: 0.3
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///content_recommender.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **preference_analysis**: User preference analysis configuration
- **history_analysis**: Viewing history analysis settings
- **engagement_analysis**: Engagement pattern analysis settings
- **recommendation**: Recommendation generation settings including weights for preference, history, and engagement
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Analyze User Preferences

Analyze user preferences:

```bash
python src/main.py --analyze-preferences "USER001"
```

### Extract Preferences from History

Extract preferences from viewing history:

```bash
python src/main.py --extract-preferences "USER001"
```

### Analyze Viewing History

Analyze viewing history:

```bash
python src/main.py --analyze-history "USER001" --days 30
```

### Analyze Engagement Patterns

Analyze engagement patterns:

```bash
python src/main.py --analyze-engagement "USER001" --days 30
```

### Generate Recommendations

Generate personalized recommendations:

```bash
python src/main.py --generate-recommendations "USER001" --limit 10 --content-type "video"
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --user-id "USER001"
```

### Complete Workflow

Run complete recommendation workflow:

```bash
# Extract preferences from history
python src/main.py --extract-preferences "USER001"

# Analyze viewing history
python src/main.py --analyze-history "USER001"

# Analyze engagement
python src/main.py --analyze-engagement "USER001"

# Generate recommendations
python src/main.py --generate-recommendations "USER001" --limit 10

# Generate reports
python src/main.py --report
```

### Command-Line Arguments

```
--analyze-preferences USER_ID          Analyze user preferences
--extract-preferences USER_ID          Extract preferences from viewing history
--analyze-history USER_ID              Analyze viewing history
--analyze-engagement USER_ID          Analyze engagement patterns
--generate-recommendations USER_ID     Generate personalized recommendations
--report                               Generate analysis reports
--user-id ID                           Filter by user ID
--limit N                              Maximum number of recommendations (default: 10)
--content-type TYPE                    Filter by content type
--days N                               Number of days to analyze (default: 30)
--config PATH                          Path to configuration file (default: config.yaml)
```

## Project Structure

```
content-recommender/
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
│   ├── preference_analyzer.py # User preference analysis
│   ├── history_analyzer.py   # Viewing history analysis
│   ├── engagement_analyzer.py # Engagement pattern analysis
│   ├── recommendation_generator.py # Recommendation generation
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── recommendation_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates preference analysis, history analysis, engagement analysis, recommendation generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for users, content, preferences, viewing history, engagement patterns, recommendations, and metrics
- **src/preference_analyzer.py**: Analyzes user preferences with extraction from history
- **src/history_analyzer.py**: Analyzes viewing history with similarity scoring
- **src/engagement_analyzer.py**: Analyzes engagement patterns across content types
- **src/recommendation_generator.py**: Generates personalized recommendations using hybrid approach
- **src/report_generator.py**: Generates HTML and CSV reports with recommendation data
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

- Preference analysis functionality
- History analysis algorithms
- Engagement pattern analysis
- Recommendation generation logic
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

### Preferences Not Extracted

**Problem**: Preferences are not being extracted from viewing history.

**Solutions**:
- Verify user has viewing history entries
- Check minimum views threshold in extraction logic
- Ensure content has category, content_type, or tags
- Review preference extraction settings
- Check that preferences are being saved to database

### Recommendations Not Generated

**Problem**: Recommendations are not being generated or scores are low.

**Solutions**:
- Verify user has preferences or viewing history
- Check that content exists in database
- Review recommendation weights in configuration
- Ensure all analyzers are working correctly
- Check that recommendation scores are calculated properly

### Low Recommendation Quality

**Problem**: Recommendations have low scores or poor relevance.

**Solutions**:
- Adjust recommendation weights in `config.yaml`
- Ensure sufficient user data (preferences, history, engagement)
- Review preference extraction thresholds
- Check that content metadata is complete
- Verify engagement patterns are being tracked

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient user and recommendation data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `User not found`: Verify user ID is correct and user exists
- `Content not found`: Ensure content is created before generating recommendations
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

## Content Types

The system supports various content types:

- **video**: Video content
- **article**: Article/blog content
- **podcast**: Podcast/audio content
- **course**: Course/educational content
- **book**: Book/e-book content
- **other**: Other content types

Content types are used for engagement analysis and filtering.

## Preference Types

The system tracks various preference types:

- **category**: Content category preferences
- **content_type**: Content type preferences
- **tag**: Tag preferences
- **duration**: Duration preferences
- **other**: Other preference types

Preferences are weighted and used in recommendation scoring.

## Recommendation Types

The system supports various recommendation types:

- **preference_based**: Based on user preferences
- **history_based**: Based on viewing history similarity
- **engagement_based**: Based on engagement patterns
- **hybrid**: Combination of all factors (default)

Recommendation types help understand recommendation sources.

## Recommendation Scores

Recommendations are scored from 0.0 to 1.0:

- **0.8-1.0**: High relevance, strong match
- **0.5-0.8**: Medium relevance, good match
- **0.0-0.5**: Low relevance, weak match

Scores are calculated using weighted combination of preference, history, and engagement scores.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
