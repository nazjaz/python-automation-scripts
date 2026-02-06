"""Tests for content calendar generator main module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.audience_analyzer import AudienceAnalyzer
from src.calendar_generator import CalendarGenerator
from src.config import Settings, load_config
from src.performance_analyzer import PerformanceAnalyzer
from src.posting_time_analyzer import PostingTimeAnalyzer


@pytest.fixture
def sample_settings():
    """Create sample settings for testing."""
    return load_config()


@pytest.fixture
def sample_historical_data():
    """Create sample historical post data."""
    return {
        "facebook": [
            {
                "id": "post_1",
                "timestamp": "2024-01-15T10:30:00",
                "content_type": "social_media",
                "likes": 150,
                "comments": 25,
                "shares": 10,
                "clicks": 50,
                "impressions": 1000,
                "reach": 800,
                "topics": ["technology"],
            },
            {
                "id": "post_2",
                "timestamp": "2024-01-16T14:00:00",
                "content_type": "blog_post",
                "likes": 200,
                "comments": 30,
                "shares": 15,
                "clicks": 75,
                "impressions": 1500,
                "reach": 1200,
                "topics": ["marketing"],
            },
        ],
        "twitter": [
            {
                "id": "tweet_1",
                "timestamp": "2024-01-15T12:00:00",
                "content_type": "announcement",
                "likes": 100,
                "comments": 20,
                "shares": 5,
                "clicks": 30,
                "impressions": 800,
                "reach": 600,
                "topics": ["ai"],
            },
        ],
    }


def test_audience_analyzer_calculate_engagement_score(sample_settings):
    """Test engagement score calculation."""
    analyzer = AudienceAnalyzer(sample_settings)
    metrics = {
        "likes": 100,
        "comments": 20,
        "shares": 10,
        "clicks": 50,
        "impressions": 1000,
        "reach": 800,
    }
    score = analyzer.calculate_engagement_score(metrics)
    assert score > 0
    assert isinstance(score, float)


def test_audience_analyzer_analyze_historical_engagement(
    sample_settings, sample_historical_data
):
    """Test historical engagement analysis."""
    analyzer = AudienceAnalyzer(sample_settings)
    results = analyzer.analyze_historical_engagement(
        sample_historical_data["facebook"]
    )
    assert "average_engagement" in results
    assert "top_performing_content_types" in results
    assert "engagement_by_day" in results
    assert "engagement_by_hour" in results


def test_posting_time_analyzer_analyze_optimal_times(
    sample_settings, sample_historical_data
):
    """Test optimal posting time analysis."""
    analyzer = PostingTimeAnalyzer(sample_settings)
    results = analyzer.analyze_optimal_times(
        sample_historical_data["facebook"]
    )
    assert isinstance(results, dict)


def test_performance_analyzer_analyze_performance(
    sample_settings, sample_historical_data
):
    """Test content performance analysis."""
    analyzer = PerformanceAnalyzer(sample_settings)
    results = analyzer.analyze_performance(
        sample_historical_data["facebook"]
    )
    assert "average_engagement_rate" in results
    assert "average_ctr" in results
    assert "high_performing_content" in results
    assert "performance_by_type" in results


def test_calendar_generator_generate_calendar(sample_settings):
    """Test calendar generation."""
    generator = CalendarGenerator(sample_settings)
    calendar = generator.generate_calendar("facebook")
    assert isinstance(calendar, list)
    assert len(calendar) > 0


def test_calendar_generator_generate_multi_platform_calendar(
    sample_settings
):
    """Test multi-platform calendar generation."""
    generator = CalendarGenerator(sample_settings)
    platforms = ["facebook", "twitter"]
    calendar = generator.generate_multi_platform_calendar(platforms)
    assert isinstance(calendar, dict)
    assert "facebook" in calendar
    assert "twitter" in calendar


def test_calendar_generator_with_historical_data(
    sample_settings, sample_historical_data
):
    """Test calendar generation with historical data."""
    generator = CalendarGenerator(sample_settings)
    calendar = generator.generate_calendar(
        "facebook", sample_historical_data["facebook"]
    )
    assert isinstance(calendar, list)
    assert len(calendar) > 0


def test_settings_load_config():
    """Test configuration loading."""
    settings = load_config()
    assert isinstance(settings, Settings)
    assert settings.calendar.weeks_ahead > 0


def test_settings_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        from src.config import CalendarConfig

        CalendarConfig(content_mix={"type1": 50, "type2": 60})


def test_calendar_post_structure(sample_settings):
    """Test that generated calendar posts have correct structure."""
    generator = CalendarGenerator(sample_settings)
    calendar = generator.generate_calendar("facebook")
    if calendar:
        post = calendar[0]
        assert "platform" in post
        assert "scheduled_time" in post
        assert "date" in post
        assert "time" in post
        assert "content_type" in post
        assert "status" in post


def test_empty_historical_data_handling(sample_settings):
    """Test handling of empty historical data."""
    analyzer = AudienceAnalyzer(sample_settings)
    results = analyzer.analyze_historical_engagement([])
    assert results["average_engagement"] == 0.0
    assert results["top_performing_content_types"] == []


def test_date_parsing(sample_settings):
    """Test date parsing in analyzers."""
    analyzer = AudienceAnalyzer(sample_settings)
    test_dates = [
        "2024-01-15T10:30:00",
        "2024-01-15",
        "2024-01-15 10:30:00",
    ]
    for date_str in test_dates:
        parsed = analyzer._parse_date(date_str)
        assert parsed is not None
        assert isinstance(parsed, datetime)
