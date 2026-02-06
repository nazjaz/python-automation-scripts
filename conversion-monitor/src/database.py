"""Database models and operations for conversion monitoring."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Website(Base):
    """Website being monitored."""

    __tablename__ = "websites"

    id = Column(Integer, primary_key=True)
    domain = Column(String(200), nullable=False, unique=True)
    website_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="website")
    conversion_goals = relationship("ConversionGoal", back_populates="website")


class Session(Base):
    """User session on website."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(100))
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float)
    page_views = Column(Integer, default=0)
    converted = Column(String(10), default="false")
    conversion_goal_id = Column(Integer, ForeignKey("conversion_goals.id"), nullable=True)

    website = relationship("Website", back_populates="sessions")
    events = relationship("Event", back_populates="session", cascade="all, delete-orphan")
    conversion_goal = relationship("ConversionGoal")


class Event(Base):
    """User event in session."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_name = Column(String(200))
    page_url = Column(String(500))
    page_title = Column(String(500))
    timestamp = Column(DateTime, nullable=False)
    metadata = Column(Text)

    session = relationship("Session", back_populates="events")


class ConversionGoal(Base):
    """Conversion goal definition."""

    __tablename__ = "conversion_goals"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    goal_name = Column(String(200), nullable=False)
    goal_type = Column(String(100))
    target_url = Column(String(500))
    target_event = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website", back_populates="conversion_goals")
    sessions = relationship("Session", back_populates="conversion_goal")


class ConversionRate(Base):
    """Conversion rate metric over time."""

    __tablename__ = "conversion_rates"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    conversion_goal_id = Column(Integer, ForeignKey("conversion_goals.id"), nullable=True)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_sessions = Column(Integer, default=0)
    converted_sessions = Column(Integer, default=0)
    conversion_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website")
    conversion_goal = relationship("ConversionGoal")


class JourneyStep(Base):
    """Step in user journey."""

    __tablename__ = "journey_steps"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    step_name = Column(String(200), nullable=False)
    step_order = Column(Integer, nullable=False)
    page_url = Column(String(500))
    event_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website")


class DropOffPoint(Base):
    """Identified drop-off point in user journey."""

    __tablename__ = "dropoff_points"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    journey_step_id = Column(Integer, ForeignKey("journey_steps.id"), nullable=True)
    dropoff_rate = Column(Float, nullable=False)
    sessions_entered = Column(Integer, default=0)
    sessions_exited = Column(Integer, default=0)
    identified_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website")
    journey_step = relationship("JourneyStep")


class Recommendation(Base):
    """Optimization recommendation."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    dropoff_point_id = Column(Integer, ForeignKey("dropoff_points.id"), nullable=True)
    recommendation_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    expected_impact = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website")
    dropoff_point = relationship("DropOffPoint")


class DatabaseManager:
    """Database operations manager."""

    def __init__(self, database_url: str):
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get database session.

        Returns:
            Database session object.
        """
        return self.SessionLocal()

    def add_website(
        self, domain: str, website_name: Optional[str] = None
    ) -> Website:
        """Add a new website.

        Args:
            domain: Website domain.
            website_name: Website name.

        Returns:
            Created Website object.
        """
        session = self.get_session()
        try:
            website = Website(domain=domain, website_name=website_name or domain)
            session.add(website)
            session.commit()
            session.refresh(website)
            return website
        finally:
            session.close()

    def get_website(self, website_id: int) -> Optional[Website]:
        """Get website by ID.

        Args:
            website_id: Website ID.

        Returns:
            Website object or None.
        """
        session = self.get_session()
        try:
            return session.query(Website).filter(Website.id == website_id).first()
        finally:
            session.close()

    def get_website_by_domain(self, domain: str) -> Optional[Website]:
        """Get website by domain.

        Args:
            domain: Website domain.

        Returns:
            Website object or None.
        """
        session = self.get_session()
        try:
            return session.query(Website).filter(Website.domain == domain).first()
        finally:
            session.close()

    def add_conversion_goal(
        self,
        website_id: int,
        goal_name: str,
        goal_type: str,
        target_url: Optional[str] = None,
        target_event: Optional[str] = None,
    ) -> ConversionGoal:
        """Add conversion goal.

        Args:
            website_id: Website ID.
            goal_name: Goal name.
            goal_type: Goal type (purchase, signup, download, etc.).
            target_url: Target URL for conversion.
            target_event: Target event name for conversion.

        Returns:
            Created ConversionGoal object.
        """
        session = self.get_session()
        try:
            goal = ConversionGoal(
                website_id=website_id,
                goal_name=goal_name,
                goal_type=goal_type,
                target_url=target_url,
                target_event=target_event,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal
        finally:
            session.close()

    def get_website_goals(self, website_id: int) -> List[ConversionGoal]:
        """Get all conversion goals for website.

        Args:
            website_id: Website ID.

        Returns:
            List of ConversionGoal objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(ConversionGoal)
                .filter(ConversionGoal.website_id == website_id)
                .all()
            )
        finally:
            session.close()

    def add_session(
        self,
        website_id: int,
        session_id: str,
        started_at: datetime,
        user_id: Optional[str] = None,
        ended_at: Optional[datetime] = None,
    ) -> Session:
        """Add a session.

        Args:
            website_id: Website ID.
            session_id: Session identifier.
            started_at: Session start time.
            user_id: User identifier.
            ended_at: Session end time.

        Returns:
            Created Session object.
        """
        session = self.get_session()
        try:
            duration_seconds = None
            if ended_at and started_at:
                duration_seconds = (ended_at - started_at).total_seconds()

            db_session = Session(
                website_id=website_id,
                session_id=session_id,
                user_id=user_id,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=duration_seconds,
            )
            session.add(db_session)
            session.commit()
            session.refresh(db_session)
            return db_session
        finally:
            session.close()

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by session ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session object or None.
        """
        session = self.get_session()
        try:
            return session.query(Session).filter(Session.session_id == session_id).first()
        finally:
            session.close()

    def update_session(
        self,
        session_id: str,
        ended_at: Optional[datetime] = None,
        converted: Optional[str] = None,
        conversion_goal_id: Optional[int] = None,
        page_views: Optional[int] = None,
    ) -> None:
        """Update session.

        Args:
            session_id: Session identifier.
            ended_at: Session end time.
            converted: Whether session converted (true/false).
            conversion_goal_id: Conversion goal ID.
            page_views: Number of page views.
        """
        session = self.get_session()
        try:
            db_session = session.query(Session).filter(Session.session_id == session_id).first()
            if db_session:
                if ended_at:
                    db_session.ended_at = ended_at
                    if db_session.started_at:
                        db_session.duration_seconds = (
                            ended_at - db_session.started_at
                        ).total_seconds()
                if converted:
                    db_session.converted = converted
                if conversion_goal_id:
                    db_session.conversion_goal_id = conversion_goal_id
                if page_views is not None:
                    db_session.page_views = page_views
                session.commit()
        finally:
            session.close()

    def add_event(
        self,
        session_id: int,
        event_type: str,
        timestamp: datetime,
        event_name: Optional[str] = None,
        page_url: Optional[str] = None,
        page_title: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> Event:
        """Add event to session.

        Args:
            session_id: Session ID.
            event_type: Event type (pageview, click, form_submit, etc.).
            timestamp: Event timestamp.
            event_name: Event name.
            page_url: Page URL.
            page_title: Page title.
            metadata: Additional metadata as JSON string.

        Returns:
            Created Event object.
        """
        session = self.get_session()
        try:
            event = Event(
                session_id=session_id,
                event_type=event_type,
                event_name=event_name,
                page_url=page_url,
                page_title=page_title,
                timestamp=timestamp,
                metadata=metadata,
            )
            session.add(event)

            db_session = session.query(Session).filter(Session.id == session_id).first()
            if db_session:
                db_session.page_views = (
                    session.query(Event)
                    .filter(Event.session_id == session_id)
                    .count()
                    + 1
                )

            session.commit()
            session.refresh(event)
            return event
        finally:
            session.close()

    def get_session_events(
        self, session_id: int, limit: Optional[int] = None
    ) -> List[Event]:
        """Get events for a session.

        Args:
            session_id: Session ID.
            limit: Maximum number of events to return.

        Returns:
            List of Event objects ordered by timestamp.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Event)
                .filter(Event.session_id == session_id)
                .order_by(Event.timestamp.asc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_recent_sessions(
        self,
        website_id: Optional[int] = None,
        hours: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        """Get recent sessions.

        Args:
            website_id: Optional website ID to filter by.
            hours: Optional number of hours to look back.
            limit: Maximum number of sessions to return.

        Returns:
            List of Session objects.
        """
        session = self.get_session()
        try:
            query = session.query(Session).order_by(Session.started_at.desc())

            if website_id:
                query = query.filter(Session.website_id == website_id)

            if hours:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(Session.started_at >= cutoff)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_conversion_rate(
        self,
        website_id: int,
        time_window_start: datetime,
        time_window_end: datetime,
        total_sessions: int,
        converted_sessions: int,
        conversion_goal_id: Optional[int] = None,
    ) -> ConversionRate:
        """Add conversion rate metric.

        Args:
            website_id: Website ID.
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_sessions: Total number of sessions.
            converted_sessions: Number of converted sessions.
            conversion_goal_id: Optional conversion goal ID.

        Returns:
            Created ConversionRate object.
        """
        session = self.get_session()
        try:
            conversion_rate_value = (
                converted_sessions / total_sessions * 100 if total_sessions > 0 else 0.0
            )

            conversion_rate = ConversionRate(
                website_id=website_id,
                conversion_goal_id=conversion_goal_id,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_sessions=total_sessions,
                converted_sessions=converted_sessions,
                conversion_rate=conversion_rate_value,
            )
            session.add(conversion_rate)
            session.commit()
            session.refresh(conversion_rate)
            return conversion_rate
        finally:
            session.close()

    def get_conversion_rates(
        self,
        website_id: Optional[int] = None,
        conversion_goal_id: Optional[int] = None,
        hours: Optional[int] = None,
    ) -> List[ConversionRate]:
        """Get conversion rate metrics.

        Args:
            website_id: Optional website ID to filter by.
            conversion_goal_id: Optional conversion goal ID to filter by.
            hours: Optional number of hours to look back.

        Returns:
            List of ConversionRate objects.
        """
        session = self.get_session()
        try:
            query = session.query(ConversionRate).order_by(
                ConversionRate.time_window_start.desc()
            )

            if website_id:
                query = query.filter(ConversionRate.website_id == website_id)
            if conversion_goal_id:
                query = query.filter(
                    ConversionRate.conversion_goal_id == conversion_goal_id
                )
            if hours:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(ConversionRate.time_window_start >= cutoff)

            return query.all()
        finally:
            session.close()

    def add_journey_step(
        self,
        website_id: int,
        step_name: str,
        step_order: int,
        page_url: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> JourneyStep:
        """Add journey step.

        Args:
            website_id: Website ID.
            step_name: Step name.
            step_order: Step order in journey.
            page_url: Page URL for step.
            event_type: Event type for step.

        Returns:
            Created JourneyStep object.
        """
        session = self.get_session()
        try:
            step = JourneyStep(
                website_id=website_id,
                step_name=step_name,
                step_order=step_order,
                page_url=page_url,
                event_type=event_type,
            )
            session.add(step)
            session.commit()
            session.refresh(step)
            return step
        finally:
            session.close()

    def get_journey_steps(self, website_id: int) -> List[JourneyStep]:
        """Get journey steps for website.

        Args:
            website_id: Website ID.

        Returns:
            List of JourneyStep objects ordered by step_order.
        """
        session = self.get_session()
        try:
            return (
                session.query(JourneyStep)
                .filter(JourneyStep.website_id == website_id)
                .order_by(JourneyStep.step_order)
                .all()
            )
        finally:
            session.close()

    def add_dropoff_point(
        self,
        website_id: int,
        dropoff_rate: float,
        sessions_entered: int,
        sessions_exited: int,
        journey_step_id: Optional[int] = None,
    ) -> DropOffPoint:
        """Add drop-off point.

        Args:
            website_id: Website ID.
            dropoff_rate: Drop-off rate (0.0 to 1.0).
            sessions_entered: Number of sessions that entered this point.
            sessions_exited: Number of sessions that exited at this point.
            journey_step_id: Optional journey step ID.

        Returns:
            Created DropOffPoint object.
        """
        session = self.get_session()
        try:
            dropoff = DropOffPoint(
                website_id=website_id,
                journey_step_id=journey_step_id,
                dropoff_rate=dropoff_rate,
                sessions_entered=sessions_entered,
                sessions_exited=sessions_exited,
            )
            session.add(dropoff)
            session.commit()
            session.refresh(dropoff)
            return dropoff
        finally:
            session.close()

    def get_dropoff_points(
        self, website_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[DropOffPoint]:
        """Get drop-off points.

        Args:
            website_id: Optional website ID to filter by.
            limit: Maximum number of points to return.

        Returns:
            List of DropOffPoint objects ordered by dropoff_rate descending.
        """
        session = self.get_session()
        try:
            query = session.query(DropOffPoint).order_by(DropOffPoint.dropoff_rate.desc())
            if website_id:
                query = query.filter(DropOffPoint.website_id == website_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_recommendation(
        self,
        website_id: int,
        recommendation_type: str,
        title: str,
        description: str,
        priority: str,
        expected_impact: Optional[float] = None,
        dropoff_point_id: Optional[int] = None,
    ) -> Recommendation:
        """Add optimization recommendation.

        Args:
            website_id: Website ID.
            recommendation_type: Recommendation type.
            title: Recommendation title.
            description: Recommendation description.
            priority: Priority level (low, medium, high, urgent).
            expected_impact: Expected impact score (0.0 to 1.0).
            dropoff_point_id: Optional drop-off point ID.

        Returns:
            Created Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                website_id=website_id,
                dropoff_point_id=dropoff_point_id,
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                priority=priority,
                expected_impact=expected_impact,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_recommendations(
        self, website_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Recommendation]:
        """Get recommendations.

        Args:
            website_id: Optional website ID to filter by.
            limit: Maximum number of recommendations to return.

        Returns:
            List of Recommendation objects ordered by expected_impact descending.
        """
        session = self.get_session()
        try:
            query = session.query(Recommendation).order_by(
                Recommendation.expected_impact.desc()
            )
            if website_id:
                query = query.filter(Recommendation.website_id == website_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
