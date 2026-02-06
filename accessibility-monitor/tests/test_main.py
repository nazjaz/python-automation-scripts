"""Test suite for accessibility monitoring system."""

import pytest
from datetime import datetime, date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Website,
    AccessibilityScan,
    Violation,
    RemediationTask,
)
from src.accessibility_scanner import AccessibilityScanner
from src.wcag_validator import WCAGValidator
from src.remediation_generator import RemediationGenerator
from src.progress_tracker import ProgressTracker


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
        "accessibility": {
            "wcag_version": "2.1",
            "target_level": "AA",
            "timeout_seconds": 30,
            "max_pages": 50,
        },
        "scanning": {
            "check_images": True,
            "check_forms": True,
            "check_headings": True,
        },
        "remediation": {
            "generate_reports": True,
        },
        "progress_tracking": {
            "improvement_threshold": 0.05,
            "min_scans_for_trend": 3,
        },
    }


@pytest.fixture
def sample_website(test_db):
    """Create sample website for testing."""
    website = test_db.add_website(
        url="https://example.com",
        name="Example Website",
    )
    return website


@pytest.fixture
def sample_scan(test_db, sample_website):
    """Create sample scan for testing."""
    scan = test_db.add_scan(
        website_id=sample_website.id,
        page_url="https://example.com/page",
        compliance_score=0.85,
        total_violations=5,
        high_violations=2,
        medium_violations=3,
    )
    return scan


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            websites = session.query(Website).all()
            assert len(websites) == 0
        finally:
            session.close()

    def test_add_website(self, test_db):
        """Test adding website."""
        website = test_db.add_website(
            url="https://test.com",
            name="Test Website",
        )
        assert website.id is not None
        assert website.url == "https://test.com"

    def test_add_scan(self, test_db, sample_website):
        """Test adding scan."""
        scan = test_db.add_scan(
            website_id=sample_website.id,
            page_url="https://example.com",
            compliance_score=0.9,
            total_violations=3,
        )
        assert scan.id is not None
        assert scan.compliance_score == 0.9

    def test_add_violation(self, test_db, sample_scan):
        """Test adding violation."""
        violation = test_db.add_violation(
            scan_id=sample_scan.id,
            wcag_criterion="1.1.1",
            severity="high",
            violation_type="missing_alt_text",
            description="Image missing alt text",
        )
        assert violation.id is not None
        assert violation.wcag_criterion == "1.1.1"


class TestWCAGValidator:
    """Test WCAG validator functionality."""

    def test_check_images(self, test_db, sample_config):
        """Test image checking."""
        html = '<html><body><img src="test.jpg"></body></html>'
        validator = WCAGValidator(test_db, sample_config)
        violations = validator._check_images(BeautifulSoup(html, "html.parser"))

        assert len(violations) > 0
        assert any(v["violation_type"] == "missing_alt_text" for v in violations)

    def test_check_headings(self, test_db, sample_config):
        """Test heading checking."""
        html = '<html><body><h2>Heading</h2></body></html>'
        validator = WCAGValidator(test_db, sample_config)
        violations = validator._check_headings(BeautifulSoup(html, "html.parser"))

        assert any(v["violation_type"] == "missing_h1" for v in violations)

    def test_check_forms(self, test_db, sample_config):
        """Test form checking."""
        html = '<html><body><input type="text" id="test"></body></html>'
        validator = WCAGValidator(test_db, sample_config)
        violations = validator._check_forms(BeautifulSoup(html, "html.parser"))

        assert len(violations) > 0


class TestRemediationGenerator:
    """Test remediation generator functionality."""

    def test_generate_remediation_tasks(self, test_db, sample_config, sample_scan):
        """Test remediation task generation."""
        violation = test_db.add_violation(
            scan_id=sample_scan.id,
            wcag_criterion="1.1.1",
            severity="high",
            violation_type="missing_alt_text",
            description="Image missing alt text",
        )

        generator = RemediationGenerator(test_db, sample_config)
        tasks = generator.generate_remediation_tasks(scan_id=sample_scan.id)

        assert len(tasks) == 1
        assert tasks[0].violation_id == violation.id


class TestProgressTracker:
    """Test progress tracker functionality."""

    def test_record_daily_metrics(self, test_db, sample_config, sample_website):
        """Test daily metrics recording."""
        scan = test_db.add_scan(
            website_id=sample_website.id,
            page_url="https://example.com",
            compliance_score=0.9,
            total_violations=2,
        )

        tracker = ProgressTracker(test_db, sample_config)
        metric = tracker.record_daily_metrics(website_id=sample_website.id)

        assert metric is not None
        assert metric.compliance_score == 0.9

    def test_get_progress_trend(self, test_db, sample_config, sample_website):
        """Test progress trend calculation."""
        for i in range(5):
            test_db.add_progress_metric(
                website_id=sample_website.id,
                metric_date=date.today() - timedelta(days=5-i),
                compliance_score=0.7 + (i * 0.05),
                total_violations=10 - i,
            )

        tracker = ProgressTracker(test_db, sample_config)
        trend = tracker.get_progress_trend(website_id=sample_website.id, days=7)

        assert trend["trend"] in ["improving", "stable", "declining"]


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "accessibility" in config
            assert "scanning" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
