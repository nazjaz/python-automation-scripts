"""Tracks subscription lifecycle metrics."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Subscription, Customer, SubscriptionMetric

logger = logging.getLogger(__name__)


class MetricsTracker:
    """Tracks subscription lifecycle metrics."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize metrics tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.metrics_config = config.get("metrics", {})
        self.window_days = self.metrics_config.get("calculation_window_days", 30)

    def calculate_mrr(
        self,
        metric_date: Optional[date] = None,
    ) -> float:
        """Calculate Monthly Recurring Revenue (MRR).

        Args:
            metric_date: Optional date for metric calculation.

        Returns:
            MRR value.
        """
        metric_date = metric_date or date.today()

        subscriptions = (
            self.db_manager.get_session()
            .query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.start_date <= metric_date,
            )
            .all()
        )

        mrr = 0.0

        for subscription in subscriptions:
            if subscription.billing_cycle == "monthly":
                mrr += subscription.monthly_revenue
            elif subscription.billing_cycle == "quarterly":
                mrr += subscription.monthly_revenue / 3.0
            elif subscription.billing_cycle == "annual":
                mrr += subscription.monthly_revenue / 12.0
            else:
                mrr += subscription.monthly_revenue

        self.db_manager.add_metric(
            metric_date=metric_date,
            metric_type="mrr",
            value=mrr,
        )

        logger.info(
            f"Calculated MRR: ${mrr:.2f}",
            extra={"metric_date": metric_date, "mrr": mrr},
        )

        return mrr

    def calculate_arr(
        self,
        metric_date: Optional[date] = None,
    ) -> float:
        """Calculate Annual Recurring Revenue (ARR).

        Args:
            metric_date: Optional date for metric calculation.

        Returns:
            ARR value.
        """
        mrr = self.calculate_mrr(metric_date)
        arr = mrr * 12.0

        metric_date = metric_date or date.today()

        self.db_manager.add_metric(
            metric_date=metric_date,
            metric_type="arr",
            value=arr,
        )

        logger.info(
            f"Calculated ARR: ${arr:.2f}",
            extra={"metric_date": metric_date, "arr": arr},
        )

        return arr

    def calculate_churn_rate(
        self,
        metric_date: Optional[date] = None,
        window_days: Optional[int] = None,
    ) -> float:
        """Calculate churn rate.

        Args:
            metric_date: Optional date for metric calculation.
            window_days: Optional calculation window in days.

        Returns:
            Churn rate (0.0 to 1.0).
        """
        metric_date = metric_date or date.today()
        window_days = window_days or self.window_days

        start_date = metric_date - timedelta(days=window_days)

        cancelled_subscriptions = (
            self.db_manager.get_session()
            .query(Subscription)
            .filter(
                Subscription.status == "cancelled",
                Subscription.end_date >= start_date,
                Subscription.end_date <= metric_date,
            )
            .count()
        )

        active_at_start = (
            self.db_manager.get_session()
            .query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.start_date <= start_date,
            )
            .count()
        )

        if active_at_start == 0:
            churn_rate = 0.0
        else:
            churn_rate = cancelled_subscriptions / float(active_at_start)

        self.db_manager.add_metric(
            metric_date=metric_date,
            metric_type="churn_rate",
            value=churn_rate,
        )

        logger.info(
            f"Calculated churn rate: {churn_rate:.2%}",
            extra={"metric_date": metric_date, "churn_rate": churn_rate},
        )

        return churn_rate

    def calculate_renewal_rate(
        self,
        metric_date: Optional[date] = None,
        window_days: Optional[int] = None,
    ) -> float:
        """Calculate renewal rate.

        Args:
            metric_date: Optional date for metric calculation.
            window_days: Optional calculation window in days.

        Returns:
            Renewal rate (0.0 to 1.0).
        """
        from src.database import Renewal

        metric_date = metric_date or date.today()
        window_days = window_days or self.window_days

        start_date = metric_date - timedelta(days=window_days)

        successful_renewals = (
            self.db_manager.get_session()
            .query(Renewal)
            .filter(
                Renewal.status == "success",
                Renewal.renewal_date >= start_date,
                Renewal.renewal_date <= metric_date,
            )
            .count()
        )

        total_renewals = (
            self.db_manager.get_session()
            .query(Renewal)
            .filter(
                Renewal.renewal_date >= start_date,
                Renewal.renewal_date <= metric_date,
            )
            .count()
        )

        if total_renewals == 0:
            renewal_rate = 0.0
        else:
            renewal_rate = successful_renewals / float(total_renewals)

        self.db_manager.add_metric(
            metric_date=metric_date,
            metric_type="renewal_rate",
            value=renewal_rate,
        )

        logger.info(
            f"Calculated renewal rate: {renewal_rate:.2%}",
            extra={"metric_date": metric_date, "renewal_rate": renewal_rate},
        )

        return renewal_rate

    def calculate_lifetime_value(
        self,
        customer_id: int,
    ) -> float:
        """Calculate customer lifetime value.

        Args:
            customer_id: Customer ID.

        Returns:
            Lifetime value.
        """
        customer = (
            self.db_manager.get_session()
            .query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return 0.0

        ltv = 0.0

        for subscription in customer.subscriptions:
            if subscription.status in ["active", "cancelled", "expired"]:
                months_active = (
                    (subscription.end_date or date.today()) - subscription.start_date
                ).days / 30.0
                ltv += subscription.monthly_revenue * months_active

        logger.info(
            f"Calculated LTV for customer {customer_id}: ${ltv:.2f}",
            extra={"customer_id": customer_id, "ltv": ltv},
        )

        return ltv

    def track_all_metrics(
        self,
        metric_date: Optional[date] = None,
    ) -> Dict:
        """Track all configured metrics.

        Args:
            metric_date: Optional date for metric calculation.

        Returns:
            Dictionary with all metric values.
        """
        metric_date = metric_date or date.today()

        metrics = {}

        if self.metrics_config.get("track_mrr", True):
            metrics["mrr"] = self.calculate_mrr(metric_date)

        if self.metrics_config.get("track_arr", True):
            metrics["arr"] = self.calculate_arr(metric_date)

        if self.metrics_config.get("track_churn_rate", True):
            metrics["churn_rate"] = self.calculate_churn_rate(metric_date)

        if self.metrics_config.get("track_renewal_rate", True):
            metrics["renewal_rate"] = self.calculate_renewal_rate(metric_date)

        logger.info(
            f"Tracked all metrics",
            extra={"metric_date": metric_date, "metrics": metrics},
        )

        return metrics
