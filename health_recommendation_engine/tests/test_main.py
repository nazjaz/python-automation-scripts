"""Tests for health recommendation engine."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from health_recommendation_engine.src.main import (
    ActivityDataConfig,
    ActivityMetrics,
    RecommendationConfig,
    RecommendationPriority,
    SleepDataConfig,
    SleepMetrics,
    analyze_activity,
    analyze_sleep,
    generate_recommendations,
)


def test_analyze_activity_basic():
    """Test basic activity analysis."""
    now = datetime.now()
    activities = [
        ActivityMetrics(
            date=now - timedelta(days=2),
            steps=8000,
            calories=2000.0,
            active_minutes=25,
        ),
        ActivityMetrics(
            date=now - timedelta(days=1),
            steps=12000,
            calories=2500.0,
            active_minutes=35,
        ),
        ActivityMetrics(date=now, steps=10000, calories=2200.0, active_minutes=30),
    ]

    config = RecommendationConfig(target_steps_per_day=10000, target_active_minutes=30)

    summary = analyze_activity(activities, config)

    assert summary["avg_steps_per_day"] == 10000.0
    assert summary["total_steps"] == 30000
    assert summary["days_with_data"] == 3
    assert summary["steps_target_met_days"] == 2


def test_analyze_sleep_basic():
    """Test basic sleep analysis."""
    now = datetime.now()
    sleep_records = [
        SleepMetrics(
            date=now - timedelta(days=2),
            sleep_hours=7.0,
            sleep_quality=7.5,
        ),
        SleepMetrics(
            date=now - timedelta(days=1),
            sleep_hours=8.0,
            sleep_quality=8.0,
        ),
        SleepMetrics(date=now, sleep_hours=7.5, sleep_quality=7.8),
    ]

    config = RecommendationConfig(
        target_sleep_hours=7.5, min_sleep_hours=7.0, max_sleep_hours=9.0
    )

    summary = analyze_sleep(sleep_records, config)

    assert summary["avg_sleep_hours"] == 7.5
    assert summary["min_sleep_hours"] == 7.0
    assert summary["max_sleep_hours"] == 8.0
    assert summary["days_with_data"] == 3
    assert summary["sleep_target_met_days"] == 3
    assert summary["avg_sleep_quality"] == pytest.approx(7.77, abs=0.01)


def test_generate_recommendations_low_steps():
    """Test recommendation generation for low step count."""
    activity_summary = {"avg_steps_per_day": 5000.0}
    sleep_summary = {"avg_sleep_hours": 7.5}
    health_summary = {}

    config = RecommendationConfig(target_steps_per_day=10000)

    recommendations = generate_recommendations(
        activity_summary, sleep_summary, health_summary, config
    )

    assert len(recommendations) > 0
    steps_rec = next(
        (r for r in recommendations if "steps" in r.title.lower()), None
    )
    assert steps_rec is not None
    assert steps_rec.priority == RecommendationPriority.HIGH
    assert steps_rec.current_value == 5000.0
    assert steps_rec.target_value == 10000.0


def test_generate_recommendations_low_sleep():
    """Test recommendation generation for insufficient sleep."""
    activity_summary = {"avg_steps_per_day": 10000.0}
    sleep_summary = {"avg_sleep_hours": 6.0}
    health_summary = {}

    config = RecommendationConfig(
        target_sleep_hours=7.5, min_sleep_hours=7.0, max_sleep_hours=9.0
    )

    recommendations = generate_recommendations(
        activity_summary, sleep_summary, health_summary, config
    )

    assert len(recommendations) > 0
    sleep_rec = next(
        (r for r in recommendations if "sleep" in r.title.lower() and "duration" in r.title.lower()),
        None,
    )
    assert sleep_rec is not None
    assert sleep_rec.priority == RecommendationPriority.HIGH
    assert sleep_rec.current_value == 6.0


def test_generate_recommendations_poor_sleep_quality():
    """Test recommendation generation for poor sleep quality."""
    activity_summary = {"avg_steps_per_day": 10000.0}
    sleep_summary = {"avg_sleep_hours": 7.5, "avg_sleep_quality": 5.0}
    health_summary = {}

    config = RecommendationConfig()

    recommendations = generate_recommendations(
        activity_summary, sleep_summary, health_summary, config
    )

    quality_rec = next(
        (r for r in recommendations if "quality" in r.title.lower()),
        None,
    )
    assert quality_rec is not None
    assert quality_rec.current_value == 5.0


def test_empty_data_handling():
    """Test handling of empty data."""
    activity_summary = {}
    sleep_summary = {}
    health_summary = {}

    config = RecommendationConfig()

    recommendations = generate_recommendations(
        activity_summary, sleep_summary, health_summary, config
    )

    assert isinstance(recommendations, list)


def test_activity_summary_calculation():
    """Test activity summary calculation with missing data."""
    now = datetime.now()
    activities = [
        ActivityMetrics(date=now, steps=10000),
        ActivityMetrics(date=now - timedelta(days=1), calories=2000.0),
        ActivityMetrics(date=now - timedelta(days=2), active_minutes=30),
    ]

    config = RecommendationConfig()

    summary = analyze_activity(activities, config)

    assert "avg_steps_per_day" in summary
    assert summary["avg_steps_per_day"] == 10000.0
    assert summary["days_with_data"] == 1
