# Content Calendar Generator

Automatically generates personalized content calendars by analyzing audience engagement, optimal posting times, and content performance, with automated scheduling across multiple social media platforms.

## Features

- **Audience Engagement Analysis**: Analyzes historical post data to identify engagement patterns and trending topics
- **Optimal Posting Time Detection**: Determines best posting times based on audience activity patterns
- **Content Performance Analysis**: Identifies high-performing content types and formats
- **Multi-Platform Support**: Generates calendars for Facebook, Twitter, Instagram, and LinkedIn
- **Automated Scheduling**: Automatically schedules posts across platforms using platform APIs
- **Personalized Content Mix**: Generates content calendars based on historical performance data
- **Configurable Content Types**: Supports multiple content types with customizable distribution

## Prerequisites

- Python 3.8 or higher
- Social media platform API credentials (Facebook, Twitter, Instagram, LinkedIn)
- Access to historical post data (optional, for analysis)

## Installation

1. Clone or navigate to the project directory:
```bash
cd content-calendar-generator
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API credentials
```

5. Configure settings:
```bash
# Edit config.yaml to customize calendar generation settings
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Facebook API
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# Twitter API
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Instagram API
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id

# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id
```

### Configuration File

The `config.yaml` file contains settings for:
- Calendar generation (weeks ahead, posts per day, content types)
- Platform-specific settings (optimal posting times, posts per day)
- Engagement analysis (metrics, weights, thresholds)
- Performance analysis (metrics, thresholds)
- Scheduling (auto-schedule, retry logic)

## Usage

### Basic Usage

Generate a content calendar for default platforms (Facebook, Twitter):
```bash
python src/main.py
```

### Generate Calendar for Specific Platforms

```bash
python src/main.py --platforms facebook twitter instagram linkedin
```

### Generate Calendar with Historical Data Analysis

```bash
python src/main.py --historical-data data/historical_posts.json
```

### Generate Calendar Starting from Specific Date

```bash
python src/main.py --start-date 2024-01-01
```

### Generate and Schedule Calendar

```bash
python src/main.py --schedule
```

### Dry Run (Generate Without Scheduling)

```bash
python src/main.py --dry-run
```

### Custom Output Path

```bash
python src/main.py --output calendars/my_calendar.json
```

### Using Custom Configuration

```bash
python src/main.py --config custom_config.yaml
```

## Project Structure

```
content-calendar-generator/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── audience_analyzer.py
│   ├── posting_time_analyzer.py
│   ├── performance_analyzer.py
│   ├── calendar_generator.py
│   └── platform_scheduler.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

### File Descriptions

- `src/main.py`: Main entry point and CLI interface
- `src/config.py`: Configuration management and validation
- `src/audience_analyzer.py`: Audience engagement analysis module
- `src/posting_time_analyzer.py`: Optimal posting time analysis module
- `src/performance_analyzer.py`: Content performance analysis module
- `src/calendar_generator.py`: Calendar generation engine
- `src/platform_scheduler.py`: Multi-platform scheduling module

## Historical Data Format

When providing historical data for analysis, use the following JSON format:

```json
{
  "facebook": [
    {
      "id": "post_123",
      "timestamp": "2024-01-15T10:30:00",
      "content_type": "social_media",
      "likes": 150,
      "comments": 25,
      "shares": 10,
      "clicks": 50,
      "impressions": 1000,
      "reach": 800,
      "topics": ["technology", "ai"]
    }
  ],
  "twitter": [
    {
      "id": "tweet_456",
      "timestamp": "2024-01-15T14:00:00",
      "content_type": "announcement",
      "likes": 200,
      "comments": 30,
      "shares": 15,
      "clicks": 75,
      "impressions": 2000,
      "reach": 1500,
      "topics": ["marketing"]
    }
  ]
}
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Common Issues

**Error: "Platform credentials not configured"**
- Ensure all required API credentials are set in `.env` file
- Verify credentials are valid and have necessary permissions

**Error: "Configuration file not found"**
- Ensure `config.yaml` exists in project root
- Use `--config` flag to specify custom config path

**Error: "No historical data provided"**
- Historical data is optional but recommended for better calendar generation
- Calendar will use default optimal times from config if no historical data

**Scheduling fails for specific platform**
- Check API credentials for that platform
- Verify API tokens have scheduling permissions
- Check platform API status and rate limits

### Error Messages

- `FileNotFoundError`: Configuration or data file not found
- `ValueError`: Invalid configuration values (e.g., content mix not summing to 100)
- `PermissionError`: Insufficient API permissions for scheduling
- `requests.RequestException`: API request failed (check network and credentials)

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update README.md for new features
6. Use conventional commit messages

## License

This project is licensed under the MIT License.
