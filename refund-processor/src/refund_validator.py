"""Refund request validation service."""

import logging
from typing import Optional

from src.database import DatabaseManager, Order

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


class RefundValidator:
    """Validates refund requests against business rules."""

    def __init__(self, db_manager: DatabaseManager, validation_config: dict):
        """Initialize refund validator.

        Args:
            db_manager: Database manager instance.
            validation_config: Validation configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = validation_config

    def validate_request(
        self,
        order_id: Optional[str],
        customer_email: Optional[str],
        requested_amount: Optional[float],
        refund_reason: Optional[str],
    ) -> dict:
        """Validate refund request.

        Args:
            order_id: Order identifier.
            customer_email: Customer email address.
            requested_amount: Requested refund amount.
            refund_reason: Reason for refund.

        Returns:
            Dictionary with validation result and errors.

        Raises:
            ValidationError: If validation fails.
        """
        errors = []

        if self.config.get("require_order_id", True):
            if not order_id:
                errors.append("Order ID is required")
            elif not isinstance(order_id, str) or len(order_id.strip()) == 0:
                errors.append("Order ID must be a non-empty string")

        if self.config.get("require_customer_email", True):
            if not customer_email:
                errors.append("Customer email is required")
            elif "@" not in str(customer_email):
                errors.append("Invalid email format")

        if requested_amount is None:
            errors.append("Requested amount is required")
        elif not isinstance(requested_amount, (int, float)) or requested_amount <= 0:
            errors.append("Requested amount must be a positive number")

        if not refund_reason:
            errors.append("Refund reason is required")

        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        if self.config.get("validate_order_exists", True) and order_id:
            order = self.db_manager.get_order_by_id(order_id)
            if not order:
                raise ValidationError(f"Order {order_id} not found")

            if self.config.get("validate_customer_match", True):
                if order.customer_email.lower() != customer_email.lower():
                    raise ValidationError(
                        "Customer email does not match order customer"
                    )

        if self.config.get("check_duplicate_refunds", True) and order_id:
            refund_count = self.db_manager.get_refund_count_for_order(order_id)
            max_refunds = self.config.get("max_refunds_per_order", 3)
            if refund_count >= max_refunds:
                raise ValidationError(
                    f"Maximum refunds ({max_refunds}) already processed for this order"
                )

        logger.info(f"Refund request validated successfully for order {order_id}")
        return {"valid": True, "errors": []}
