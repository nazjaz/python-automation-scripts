"""Database models and operations for storing travel itineraries."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Itinerary(Base):
    """Itinerary model for storing travel plans."""

    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    traveler_name = Column(String, nullable=False)
    traveler_email = Column(String, nullable=False)
    traveler_phone = Column(String, nullable=True)
    trip_start_date = Column(DateTime, nullable=False)
    trip_end_date = Column(DateTime, nullable=False)
    destination = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FlightBooking(Base):
    """Flight booking model."""

    __tablename__ = "flight_bookings"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, index=True, nullable=False)
    airline = Column(String, nullable=False)
    flight_number = Column(String, nullable=False)
    departure_airport = Column(String, nullable=False)
    arrival_airport = Column(String, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    gate = Column(String, nullable=True)
    seat = Column(String, nullable=True)
    confirmation_code = Column(String, nullable=False)
    status = Column(String, default="confirmed")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HotelBooking(Base):
    """Hotel booking model."""

    __tablename__ = "hotel_bookings"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, index=True, nullable=False)
    hotel_name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    confirmation_code = Column(String, nullable=False)
    room_type = Column(String, nullable=True)
    status = Column(String, default="confirmed")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityBooking(Base):
    """Activity booking model."""

    __tablename__ = "activity_bookings"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, index=True, nullable=False)
    activity_name = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    confirmation_code = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, default="confirmed")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    """Reminder model for tracking sent reminders."""

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, index=True, nullable=False)
    reminder_type = Column(String, nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, database_url: str):
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get database session context manager.

        Yields:
            Database session.
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_itinerary(
        self,
        traveler_name: str,
        traveler_email: str,
        trip_start_date: datetime,
        trip_end_date: datetime,
        destination: str,
        traveler_phone: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Itinerary:
        """Create a new itinerary.

        Args:
            traveler_name: Traveler's full name.
            traveler_email: Traveler's email address.
            trip_start_date: Trip start date and time.
            trip_end_date: Trip end date and time.
            destination: Trip destination.
            traveler_phone: Traveler's phone number (optional).
            timezone: Timezone for the trip.

        Returns:
            Created Itinerary object.
        """
        with self.get_session() as session:
            itinerary = Itinerary(
                traveler_name=traveler_name,
                traveler_email=traveler_email,
                traveler_phone=traveler_phone,
                trip_start_date=trip_start_date,
                trip_end_date=trip_end_date,
                destination=destination,
                timezone=timezone,
            )
            session.add(itinerary)
            session.commit()
            session.refresh(itinerary)
            return itinerary

    def get_itinerary(self, itinerary_id: int) -> Optional[Itinerary]:
        """Get itinerary by ID.

        Args:
            itinerary_id: Itinerary ID.

        Returns:
            Itinerary object if found, None otherwise.
        """
        with self.get_session() as session:
            return session.query(Itinerary).filter(Itinerary.id == itinerary_id).first()
