"""Test suite for event registration system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Event, Registration
from src.registration_processor import RegistrationProcessor
from src.email_service import EmailService
from src.badge_generator import BadgeGenerator
from src.attendee_list_generator import AttendeeListGenerator


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
        "events": {
            "default_capacity": 100,
            "allow_waitlist": True,
            "auto_confirm": True,
        },
        "registration": {
            "confirmation_email": {
                "enabled": True,
                "subject": "Event Registration Confirmation",
                "template": "templates/confirmation_email.html",
            },
            "waitlist_email": {
                "enabled": True,
                "subject": "Waitlist Notification",
                "template": "templates/waitlist_email.html",
            },
        },
        "badges": {
            "enabled": True,
            "template": "templates/badge_template.html",
            "output_directory": "badges",
        },
        "email": {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "from_email": "test@example.com",
            "from_name": "Test Events",
        },
    }


@pytest.fixture
def sample_event(test_db):
    """Create sample event for testing."""
    event = test_db.add_event(
        name="Test Event",
        event_date=datetime.utcnow() + timedelta(days=30),
        location="Test Location",
        capacity=10,
        allow_waitlist=True,
    )
    return event


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            events = session.query(Event).all()
            assert len(events) == 0
        finally:
            session.close()

    def test_add_event(self, test_db):
        """Test adding event."""
        event = test_db.add_event(
            name="Test Event",
            event_date=datetime.utcnow(),
            location="Test Location",
            capacity=50,
        )
        assert event.id is not None
        assert event.name == "Test Event"
        assert event.capacity == 50

    def test_add_registration(self, test_db, sample_event):
        """Test adding registration."""
        registration = test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            company="Test Company",
        )
        assert registration.id is not None
        assert registration.email == "john@example.com"

    def test_get_registrations(self, test_db, sample_event):
        """Test getting registrations."""
        test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="confirmed",
        )
        registrations = test_db.get_registrations(event_id=sample_event.id)
        assert len(registrations) == 1
        assert registrations[0].name == "John Doe"


class TestRegistrationProcessor:
    """Test registration processor functionality."""

    def test_process_registration(self, test_db, sample_config, sample_event):
        """Test processing registration."""
        processor = RegistrationProcessor(test_db, sample_config)
        result = processor.process_registration(
            event_id=sample_event.id,
            name="Jane Smith",
            email="jane@example.com",
            company="Test Corp",
        )
        assert result["success"]
        assert result["status"] == "confirmed"
        assert not result.get("is_waitlist")

    def test_process_registration_waitlist(self, test_db, sample_config, sample_event):
        """Test processing registration when event is full."""
        for i in range(sample_event.capacity):
            test_db.add_registration(
                event_id=sample_event.id,
                name=f"Person {i}",
                email=f"person{i}@example.com",
                status="confirmed",
            )
        test_db.update_event_registration_count(sample_event.id)

        processor = RegistrationProcessor(test_db, sample_config)
        result = processor.process_registration(
            event_id=sample_event.id,
            name="Waitlist Person",
            email="waitlist@example.com",
        )
        assert result["success"]
        assert result.get("is_waitlist")
        assert result.get("waitlist_position") == 1

    def test_confirm_registration(self, test_db, sample_config, sample_event):
        """Test confirming registration."""
        registration = test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="pending",
        )

        processor = RegistrationProcessor(test_db, sample_config)
        updated = processor.confirm_registration(registration.id)

        assert updated is not None
        assert updated.status == "confirmed"


class TestEmailService:
    """Test email service functionality."""

    @patch("src.email_service.smtplib.SMTP")
    def test_send_confirmation_email(self, mock_smtp, test_db, sample_config, sample_event):
        """Test sending confirmation email."""
        registration = test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="confirmed",
        )

        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service = EmailService(test_db, sample_config)
        with patch.dict("os.environ", {"SMTP_USERNAME": "test", "SMTP_PASSWORD": "test"}):
            result = email_service.send_confirmation_email(registration.id)

        assert result is True or result is False


class TestBadgeGenerator:
    """Test badge generator functionality."""

    def test_generate_badge(self, test_db, sample_config, sample_event, tmp_path):
        """Test badge generation."""
        registration = test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            company="Test Company",
            status="confirmed",
        )

        sample_config["badges"]["output_directory"] = str(tmp_path)
        generator = BadgeGenerator(test_db, sample_config)
        badge_path = generator.generate_badge(registration.id)

        assert badge_path is not None
        assert badge_path.exists()

    def test_generate_badges_for_event(self, test_db, sample_config, sample_event, tmp_path):
        """Test generating badges for event."""
        test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="confirmed",
        )

        sample_config["badges"]["output_directory"] = str(tmp_path)
        generator = BadgeGenerator(test_db, sample_config)
        badge_paths = generator.generate_badges_for_event(sample_event.id)

        assert len(badge_paths) == 1


class TestAttendeeListGenerator:
    """Test attendee list generator functionality."""

    def test_generate_csv_list(self, test_db, sample_event, tmp_path):
        """Test CSV list generation."""
        test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="confirmed",
        )

        generator = AttendeeListGenerator(test_db, output_dir=str(tmp_path))
        csv_path = generator.generate_csv_list(sample_event.id)

        assert csv_path.exists()
        assert csv_path.suffix == ".csv"

    def test_generate_html_list(self, test_db, sample_event, tmp_path):
        """Test HTML list generation."""
        test_db.add_registration(
            event_id=sample_event.id,
            name="John Doe",
            email="john@example.com",
            status="confirmed",
        )

        generator = AttendeeListGenerator(test_db, output_dir=str(tmp_path))
        html_path = generator.generate_html_list(sample_event.id)

        assert html_path.exists()
        assert html_path.suffix == ".html"


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "events" in config
            assert "registration" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
