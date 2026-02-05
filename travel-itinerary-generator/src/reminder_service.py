"""Reminder scheduling and management service."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.database import DatabaseManager, Itinerary, Reminder
from src.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing travel reminders."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        notification_service: NotificationService,
        reminder_hours: list[int],
    ):
        """Initialize reminder service.

        Args:
            db_manager: Database manager instance.
            notification_service: Notification service instance.
            reminder_hours: List of hours before trip to send reminders.
        """
        self.db_manager = db_manager
        self.notification_service = notification_service
        self.reminder_hours = sorted(reminder_hours, reverse=True)

    def schedule_reminders(self, itinerary_id: int) -> list[Reminder]:
        """Schedule reminders for an itinerary.

        Args:
            itinerary_id: Itinerary ID.

        Returns:
            List of created Reminder objects.
        """
        with self.db_manager.get_session() as session:
            itinerary = (
                session.query(Itinerary)
                .filter(Itinerary.id == itinerary_id)
                .first()
            )

            if not itinerary:
                logger.warning(f"Itinerary {itinerary_id} not found")
                return []

            reminders = []
            for hours_before in self.reminder_hours:
                reminder_time = itinerary.trip_start_date - timedelta(hours=hours_before)

                if reminder_time > datetime.utcnow():
                    reminder = Reminder(
                        itinerary_id=itinerary_id,
                        reminder_type="trip_start",
                        reminder_time=reminder_time,
                    )
                    session.add(reminder)
                    reminders.append(reminder)

            session.commit()

            for reminder in reminders:
                session.refresh(reminder)

            logger.info(
                f"Scheduled {len(reminders)} reminders for itinerary {itinerary_id}"
            )
            return reminders

    def process_due_reminders(self) -> int:
        """Process and send due reminders.

        Returns:
            Number of reminders sent.
        """
        with self.db_manager.get_session() as session:
            due_reminders = (
                session.query(Reminder)
                .filter(
                    Reminder.sent == False,
                    Reminder.reminder_time <= datetime.utcnow(),
                )
                .all()
            )

            sent_count = 0
            for reminder in due_reminders:
                itinerary = (
                    session.query(Itinerary)
                    .filter(Itinerary.id == reminder.itinerary_id)
                    .first()
                )

                if not itinerary:
                    continue

                hours_until = (
                    itinerary.trip_start_date - datetime.utcnow()
                ).total_seconds() / 3600

                success = self.notification_service.send_travel_reminder(
                    to_email=itinerary.traveler_email,
                    traveler_name=itinerary.traveler_name,
                    trip_start_date=itinerary.trip_start_date.isoformat(),
                    destination=itinerary.destination,
                    hours_until=int(hours_until),
                )

                if success:
                    reminder.sent = True
                    reminder.sent_at = datetime.utcnow()
                    sent_count += 1

            session.commit()

            logger.info(f"Processed {sent_count} reminders")
            return sent_count
