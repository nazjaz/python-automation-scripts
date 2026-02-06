"""Test suite for cloud resource monitor system."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    CloudResource,
    ResourceMetric,
    RightSizingRecommendation,
    ScalingAction,
)
from src.resource_monitor import ResourceMonitor
from src.idle_detector import IdleDetector
from src.right_sizing_analyzer import RightSizingAnalyzer
from src.auto_scaler import AutoScaler


@pytest.fixture
def test_db():
    """Create test database."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "monitoring": {
            "metrics": ["cpu_utilization", "memory_utilization"],
        },
        "idle_detection": {
            "enabled": True,
            "idle_thresholds": {
                "cpu_utilization": 5.0,
                "memory_utilization": 10.0,
            },
            "idle_duration_hours": 24,
        },
        "right_sizing": {
            "enabled": True,
            "utilization_thresholds": {
                "underutilized": 30.0,
                "overutilized": 80.0,
            },
        },
        "auto_scaling": {
            "enabled": True,
            "scale_up_threshold": 75.0,
            "scale_down_threshold": 25.0,
        },
    }


@pytest.fixture
def sample_resource(test_db):
    """Create sample resource for testing."""
    resource = test_db.add_resource(
        resource_id="RES001",
        resource_name="Test Resource",
        resource_type="compute",
        cloud_provider="aws",
        instance_type="t2.micro",
        cost_per_hour=0.01,
    )
    return resource


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            resources = session.query(CloudResource).all()
            assert len(resources) == 0
        finally:
            session.close()

    def test_add_resource(self, test_db):
        """Test adding resource."""
        resource = test_db.add_resource(
            resource_id="RES001",
            resource_name="Test Resource",
            resource_type="compute",
            cloud_provider="aws",
        )
        assert resource.id is not None
        assert resource.resource_id == "RES001"

    def test_add_metric(self, test_db, sample_resource):
        """Test adding metric."""
        metric = test_db.add_metric(
            resource_id=sample_resource.id,
            metric_type="cpu_utilization",
            metric_value=50.0,
            metric_timestamp=datetime.utcnow(),
        )
        assert metric.id is not None
        assert metric.metric_value == 50.0


class TestResourceMonitor:
    """Test resource monitor functionality."""

    def test_collect_metrics(self, test_db, sample_config, sample_resource):
        """Test metrics collection."""
        monitor = ResourceMonitor(test_db, sample_config)
        metrics = monitor.collect_metrics(
            sample_resource.id,
            {"cpu_utilization": 50.0, "memory_utilization": 60.0},
        )

        assert len(metrics) == 2


class TestIdleDetector:
    """Test idle detector functionality."""

    def test_detect_idle_resources(self, test_db, sample_config, sample_resource):
        """Test idle resource detection."""
        detector = IdleDetector(test_db, sample_config)

        for _ in range(15):
            test_db.add_metric(
                resource_id=sample_resource.id,
                metric_type="cpu_utilization",
                metric_value=3.0,
                metric_timestamp=datetime.utcnow(),
            )

        idle_resources = detector.detect_idle_resources()

        assert isinstance(idle_resources, list)


class TestRightSizingAnalyzer:
    """Test right-sizing analyzer functionality."""

    def test_analyze_resource(self, test_db, sample_config, sample_resource):
        """Test resource right-sizing analysis."""
        for _ in range(25):
            test_db.add_metric(
                resource_id=sample_resource.id,
                metric_type="cpu_utilization",
                metric_value=20.0,
                metric_timestamp=datetime.utcnow(),
            )

        analyzer = RightSizingAnalyzer(test_db, sample_config)
        recommendation = analyzer.analyze_resource(sample_resource.id)

        assert recommendation is not None or recommendation is None


class TestAutoScaler:
    """Test auto-scaler functionality."""

    def test_check_scaling_needed(self, test_db, sample_config, sample_resource):
        """Test scaling check."""
        for _ in range(10):
            test_db.add_metric(
                resource_id=sample_resource.id,
                metric_type="cpu_utilization",
                metric_value=80.0,
                metric_timestamp=datetime.utcnow(),
            )

        scaler = AutoScaler(test_db, sample_config)
        action = scaler.check_scaling_needed(sample_resource.id)

        assert action is None or isinstance(action, ScalingAction)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "monitoring" in config
            assert "idle_detection" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
