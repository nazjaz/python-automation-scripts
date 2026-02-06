"""Database models and operations for event registration data."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Float,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class Event(Base):
    """Database model for events."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False, index=True)
    location = Column(String(500))
    capacity = Column(Integer, nullable=False, default=100)
    current_registrations = Column(Integer, default=0)
    allow_waitlist = Column(Boolean, default=True)
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name={self.name}, event_date={self.event_date})>"


class Registration(Base):
    """Database model for event registrations."""

    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255))
    phone = Column(String(50))
    ticket_type = Column(String(100))
    dietary_restrictions = Column(Text)
    special_requests = Column(Text)
    status = Column(String(50), default="pending", index=True)
    is_waitlist = Column(Boolean, default=False, index=True)
    waitlist_position = Column(Integer)
    confirmation_sent = Column(Boolean, default=False)
    badge_generated = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime)

    event = relationship("Event", back_populates="registrations")

    def __repr__(self) -> str:
        return (
            f"<Registration(id={self.id}, event_id={self.event_id}, "
            f"email={self.email}, status={self.status})>"
        )


class DatabaseManager:
    """Manages database operations for event registration data."""

    def __init__(self, database_url: str) -> None:
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session.

        Returns:
            SQLAlchemy session object.
        """
        return self.SessionLocal()

    def add_event(
        self,
        name: str,
        event_date: datetime,
        location: Optional[str] = None,
        description: Optional[str] = None,
        capacity: int = 100,
        allow_waitlist: bool = True,
        status: str = "active",
    ) -> Event:
        """Add or update event.

        Args:
            name: Event name.
            event_date: Event date and time.
            location: Optional event location.
            description: Optional event description.
            capacity: Maximum capacity.
            allow_waitlist: Whether to allow waitlist.
            status: Event status.

        Returns:
            Event object.
        """
        session = self.get_session()
        try:
            event = Event(
                name=name,
                event_date=event_date,
                location=location,
                description=description,
                capacity=capacity,
                allow_waitlist=allow_waitlist,
                status=status,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        finally:
            session.close()

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get event by ID.

        Args:
            event_id: Event ID.

        Returns:
            Event object or None.
        """
        session = self.get_session()
        try:
            return session.query(Event).filter(Event.id == event_id).first()
        finally:
            session.close()

    def get_events(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """Get events with optional filtering.

        Args:
            status: Optional status filter.
            limit: Optional limit on number of results.

        Returns:
            List of Event objects.
        """
        session = self.get_session()
        try:
            query = session.query(Event)

            if status:
                query = query.filter(Event.status == status)

            query = query.order_by(Event.event_date.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_registration(
        self,
        event_id: int,
        name: str,
        email: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        ticket_type: Optional[str] = None,
        dietary_restrictions: Optional[str] = None,
        special_requests: Optional[str] = None,
        status: str = "pending",
        is_waitlist: bool = False,
    ) -> Registration:
        """Add registration.

        Args:
            event_id: Event ID.
            name: Registrant name.
            email: Registrant email.
            company: Optional company name.
            phone: Optional phone number.
            ticket_type: Optional ticket type.
            dietary_restrictions: Optional dietary restrictions.
            special_requests: Optional special requests.
            status: Registration status.
            is_waitlist: Whether this is a waitlist registration.

        Returns:
            Registration object.
        """
        session = self.get_session()
        try:
            registration = Registration(
                event_id=event_id,
                name=name,
                email=email,
                company=company,
                phone=phone,
                ticket_type=ticket_type,
                dietary_restrictions=dietary_restrictions,
                special_requests=special_requests,
                status=status,
                is_waitlist=is_waitlist,
            )
            session.add(registration)
            session.commit()
            session.refresh(registration)
            return registration
        finally:
            session.close()

    def get_registrations(
        self,
        event_id: Optional[int] = None,
        status: Optional[str] = None,
        is_waitlist: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Registration]:
        """Get registrations with optional filtering.

        Args:
            event_id: Optional event ID filter.
            status: Optional status filter.
            is_waitlist: Optional waitlist filter.
            limit: Optional limit on number of results.

        Returns:
            List of Registration objects.
        """
        session = self.get_session()
        try:
            query = session.query(Registration)

            if event_id:
                query = query.filter(Registration.event_id == event_id)

            if status:
                query = query.filter(Registration.status == status)

            if is_waitlist is not None:
                query = query.filter(Registration.is_waitlist == is_waitlist)

            query = query.order_by(Registration.registered_at.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def update_registration_status(
        self,
        registration_id: int,
        status: str,
        is_waitlist: Optional[bool] = None,
        waitlist_position: Optional[int] = None,
    ) -> Optional[Registration]:
        """Update registration status.

        Args:
            registration_id: Registration ID.
            status: New status.
            is_waitlist: Optional waitlist flag.
            waitlist_position: Optional waitlist position.

        Returns:
            Updated Registration object or None.
        """
        session = self.get_session()
        try:
            registration = (
                session.query(Registration)
                .filter(Registration.id == registration_id)
                .first()
            )

            if registration:
                registration.status = status
                if is_waitlist is not None:
                    registration.is_waitlist = is_waitlist
                if waitlist_position is not None:
                    registration.waitlist_position = waitlist_position
                if status == "confirmed":
                    registration.confirmed_at = datetime.utcnow()

                session.commit()
                session.refresh(registration)
                return registration

            return None
        finally:
            session.close()

    def update_event_registration_count(self, event_id: int) -> None:
        """Update event registration count.

        Args:
            event_id: Event ID.
        """
        session = self.get_session()
        try:
            event = session.query(Event).filter(Event.id == event_id).first()
            if event:
                confirmed_count = (
                    session.query(Registration)
                    .filter(Registration.event_id == event_id)
                    .filter(Registration.status == "confirmed")
                    .filter(Registration.is_waitlist == False)
                    .count()
                )
                event.current_registrations = confirmed_count
                session.commit()
        finally:
            session.close()

    def get_waitlist_registrations(
        self, event_id: int, limit: Optional[int] = None
    ) -> List[Registration]:
        """Get waitlist registrations for event.

        Args:
            event_id: Event ID.
            limit: Optional limit on number of results.

        Returns:
            List of waitlist Registration objects ordered by position.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Registration)
                .filter(Registration.event_id == event_id)
                .filter(Registration.is_waitlist == True)
                .filter(Registration.status == "pending")
                .order_by(Registration.waitlist_position.asc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def update_waitlist_positions(self, event_id: int) -> None:
        """Update waitlist positions for event.

        Args:
            event_id: Event ID.
        """
        session = self.get_session()
        try:
            waitlist_regs = (
                session.query(Registration)
                .filter(Registration.event_id == event_id)
                .filter(Registration.is_waitlist == True)
                .filter(Registration.status == "pending")
                .order_by(Registration.registered_at.asc())
                .all()
            )

            for position, registration in enumerate(waitlist_regs, start=1):
                registration.waitlist_position = position

            session.commit()
        finally:
            session.close()
