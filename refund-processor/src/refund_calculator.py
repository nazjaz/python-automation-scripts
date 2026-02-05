"""Refund amount calculation service."""

import logging
from typing import Optional

from src.database import DatabaseManager, Order

logger = logging.getLogger(__name__)


class RefundCalculator:
    """Calculates refund amounts including fees and adjustments."""

    def __init__(self, db_manager: DatabaseManager, policy_config: dict):
        """Initialize refund calculator.

        Args:
            db_manager: Database manager instance.
            policy_config: Refund policy configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = policy_config

    def calculate_refund(
        self,
        order_id: str,
        requested_amount: float,
        refund_reason: str,
        apply_restocking_fee: bool = True,
    ) -> dict:
        """Calculate refund amount with fees.

        Args:
            order_id: Order identifier.
            requested_amount: Requested refund amount.
            refund_reason: Reason for refund.
            apply_restocking_fee: Whether to apply restocking fee.

        Returns:
            Dictionary with calculated refund amounts.
        """
        order = self.db_manager.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        refund_amount = min(requested_amount, order.total_amount)

        restocking_fee = 0.0
        if apply_restocking_fee:
            restocking_fee_percentage = self.config.get(
                "restocking_fee_percentage", 0.10
            )
            restocking_fee_minimum = self.config.get("restocking_fee_minimum", 5.00)

            calculated_fee = refund_amount * restocking_fee_percentage
            restocking_fee = max(calculated_fee, restocking_fee_minimum)

        net_refund_amount = refund_amount - restocking_fee

        if net_refund_amount < 0:
            net_refund_amount = 0.0
            restocking_fee = refund_amount

        logger.info(
            f"Calculated refund for order {order_id}: "
            f"${refund_amount:.2f} - ${restocking_fee:.2f} fee = "
            f"${net_refund_amount:.2f}"
        )

        return {
            "refund_amount": refund_amount,
            "restocking_fee": restocking_fee,
            "net_refund_amount": net_refund_amount,
            "currency": order.currency,
            "original_order_amount": order.total_amount,
        }
