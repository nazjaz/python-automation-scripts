"""Flight booking integration and management."""

import logging
from datetime import datetime
from typing import Optional

import requests

from src.database import DatabaseManager, FlightBooking

logger = logging.getLogger(__name__)


class FlightService:
    """Service for managing flight bookings."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: str,
        api_secret: str,
        api_provider: str = "amadeus",
    ):
        """Initialize flight service.

        Args:
            db_manager: Database manager instance.
            api_key: Flight API key.
            api_secret: Flight API secret.
            api_provider: API provider name.
        """
        self.db_manager = db_manager
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_provider = api_provider

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime] = None,
    ) -> list[dict]:
        """Search for available flights.

        Args:
            origin: Origin airport code.
            destination: Destination airport code.
            departure_date: Departure date and time.
            return_date: Return date and time (optional for one-way).

        Returns:
            List of available flight options.
        """
        logger.info(
            f"Searching flights: {origin} to {destination} on {departure_date}"
        )

        try:
            if self.api_provider == "amadeus":
                return self._search_amadeus(origin, destination, departure_date, return_date)
            else:
                logger.warning(f"Unsupported API provider: {self.api_provider}")
                return []

        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return []

    def _search_amadeus(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime],
    ) -> list[dict]:
        """Search flights using Amadeus API (mock implementation).

        Args:
            origin: Origin airport code.
            destination: Destination airport code.
            departure_date: Departure date.
            return_date: Return date.

        Returns:
            List of flight options.
        """
        return [
            {
                "airline": "Example Airlines",
                "flight_number": "EX123",
                "departure_airport": origin,
                "arrival_airport": destination,
                "departure_time": departure_date,
                "arrival_time": departure_date.replace(hour=departure_date.hour + 3),
                "price": 299.99,
            }
        ]

    def book_flight(
        self,
        itinerary_id: int,
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        arrival_time: datetime,
        confirmation_code: Optional[str] = None,
        gate: Optional[str] = None,
        seat: Optional[str] = None,
    ) -> FlightBooking:
        """Book a flight and store in database.

        Args:
            itinerary_id: Itinerary ID.
            airline: Airline name.
            flight_number: Flight number.
            departure_airport: Departure airport code.
            arrival_airport: Arrival airport code.
            departure_time: Departure date and time.
            arrival_time: Arrival date and time.
            confirmation_code: Booking confirmation code.
            gate: Gate number (optional).
            seat: Seat assignment (optional).

        Returns:
            Created FlightBooking object.
        """
        if confirmation_code is None:
            confirmation_code = f"FL{itinerary_id}{flight_number}"

        with self.db_manager.get_session() as session:
            booking = FlightBooking(
                itinerary_id=itinerary_id,
                airline=airline,
                flight_number=flight_number,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                departure_time=departure_time,
                arrival_time=arrival_time,
                confirmation_code=confirmation_code,
                gate=gate,
                seat=seat,
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)

        logger.info(f"Flight booked: {flight_number} for itinerary {itinerary_id}")
        return booking

    def check_flight_updates(self, flight_booking_id: int) -> Optional[dict]:
        """Check for flight updates (gate changes, delays, etc.).

        Args:
            flight_booking_id: Flight booking ID.

        Returns:
            Dictionary with update information or None if no updates.
        """
        with self.db_manager.get_session() as session:
            booking = (
                session.query(FlightBooking)
                .filter(FlightBooking.id == flight_booking_id)
                .first()
            )

            if not booking:
                return None

            try:
                if self.api_provider == "amadeus":
                    updates = self._check_amadeus_updates(booking)
                    if updates:
                        booking.gate = updates.get("gate", booking.gate)
                        booking.status = updates.get("status", booking.status)
                        session.commit()
                    return updates
            except Exception as e:
                logger.error(f"Error checking flight updates: {e}")
                return None

        return None

    def _check_amadeus_updates(self, booking: FlightBooking) -> Optional[dict]:
        """Check updates using Amadeus API (mock implementation).

        Args:
            booking: FlightBooking object.

        Returns:
            Dictionary with updates or None.
        """
        return None
