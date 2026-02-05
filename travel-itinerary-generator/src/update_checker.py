"""Real-time travel update checking service."""

import logging
from datetime import datetime
from typing import Optional

from src.database import DatabaseManager, FlightBooking, Itinerary
from src.flight_service import FlightService
from src.notification_service import NotificationService

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Service for checking and notifying about travel updates."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        flight_service: FlightService,
        notification_service: NotificationService,
    ):
        """Initialize update checker.

        Args:
            db_manager: Database manager instance.
            flight_service: Flight service instance.
            notification_service: Notification service instance.
        """
        self.db_manager = db_manager
        self.flight_service = flight_service
        self.notification_service = notification_service

    def check_all_updates(self) -> int:
        """Check for updates on all active itineraries.

        Returns:
            Number of updates found and notified.
        """
        with self.db_manager.get_session() as session:
            active_itineraries = (
                session.query(Itinerary)
                .filter(Itinerary.status == "active")
                .all()
            )

            update_count = 0
            for itinerary in active_itineraries:
                updates = self.check_itinerary_updates(itinerary.id)
                if updates:
                    update_count += len(updates)

            logger.info(f"Checked updates for {len(active_itineraries)} itineraries")
            return update_count

    def check_itinerary_updates(self, itinerary_id: int) -> list[dict]:
        """Check for updates on a specific itinerary.

        Args:
            itinerary_id: Itinerary ID.

        Returns:
            List of update dictionaries.
        """
        with self.db_manager.get_session() as session:
            itinerary = (
                session.query(Itinerary)
                .filter(Itinerary.id == itinerary_id)
                .first()
            )

            if not itinerary:
                return []

            flight_bookings = (
                session.query(FlightBooking)
                .filter(FlightBooking.itinerary_id == itinerary_id)
                .all()
            )

            updates = []
            for booking in flight_bookings:
                flight_updates = self.flight_service.check_flight_updates(booking.id)
                if flight_updates:
                    update_message = self._format_flight_update(booking, flight_updates)
                    self.notification_service.send_update_notification(
                        to_email=itinerary.traveler_email,
                        traveler_name=itinerary.traveler_name,
                        update_type="flight_update",
                        update_message=update_message,
                    )
                    updates.append(
                        {
                            "type": "flight_update",
                            "booking_id": booking.id,
                            "details": flight_updates,
                        }
                    )

            return updates

    def _format_flight_update(
        self, booking: FlightBooking, updates: dict
    ) -> str:
        """Format flight update message.

        Args:
            booking: FlightBooking object.
            updates: Update dictionary.

        Returns:
            Formatted update message.
        """
        message_parts = [f"Update for flight {booking.flight_number}:"]

        if "gate" in updates and updates["gate"] != booking.gate:
            message_parts.append(f"Gate changed to {updates['gate']}")

        if "status" in updates:
            message_parts.append(f"Status: {updates['status']}")

        return " ".join(message_parts)
