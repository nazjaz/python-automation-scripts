"""Database models and operations for complaint processing."""

from datetime import datetime
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


class Customer(Base):
    """Customer information."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(100), unique=True, nullable=False)
    customer_name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="customer", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="customer", cascade="all, delete-orphan")


class Complaint(Base):
    """Customer complaint."""

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(String(100), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    complaint_text = Column(Text, nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    priority = Column(String(20), default="medium")
    status = Column(String(50), default="new")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    assigned_to = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_time_hours = Column(Float, nullable=True)

    customer = relationship("Customer", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    resolution = relationship("Resolution", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    updates = relationship("ComplaintUpdate", back_populates="complaint", cascade="all, delete-orphan")


class Department(Base):
    """Department for handling complaints."""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    department_name = Column(String(200), nullable=False, unique=True)
    department_code = Column(String(50), unique=True)
    description = Column(Text)
    contact_email = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="department")
    routing_rules = relationship("RoutingRule", back_populates="department", cascade="all, delete-orphan")


class RoutingRule(Base):
    """Rule for routing complaints to departments."""

    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    category = Column(String(100))
    keywords = Column(Text)
    priority_threshold = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="routing_rules")


class Resolution(Base):
    """Complaint resolution information."""

    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False)
    resolution_text = Column(Text, nullable=False)
    resolution_type = Column(String(100))
    resolved_by = Column(String(200))
    resolved_at = Column(DateTime, default=datetime.utcnow)
    customer_satisfaction_score = Column(Float, nullable=True)

    complaint = relationship("Complaint", back_populates="resolution")


class ComplaintUpdate(Base):
    """Update on complaint status."""

    __tablename__ = "complaint_updates"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    update_text = Column(Text, nullable=False)
    status = Column(String(50))
    updated_by = Column(String(200))
    updated_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="updates")


class FollowUp(Base):
    """Customer satisfaction follow-up."""

    __tablename__ = "followups"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    followup_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    response_received = Column(String(10), default="false")
    satisfaction_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint")
    customer = relationship("Customer", back_populates="followups")


class ComplaintMetric(Base):
    """Complaint processing metric."""

    __tablename__ = "complaint_metrics"

    id = Column(Integer, primary_key=True)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_complaints = Column(Integer, default=0)
    resolved_complaints = Column(Integer, default=0)
    average_resolution_time_hours = Column(Float)
    average_satisfaction_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


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

    def add_customer(
        self,
        customer_id: str,
        customer_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """Add a new customer.

        Args:
            customer_id: Customer identifier.
            customer_name: Customer name.
            email: Email address.
            phone: Phone number.

        Returns:
            Created Customer object.
        """
        session = self.get_session()
        try:
            customer = Customer(
                customer_id=customer_id,
                customer_name=customer_name,
                email=email,
                phone=phone,
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer
        finally:
            session.close()

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by customer ID.

        Args:
            customer_id: Customer identifier.

        Returns:
            Customer object or None.
        """
        session = self.get_session()
        try:
            return session.query(Customer).filter(Customer.customer_id == customer_id).first()
        finally:
            session.close()

    def add_department(
        self,
        department_name: str,
        department_code: Optional[str] = None,
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> Department:
        """Add a new department.

        Args:
            department_name: Department name.
            department_code: Department code.
            description: Department description.
            contact_email: Contact email.

        Returns:
            Created Department object.
        """
        session = self.get_session()
        try:
            department = Department(
                department_name=department_name,
                department_code=department_code,
                description=description,
                contact_email=contact_email,
            )
            session.add(department)
            session.commit()
            session.refresh(department)
            return department
        finally:
            session.close()

    def get_department(self, department_name: str) -> Optional[Department]:
        """Get department by name.

        Args:
            department_name: Department name.

        Returns:
            Department object or None.
        """
        session = self.get_session()
        try:
            return session.query(Department).filter(Department.department_name == department_name).first()
        finally:
            session.close()

    def get_all_departments(self) -> List[Department]:
        """Get all departments.

        Returns:
            List of Department objects.
        """
        session = self.get_session()
        try:
            return session.query(Department).all()
        finally:
            session.close()

    def add_routing_rule(
        self,
        department_id: int,
        category: Optional[str] = None,
        keywords: Optional[str] = None,
        priority_threshold: Optional[str] = None,
    ) -> RoutingRule:
        """Add routing rule.

        Args:
            department_id: Department ID.
            category: Complaint category.
            keywords: Keywords as comma-separated string.
            priority_threshold: Priority threshold.

        Returns:
            Created RoutingRule object.
        """
        session = self.get_session()
        try:
            rule = RoutingRule(
                department_id=department_id,
                category=category,
                keywords=keywords,
                priority_threshold=priority_threshold,
            )
            session.add(rule)
            session.commit()
            session.refresh(rule)
            return rule
        finally:
            session.close()

    def add_complaint(
        self,
        complaint_id: str,
        customer_id: int,
        complaint_text: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        priority: str = "medium",
    ) -> Complaint:
        """Add a new complaint.

        Args:
            complaint_id: Complaint identifier.
            customer_id: Customer ID.
            complaint_text: Complaint text.
            category: Complaint category.
            subcategory: Complaint subcategory.
            priority: Priority level (low, medium, high, urgent).

        Returns:
            Created Complaint object.
        """
        session = self.get_session()
        try:
            complaint = Complaint(
                complaint_id=complaint_id,
                customer_id=customer_id,
                complaint_text=complaint_text,
                category=category,
                subcategory=subcategory,
                priority=priority,
            )
            session.add(complaint)
            session.commit()
            session.refresh(complaint)
            return complaint
        finally:
            session.close()

    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        """Get complaint by complaint ID.

        Args:
            complaint_id: Complaint identifier.

        Returns:
            Complaint object or None.
        """
        session = self.get_session()
        try:
            return session.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
        finally:
            session.close()

    def update_complaint_status(
        self,
        complaint_id: str,
        status: str,
        department_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
    ) -> None:
        """Update complaint status.

        Args:
            complaint_id: Complaint identifier.
            status: New status.
            department_id: Department ID.
            assigned_to: Assigned to person/team.
        """
        session = self.get_session()
        try:
            complaint = session.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
            if complaint:
                complaint.status = status
                if department_id:
                    complaint.department_id = department_id
                if assigned_to:
                    complaint.assigned_to = assigned_to
                session.commit()
        finally:
            session.close()

    def get_open_complaints(
        self, department_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Complaint]:
        """Get open complaints.

        Args:
            department_id: Optional department ID to filter by.
            limit: Maximum number of complaints to return.

        Returns:
            List of Complaint objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Complaint)
                .filter(Complaint.status.in_(["new", "assigned", "in_progress"]))
                .order_by(Complaint.created_at.desc())
            )
            if department_id:
                query = query.filter(Complaint.department_id == department_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_resolution(
        self,
        complaint_id: int,
        resolution_text: str,
        resolution_type: str,
        resolved_by: str,
    ) -> Resolution:
        """Add resolution for complaint.

        Args:
            complaint_id: Complaint ID.
            resolution_text: Resolution text.
            resolution_type: Resolution type.
            resolved_by: Person who resolved.

        Returns:
            Created Resolution object.
        """
        session = self.get_session()
        try:
            resolution = Resolution(
                complaint_id=complaint_id,
                resolution_text=resolution_text,
                resolution_type=resolution_type,
                resolved_by=resolved_by,
            )
            session.add(resolution)

            complaint = session.query(Complaint).filter(Complaint.id == complaint_id).first()
            if complaint:
                complaint.status = "resolved"
                complaint.resolved_at = datetime.utcnow()
                if complaint.created_at:
                    resolution_time = (datetime.utcnow() - complaint.created_at).total_seconds() / 3600
                    complaint.resolution_time_hours = resolution_time

            session.commit()
            session.refresh(resolution)
            return resolution
        finally:
            session.close()

    def get_resolution(self, complaint_id: int) -> Optional[Resolution]:
        """Get resolution for complaint.

        Args:
            complaint_id: Complaint ID.

        Returns:
            Resolution object or None.
        """
        session = self.get_session()
        try:
            return session.query(Resolution).filter(Resolution.complaint_id == complaint_id).first()
        finally:
            session.close()

    def add_complaint_update(
        self,
        complaint_id: int,
        update_text: str,
        status: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> ComplaintUpdate:
        """Add update to complaint.

        Args:
            complaint_id: Complaint ID.
            update_text: Update text.
            status: Status update.
            updated_by: Person who updated.

        Returns:
            Created ComplaintUpdate object.
        """
        session = self.get_session()
        try:
            update = ComplaintUpdate(
                complaint_id=complaint_id,
                update_text=update_text,
                status=status,
                updated_by=updated_by,
            )
            session.add(update)
            session.commit()
            session.refresh(update)
            return update
        finally:
            session.close()

    def add_followup(
        self,
        complaint_id: int,
        customer_id: int,
        followup_type: str,
        message: str,
    ) -> FollowUp:
        """Add follow-up for complaint.

        Args:
            complaint_id: Complaint ID.
            customer_id: Customer ID.
            followup_type: Follow-up type (satisfaction_survey, feedback_request, etc.).
            message: Follow-up message.

        Returns:
            Created FollowUp object.
        """
        session = self.get_session()
        try:
            followup = FollowUp(
                complaint_id=complaint_id,
                customer_id=customer_id,
                followup_type=followup_type,
                message=message,
            )
            session.add(followup)
            session.commit()
            session.refresh(followup)
            return followup
        finally:
            session.close()

    def get_pending_followups(self, limit: Optional[int] = None) -> List[FollowUp]:
        """Get pending follow-ups.

        Args:
            limit: Maximum number of follow-ups to return.

        Returns:
            List of FollowUp objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(FollowUp)
                .filter(FollowUp.sent_at.is_(None))
                .order_by(FollowUp.created_at.asc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_followup_sent(
        self, followup_id: int, satisfaction_score: Optional[float] = None
    ) -> None:
        """Mark follow-up as sent.

        Args:
            followup_id: Follow-up ID.
            satisfaction_score: Optional satisfaction score.
        """
        session = self.get_session()
        try:
            followup = session.query(FollowUp).filter(FollowUp.id == followup_id).first()
            if followup:
                followup.sent_at = datetime.utcnow()
                if satisfaction_score:
                    followup.satisfaction_score = satisfaction_score
                session.commit()
        finally:
            session.close()

    def add_complaint_metric(
        self,
        time_window_start: datetime,
        time_window_end: datetime,
        total_complaints: int,
        resolved_complaints: int,
        average_resolution_time_hours: Optional[float] = None,
        average_satisfaction_score: Optional[float] = None,
    ) -> ComplaintMetric:
        """Add complaint processing metric.

        Args:
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_complaints: Total number of complaints.
            resolved_complaints: Number of resolved complaints.
            average_resolution_time_hours: Average resolution time in hours.
            average_satisfaction_score: Average satisfaction score.

        Returns:
            Created ComplaintMetric object.
        """
        session = self.get_session()
        try:
            metric = ComplaintMetric(
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_complaints=total_complaints,
                resolved_complaints=resolved_complaints,
                average_resolution_time_hours=average_resolution_time_hours,
                average_satisfaction_score=average_satisfaction_score,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_recent_metrics(self, days: int = 7) -> List[ComplaintMetric]:
        """Get recent complaint metrics.

        Args:
            days: Number of days to look back.

        Returns:
            List of ComplaintMetric objects.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)
            return (
                session.query(ComplaintMetric)
                .filter(ComplaintMetric.time_window_start >= cutoff)
                .order_by(ComplaintMetric.time_window_start.desc())
                .all()
            )
        finally:
            session.close()
