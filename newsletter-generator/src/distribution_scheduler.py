"""Schedules newsletter distribution to subscriber segments."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Newsletter, Subscriber, NewsletterDistribution

logger = logging.getLogger(__name__)


class DistributionScheduler:
    """Schedules newsletter distribution to subscriber segments."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize distribution scheduler.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.distribution_config = config.get("distribution", {})
        self.default_send_time = self.distribution_config.get("default_send_time", "09:00")
        self.batch_size = self.distribution_config.get("batch_size", 100)

    def schedule_distribution(
        self,
        newsletter_id: int,
        segment: Optional[str] = None,
        send_time: Optional[datetime] = None,
    ) -> Dict:
        """Schedule newsletter distribution.

        Args:
            newsletter_id: Newsletter ID.
            segment: Optional subscriber segment.
            send_time: Optional send time.

        Returns:
            Dictionary with scheduling results.
        """
        newsletter = (
            self.db_manager.get_session()
            .query(Newsletter)
            .filter(Newsletter.id == newsletter_id)
            .first()
        )

        if not newsletter:
            raise ValueError(f"Newsletter {newsletter_id} not found")

        if send_time is None:
            send_time = self._calculate_send_time()

        newsletter.scheduled_send_time = send_time
        if segment:
            newsletter.segment = segment

        session = self.db_manager.get_session()
        try:
            session.merge(newsletter)
            session.commit()
        finally:
            session.close()

        subscribers = self.db_manager.get_subscribers(segment=segment, active_only=True)

        scheduled_count = 0
        for subscriber in subscribers:
            distribution = self.db_manager.add_distribution(
                newsletter_id=newsletter_id,
                subscriber_id=subscriber.id,
            )
            scheduled_count += 1

        logger.info(
            f"Scheduled distribution for newsletter {newsletter_id}",
            extra={
                "newsletter_id": newsletter_id,
                "segment": segment,
                "subscriber_count": scheduled_count,
                "send_time": send_time,
            },
        )

        return {
            "success": True,
            "newsletter_id": newsletter_id,
            "scheduled_count": scheduled_count,
            "send_time": send_time,
        }

    def _calculate_send_time(self) -> datetime:
        """Calculate send time from default.

        Returns:
            Calculated send datetime.
        """
        today = datetime.now().date()
        hour, minute = map(int, self.default_send_time.split(":"))
        send_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))

        if send_time < datetime.now():
            send_time += timedelta(days=1)

        return send_time

    def get_scheduled_distributions(
        self,
        limit: Optional[int] = None,
    ) -> List[Newsletter]:
        """Get newsletters scheduled for distribution.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of scheduled Newsletter objects.
        """
        newsletters = self.db_manager.get_unsent_newsletters(limit=limit)

        now = datetime.now()
        ready_to_send = [
            n for n in newsletters
            if n.scheduled_send_time and n.scheduled_send_time <= now
        ]

        return ready_to_send

    def send_newsletter(
        self,
        newsletter_id: int,
    ) -> Dict:
        """Send newsletter to scheduled subscribers.

        Args:
            newsletter_id: Newsletter ID.

        Returns:
            Dictionary with sending results.
        """
        newsletter = (
            self.db_manager.get_session()
            .query(Newsletter)
            .filter(Newsletter.id == newsletter_id)
            .first()
        )

        if not newsletter:
            raise ValueError(f"Newsletter {newsletter_id} not found")

        distributions = (
            self.db_manager.get_session()
            .query(NewsletterDistribution)
            .filter(
                NewsletterDistribution.newsletter_id == newsletter_id,
                NewsletterDistribution.sent_at.is_(None),
            )
            .all()
        )

        sent_count = 0
        failed_count = 0

        for distribution in distributions:
            try:
                subscriber = (
                    self.db_manager.get_session()
                    .query(Subscriber)
                    .filter(Subscriber.id == distribution.subscriber_id)
                    .first()
                )

                if subscriber and subscriber.active:
                    self._send_to_subscriber(newsletter, subscriber, distribution)
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to send newsletter to subscriber {distribution.subscriber_id}: {e}",
                    extra={"subscriber_id": distribution.subscriber_id, "error": str(e)},
                )
                failed_count += 1

        if sent_count > 0:
            newsletter.sent = True
            newsletter.sent_at = datetime.utcnow()

            session = self.db_manager.get_session()
            try:
                session.merge(newsletter)
                session.commit()
            finally:
                session.close()

        logger.info(
            f"Sent newsletter {newsletter_id}",
            extra={
                "newsletter_id": newsletter_id,
                "sent_count": sent_count,
                "failed_count": failed_count,
            },
        )

        return {
            "success": True,
            "sent_count": sent_count,
            "failed_count": failed_count,
        }

    def _send_to_subscriber(
        self,
        newsletter: Newsletter,
        subscriber: Subscriber,
        distribution: NewsletterDistribution,
    ) -> None:
        """Send newsletter to individual subscriber.

        Args:
            newsletter: Newsletter object.
            subscriber: Subscriber object.
            distribution: NewsletterDistribution object.
        """
        distribution.sent_at = datetime.utcnow()

        session = self.db_manager.get_session()
        try:
            session.merge(distribution)
            session.commit()
        finally:
            session.close()

        logger.debug(
            f"Sent newsletter to subscriber {subscriber.email}",
            extra={"subscriber_id": subscriber.id, "newsletter_id": newsletter.id},
        )
