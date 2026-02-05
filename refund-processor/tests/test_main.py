"""Unit tests for refund processing automation."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.database import DatabaseManager, Order, RefundRequest
from src.refund_validator import RefundValidator, ValidationError
from src.policy_checker import PolicyChecker, PolicyError
from src.refund_calculator import RefundCalculator
from src.payment_integrator import PaymentIntegrator, PaymentIntegrationError
from src.email_service import EmailService


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock(spec=DatabaseManager)


@pytest.fixture
def sample_order():
    """Create sample order."""
    order = MagicMock(spec=Order)
    order.order_id = "ORD-12345"
    order.customer_email = "customer@example.com"
    order.customer_name = "Test Customer"
    order.total_amount = 100.00
    order.currency = "USD"
    order.payment_provider = "stripe"
    order.payment_transaction_id = "ch_1234567890"
    order.order_date = datetime.utcnow() - timedelta(days=10)
    return order


class TestRefundValidator:
    """Tests for RefundValidator class."""

    def test_validate_request_success(self, mock_db_manager, sample_order):
        """Test successful validation."""
        validation_config = {
            "require_order_id": True,
            "require_customer_email": True,
            "validate_order_exists": True,
            "validate_customer_match": True,
        }

        validator = RefundValidator(mock_db_manager, validation_config)
        mock_db_manager.get_order_by_id.return_value = sample_order

        result = validator.validate_request(
            order_id="ORD-12345",
            customer_email="customer@example.com",
            requested_amount=50.00,
            refund_reason="defective_product",
        )

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_request_missing_order_id(self, mock_db_manager):
        """Test validation with missing order ID."""
        validation_config = {"require_order_id": True}

        validator = RefundValidator(mock_db_manager, validation_config)

        with pytest.raises(ValidationError, match="Order ID is required"):
            validator.validate_request(
                order_id=None,
                customer_email="customer@example.com",
                requested_amount=50.00,
                refund_reason="defective_product",
            )

    def test_validate_request_order_not_found(self, mock_db_manager):
        """Test validation with non-existent order."""
        validation_config = {
            "require_order_id": True,
            "validate_order_exists": True,
        }

        validator = RefundValidator(mock_db_manager, validation_config)
        mock_db_manager.get_order_by_id.return_value = None

        with pytest.raises(ValidationError, match="Order.*not found"):
            validator.validate_request(
                order_id="ORD-99999",
                customer_email="customer@example.com",
                requested_amount=50.00,
                refund_reason="defective_product",
            )


class TestPolicyChecker:
    """Tests for PolicyChecker class."""

    def test_check_policy_success(self, mock_db_manager, sample_order):
        """Test successful policy check."""
        policy_config = {
            "max_refund_days": 90,
            "min_refund_amount": 1.00,
            "max_refund_amount": 10000.00,
            "auto_approve_threshold": 50.00,
            "refund_reasons": ["defective_product", "not_as_described"],
        }

        checker = PolicyChecker(mock_db_manager, policy_config)
        mock_db_manager.get_order_by_id.return_value = sample_order

        result = checker.check_policy(
            order_id="ORD-12345",
            requested_amount=50.00,
            refund_reason="defective_product",
        )

        assert result["approved"] is True
        assert result["approval_status"] == "auto_approved"

    def test_check_policy_exceeds_max_days(self, mock_db_manager):
        """Test policy check with order exceeding max refund days."""
        old_order = MagicMock(spec=Order)
        old_order.order_id = "ORD-OLD"
        old_order.total_amount = 100.00
        old_order.order_date = datetime.utcnow() - timedelta(days=100)

        policy_config = {"max_refund_days": 90}

        checker = PolicyChecker(mock_db_manager, policy_config)
        mock_db_manager.get_order_by_id.return_value = old_order

        with pytest.raises(PolicyError, match="exceeds maximum refund period"):
            checker.check_policy(
                order_id="ORD-OLD",
                requested_amount=50.00,
                refund_reason="defective_product",
            )

    def test_check_policy_requires_approval(self, mock_db_manager, sample_order):
        """Test policy check requiring approval."""
        policy_config = {
            "max_refund_days": 90,
            "auto_approve_threshold": 50.00,
            "require_approval_above": 500.00,
            "refund_reasons": ["defective_product"],
        }

        checker = PolicyChecker(mock_db_manager, policy_config)
        mock_db_manager.get_order_by_id.return_value = sample_order

        result = checker.check_policy(
            order_id="ORD-12345",
            requested_amount=600.00,
            refund_reason="defective_product",
        )

        assert result["requires_approval"] is True
        assert result["approval_status"] == "requires_approval"


class TestRefundCalculator:
    """Tests for RefundCalculator class."""

    def test_calculate_refund_with_fee(self, mock_db_manager, sample_order):
        """Test refund calculation with restocking fee."""
        policy_config = {
            "restocking_fee_percentage": 0.10,
            "restocking_fee_minimum": 5.00,
        }

        calculator = RefundCalculator(mock_db_manager, policy_config)
        mock_db_manager.get_order_by_id.return_value = sample_order

        result = calculator.calculate_refund(
            order_id="ORD-12345",
            requested_amount=100.00,
            refund_reason="defective_product",
            apply_restocking_fee=True,
        )

        assert result["refund_amount"] == 100.00
        assert result["restocking_fee"] == 10.00
        assert result["net_refund_amount"] == 90.00

    def test_calculate_refund_no_fee(self, mock_db_manager, sample_order):
        """Test refund calculation without restocking fee."""
        policy_config = {
            "restocking_fee_percentage": 0.10,
            "restocking_fee_minimum": 5.00,
        }

        calculator = RefundCalculator(mock_db_manager, policy_config)
        mock_db_manager.get_order_by_id.return_value = sample_order

        result = calculator.calculate_refund(
            order_id="ORD-12345",
            requested_amount=50.00,
            refund_reason="defective_product",
            apply_restocking_fee=False,
        )

        assert result["refund_amount"] == 50.00
        assert result["restocking_fee"] == 0.0
        assert result["net_refund_amount"] == 50.00


class TestPaymentIntegrator:
    """Tests for PaymentIntegrator class."""

    @patch("requests.post")
    def test_process_stripe_refund_success(self, mock_post):
        """Test successful Stripe refund processing."""
        integrator = PaymentIntegrator("stripe", "api_key", "secret_key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "re_1234567890",
            "status": "succeeded",
            "amount": 5000,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = integrator.process_refund(
            transaction_id="ch_1234567890", amount=50.00, currency="USD"
        )

        assert result["success"] is True
        assert result["refund_id"] == "re_1234567890"
        mock_post.assert_called_once()

    def test_process_refund_unsupported_provider(self):
        """Test refund with unsupported provider."""
        integrator = PaymentIntegrator("unsupported", "key", "secret")

        with pytest.raises(PaymentIntegrationError, match="Unsupported payment provider"):
            integrator.process_refund(
                transaction_id="tx_123", amount=50.00, currency="USD"
            )


class TestEmailService:
    """Tests for EmailService class."""

    @patch("smtplib.SMTP")
    def test_send_refund_confirmation(self, mock_smtp):
        """Test refund confirmation email sending."""
        service = EmailService(
            "smtp.example.com",
            587,
            "user",
            "pass",
            "from@example.com",
            "Test Service",
        )

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch.object(service, "send_email", return_value=True) as mock_send:
            result = service.send_refund_confirmation(
                to_email="customer@example.com",
                customer_name="Test Customer",
                order_id="ORD-12345",
                refund_amount=100.00,
                net_refund_amount=90.00,
                restocking_fee=10.00,
                currency="USD",
                refund_reason="defective_product",
            )

            assert result is True
            mock_send.assert_called_once()
