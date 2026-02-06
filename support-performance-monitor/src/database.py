"""Database models and operations for support performance data."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class SupportTicket(Base):
    """Database model for support tickets."""

    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    priority = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False, index=True)
    assigned_agent = Column(String(255), index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    first_response_at = Column(DateTime, index=True)
    resolved_at = Column(DateTime, index=True)
    closed_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    responses = relationship("TicketResponse", back_populates="ticket", cascade="all, delete-orphan")
    metrics = relationship("TicketMetrics", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, ticket_number={self.ticket_number}, status={self.status})>"


class TicketResponse(Base):
    """Database model for ticket responses."""

    __tablename__ = "ticket_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    responder = Column(String(255), nullable=False)
    response_type = Column(String(50), nullable=False)
    response_text = Column(Text)
    response_time_minutes = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    ticket = relationship("SupportTicket", back_populates="responses")

    def __repr__(self) -> str:
        return (
            f"<TicketResponse(id={self.id}, ticket_id={self.ticket_id}, "
            f"responder={self.responder}, response_time_minutes={self.response_time_minutes})>"
        )


class TicketMetrics(Base):
    """Database model for ticket performance metrics."""

    __tablename__ = "ticket_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    first_response_time_minutes = Column(Float)
    resolution_time_hours = Column(Float)
    response_count = Column(Integer, default=0)
    sla_met = Column(Boolean)
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

    ticket = relationship("SupportTicket", back_populates="metrics")

    def __repr__(self) -> str:
        return (
            f"<TicketMetrics(id={self.id}, ticket_id={self.ticket_id}, "
            f"first_response_time_minutes={self.first_response_time_minutes})>"
        )


class PerformanceMetric(Base):
    """Database model for aggregated performance metrics."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(DateTime, nullable=False, index=True)
    category = Column(String(100), index=True)
    agent = Column(String(255), index=True)
    total_tickets = Column(Integer, default=0)
    resolved_tickets = Column(Integer, default=0)
    resolution_rate = Column(Float)
    average_response_time_minutes = Column(Float)
    average_resolution_time_hours = Column(Float)
    sla_compliance_percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric(id={self.id}, metric_date={self.metric_date}, "
            f"resolution_rate={self.resolution_rate})>"
        )


class Bottleneck(Base):
    """Database model for identified bottlenecks."""

    __tablename__ = "bottlenecks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bottleneck_type = Column(String(100), nullable=False, index=True)
    identifier = Column(String(255), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    impact_percentage = Column(Float)
    ticket_count = Column(Integer)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<Bottleneck(id={self.id}, bottleneck_type={self.bottleneck_type}, "
            f"identifier={self.identifier}, severity={self.severity})>"
        )


class DatabaseManager:
    """Manages database operations for support performance data."""

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

    def add_ticket(
        self,
        ticket_number: str,
        title: str,
        category: str,
        priority: str,
        customer_email: str,
        description: Optional[str] = None,
        status: str = "open",
        assigned_agent: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> SupportTicket:
        """Add or update support ticket.

        Args:
            ticket_number: Unique ticket number.
            title: Ticket title.
            category: Ticket category.
            priority: Priority level.
            customer_email: Customer email address.
            description: Optional ticket description.
            status: Ticket status.
            assigned_agent: Optional assigned agent.
            created_at: Optional creation timestamp.

        Returns:
            SupportTicket object.
        """
        session = self.get_session()
        try:
            ticket = (
                session.query(SupportTicket)
                .filter(SupportTicket.ticket_number == ticket_number)
                .first()
            )

            if ticket is None:
                ticket = SupportTicket(
                    ticket_number=ticket_number,
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    status=status,
                    customer_email=customer_email,
                    assigned_agent=assigned_agent,
                    created_at=created_at or datetime.utcnow(),
                )
                session.add(ticket)
            else:
                ticket.title = title
                ticket.description = description
                ticket.category = category
                ticket.priority = priority
                ticket.status = status
                ticket.assigned_agent = assigned_agent
                ticket.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(ticket)
            return ticket
        finally:
            session.close()

    def add_response(
        self,
        ticket_id: int,
        responder: str,
        response_type: str,
        response_text: Optional[str] = None,
        response_time_minutes: Optional[float] = None,
    ) -> TicketResponse:
        """Add ticket response.

        Args:
            ticket_id: Ticket ID.
            responder: Responder name or email.
            response_type: Type of response (agent, customer, system).
            response_text: Optional response text.
            response_time_minutes: Optional response time in minutes.

        Returns:
            TicketResponse object.
        """
        session = self.get_session()
        try:
            response = TicketResponse(
                ticket_id=ticket_id,
                responder=responder,
                response_type=response_type,
                response_text=response_text,
                response_time_minutes=response_time_minutes,
            )
            session.add(response)
            session.commit()
            session.refresh(response)
            return response
        finally:
            session.close()

    def update_ticket_status(
        self,
        ticket_id: int,
        status: str,
        first_response_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
        closed_at: Optional[datetime] = None,
    ) -> Optional[SupportTicket]:
        """Update ticket status and timestamps.

        Args:
            ticket_id: Ticket ID.
            status: New status.
            first_response_at: Optional first response timestamp.
            resolved_at: Optional resolution timestamp.
            closed_at: Optional closure timestamp.

        Returns:
            Updated SupportTicket object or None.
        """
        session = self.get_session()
        try:
            ticket = session.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

            if ticket:
                ticket.status = status
                if first_response_at:
                    ticket.first_response_at = first_response_at
                if resolved_at:
                    ticket.resolved_at = resolved_at
                if closed_at:
                    ticket.closed_at = closed_at
                ticket.updated_at = datetime.utcnow()

                session.commit()
                session.refresh(ticket)
                return ticket

            return None
        finally:
            session.close()

    def get_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        agent: Optional[str] = None,
        limit: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[SupportTicket]:
        """Get tickets with optional filtering.

        Args:
            status: Optional status filter.
            category: Optional category filter.
            priority: Optional priority filter.
            agent: Optional agent filter.
            limit: Optional limit on number of results.
            days: Optional number of days to look back.

        Returns:
            List of SupportTicket objects.
        """
        session = self.get_session()
        try:
            query = session.query(SupportTicket)

            if status:
                query = query.filter(SupportTicket.status == status)

            if category:
                query = query.filter(SupportTicket.category == category)

            if priority:
                query = query.filter(SupportTicket.priority == priority)

            if agent:
                query = query.filter(SupportTicket.assigned_agent == agent)

            if days:
                from datetime import timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(SupportTicket.created_at >= cutoff_date)

            query = query.order_by(SupportTicket.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_metrics(
        self,
        ticket_id: int,
        first_response_time_minutes: Optional[float] = None,
        resolution_time_hours: Optional[float] = None,
        response_count: int = 0,
        sla_met: Optional[bool] = None,
    ) -> TicketMetrics:
        """Add ticket metrics.

        Args:
            ticket_id: Ticket ID.
            first_response_time_minutes: Optional first response time.
            resolution_time_hours: Optional resolution time.
            response_count: Number of responses.
            sla_met: Whether SLA was met.

        Returns:
            TicketMetrics object.
        """
        session = self.get_session()
        try:
            metrics = TicketMetrics(
                ticket_id=ticket_id,
                first_response_time_minutes=first_response_time_minutes,
                resolution_time_hours=resolution_time_hours,
                response_count=response_count,
                sla_met=sla_met,
            )
            session.add(metrics)
            session.commit()
            session.refresh(metrics)
            return metrics
        finally:
            session.close()

    def add_performance_metric(
        self,
        metric_date: datetime,
        total_tickets: int = 0,
        resolved_tickets: int = 0,
        resolution_rate: Optional[float] = None,
        average_response_time_minutes: Optional[float] = None,
        average_resolution_time_hours: Optional[float] = None,
        sla_compliance_percentage: Optional[float] = None,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> PerformanceMetric:
        """Add performance metric.

        Args:
            metric_date: Metric date.
            total_tickets: Total number of tickets.
            resolved_tickets: Number of resolved tickets.
            resolution_rate: Resolution rate.
            average_response_time_minutes: Average response time.
            average_resolution_time_hours: Average resolution time.
            sla_compliance_percentage: SLA compliance percentage.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            PerformanceMetric object.
        """
        session = self.get_session()
        try:
            metric = PerformanceMetric(
                metric_date=metric_date,
                category=category,
                agent=agent,
                total_tickets=total_tickets,
                resolved_tickets=resolved_tickets,
                resolution_rate=resolution_rate,
                average_response_time_minutes=average_response_time_minutes,
                average_resolution_time_hours=average_resolution_time_hours,
                sla_compliance_percentage=sla_compliance_percentage,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def add_bottleneck(
        self,
        bottleneck_type: str,
        identifier: str,
        severity: str,
        description: str,
        impact_percentage: Optional[float] = None,
        ticket_count: Optional[int] = None,
    ) -> Bottleneck:
        """Add bottleneck record.

        Args:
            bottleneck_type: Type of bottleneck (category, agent, time_period).
            identifier: Identifier (category name, agent name, etc.).
            severity: Severity level (low, medium, high, critical).
            description: Bottleneck description.
            impact_percentage: Impact percentage.
            ticket_count: Number of tickets affected.

        Returns:
            Bottleneck object.
        """
        session = self.get_session()
        try:
            bottleneck = Bottleneck(
                bottleneck_type=bottleneck_type,
                identifier=identifier,
                severity=severity,
                description=description,
                impact_percentage=impact_percentage,
                ticket_count=ticket_count,
            )
            session.add(bottleneck)
            session.commit()
            session.refresh(bottleneck)
            return bottleneck
        finally:
            session.close()

    def get_unresolved_bottlenecks(
        self, limit: Optional[int] = None
    ) -> List[Bottleneck]:
        """Get unresolved bottlenecks.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of unresolved Bottleneck objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Bottleneck)
                .filter(Bottleneck.resolved == False)
                .order_by(Bottleneck.detected_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
