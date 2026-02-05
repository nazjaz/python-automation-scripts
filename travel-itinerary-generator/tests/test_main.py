"""Unit tests for travel itinerary generator automation."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.database import DatabaseManager, Itinerary
from src.flight_service import FlightService
from src.hotel_service import HotelService
from src.activity_service import ActivityService
from src.notification_service import NotificationService
from src.reminder_service import ReminderService
from src.itinerary_generator import ItineraryGenerator


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock(spec=DatabaseManager)


@pytest.fixture
def sample_itinerary():
    """Create sample itinerary."""
    itinerary = MagicMock(spec=Itinerary)
    itinerary.id = 1
    itinerary.traveler_name = "Test User"
    itinerary.traveler_email = "test@example.com"
    itinerary.destination = "Paris"
    itinerary.trip_start_date = datetime.utcnow() + timedelta(days=7)
    itinerary.trip_end_date = datetime.utcnow() + timedelta(days=10)
    return itinerary


class TestFlightService:
    """Tests for FlightService class."""

    def test_search_flights(self, mock_db_manager):
        """Test flight search."""
        service = FlightService(
            mock_db_manager, "api_key", "api_secret", "amadeus"
        )

        result = service.search_flights(
            "JFK", "LHR", datetime.utcnow() + timedelta(days=7)
        )

        assert isinstance(result, list)

    def test_book_flight(self, mock_db_manager):
        """Test flight booking."""
        service = FlightService(
            mock_db_manager, "api_key", "api_secret", "amadeus"
        )

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        booking = service.book_flight(
            itinerary_id=1,
            airline="Test Airlines",
            flight_number="TA123",
            departure_airport="JFK",
            arrival_airport="LHR",
            departure_time=datetime.utcnow() + timedelta(days=7),
            arrival_time=datetime.utcnow() + timedelta(days=7, hours=8),
        )

        assert booking is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestHotelService:
    """Tests for HotelService class."""

    def test_search_hotels(self, mock_db_manager):
        """Test hotel search."""
        service = HotelService(mock_db_manager, "api_key", "booking")

        result = service.search_hotels(
            "Paris",
            datetime.utcnow() + timedelta(days=7),
            datetime.utcnow() + timedelta(days=10),
        )

        assert isinstance(result, list)

    def test_book_hotel(self, mock_db_manager):
        """Test hotel booking."""
        service = HotelService(mock_db_manager, "api_key", "booking")

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        booking = service.book_hotel(
            itinerary_id=1,
            hotel_name="Test Hotel",
            address="123 Test St",
            check_in_date=datetime.utcnow() + timedelta(days=7),
            check_out_date=datetime.utcnow() + timedelta(days=10),
        )

        assert booking is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestNotificationService:
    """Tests for NotificationService class."""

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        """Test email sending."""
        service = NotificationService(
            "smtp.example.com",
            587,
            "user",
            "pass",
            "from@example.com",
            "Test Service",
        )

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = service.send_email(
            "to@example.com", "Test Subject", "Test Body", is_html=False
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()

    def test_send_travel_reminder(self):
        """Test travel reminder email."""
        service = NotificationService(
            "smtp.example.com",
            587,
            "user",
            "pass",
            "from@example.com",
            "Test Service",
        )

        with patch.object(service, "send_email", return_value=True) as mock_send:
            result = service.send_travel_reminder(
                "test@example.com",
                "Test User",
                "2024-01-01",
                "Paris",
                24,
            )

            assert result is True
            mock_send.assert_called_once()


class TestReminderService:
    """Tests for ReminderService class."""

    def test_schedule_reminders(self, mock_db_manager, sample_itinerary):
        """Test reminder scheduling."""
        notification_service = NotificationService(
            "smtp.example.com", 587, "user", "pass", "from@example.com", "Test"
        )
        reminder_service = ReminderService(
            mock_db_manager, notification_service, [72, 24, 2]
        )

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = (
            sample_itinerary
        )

        reminders = reminder_service.schedule_reminders(1)

        assert len(reminders) > 0
        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()
