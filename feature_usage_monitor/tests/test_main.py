"""Tests for feature usage monitoring analytics."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Set

import pandas as pd
import pytest

from feature_usage_monitor.src.main import (
    AdoptionMetrics,
    FeatureConfig,
    FeatureUsage,
    UnusedFeature,
    UsageDataConfig,
    analyze_feature_usage,
    calculate_adoption_rates,
    identify_unused_features,
)


def test_analyze_feature_usage_basic():
    """Test basic feature usage analysis."""
    now = datetime.now()
    df = pd.DataFrame(
        {
            "user_id": ["user1", "user2", "user1", "user3"],
            "feature_name": ["feature_a", "feature_a", "feature_b", "feature_a"],
            "timestamp": [
                now - timedelta(hours=2),
                now - timedelta(hours=1),
                now - timedelta(hours=3),
                now,
            ],
        }
    )

    config = UsageDataConfig(
        file_path="dummy.csv",
        user_id_column="user_id",
        feature_name_column="feature_name",
        timestamp_column="timestamp",
    )

    from feature_usage_monitor.src.main import AnalysisConfig

    analysis_config = AnalysisConfig(lookback_days=30, analysis_window_days=7)

    usage_stats = analyze_feature_usage(df, config, analysis_config)

    assert "feature_a" in usage_stats
    assert "feature_b" in usage_stats
    assert usage_stats["feature_a"].total_usage_count == 3
    assert usage_stats["feature_a"].unique_users == 3
    assert usage_stats["feature_b"].total_usage_count == 1
    assert usage_stats["feature_b"].unique_users == 1


def test_calculate_adoption_rates():
    """Test adoption rate calculation."""
    now = datetime.now()
    df = pd.DataFrame(
        {
            "user_id": ["user1", "user2", "user3", "user1"],
            "feature_name": ["feature_a", "feature_a", "feature_b", "feature_b"],
            "timestamp": [
                now - timedelta(days=5),
                now - timedelta(days=3),
                now - timedelta(days=2),
                now - timedelta(days=1),
            ],
        }
    )

    config = UsageDataConfig(
        file_path="dummy.csv",
        user_id_column="user_id",
        feature_name_column="feature_name",
        timestamp_column="timestamp",
    )

    feature_config = FeatureConfig()
    from feature_usage_monitor.src.main import AnalysisConfig

    analysis_config = AnalysisConfig(lookback_days=30, analysis_window_days=7)

    adoption_metrics = calculate_adoption_rates(df, config, feature_config, analysis_config)

    assert "feature_a" in adoption_metrics
    assert "feature_b" in adoption_metrics
    assert adoption_metrics["feature_a"].adopted_users == 2
    assert adoption_metrics["feature_b"].adopted_users == 2


def test_identify_unused_features():
    """Test unused feature identification."""
    feature_usage = {
        "feature_a": FeatureUsage(
            feature_name="feature_a",
            total_usage_count=100,
            unique_users=50,
            adoption_rate=0.5,
            avg_usage_per_user=2.0,
        ),
        "feature_b": FeatureUsage(
            feature_name="feature_b",
            total_usage_count=2,
            unique_users=1,
            adoption_rate=0.01,
            avg_usage_per_user=2.0,
        ),
    }

    all_features: Set[str] = {"feature_a", "feature_b", "feature_c"}
    feature_config = FeatureConfig(min_usage_threshold=10, unused_threshold_percentage=0.01)
    total_users = 1000

    unused = identify_unused_features(feature_usage, all_features, feature_config, total_users)

    unused_names = {f.feature_name for f in unused}
    assert "feature_c" in unused_names
    assert "feature_b" in unused_names
    assert "feature_a" not in unused_names


def test_empty_data_handling():
    """Test handling of empty data."""
    df = pd.DataFrame()

    config = UsageDataConfig(
        file_path="dummy.csv",
        user_id_column="user_id",
        feature_name_column="feature_name",
        timestamp_column="timestamp",
    )

    from feature_usage_monitor.src.main import AnalysisConfig

    analysis_config = AnalysisConfig()

    usage_stats = analyze_feature_usage(df, config, analysis_config)
    assert len(usage_stats) == 0


def test_trend_detection():
    """Test usage trend detection."""
    now = datetime.now()
    df = pd.DataFrame(
        {
            "user_id": ["user1"] * 10,
            "feature_name": ["feature_a"] * 10,
            "timestamp": [
                now - timedelta(days=10),
                now - timedelta(days=9),
                now - timedelta(days=8),
                now - timedelta(days=7),
                now - timedelta(days=6),
                now - timedelta(days=2),
                now - timedelta(days=1),
                now - timedelta(hours=12),
                now - timedelta(hours=6),
                now,
            ],
        }
    )

    config = UsageDataConfig(
        file_path="dummy.csv",
        user_id_column="user_id",
        feature_name_column="feature_name",
        timestamp_column="timestamp",
    )

    from feature_usage_monitor.src.main import AnalysisConfig

    analysis_config = AnalysisConfig(lookback_days=30, analysis_window_days=7)

    usage_stats = analyze_feature_usage(df, config, analysis_config)

    assert "feature_a" in usage_stats
    assert usage_stats["feature_a"].usage_trend in ["increasing", "stable"]
