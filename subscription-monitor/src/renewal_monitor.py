"""Monitors subscription renewals."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Subscription, Renewal

logger = logging.getLogger(__name__)


class RenewalMonitor:
    """Monitors subscription renewals."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize renewal monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.monitoring_config = config.get("monitoring", {})
        self.days_ahead = self.monitoring_config.get("renewal_check_days_ahead", 30)
        self.days_past = self.monitoring_config.get("renewal_check_days_past", 7)

    def check_renewals(
        self,
        days_ahead: Optional[int] = None,
        days_past: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Subscription]:
        """Check subscriptions due for renewal.

        Args:
            days_ahead: Optional days ahead to check.
            days_past: Optional days past to check.
            status: Optional status filter.

        Returns:
            List of Subscription objects due for renewal.
        """
        days_ahead = days_ahead or self.days_ahead
        days_past = days_past or self.days_past

        subscriptions = self.db_manager.get_subscriptions_due_for_renewal(
            days_ahead=days_ahead,
            days_past=days_past,
            status=status,
        )

        logger.info(
            f"Found {len(subscriptions)} subscriptions due for renewal",
            extra={"subscription_count": len(subscriptions)},
        )

        return subscriptions

    def process_renewal(
        self,
        subscription_id: int,
        renewal_date: Optional[date] = None,
        amount: Optional[float] = None,
        status: str = "success",
    ) -> Renewal:
        """Process a subscription renewal.

        Args:
            subscription_id: Subscription ID.
            renewal_date: Optional renewal date (uses subscription renewal_date if not provided).
            amount: Optional renewal amount (uses subscription monthly_revenue if not provided).
            status: Renewal status.

        Returns:
            Renewal object.
        """
        subscription = (
            self.db_manager.get_session()
            .query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )

        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        renewal_date = renewal_date or subscription.renewal_date
        amount = amount or subscription.monthly_revenue

        previous_renewal_date = subscription.renewal_date

        renewal = self.db_manager.add_renewal(
            subscription_id=subscription_id,
            renewal_date=renewal_date,
            amount=amount,
            status=status,
            previous_renewal_date=previous_renewal_date,
        )

        if status == "success":
            from datetime import timedelta

            if subscription.billing_cycle == "monthly":
                next_renewal = renewal_date + timedelta(days=30)
            elif subscription.billing_cycle == "quarterly":
                next_renewal = renewal_date + timedelta(days=90)
            elif subscription.billing_cycle == "annual":
                next_renewal = renewal_date + timedelta(days=365)
            else:
                next_renewal = renewal_date + timedelta(days=30)

            subscription.renewal_date = next_renewal
            subscription.status = "active"
            renewal.processed_at = datetime.utcnow()

            session = self.db_manager.get_session()
            try:
                session.merge(subscription)
                session.merge(renewal)
                session.commit()
            finally:
                session.close()

        logger.info(
            f"Processed renewal for subscription {subscription_id}",
            extra={
                "subscription_id": subscription_id,
                "renewal_date": renewal_date,
                "status": status,
            },
        )

        return renewal

    def identify_upcoming_renewals(
        self,
        days_ahead: int = 30,
    ) -> List[Dict]:
        """Identify upcoming renewals that need attention.

        Args:
            days_ahead: Days ahead to check.

        Returns:
            List of dictionaries with renewal information.
        """
        subscriptions = self.check_renewals(days_ahead=days_ahead, status="active")

        upcoming_renewals = []

        for subscription in subscriptions:
            days_until_renewal = (subscription.renewal_date - date.today()).days

            upcoming_renewals.append(
                {
                    "subscription_id": subscription.id,
                    "customer_id": subscription.customer_id,
                    "renewal_date": subscription.renewal_date,
                    "days_until_renewal": days_until_renewal,
                    "amount": subscription.monthly_revenue,
                    "auto_renewal": subscription.auto_renewal,
                    "status": subscription.status,
                }
            )

        logger.info(
            f"Identified {len(upcoming_renewals)} upcoming renewals",
            extra={"upcoming_renewal_count": len(upcoming_renewals)},
        )

        return upcoming_renewals
