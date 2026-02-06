# Content Performance Monitor API Documentation

## Overview

The Content Performance Monitor provides a comprehensive API for monitoring content performance across multiple platforms, analyzing engagement metrics, and generating strategic recommendations.

## Architecture

The system is built with a modular architecture:

- **Platform Connectors**: Collect data from various social media platforms
- **Metrics Analyzer**: Calculates engagement, reach, and performance scores
- **Top Content Identifier**: Identifies and ranks top-performing content
- **Strategy Recommender**: Generates actionable content strategy recommendations
- **Report Generator**: Creates HTML and CSV reports with insights

## Database Schema

### ContentPost

Stores information about content posts across platforms.

- `id`: Primary key
- `platform`: Platform name (facebook, twitter, instagram, linkedin, youtube)
- `content_id`: Unique content identifier on platform
- `title`: Content title or description
- `content_type`: Type of content (video, image, text, link)
- `posted_at`: When content was posted
- `created_at`: When record was created

### ContentMetrics

Stores performance metrics for content posts.

- `id`: Primary key
- `content_post_id`: Foreign key to ContentPost
- `platform`: Platform name
- `metric_name`: Name of metric (likes, comments, views, etc.)
- `metric_value`: Numeric value of metric
- `recorded_at`: When metric was recorded

### ContentAnalysis

Stores analysis results and scores for content.

- `id`: Primary key
- `content_post_id`: Foreign key to ContentPost
- `platform`: Platform name
- `engagement_score`: Calculated engagement score (0.0 to 1.0)
- `reach_score`: Calculated reach score (0.0 to 1.0)
- `views_score`: Calculated views score (0.0 to 1.0)
- `overall_score`: Overall performance score (0.0 to 1.0)
- `analyzed_at`: When analysis was performed
- `recommendations`: Text recommendations (optional)

## Usage Examples

### Collecting Content Data

```python
from src.config import load_config, get_settings
from src.database import DatabaseManager
from src.platform_connector import PlatformManager

config = load_config()
settings = get_settings()
db_manager = DatabaseManager(settings.database.url)
db_manager.create_tables()

platform_manager = PlatformManager(db_manager, config["platforms"])
platform_data = platform_manager.collect_content_data(limit=100, days=30)
platform_manager.store_content_data(platform_data)
```

### Analyzing Content Performance

```python
from src.metrics_analyzer import MetricsAnalyzer

analyzer = MetricsAnalyzer(db_manager, config["platforms"])
analyzed_count = analyzer.analyze_all_content(platform="facebook", days=30)
```

### Generating Reports

```python
from src.top_content_identifier import TopContentIdentifier
from src.strategy_recommender import StrategyRecommender
from src.report_generator import ReportGenerator

identifier = TopContentIdentifier(db_manager, top_count=10)
recommender = StrategyRecommender(db_manager, identifier, config)
generator = ReportGenerator(db_manager, identifier, recommender, config)

reports = generator.generate_reports(platform="facebook")
```

## Extending the System

### Adding a New Platform

1. Create a new connector class inheriting from `PlatformConnector`
2. Implement `normalize_metrics()` method for platform-specific metric mapping
3. Optionally implement `fetch_content_data()` for real API integration
4. Add platform configuration to `config.yaml`
5. Register connector in `PlatformManager`

### Adding New Metrics

1. Add metric name to platform configuration in `config.yaml`
2. Update `normalize_metrics()` in platform connector if needed
3. Adjust scoring weights in platform configuration
4. Update report templates to display new metrics
