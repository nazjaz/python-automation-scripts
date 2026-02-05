"""Hotel booking integration and management."""

import logging
from datetime import datetime
from typing import Optional

from src.database import DatabaseManager, HotelBooking

logger = logging.getLogger(__name__)


class HotelService:
    """Service for managing hotel bookings."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: str,
        api_provider: str = "booking",
    ):
        """Initialize hotel service.

        Args:
            db_manager: Database manager instance.
            api_key: Hotel API key.
            api_provider: API provider name.
        """
        self.db_manager = db_manager
        self.api_key = api_key
        self.api_provider = api_provider

    def search_hotels(
        self,
        destination: str,
        check_in_date: datetime,
        check_out_date: datetime,
        guests: int = 1,
    ) -> list[dict]:
        """Search for available hotels.

        Args:
            destination: Destination city or location.
            check_in_date: Check-in date.
            check_out_date: Check-out date.
            guests: Number of guests.

        Returns:
            List of available hotel options.
        """
        logger.info(
            f"Searching hotels in {destination} from {check_in_date} to {check_out_date}"
        )

        try:
            if self.api_provider == "booking":
                return self._search_booking(destination, check_in_date, check_out_date, guests)
            else:
                logger.warning(f"Unsupported API provider: {self.api_provider}")
                return []

        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return []

    def _search_booking(
        self,
        destination: str,
        check_in_date: datetime,
        check_out_date: datetime,
        guests: int,
    ) -> list[dict]:
        """Search hotels using Booking.com API (mock implementation).

        Args:
            destination: Destination.
            check_in_date: Check-in date.
            check_out_date: Check-out date.
            guests: Number of guests.

        Returns:
            List of hotel options.
        """
        return [
            {
                "hotel_name": "Example Hotel",
                "address": f"123 Main St, {destination}",
                "price_per_night": 150.00,
                "rating": 4.5,
                "room_types": ["Standard", "Deluxe"],
            }
        ]

    def book_hotel(
        self,
        itinerary_id: int,
        hotel_name: str,
        address: str,
        check_in_date: datetime,
        check_out_date: datetime,
        confirmation_code: Optional[str] = None,
        room_type: Optional[str] = None,
    ) -> HotelBooking:
        """Book a hotel and store in database.

        Args:
            itinerary_id: Itinerary ID.
            hotel_name: Hotel name.
            address: Hotel address.
            check_in_date: Check-in date and time.
            check_out_date: Check-out date and time.
            confirmation_code: Booking confirmation code.
            room_type: Room type (optional).

        Returns:
            Created HotelBooking object.
        """
        if confirmation_code is None:
            confirmation_code = f"HT{itinerary_id}{hotel_name[:3].upper()}"

        with self.db_manager.get_session() as session:
            booking = HotelBooking(
                itinerary_id=itinerary_id,
                hotel_name=hotel_name,
                address=address,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                confirmation_code=confirmation_code,
                room_type=room_type,
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)

        logger.info(f"Hotel booked: {hotel_name} for itinerary {itinerary_id}")
        return booking
