"""Unit tests for customer onboarding automation."""

import pytest
from unittest.mock import MagicMock, patch

from src.account_manager import AccountManager
from src.database import DatabaseManager, Customer
from src.email_service import EmailService
from src.onboarding_tracker import OnboardingTracker
from src.resource_manager import ResourceManager


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock(spec=DatabaseManager)


@pytest.fixture
def mock_customer():
    """Create mock customer object."""
    customer = MagicMock(spec=Customer)
    customer.id = 1
    customer.email = "test@example.com"
    customer.name = "Test User"
    customer.company_name = "Test Company"
    customer.account_id = None
    customer.completion_percentage = 0.0
    return customer


class TestEmailService:
    """Tests for EmailService class."""

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        service = EmailService(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="Test",
        )

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = service.send_email(
            "to@example.com", "Test Subject", "Test Body", is_html=False
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.send_message.assert_called_once()

    def test_send_welcome_email_default_template(self, mock_customer):
        """Test welcome email with default template."""
        service = EmailService(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="Test",
        )

        with patch.object(service, "send_email", return_value=True) as mock_send:
            result = service.send_welcome_email(
                "test@example.com", "Test User", "Test Company"
            )

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "test@example.com" in call_args[0]
            assert "Test Company" in call_args[1] or "our platform" in call_args[1]


class TestAccountManager:
    """Tests for AccountManager class."""

    def test_setup_account(self, mock_db_manager, mock_customer):
        """Test account setup."""
        manager = AccountManager(mock_db_manager)

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )

        account_id = manager.setup_account(1)

        assert account_id is not None
        assert account_id.startswith("ACC-")
        assert mock_customer.account_id == account_id
        mock_session.commit.assert_called_once()

    def test_setup_account_customer_not_found(self, mock_db_manager):
        """Test account setup with non-existent customer."""
        manager = AccountManager(mock_db_manager)

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Customer with ID 1 not found"):
            manager.setup_account(1)


class TestOnboardingTracker:
    """Tests for OnboardingTracker class."""

    def test_initialize_steps(self, mock_db_manager):
        """Test step initialization."""
        tracker = OnboardingTracker(mock_db_manager)

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        step_configs = [
            {"name": "welcome_email", "order": 1, "required": True},
            {"name": "account_setup", "order": 2, "required": True},
        ]

        steps = tracker.initialize_steps(1, step_configs)

        assert len(steps) == 2
        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()

    def test_complete_step(self, mock_db_manager):
        """Test step completion."""
        tracker = OnboardingTracker(mock_db_manager)

        mock_step = MagicMock()
        mock_step.is_completed = False
        mock_step.step_name = "welcome_email"

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_step
        )

        with patch.object(tracker, "_update_completion_percentage"):
            result = tracker.complete_step(1, "welcome_email")

            assert result is True
            assert mock_step.is_completed is True
            mock_session.commit.assert_called_once()


class TestResourceManager:
    """Tests for ResourceManager class."""

    def test_assign_default_resources(self, mock_db_manager):
        """Test default resource assignment."""
        manager = ResourceManager(mock_db_manager)

        mock_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session

        default_resources = [
            {"type": "documentation_access", "name": "User Guide"},
            {"type": "support_access", "name": "Priority Support"},
        ]

        assignments = manager.assign_default_resources(1, default_resources)

        assert len(assignments) == 2
        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()

    @patch("requests.post")
    def test_assign_resource_via_api_success(self, mock_post, mock_db_manager):
        """Test successful API resource assignment."""
        manager = ResourceManager(
            mock_db_manager, api_url="https://api.example.com", api_key="test-key"
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = manager.assign_resource_via_api(1, "documentation", "Guide")

        assert result is True
        mock_post.assert_called_once()

    def test_assign_resource_via_api_not_configured(self, mock_db_manager):
        """Test API assignment when API not configured."""
        manager = ResourceManager(mock_db_manager)

        result = manager.assign_resource_via_api(1, "documentation", "Guide")

        assert result is False
