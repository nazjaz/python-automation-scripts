"""Test suite for support performance monitoring system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    SupportTicket,
    TicketResponse,
    TicketMetrics,
    Bottleneck,
)
from src.response_time_tracker import ResponseTimeTracker
from src.resolution_rate_analyzer import ResolutionRateAnalyzer
from src.bottleneck_identifier import BottleneckIdentifier
from src.dashboard_generator import DashboardGenerator


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
        "support": {
            "response_time_thresholds": {
                "first_response_minutes": 60,
                "resolution_hours": 24,
            },
            "ticket_categories": ["technical", "billing"],
            "priority_levels": ["low", "medium", "high"],
        },
        "performance": {
            "resolution_rate_target": 0.85,
            "bottleneck_threshold_percentage": 20.0,
        },
        "bottleneck_detection": {
            "enabled": True,
            "check_categories": True,
            "check_agents": True,
            "min_tickets_for_analysis": 5,
        },
        "dashboard": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "dashboards",
        },
    }


@pytest.fixture
def sample_ticket(test_db):
    """Create sample ticket for testing."""
    ticket = test_db.add_ticket(
        ticket_number="TICKET-001",
        title="Test Ticket",
        category="technical",
        priority="high",
        customer_email="customer@example.com",
        assigned_agent="agent1@example.com",
    )
    return ticket


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            tickets = session.query(SupportTicket).all()
            assert len(tickets) == 0
        finally:
            session.close()

    def test_add_ticket(self, test_db):
        """Test adding ticket."""
        ticket = test_db.add_ticket(
            ticket_number="TICKET-001",
            title="Test",
            category="technical",
            priority="high",
            customer_email="test@example.com",
        )
        assert ticket.id is not None
        assert ticket.ticket_number == "TICKET-001"

    def test_add_response(self, test_db, sample_ticket):
        """Test adding response."""
        response = test_db.add_response(
            ticket_id=sample_ticket.id,
            responder="agent1@example.com",
            response_type="agent",
            response_text="Test response",
        )
        assert response.id is not None
        assert response.responder == "agent1@example.com"

    def test_update_ticket_status(self, test_db, sample_ticket):
        """Test updating ticket status."""
        updated = test_db.update_ticket_status(
            ticket_id=sample_ticket.id,
            status="resolved",
            resolved_at=datetime.utcnow(),
        )
        assert updated is not None
        assert updated.status == "resolved"


class TestResponseTimeTracker:
    """Test response time tracker functionality."""

    def test_calculate_first_response_time(self, test_db, sample_config, sample_ticket):
        """Test first response time calculation."""
        sample_ticket.first_response_at = datetime.utcnow() + timedelta(minutes=30)

        tracker = ResponseTimeTracker(test_db, sample_config)
        response_time = tracker.calculate_first_response_time(sample_ticket)

        assert response_time is not None
        assert response_time == 30.0

    def test_get_average_response_time(self, test_db, sample_config, sample_ticket):
        """Test average response time calculation."""
        test_db.update_ticket_status(
            ticket_id=sample_ticket.id,
            status="resolved",
            first_response_at=datetime.utcnow() + timedelta(minutes=20),
            resolved_at=datetime.utcnow() + timedelta(hours=2),
        )

        tracker = ResponseTimeTracker(test_db, sample_config)
        avg_time = tracker.get_average_response_time(days=7)

        assert avg_time is not None
        assert avg_time >= 0

    def test_get_sla_compliance_rate(self, test_db, sample_config, sample_ticket):
        """Test SLA compliance rate calculation."""
        test_db.update_ticket_status(
            ticket_id=sample_ticket.id,
            status="resolved",
            first_response_at=datetime.utcnow() + timedelta(minutes=30),
        )

        tracker = ResponseTimeTracker(test_db, sample_config)
        compliance = tracker.get_sla_compliance_rate(days=7)

        assert compliance is not None
        assert 0.0 <= compliance <= 1.0


class TestResolutionRateAnalyzer:
    """Test resolution rate analyzer functionality."""

    def test_calculate_resolution_rate(self, test_db, sample_config, sample_ticket):
        """Test resolution rate calculation."""
        test_db.update_ticket_status(
            ticket_id=sample_ticket.id,
            status="resolved",
            resolved_at=datetime.utcnow(),
        )

        analyzer = ResolutionRateAnalyzer(test_db, sample_config)
        result = analyzer.calculate_resolution_rate(days=7)

        assert "resolution_rate" in result
        assert 0.0 <= result["resolution_rate"] <= 1.0

    def test_get_resolution_rate_by_category(self, test_db, sample_config, sample_ticket):
        """Test resolution rate by category."""
        analyzer = ResolutionRateAnalyzer(test_db, sample_config)
        rates = analyzer.get_resolution_rate_by_category(days=7)

        assert isinstance(rates, dict)
        assert "technical" in rates


class TestBottleneckIdentifier:
    """Test bottleneck identifier functionality."""

    def test_identify_category_bottlenecks(self, test_db, sample_config):
        """Test category bottleneck identification."""
        for i in range(10):
            test_db.add_ticket(
                ticket_number=f"TICKET-{i:03d}",
                title=f"Ticket {i}",
                category="technical",
                priority="high",
                customer_email=f"customer{i}@example.com",
                status="open",
            )

        identifier = BottleneckIdentifier(test_db, sample_config)
        bottlenecks = identifier.identify_category_bottlenecks(days=7)

        assert isinstance(bottlenecks, list)

    def test_identify_all_bottlenecks(self, test_db, sample_config):
        """Test identifying all bottlenecks."""
        identifier = BottleneckIdentifier(test_db, sample_config)
        bottlenecks = identifier.identify_all_bottlenecks(days=7)

        assert isinstance(bottlenecks, list)


class TestDashboardGenerator:
    """Test dashboard generator functionality."""

    def test_generate_html_dashboard(self, test_db, sample_config, tmp_path):
        """Test HTML dashboard generation."""
        sample_config["dashboard"]["output_directory"] = str(tmp_path)

        generator = DashboardGenerator(test_db, sample_config, output_dir=str(tmp_path))
        dashboard_path = generator.generate_html_dashboard(days=7)

        assert dashboard_path.exists()
        assert dashboard_path.suffix == ".html"

    def test_generate_csv_dashboard(self, test_db, sample_config, tmp_path):
        """Test CSV dashboard generation."""
        sample_config["dashboard"]["output_directory"] = str(tmp_path)

        generator = DashboardGenerator(test_db, sample_config, output_dir=str(tmp_path))
        dashboard_path = generator.generate_csv_dashboard(days=7)

        assert dashboard_path.exists()
        assert dashboard_path.suffix == ".csv"


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "support" in config
            assert "monitoring" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
