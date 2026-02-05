"""Activity booking integration and management."""

import logging
from datetime import datetime
from typing import Optional

from src.database import DatabaseManager, ActivityBooking

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for managing activity bookings."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: str,
        api_provider: str = "tripadvisor",
    ):
        """Initialize activity service.

        Args:
            db_manager: Database manager instance.
            api_key: Activity API key.
            api_provider: API provider name.
        """
        self.db_manager = db_manager
        self.api_key = api_key
        self.api_provider = api_provider

    def search_activities(
        self, destination: str, date: datetime, activity_type: Optional[str] = None
    ) -> list[dict]:
        """Search for available activities.

        Args:
            destination: Destination city or location.
            date: Date for the activity.
            activity_type: Type of activity (optional).

        Returns:
            List of available activity options.
        """
        logger.info(f"Searching activities in {destination} on {date}")

        try:
            if self.api_provider == "tripadvisor":
                return self._search_tripadvisor(destination, date, activity_type)
            else:
                logger.warning(f"Unsupported API provider: {self.api_provider}")
                return []

        except Exception as e:
            logger.error(f"Error searching activities: {e}")
            return []

    def _search_tripadvisor(
        self, destination: str, date: datetime, activity_type: Optional[str]
    ) -> list[dict]:
        """Search activities using Tripadvisor API (mock implementation).

        Args:
            destination: Destination.
            date: Activity date.
            activity_type: Activity type.

        Returns:
            List of activity options.
        """
        return [
            {
                "activity_name": "City Tour",
                "activity_type": "tour",
                "location": destination,
                "duration_hours": 3,
                "price": 50.00,
                "rating": 4.7,
            }
        ]

    def book_activity(
        self,
        itinerary_id: int,
        activity_name: str,
        activity_type: str,
        location: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        confirmation_code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ActivityBooking:
        """Book an activity and store in database.

        Args:
            itinerary_id: Itinerary ID.
            activity_name: Activity name.
            activity_type: Type of activity.
            location: Activity location.
            start_time: Activity start time.
            end_time: Activity end time (optional).
            confirmation_code: Booking confirmation code.
            notes: Additional notes (optional).

        Returns:
            Created ActivityBooking object.
        """
        if confirmation_code is None:
            confirmation_code = f"AC{itinerary_id}{activity_name[:3].upper()}"

        with self.db_manager.get_session() as session:
            booking = ActivityBooking(
                itinerary_id=itinerary_id,
                activity_name=activity_name,
                activity_type=activity_type,
                location=location,
                start_time=start_time,
                end_time=end_time,
                confirmation_code=confirmation_code,
                notes=notes,
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)

        logger.info(f"Activity booked: {activity_name} for itinerary {itinerary_id}")
        return booking
