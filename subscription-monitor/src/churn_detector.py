"""Detects churn risks for customers."""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Customer, Subscription, ChurnRisk, PaymentFailure

logger = logging.getLogger(__name__)


class ChurnDetector:
    """Detects churn risks for customers."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize churn detector.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.churn_config = config.get("churn_detection", {})
        self.risk_factors = self.churn_config.get("risk_factors", {})
        self.risk_levels = self.churn_config.get("risk_levels", {})

    def assess_churn_risk(
        self,
        customer_id: int,
    ) -> ChurnRisk:
        """Assess churn risk for customer.

        Args:
            customer_id: Customer ID.

        Returns:
            ChurnRisk object.
        """
        customer = (
            self.db_manager.get_session()
            .query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        risk_score, risk_level, factors = self._calculate_risk_score(customer)

        churn_risk = self.db_manager.add_churn_risk(
            customer_id=customer_id,
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            engagement_score=self._calculate_engagement_score(customer),
            days_since_last_activity=self._get_days_since_last_activity(customer),
            payment_failure_count=self._get_payment_failure_count(customer),
            support_ticket_count=0,
        )

        logger.info(
            f"Assessed churn risk for customer {customer_id}",
            extra={
                "customer_id": customer_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
            },
        )

        return churn_risk

    def _calculate_risk_score(self, customer: Customer) -> tuple:
        """Calculate churn risk score.

        Args:
            customer: Customer object.

        Returns:
            Tuple of (risk_score, risk_level, factors).
        """
        risk_score = 0.0
        factors = []

        payment_failures = self._get_payment_failure_count(customer)
        if payment_failures >= self.risk_factors.get("payment_failures", 2):
            risk_score += 0.3
            factors.append(f"Payment failures: {payment_failures}")

        engagement_score = self._calculate_engagement_score(customer)
        if engagement_score < self.risk_factors.get("engagement_score_threshold", 0.3):
            risk_score += 0.25
            factors.append(f"Low engagement score: {engagement_score:.2f}")

        days_since_activity = self._get_days_since_last_activity(customer)
        if days_since_activity > self.risk_factors.get("days_since_last_activity", 30):
            risk_score += 0.2
            factors.append(f"Days since last activity: {days_since_activity}")

        subscriptions = customer.subscriptions
        active_subscriptions = [s for s in subscriptions if s.status == "active"]
        if not active_subscriptions:
            risk_score += 0.25
            factors.append("No active subscriptions")

        for subscription in active_subscriptions:
            if not subscription.auto_renewal:
                risk_score += 0.1
                factors.append(f"Auto-renewal disabled for subscription {subscription.subscription_id}")

            days_until_renewal = (subscription.renewal_date - date.today()).days
            if days_until_renewal < 7:
                risk_score += 0.15
                factors.append(f"Renewal in {days_until_renewal} days")

        risk_score = min(1.0, risk_score)

        if risk_score >= self.risk_levels.get("critical", 0.9):
            risk_level = "critical"
        elif risk_score >= self.risk_levels.get("high", 0.7):
            risk_level = "high"
        elif risk_score >= self.risk_levels.get("medium", 0.4):
            risk_level = "medium"
        else:
            risk_level = "low"

        factors_str = "; ".join(factors) if factors else "No significant risk factors"

        return risk_score, risk_level, factors_str

    def _calculate_engagement_score(self, customer: Customer) -> float:
        """Calculate customer engagement score.

        Args:
            customer: Customer object.

        Returns:
            Engagement score (0.0 to 1.0).
        """
        score = 0.5

        subscriptions = customer.subscriptions
        active_count = len([s for s in subscriptions if s.status == "active"])

        if active_count > 0:
            score += 0.3

        days_since_activity = self._get_days_since_last_activity(customer)
        if days_since_activity < 7:
            score += 0.2
        elif days_since_activity < 30:
            score += 0.1

        return min(1.0, score)

    def _get_days_since_last_activity(self, customer: Customer) -> int:
        """Get days since last customer activity.

        Args:
            customer: Customer object.

        Returns:
            Days since last activity.
        """
        subscriptions = customer.subscriptions
        if not subscriptions:
            return 999

        latest_renewal = None
        for subscription in subscriptions:
            renewals = subscription.renewals
            if renewals:
                latest = max(renewals, key=lambda r: r.renewal_date)
                if latest_renewal is None or latest.renewal_date > latest_renewal:
                    latest_renewal = latest.renewal_date

        if latest_renewal:
            return (date.today() - latest_renewal).days

        latest_start = max([s.start_date for s in subscriptions])
        return (date.today() - latest_start).days

    def _get_payment_failure_count(self, customer: Customer) -> int:
        """Get payment failure count for customer.

        Args:
            customer: Customer object.

        Returns:
            Payment failure count.
        """
        count = 0
        for subscription in customer.subscriptions:
            failures = [
                f for f in subscription.payment_failures if not f.resolved
            ]
            count += len(failures)

        return count

    def identify_at_risk_customers(
        self,
        risk_level: str = "high",
        limit: Optional[int] = None,
    ) -> List[ChurnRisk]:
        """Identify customers at risk of churning.

        Args:
            risk_level: Minimum risk level to include.
            limit: Optional limit on number of results.

        Returns:
            List of ChurnRisk objects.
        """
        customers = (
            self.db_manager.get_session()
            .query(Customer)
            .all()
        )

        at_risk = []

        for customer in customers:
            risk = self.assess_churn_risk(customer.id)

            if risk.risk_level in ["high", "critical"] or (
                risk_level == "medium" and risk.risk_level in ["medium", "high", "critical"]
            ):
                at_risk.append(risk)

        at_risk.sort(key=lambda x: x.risk_score, reverse=True)

        if limit:
            at_risk = at_risk[:limit]

        logger.info(
            f"Identified {len(at_risk)} at-risk customers",
            extra={"at_risk_count": len(at_risk), "risk_level": risk_level},
        )

        return at_risk
