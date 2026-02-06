"""Tests for deployment monitoring."""

from datetime import datetime, timedelta

import pytest

from deployment_monitor.src.main import (
    DeploymentRecord,
    DeploymentStatus,
    MetricsConfig,
    QualityMetrics,
    RegressionConfig,
    RegressionSeverity,
    calculate_deployment_frequency,
    calculate_mttr,
    calculate_quality_metrics,
    calculate_success_rate,
    identify_regression_patterns,
)


def test_calculate_success_rate():
    """Test success rate calculation."""
    deployments = [
        DeploymentRecord(
            deployment_id="dep_001",
            timestamp=datetime.now(),
            status=DeploymentStatus.SUCCESS,
        ),
        DeploymentRecord(
            deployment_id="dep_002",
            timestamp=datetime.now(),
            status=DeploymentStatus.SUCCESS,
        ),
        DeploymentRecord(
            deployment_id="dep_003",
            timestamp=datetime.now(),
            status=DeploymentStatus.FAILED,
        ),
    ]

    success_rate, successful, total = calculate_success_rate(deployments)

    assert success_rate == pytest.approx(0.6667, abs=0.01)
    assert successful == 2
    assert total == 3


def test_calculate_success_rate_empty():
    """Test success rate calculation with empty data."""
    success_rate, successful, total = calculate_success_rate([])

    assert success_rate == 0.0
    assert successful == 0
    assert total == 0


def test_calculate_deployment_frequency():
    """Test deployment frequency calculation."""
    now = datetime.now()
    deployments = [
        DeploymentRecord(
            deployment_id=f"dep_{i:03d}",
            timestamp=now - timedelta(days=i),
            status=DeploymentStatus.SUCCESS,
        )
        for i in range(7)
    ]

    frequency = calculate_deployment_frequency(deployments, 7)

    assert frequency == pytest.approx(1.0, abs=0.1)


def test_calculate_mttr():
    """Test MTTR calculation."""
    now = datetime.now()
    deployments = [
        DeploymentRecord(
            deployment_id="dep_001",
            timestamp=now - timedelta(hours=10),
            status=DeploymentStatus.FAILED,
        ),
        DeploymentRecord(
            deployment_id="dep_002",
            timestamp=now - timedelta(hours=8),
            status=DeploymentStatus.SUCCESS,
        ),
        DeploymentRecord(
            deployment_id="dep_003",
            timestamp=now - timedelta(hours=5),
            status=DeploymentStatus.FAILED,
        ),
        DeploymentRecord(
            deployment_id="dep_004",
            timestamp=now - timedelta(hours=3),
            status=DeploymentStatus.SUCCESS,
        ),
    ]

    mttr = calculate_mttr(deployments, 30)

    assert mttr is not None
    assert mttr > 0
    assert mttr == pytest.approx(3.0, abs=0.5)


def test_calculate_mttr_insufficient_data():
    """Test MTTR calculation with insufficient data."""
    deployments = [
        DeploymentRecord(
            deployment_id="dep_001",
            timestamp=datetime.now(),
            status=DeploymentStatus.SUCCESS,
        ),
    ]

    mttr = calculate_mttr(deployments, 30)

    assert mttr is None


def test_identify_regression_patterns():
    """Test regression pattern identification."""
    now = datetime.now()
    baseline_start = now - timedelta(days=37)
    baseline_end = now - timedelta(days=7)
    comparison_start = baseline_end

    baseline_deployments = [
        DeploymentRecord(
            deployment_id=f"baseline_{i}",
            timestamp=baseline_start + timedelta(days=i),
            status=DeploymentStatus.SUCCESS,
        )
        for i in range(30)
    ]

    comparison_deployments = [
        DeploymentRecord(
            deployment_id=f"compare_{i}",
            timestamp=comparison_start + timedelta(days=i),
            status=DeploymentStatus.FAILED if i < 5 else DeploymentStatus.SUCCESS,
        )
        for i in range(7)
    ]

    all_deployments = baseline_deployments + comparison_deployments

    config = RegressionConfig(
        lookback_window_days=30,
        comparison_window_days=7,
        success_rate_threshold=0.05,
    )

    patterns = identify_regression_patterns(all_deployments, config)

    assert len(patterns) > 0
    assert any(
        p.pattern_type == "success_rate_decline" for p in patterns
    )


def test_calculate_quality_metrics():
    """Test quality metrics calculation."""
    now = datetime.now()
    deployments = [
        DeploymentRecord(
            deployment_id=f"dep_{i:03d}",
            timestamp=now - timedelta(days=i % 7),
            status=(
                DeploymentStatus.SUCCESS
                if i % 10 != 0
                else DeploymentStatus.FAILED
            ),
        )
        for i in range(20)
    ]

    config = MetricsConfig(
        mttr_window_days=30,
        deployment_frequency_window_days=7,
        change_failure_rate_window_days=30,
    )

    metrics = calculate_quality_metrics(deployments, config)

    assert isinstance(metrics, QualityMetrics)
    assert metrics.deployment_frequency >= 0
    assert 0.0 <= metrics.success_rate <= 1.0
    assert 0.0 <= metrics.failure_rate <= 1.0
    assert 0.0 <= metrics.change_failure_rate <= 1.0
    assert metrics.deployment_count == 20


def test_regression_severity_critical():
    """Test critical regression severity detection."""
    now = datetime.now()
    baseline_deployments = [
        DeploymentRecord(
            deployment_id=f"baseline_{i}",
            timestamp=now - timedelta(days=30 + i),
            status=DeploymentStatus.SUCCESS,
        )
        for i in range(30)
    ]

    comparison_deployments = [
        DeploymentRecord(
            deployment_id=f"compare_{i}",
            timestamp=now - timedelta(days=i),
            status=DeploymentStatus.FAILED,
        )
        for i in range(7)
    ]

    all_deployments = baseline_deployments + comparison_deployments

    config = RegressionConfig(
        lookback_window_days=30,
        comparison_window_days=7,
        success_rate_threshold=0.05,
        failure_rate_threshold=0.20,
    )

    patterns = identify_regression_patterns(all_deployments, config)

    critical_patterns = [
        p for p in patterns if p.severity == RegressionSeverity.CRITICAL
    ]
    assert len(critical_patterns) > 0
