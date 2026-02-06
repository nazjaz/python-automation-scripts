"""Test suite for subscription monitor system."""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Customer,
    Subscription,
    Renewal,
    ChurnRisk,
    RetentionCampaign,
)
from src.renewal_monitor import RenewalMonitor
from src.churn_detector import ChurnDetector
from src.campaign_trigger import CampaignTrigger
from src.metrics_tracker import MetricsTracker


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
            "renewal_check_days_ahead": 30,
            "renewal_check_days_past": 7,
        },
        "churn_detection": {
            "enabled": True,
            "risk_factors": {
                "payment_failures": 2,
                "engagement_score_threshold": 0.3,
            },
            "risk_levels": {
                "low": 0.0,
                "medium": 0.4,
                "high": 0.7,
            },
        },
        "retention": {
            "campaigns_enabled": True,
            "campaign_types": ["email_discount", "email_engagement"],
            "trigger_conditions": {
                "high_risk_churn": True,
                "payment_failure": True,
            },
        },
        "metrics": {
            "track_mrr": True,
            "track_churn_rate": True,
            "calculation_window_days": 30,
        },
    }


@pytest.fixture
def sample_customer(test_db):
    """Create sample customer for testing."""
    customer = test_db.add_customer(
        customer_id="CUST001",
        name="Test Customer",
        email="test@example.com",
    )
    return customer


@pytest.fixture
def sample_subscription(test_db, sample_customer):
    """Create sample subscription for testing."""
    subscription = test_db.add_subscription(
        customer_id=sample_customer.id,
        subscription_id="SUB001",
        plan_name="Basic Plan",
        status="active",
        billing_cycle="monthly",
        monthly_revenue=29.99,
        start_date=date.today() - timedelta(days=30),
        renewal_date=date.today() + timedelta(days=5),
    )
    return subscription


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            customers = session.query(Customer).all()
            assert len(customers) == 0
        finally:
            session.close()

    def test_add_customer(self, test_db):
        """Test adding customer."""
        customer = test_db.add_customer(
            customer_id="CUST001",
            name="John Doe",
            email="john@example.com",
        )
        assert customer.id is not None
        assert customer.customer_id == "CUST001"

    def test_add_subscription(self, test_db, sample_customer):
        """Test adding subscription."""
        subscription = test_db.add_subscription(
            customer_id=sample_customer.id,
            subscription_id="SUB001",
            plan_name="Basic Plan",
            status="active",
            billing_cycle="monthly",
            monthly_revenue=29.99,
            start_date=date.today(),
            renewal_date=date.today() + timedelta(days=30),
        )
        assert subscription.id is not None
        assert subscription.status == "active"


class TestRenewalMonitor:
    """Test renewal monitor functionality."""

    def test_check_renewals(self, test_db, sample_config, sample_subscription):
        """Test checking renewals."""
        monitor = RenewalMonitor(test_db, sample_config)
        renewals = monitor.check_renewals(days_ahead=30)

        assert isinstance(renewals, list)

    def test_identify_upcoming_renewals(self, test_db, sample_config, sample_subscription):
        """Test identifying upcoming renewals."""
        monitor = RenewalMonitor(test_db, sample_config)
        upcoming = monitor.identify_upcoming_renewals(days_ahead=30)

        assert isinstance(upcoming, list)


class TestChurnDetector:
    """Test churn detector functionality."""

    def test_assess_churn_risk(self, test_db, sample_config, sample_customer):
        """Test churn risk assessment."""
        detector = ChurnDetector(test_db, sample_config)
        risk = detector.assess_churn_risk(sample_customer.id)

        assert risk is not None
        assert risk.risk_score >= 0.0
        assert risk.risk_score <= 1.0


class TestCampaignTrigger:
    """Test campaign trigger functionality."""

    def test_trigger_campaign(self, test_db, sample_config, sample_customer):
        """Test triggering campaign."""
        trigger = CampaignTrigger(test_db, sample_config)
        campaign = trigger.trigger_campaign(
            customer_id=sample_customer.id,
            campaign_type="email_discount",
        )

        assert campaign.id is not None
        assert campaign.campaign_type == "email_discount"


class TestMetricsTracker:
    """Test metrics tracker functionality."""

    def test_calculate_mrr(self, test_db, sample_config, sample_subscription):
        """Test MRR calculation."""
        tracker = MetricsTracker(test_db, sample_config)
        mrr = tracker.calculate_mrr()

        assert mrr >= 0.0

    def test_calculate_churn_rate(self, test_db, sample_config):
        """Test churn rate calculation."""
        tracker = MetricsTracker(test_db, sample_config)
        churn_rate = tracker.calculate_churn_rate()

        assert 0.0 <= churn_rate <= 1.0


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "monitoring" in config
            assert "churn_detection" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
