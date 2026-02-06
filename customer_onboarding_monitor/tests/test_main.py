"""Tests for customer onboarding monitoring analytics."""

from pathlib import Path
from typing import List

import pandas as pd

from customer_onboarding_monitor.src.main import (
    AnalysisResult,
    Config,
    StageConfig,
    StageMetrics,
    compute_stage_metrics,
    compute_time_to_value,
    generate_recommendations,
)


def _build_sample_config(tmp_path: Path) -> Config:
    """Create an in-memory config for tests."""

    stages: List[StageConfig] = [
        StageConfig(
            name="signup_started",
            display_name="Signup Started",
            target_completion_rate=0.95,
            target_time_to_complete_hours=1.0,
        ),
        StageConfig(
            name="profile_completed",
            display_name="Profile Completed",
            target_completion_rate=0.9,
            target_time_to_complete_hours=4.0,
        ),
        StageConfig(
            name="value_realized",
            display_name="Value Realized",
            target_completion_rate=0.8,
            target_time_to_complete_hours=48.0,
        ),
    ]

    return Config(
        data_path=tmp_path / "dummy.csv",
        output_path=tmp_path / "out.md",
        customer_id_column="customer_id",
        event_time_column="event_time",
        stage_column="stage",
        time_to_value_event="value_realized",
        stages=stages,
    )


def test_compute_stage_metrics_basic(tmp_path: Path) -> None:
    """Test that stage metrics are computed for each configured stage."""

    config = _build_sample_config(tmp_path)
    data = pd.DataFrame(
        {
            "customer_id": [1, 1, 1, 2, 2],
            "event_time": [
                "2024-01-01T00:00:00Z",
                "2024-01-01T01:00:00Z",
                "2024-01-02T00:00:00Z",
                "2024-01-01T00:30:00Z",
                "2024-01-03T00:00:00Z",
            ],
            "stage": [
                "signup_started",
                "profile_completed",
                "value_realized",
                "signup_started",
                "profile_completed",
            ],
        }
    )
    data["event_time"] = pd.to_datetime(data["event_time"])

    metrics = compute_stage_metrics(data, config)

    assert len(metrics) == len(config.stages)
    signup = next(m for m in metrics if m.stage_name == "signup_started")
    assert signup.entered == 2
    profile = next(m for m in metrics if m.stage_name == "profile_completed")
    assert profile.entered == 2


def test_compute_time_to_value(tmp_path: Path) -> None:
    """Test average time-to-value calculation."""

    config = _build_sample_config(tmp_path)
    data = pd.DataFrame(
        {
            "customer_id": [1, 1, 1, 2, 2],
            "event_time": [
                "2024-01-01T00:00:00Z",
                "2024-01-02T00:00:00Z",
                "2024-01-03T00:00:00Z",
                "2024-01-01T12:00:00Z",
                "2024-01-04T12:00:00Z",
            ],
            "stage": [
                "signup_started",
                "profile_completed",
                "value_realized",
                "signup_started",
                "value_realized",
            ],
        }
    )
    data["event_time"] = pd.to_datetime(data["event_time"])

    ttv_hours = compute_time_to_value(data, config)
    assert ttv_hours is not None
    assert ttv_hours > 0


def test_generate_recommendations_produces_output(tmp_path: Path) -> None:
    """Test that recommendations are produced for underperforming stages."""

    config = _build_sample_config(tmp_path)
    metrics: List[StageMetrics] = [
        StageMetrics(
            stage_name="signup_started",
            entered=10,
            completed=10,
            completion_rate=0.7,
            median_time_hours=2.0,
        )
    ]

    recs = generate_recommendations(
        stage_metrics=metrics,
        config=config,
        average_ttv_hours=72.0,
    )

    assert recs, "Expected at least one recommendation"
