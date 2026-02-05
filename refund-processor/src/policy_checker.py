"""Refund policy checking service."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.database import DatabaseManager, Order

logger = logging.getLogger(__name__)


class PolicyError(Exception):
    """Exception raised for policy violations."""

    pass


class PolicyChecker:
    """Checks refund requests against refund policies."""

    def __init__(self, db_manager: DatabaseManager, policy_config: dict):
        """Initialize policy checker.

        Args:
            db_manager: Database manager instance.
            policy_config: Refund policy configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = policy_config

    def check_policy(
        self,
        order_id: str,
        requested_amount: float,
        refund_reason: str,
        is_partial: bool = False,
    ) -> dict:
        """Check refund request against policies.

        Args:
            order_id: Order identifier.
            requested_amount: Requested refund amount.
            refund_reason: Reason for refund.
            is_partial: Whether this is a partial refund.

        Returns:
            Dictionary with policy check result and approval status.

        Raises:
            PolicyError: If policy check fails.
        """
        order = self.db_manager.get_order_by_id(order_id)
        if not order:
            raise PolicyError(f"Order {order_id} not found")

        max_days = self.config.get("max_refund_days", 90)
        order_age_days = (datetime.utcnow() - order.order_date).days

        if order_age_days > max_days:
            raise PolicyError(
                f"Refund request exceeds maximum refund period of {max_days} days. "
                f"Order is {order_age_days} days old."
            )

        min_amount = self.config.get("min_refund_amount", 1.00)
        if requested_amount < min_amount:
            raise PolicyError(
                f"Requested amount ${requested_amount:.2f} is below minimum "
                f"refund amount of ${min_amount:.2f}"
            )

        max_amount = self.config.get("max_refund_amount", 10000.00)
        if requested_amount > max_amount:
            raise PolicyError(
                f"Requested amount ${requested_amount:.2f} exceeds maximum "
                f"refund amount of ${max_amount:.2f}"
            )

        if requested_amount > order.total_amount:
            raise PolicyError(
                f"Requested amount ${requested_amount:.2f} exceeds order total "
                f"of ${order.total_amount:.2f}"
            )

        if is_partial and not self.config.get("partial_refund_allowed", True):
            raise PolicyError("Partial refunds are not allowed")

        allowed_reasons = self.config.get("refund_reasons", [])
        if allowed_reasons and refund_reason not in allowed_reasons:
            raise PolicyError(
                f"Refund reason '{refund_reason}' is not in allowed reasons list"
            )

        auto_approve_threshold = self.config.get("auto_approve_threshold", 50.00)
        require_approval_above = self.config.get("require_approval_above", 500.00)

        if requested_amount <= auto_approve_threshold:
            approval_status = "auto_approved"
        elif requested_amount >= require_approval_above:
            approval_status = "requires_approval"
        else:
            approval_status = "pending_review"

        logger.info(
            f"Policy check passed for order {order_id}: {approval_status}"
        )

        return {
            "approved": approval_status == "auto_approved",
            "approval_status": approval_status,
            "requires_approval": approval_status == "requires_approval",
        }
