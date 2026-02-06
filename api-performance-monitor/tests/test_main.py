"""Test suite for API performance monitoring system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    APIEndpoint,
    APIRequest,
    EndpointMetric,
    Bottleneck,
)
from src.api_monitor import APIMonitor
from src.response_time_tracker import ResponseTimeTracker
from src.bottleneck_analyzer import BottleneckAnalyzer
from src.recommendation_engine import RecommendationEngine


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
            "timeout_seconds": 30,
            "max_retries": 3,
        },
        "performance": {
            "slow_endpoint_threshold_ms": 1000,
            "very_slow_endpoint_threshold_ms": 5000,
            "response_time_percentiles": [50, 75, 90, 95, 99],
            "min_requests_for_analysis": 5,
        },
        "bottleneck_detection": {
            "enabled": True,
            "error_rate_threshold": 0.05,
            "min_samples_for_bottleneck": 10,
        },
        "optimization": {
            "generate_recommendations": True,
        },
    }


@pytest.fixture
def sample_endpoint(test_db):
    """Create sample endpoint for testing."""
    endpoint = test_db.add_endpoint(
        base_url="https://api.example.com",
        path="/test",
        method="GET",
    )
    return endpoint


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            endpoints = session.query(APIEndpoint).all()
            assert len(endpoints) == 0
        finally:
            session.close()

    def test_add_endpoint(self, test_db):
        """Test adding endpoint."""
        endpoint = test_db.add_endpoint(
            base_url="https://api.example.com",
            path="/test",
            method="GET",
        )
        assert endpoint.id is not None
        assert endpoint.full_url == "https://api.example.com/test"

    def test_add_request(self, test_db, sample_endpoint):
        """Test adding request."""
        request = test_db.add_request(
            endpoint_id=sample_endpoint.id,
            response_time_ms=150.5,
            status_code=200,
        )
        assert request.id is not None
        assert request.response_time_ms == 150.5


class TestAPIMonitor:
    """Test API monitor functionality."""

    @patch("src.api_monitor.requests.request")
    def test_monitor_endpoint(self, mock_request, test_db, sample_config, sample_endpoint):
        """Test endpoint monitoring."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test response"
        mock_request.return_value = mock_response

        monitor = APIMonitor(test_db, sample_config)
        request = monitor.monitor_endpoint(sample_endpoint.id)

        assert request.id is not None
        assert request.response_time_ms is not None
        assert request.status_code == 200


class TestResponseTimeTracker:
    """Test response time tracker functionality."""

    def test_calculate_metrics(self, test_db, sample_config, sample_endpoint):
        """Test metrics calculation."""
        for i in range(10):
            test_db.add_request(
                endpoint_id=sample_endpoint.id,
                response_time_ms=100.0 + i * 10,
                status_code=200,
            )

        tracker = ResponseTimeTracker(test_db, sample_config)
        metrics = tracker.calculate_metrics(sample_endpoint.id)

        assert metrics is not None
        assert metrics.avg_response_time_ms is not None
        assert metrics.request_count == 10

    def test_identify_slow_endpoints(self, test_db, sample_config, sample_endpoint):
        """Test slow endpoint identification."""
        for i in range(10):
            test_db.add_request(
                endpoint_id=sample_endpoint.id,
                response_time_ms=1500.0,
                status_code=200,
            )

        tracker = ResponseTimeTracker(test_db, sample_config)
        slow_endpoints = tracker.identify_slow_endpoints()

        assert isinstance(slow_endpoints, list)


class TestBottleneckAnalyzer:
    """Test bottleneck analyzer functionality."""

    def test_analyze_endpoint(self, test_db, sample_config, sample_endpoint):
        """Test endpoint bottleneck analysis."""
        for i in range(20):
            test_db.add_request(
                endpoint_id=sample_endpoint.id,
                response_time_ms=2000.0,
                status_code=200,
            )

        analyzer = BottleneckAnalyzer(test_db, sample_config)
        bottlenecks = analyzer.analyze_endpoint(sample_endpoint.id, hours=24)

        assert isinstance(bottlenecks, list)


class TestRecommendationEngine:
    """Test recommendation engine functionality."""

    def test_generate_recommendations(self, test_db, sample_config, sample_endpoint):
        """Test recommendation generation."""
        for i in range(15):
            test_db.add_request(
                endpoint_id=sample_endpoint.id,
                response_time_ms=800.0,
                status_code=200,
                response_size_bytes=50000,
            )

        engine = RecommendationEngine(test_db, sample_config)
        recommendations = engine.generate_recommendations(sample_endpoint.id)

        assert isinstance(recommendations, list)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "monitoring" in config
            assert "performance" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
