# Content Calendar Generator API Documentation

## Overview

The Content Calendar Generator provides a comprehensive API for generating personalized content calendars and scheduling posts across multiple social media platforms.

## Modules

### config.py

Configuration management and validation.

#### Classes

**Settings**
- Main settings container for application configuration
- Validates all configuration sections on initialization

**PlatformConfig**
- Configuration for individual social media platforms
- Fields: `enabled`, `optimal_times`, `posts_per_day`

**CalendarConfig**
- Calendar generation settings
- Fields: `weeks_ahead`, `posts_per_day`, `content_types`, `content_mix`
- Validates that content mix percentages sum to 100

#### Functions

**load_config(config_path: Optional[Path] = None) -> Settings**
- Load configuration from YAML file
- Returns validated Settings object
- Raises FileNotFoundError if config file doesn't exist

**get_settings() -> Settings**
- Get application settings with environment variables loaded
- Returns Settings object

**get_env_var(key: str, default: Optional[str] = None) -> Optional[str]**
- Get environment variable value
- Returns value or default

### audience_analyzer.py

Audience engagement analysis module.

#### Classes

**AudienceAnalyzer**
- Analyzes audience engagement patterns from historical data

**Methods**

**calculate_engagement_score(metrics: Dict[str, float]) -> float**
- Calculate weighted engagement score from metrics
- Uses configured metric weights
- Returns float score

**analyze_historical_engagement(historical_data: List[Dict]) -> Dict**
- Analyze historical engagement data
- Returns dictionary with:
  - average_engagement: Average engagement score
  - top_performing_content_types: List of best content types
  - engagement_by_day: Engagement by day of week
  - engagement_by_hour: Engagement by hour of day
  - trending_topics: List of trending topics

**get_optimal_content_types(analysis_results: Dict) -> List[str]**
- Get optimal content types based on engagement analysis
- Returns list of content types ordered by performance

### posting_time_analyzer.py

Optimal posting time analysis module.

#### Classes

**PostingTimeAnalyzer**
- Analyzes optimal posting times from historical data

**Methods**

**analyze_optimal_times(historical_data: List[Dict]) -> Dict**
- Analyze optimal posting times by day of week
- Returns dictionary mapping day names to list of (hour, score) tuples

**get_optimal_hours_for_day(optimal_times: Dict, day: str) -> List[int]**
- Get optimal hours for a specific day
- Returns list of optimal hours

**get_best_time_slots(optimal_times: Dict) -> Dict[str, List[int]]**
- Get best time slots across all days
- Returns dictionary mapping day names to optimal hours

### performance_analyzer.py

Content performance analysis module.

#### Classes

**PerformanceAnalyzer**
- Analyzes content performance metrics

**Methods**

**analyze_performance(historical_data: List[Dict]) -> Dict**
- Analyze content performance from historical data
- Returns dictionary with:
  - average_engagement_rate: Average engagement rate
  - average_ctr: Average click-through rate
  - high_performing_content: List of high-performing content IDs
  - performance_by_type: Performance metrics by content type
  - performance_trends: Performance trends over time

**get_best_content_types(performance_results: Dict) -> List[str]**
- Get best performing content types
- Returns list of content types ordered by performance

### calendar_generator.py

Content calendar generation module.

#### Classes

**CalendarGenerator**
- Generates personalized content calendars

**Methods**

**generate_calendar(platform: str, historical_data: Optional[List[Dict]] = None, start_date: Optional[datetime] = None) -> List[Dict]**
- Generate content calendar for a platform
- Returns list of scheduled content items with dates, times, and metadata

**generate_multi_platform_calendar(platforms: List[str], historical_data: Optional[Dict[str, List[Dict]]] = None, start_date: Optional[datetime] = None) -> Dict[str, List[Dict]]**
- Generate calendars for multiple platforms
- Returns dictionary mapping platform names to their calendars

### platform_scheduler.py

Platform scheduling module.

#### Classes

**PlatformScheduler**
- Manages scheduling of content across platforms

**Methods**

**schedule_post(platform: str, post: Dict[str, any]) -> Dict[str, any]**
- Schedule a single post on a platform
- Returns dictionary with scheduling result

**schedule_calendar(calendar: Dict[str, List[Dict]]) -> Dict[str, Dict]**
- Schedule all posts in a calendar
- Returns dictionary mapping platform names to scheduling results

## Data Formats

### Historical Data Format

```json
{
  "platform_name": [
    {
      "id": "post_id",
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
  ]
}
```

### Calendar Format

```json
{
  "platform_name": [
    {
      "platform": "facebook",
      "scheduled_time": "2024-01-20T09:00:00",
      "date": "2024-01-20",
      "time": "09:00",
      "content_type": "social_media",
      "status": "pending",
      "title": "Social Media - January 20, 2024"
    }
  ]
}
```

## Error Handling

All modules use specific exception types:
- `FileNotFoundError`: Configuration or data file not found
- `ValueError`: Invalid configuration values
- `PermissionError`: Insufficient API permissions
- `requests.RequestException`: API request failures

## Logging

All modules use Python's logging module with structured logging:
- INFO: Normal operations and status updates
- WARNING: Non-critical issues
- ERROR: Errors that prevent operation
- DEBUG: Detailed debugging information
