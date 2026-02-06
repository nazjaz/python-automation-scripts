"""Triggers retention campaigns for at-risk customers."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager, Customer, ChurnRisk, RetentionCampaign, Subscription

logger = logging.getLogger(__name__)


class CampaignTrigger:
    """Triggers retention campaigns for at-risk customers."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize campaign trigger.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.retention_config = config.get("retention", {})
        self.campaign_types = self.retention_config.get("campaign_types", [])
        self.trigger_conditions = self.retention_config.get("trigger_conditions", {})

    def trigger_campaign(
        self,
        customer_id: int,
        campaign_type: str,
        triggered_by: Optional[str] = None,
    ) -> RetentionCampaign:
        """Trigger a retention campaign for customer.

        Args:
            customer_id: Customer ID.
            campaign_type: Campaign type.
            triggered_by: Optional trigger reason.

        Returns:
            RetentionCampaign object.
        """
        if campaign_type not in self.campaign_types:
            raise ValueError(f"Invalid campaign type: {campaign_type}")

        campaign = self.db_manager.add_retention_campaign(
            customer_id=customer_id,
            campaign_type=campaign_type,
            triggered_by=triggered_by,
        )

        logger.info(
            f"Triggered campaign {campaign_type} for customer {customer_id}",
            extra={
                "customer_id": customer_id,
                "campaign_type": campaign_type,
                "triggered_by": triggered_by,
            },
        )

        return campaign

    def check_and_trigger_campaigns(
        self,
        customer_id: Optional[int] = None,
    ) -> List[RetentionCampaign]:
        """Check conditions and trigger campaigns.

        Args:
            customer_id: Optional customer ID filter.

        Returns:
            List of triggered RetentionCampaign objects.
        """
        if not self.retention_config.get("campaigns_enabled", True):
            return []

        triggered_campaigns = []

        if customer_id:
            customers = [
                self.db_manager.get_session()
                .query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            ]
            customers = [c for c in customers if c]
        else:
            customers = (
                self.db_manager.get_session()
                .query(Customer)
                .all()
            )

        for customer in customers:
            campaigns = self._evaluate_customer_triggers(customer)
            triggered_campaigns.extend(campaigns)

        logger.info(
            f"Triggered {len(triggered_campaigns)} campaigns",
            extra={"campaign_count": len(triggered_campaigns)},
        )

        return triggered_campaigns

    def _evaluate_customer_triggers(self, customer: Customer) -> List[RetentionCampaign]:
        """Evaluate triggers for customer and create campaigns.

        Args:
            customer: Customer object.

        Returns:
            List of RetentionCampaign objects.
        """
        campaigns = []

        if self.trigger_conditions.get("high_risk_churn", True):
            latest_risk = (
                self.db_manager.get_session()
                .query(ChurnRisk)
                .filter(
                    ChurnRisk.customer_id == customer.id,
                    ChurnRisk.resolved == False,
                )
                .order_by(ChurnRisk.assessed_at.desc())
                .first()
            )

            if latest_risk and latest_risk.risk_level in ["high", "critical"]:
                campaign_type = "email_discount" if latest_risk.risk_level == "critical" else "email_engagement"
                campaign = self.trigger_campaign(
                    customer_id=customer.id,
                    campaign_type=campaign_type,
                    triggered_by="high_risk_churn",
                )
                campaigns.append(campaign)

        if self.trigger_conditions.get("payment_failure", True):
            for subscription in customer.subscriptions:
                failures = [
                    f for f in subscription.payment_failures if not f.resolved
                ]
                if len(failures) >= 1:
                    campaign = self.trigger_campaign(
                        customer_id=customer.id,
                        campaign_type="email_discount",
                        triggered_by="payment_failure",
                    )
                    campaigns.append(campaign)
                    break

        if self.trigger_conditions.get("renewal_reminder", True):
            for subscription in customer.subscriptions:
                if subscription.status == "active":
                    from datetime import date, timedelta

                    days_until_renewal = (subscription.renewal_date - date.today()).days
                    if 7 <= days_until_renewal <= 14:
                        campaign = self.trigger_campaign(
                            customer_id=customer.id,
                            campaign_type="email_engagement",
                            triggered_by="renewal_reminder",
                        )
                        campaigns.append(campaign)
                        break

        return campaigns

    def send_campaign(
        self,
        campaign_id: int,
    ) -> RetentionCampaign:
        """Send a retention campaign.

        Args:
            campaign_id: Campaign ID.

        Returns:
            Updated RetentionCampaign object.
        """
        campaign = (
            self.db_manager.get_session()
            .query(RetentionCampaign)
            .filter(RetentionCampaign.id == campaign_id)
            .first()
        )

        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign.status = "sent"
        campaign.sent_at = datetime.utcnow()

        session = self.db_manager.get_session()
        try:
            session.merge(campaign)
            session.commit()
            session.refresh(campaign)
        finally:
            session.close()

        logger.info(
            f"Sent campaign {campaign_id}",
            extra={"campaign_id": campaign_id, "campaign_type": campaign.campaign_type},
        )

        return campaign
