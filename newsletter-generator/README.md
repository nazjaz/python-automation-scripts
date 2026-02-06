# Newsletter Generator

Automated newsletter generation system that automatically generates personalized newsletter content by curating articles, formatting layouts, personalizing sections, and scheduling distribution to subscriber segments.

## Project Description

This automation system provides comprehensive newsletter generation and distribution capabilities. It automatically curates articles from various sources, formats them into professional newsletter layouts, personalizes content for individual subscribers based on preferences and reading history, and schedules distribution to subscriber segments with automated sending.

### Target Audience

- Content marketing teams creating newsletters
- Publishers managing subscriber communications
- Marketing teams sending segmented campaigns
- Organizations distributing regular updates

## Features

- **Article Curation**: Automatically curates articles based on quality, relevance, and recency
- **Layout Formatting**: Formats newsletters with professional HTML templates
- **Personalization**: Personalizes content for individual subscribers based on preferences and history
- **Subscriber Segmentation**: Supports subscriber segments for targeted distribution
- **Scheduling**: Schedules newsletter distribution with configurable send times
- **Multi-Section Support**: Header, greeting, featured article, article list, personalized recommendations, footer
- **Reading History Tracking**: Tracks subscriber reading behavior for personalization
- **Quality Scoring**: Scores articles for quality and relevance
- **HTML Templates**: Customizable HTML newsletter templates

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd newsletter-generator
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
DATABASE_URL=sqlite:///newsletter_generator.db
APP_NAME=Newsletter Generator
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize curation criteria, personalization settings, and distribution options:

```yaml
content_curation:
  min_quality_score: 0.6
  max_article_age_days: 30

personalization:
  enabled: true
  use_subscriber_preferences: true

distribution:
  default_send_time: "09:00"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///newsletter_generator.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **newsletter**: Default settings, article limits, sender information
- **content_curation**: Article sources, curation criteria, quality thresholds
- **personalization**: Personalization levels, enabled features, section personalization
- **layout**: Template path, sections, styling options, responsive settings
- **distribution**: Scheduling settings, send times, batch sizes, retry configuration
- **segments**: Segmentation criteria, default segment, update frequency
- **email**: SMTP settings for email distribution
- **reporting**: Output formats, directory, analytics tracking
- **logging**: Log file location, rotation, and format settings

## Usage

### Add Subscriber

Add a subscriber to the system:

```bash
python src/main.py --add-subscriber --subscriber-id "SUB001" --email "user@example.com" --name "John Doe" --segment "technology"
```

### Add Article

Add an article:

```bash
python src/main.py --add-article --article-id "ART001" --title "Breaking News" --content "Article content..." --category "Technology" --quality-score 0.8
```

### Generate Newsletter

Generate a newsletter:

```bash
python src/main.py --generate-newsletter --newsletter-id "NEWS001" --title "Weekly Newsletter" --segment "technology" --article-count 5
```

### Personalize Newsletter

Personalize newsletter for a subscriber:

```bash
python src/main.py --personalize --newsletter-id "NEWS001" --subscriber-id "SUB001"
```

### Schedule Distribution

Schedule newsletter distribution:

```bash
python src/main.py --schedule --newsletter-id "NEWS001" --segment "technology" --send-time "2024-01-15 09:00"
```

### Send Scheduled

Send scheduled newsletters:

```bash
python src/main.py --send-scheduled
```

### Complete Workflow

Run complete newsletter generation workflow:

```bash
# Add subscribers
python src/main.py --add-subscriber --subscriber-id "SUB001" --email "user1@example.com" --segment "technology"
python src/main.py --add-subscriber --subscriber-id "SUB002" --email "user2@example.com" --segment "business"

# Add articles
python src/main.py --add-article --article-id "ART001" --title "Tech News" --category "Technology" --quality-score 0.9
python src/main.py --add-article --article-id "ART002" --title "Business Update" --category "Business" --quality-score 0.8

# Generate newsletter
python src/main.py --generate-newsletter --newsletter-id "NEWS001" --title "Weekly Update" --segment "technology"

# Schedule distribution
python src/main.py --schedule --newsletter-id "NEWS001" --segment "technology"

# Send scheduled
python src/main.py --send-scheduled
```

### Command-Line Arguments

```
--add-subscriber          Add a subscriber
--subscriber-id ID        Subscriber ID (required)
--email EMAIL             Subscriber email (required)
--name NAME               Subscriber name
--segment SEGMENT         Subscriber segment

--add-article             Add an article
--article-id ID           Article ID (required)
--title TITLE             Article title (required)
--content CONTENT         Article content
--category CATEGORY       Article category
--quality-score SCORE     Quality score (0.0 to 1.0)

--generate-newsletter      Generate newsletter
--newsletter-id ID        Newsletter ID (required)
--title TITLE             Newsletter title (required)
--segment SEGMENT         Subscriber segment
--article-count COUNT     Number of articles

--personalize             Personalize newsletter for subscriber
--newsletter-id ID        Newsletter ID (required)
--subscriber-id ID        Subscriber ID (required)

--schedule                Schedule newsletter distribution
--newsletter-id ID        Newsletter ID (required)
--segment SEGMENT         Subscriber segment
--send-time TIME          Send time (YYYY-MM-DD HH:MM)

--send-scheduled          Send scheduled newsletters

--config PATH             Path to configuration file (default: config.yaml)
```

## Project Structure

```
newsletter-generator/
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
│   ├── article_curator.py    # Article curation
│   ├── layout_formatter.py   # Layout formatting
│   ├── personalization_engine.py # Content personalization
│   └── distribution_scheduler.py # Distribution scheduling
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Newsletter templates
│   └── newsletter_template.html # HTML newsletter template
├── docs/                     # Documentation
├── newsletters/             # Generated newsletters
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for subscribers, articles, newsletters, distributions, reading history
- **src/article_curator.py**: Curates articles based on quality, relevance, and recency
- **src/layout_formatter.py**: Formats newsletters with HTML templates
- **src/personalization_engine.py**: Personalizes content for individual subscribers
- **src/distribution_scheduler.py**: Schedules and sends newsletter distributions
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
- Article curation algorithms
- Layout formatting functionality
- Personalization engine logic
- Distribution scheduling
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

### Article Curation Issues

**Problem**: No articles being curated or insufficient articles.

**Solutions**:
- Verify articles have been added to the database
- Check article quality scores meet minimum threshold
- Ensure articles are recent (within max age limit)
- Review curation criteria in configuration
- Add more articles to the database

### Personalization Not Working

**Problem**: Personalization not applying or showing expected results.

**Solutions**:
- Verify personalization is enabled in `config.yaml`
- Check subscriber preferences are set correctly
- Ensure reading history exists for personalization
- Review personalization level settings
- Check logs for personalization process details

### Distribution Scheduling Failures

**Problem**: Newsletters not being scheduled or sent.

**Solutions**:
- Verify newsletter has been generated
- Check subscriber segment exists
- Ensure send time format is correct (YYYY-MM-DD HH:MM)
- Review scheduling configuration
- Check logs for scheduling errors

### Template Rendering Errors

**Problem**: Newsletter template not rendering correctly.

**Solutions**:
- Verify template file exists at configured path
- Check template syntax is valid Jinja2
- Ensure all required template variables are provided
- Review template file permissions
- Check logs for template rendering errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Subscriber not found`: Verify subscriber ID exists in database
- `Article not found`: Verify article ID exists in database
- `Newsletter not found`: Verify newsletter ID exists in database
- `No articles available for curation`: Add articles to the database
- `Invalid send time format`: Use YYYY-MM-DD HH:MM format

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

## Article Curation

Articles are curated based on:

- **Relevance**: Relevance score (if available)
- **Recency**: How recent the article is (within max age)
- **Quality**: Quality score threshold
- **Popularity**: Can be added based on engagement metrics

## Personalization Features

Personalization considers:

- **Subscriber Preferences**: Category and tag preferences
- **Reading History**: Previously read articles (avoid duplicates, prioritize new content)
- **Demographics**: Demographic-based recommendations
- **Segment**: Segment-specific content

## Newsletter Sections

Supported newsletter sections:

- **Header**: Newsletter title and branding
- **Greeting**: Personalized greeting with subscriber name
- **Featured Article**: Highlighted main article
- **Article List**: List of curated articles
- **Personalized Recommendations**: Articles recommended for subscriber
- **Footer**: Unsubscribe links and preferences

## Distribution Scheduling

Distribution features:

- **Scheduled Sending**: Schedule newsletters for specific times
- **Segment Targeting**: Send to specific subscriber segments
- **Batch Processing**: Process distributions in batches
- **Retry Logic**: Automatic retry for failed sends
- **Send Tracking**: Track sent, opened, and clicked status

## Subscriber Segments

Segments can be based on:

- **Demographics**: Age, location, etc.
- **Preferences**: Content preferences and interests
- **Engagement**: Reading behavior and interaction
- **Geography**: Geographic location

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
