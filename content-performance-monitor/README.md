# Content Performance Monitor

Automated content performance monitoring system that tracks content across multiple platforms, analyzes engagement metrics, identifies top-performing content, and generates actionable content strategy recommendations.

## Project Description

This automation system monitors content performance across social media and content platforms, providing comprehensive analytics and strategic insights. The system collects performance data, calculates engagement scores, identifies top-performing content, and generates data-driven recommendations to optimize content strategy.

### Target Audience

- Marketing teams managing multi-platform content strategies
- Social media managers tracking content performance
- Content creators analyzing engagement and optimizing posting strategies
- Analytics teams generating performance reports and insights

## Features

- **Multi-Platform Monitoring**: Supports Facebook, Twitter, Instagram, LinkedIn, and YouTube
- **Engagement Metrics Analysis**: Calculates engagement, reach, and views scores with platform-specific weighting
- **Top Content Identification**: Automatically identifies and ranks top-performing content across platforms
- **Strategy Recommendations**: Generates actionable recommendations based on performance trends and top content analysis
- **Performance Reports**: Creates HTML and CSV reports with visualizations and detailed metrics
- **Trend Analysis**: Analyzes posting patterns, optimal timing, and content type performance
- **Database Persistence**: Stores all content data and metrics in SQLite database for historical tracking
- **Extensible Architecture**: Easy to add new platforms and metrics through connector system

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Platform API access (optional, for real-time data collection)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd content-performance-monitor
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
DATABASE_URL=sqlite:///content_performance.db
APP_NAME=Content Performance Monitor
LOG_LEVEL=INFO

# Optional: Platform API Keys (for real API integrations)
# FACEBOOK_API_KEY=your-facebook-api-key
# TWITTER_API_KEY=your-twitter-api-key
# INSTAGRAM_API_KEY=your-instagram-api-key
# LINKEDIN_API_KEY=your-linkedin-api-key
# YOUTUBE_API_KEY=your-youtube-api-key
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize platform settings, analysis parameters, and reporting options:

```yaml
platforms:
  - name: "facebook"
    enabled: true
    metrics:
      - "likes"
      - "comments"
      - "shares"
      - "views"
      - "reach"
    weight:
      engagement: 0.4
      reach: 0.3
      views: 0.3

analysis:
  top_content_count: 10
  analysis_period_days: 30
  engagement_threshold: 0.05

strategy:
  recommendation_count: 5
  trend_analysis_days: 7
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///content_performance.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `FACEBOOK_API_KEY` | Facebook API key for data collection | No |
| `TWITTER_API_KEY` | Twitter/X API key for data collection | No |
| `INSTAGRAM_API_KEY` | Instagram API key for data collection | No |
| `LINKEDIN_API_KEY` | LinkedIn API key for data collection | No |
| `YOUTUBE_API_KEY` | YouTube API key for data collection | No |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **platforms**: Platform configurations including enabled status, metrics to track, and scoring weights
- **analysis**: Analysis parameters including top content count, analysis period, and engagement thresholds
- **strategy**: Strategy recommendation settings including recommendation count and trend analysis period
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Collect Content Data

Collect content performance data from all enabled platforms:

```bash
python src/main.py --collect --days 30 --limit 100
```

### Analyze Content Performance

Analyze collected content and calculate performance scores:

```bash
python src/main.py --analyze --days 30
```

### Generate Strategy Report

Generate content strategy report with recommendations:

```bash
python src/main.py --report
```

### Platform-Specific Operations

Filter operations by specific platform:

```bash
python src/main.py --collect --platform facebook --days 30
python src/main.py --analyze --platform twitter --days 30
python src/main.py --report --platform instagram
```

### Complete Workflow

Run the complete workflow (collect, analyze, and report):

```bash
python src/main.py --collect --analyze --report --days 30
```

### Command-Line Arguments

```
--collect              Collect content data from platforms
--analyze              Analyze content performance and calculate scores
--report               Generate content strategy report
--platform PLATFORM   Filter by specific platform (facebook, twitter, instagram, linkedin, youtube)
--days DAYS           Number of days to look back (default: 30)
--limit LIMIT         Maximum content items per platform (default: 100)
--config PATH         Path to configuration file (default: config.yaml)
```

## Project Structure

```
content-performance-monitor/
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
│   ├── platform_connector.py # Platform data connectors
│   ├── metrics_analyzer.py    # Engagement metrics analysis
│   ├── top_content_identifier.py # Top content identification
│   ├── strategy_recommender.py  # Strategy recommendations
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── strategy_report.html  # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates data collection, analysis, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for content and metrics
- **src/platform_connector.py**: Platform-specific connectors for data collection (Facebook, Twitter, Instagram, LinkedIn, YouTube)
- **src/metrics_analyzer.py**: Calculates engagement, reach, views, and overall performance scores
- **src/top_content_identifier.py**: Identifies and ranks top-performing content
- **src/strategy_recommender.py**: Generates content strategy recommendations based on performance analysis
- **src/report_generator.py**: Generates HTML and CSV reports with recommendations and metrics
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
- Metrics calculation and analysis
- Top content identification
- Strategy recommendation generation
- Report generation (HTML and CSV)
- Platform connector functionality
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

### No Content Data Available

**Problem**: Reports show "No content data available" or empty results.

**Solutions**:
- Run `--collect` command first to gather content data
- Verify platform connectors are enabled in `config.yaml`
- Check that platform API keys are configured if using real API integrations
- Review logs for data collection errors
- Ensure sufficient content exists in the specified time period

### Low Engagement Scores

**Problem**: All content shows low engagement scores.

**Solutions**:
- Verify metrics are being collected correctly (check database)
- Adjust engagement threshold in `config.yaml` if needed
- Review platform-specific metric mappings
- Check that views/impressions data is available for engagement rate calculation

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient content data has been analyzed
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `No metrics found for content post`: Content data may not have been collected or stored correctly
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

## Platform Integration

### Adding Real API Integrations

The system includes platform connectors that currently use mock data. To integrate with real platform APIs:

1. Obtain API credentials from each platform
2. Add API keys to `.env` file
3. Implement `fetch_content_data()` method in platform connector classes
4. Update `normalize_metrics()` if platform API response format differs
5. Test integration with small data sets first

### Supported Platforms

- **Facebook**: Posts, engagement metrics, reach, impressions
- **Twitter/X**: Tweets, likes, retweets, replies, views, impressions
- **Instagram**: Posts, likes, comments, saves, views, reach
- **LinkedIn**: Posts, engagement metrics, views, impressions
- **YouTube**: Videos, likes, comments, views, watch time, subscribers

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
