"""Database models and operations for error monitoring."""

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


class ErrorLog(Base):
    """Application error log entry."""

    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True)
    error_message = Column(Text, nullable=False)
    error_type = Column(String(200))
    stack_trace = Column(Text)
    application = Column(String(100))
    environment = Column(String(50))
    severity = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))
    session_id = Column(String(100))
    request_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    category_id = Column(Integer, ForeignKey("error_categories.id"), nullable=True)
    pattern_id = Column(Integer, ForeignKey("error_patterns.id"), nullable=True)
    bug_report_id = Column(Integer, ForeignKey("bug_reports.id"), nullable=True)

    category = relationship("ErrorCategory", back_populates="errors")
    pattern = relationship("ErrorPattern", back_populates="errors")
    bug_report = relationship("BugReport", back_populates="errors")


class ErrorCategory(Base):
    """Error category classification."""

    __tablename__ = "error_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    keywords = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    errors = relationship("ErrorLog", back_populates="category")


class ErrorPattern(Base):
    """Identified error pattern."""

    __tablename__ = "error_patterns"

    id = Column(Integer, primary_key=True)
    pattern_name = Column(String(200), nullable=False)
    pattern_description = Column(Text)
    error_signature = Column(Text, nullable=False)
    frequency = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    trend = Column(String(20))

    errors = relationship("ErrorLog", back_populates="pattern")


class BugReport(Base):
    """Generated bug report."""

    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    reproduction_steps = Column(Text)
    priority = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="open")
    category = Column(String(100))
    error_rate = Column(Float)
    affected_users = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    errors = relationship("ErrorLog", back_populates="bug_report")


class ErrorRate(Base):
    """Error rate metrics over time."""

    __tablename__ = "error_rates"

    id = Column(Integer, primary_key=True)
    application = Column(String(100))
    environment = Column(String(50))
    error_count = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    error_rate = Column(Float)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
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

    def add_error_log(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        application: Optional[str] = None,
        environment: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ErrorLog:
        """Add a new error log entry.

        Args:
            error_message: Error message text.
            error_type: Error type or exception class name.
            stack_trace: Full stack trace.
            application: Application name.
            environment: Environment (production, staging, development).
            severity: Error severity (low, medium, high, critical).
            user_id: User identifier.
            session_id: Session identifier.
            request_id: Request identifier.
            ip_address: Client IP address.
            user_agent: User agent string.

        Returns:
            Created ErrorLog object.
        """
        session = self.get_session()
        try:
            error_log = ErrorLog(
                error_message=error_message,
                error_type=error_type,
                stack_trace=stack_trace,
                application=application,
                environment=environment,
                severity=severity,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(error_log)
            session.commit()
            session.refresh(error_log)
            return error_log
        finally:
            session.close()

    def get_recent_errors(
        self, limit: Optional[int] = None, hours: Optional[int] = None
    ) -> List[ErrorLog]:
        """Get recent error logs.

        Args:
            limit: Maximum number of errors to return.
            hours: Number of hours to look back.

        Returns:
            List of ErrorLog objects.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            query = session.query(ErrorLog).order_by(ErrorLog.timestamp.desc())

            if hours:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(ErrorLog.timestamp >= cutoff)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_error_category(
        self, name: str, description: Optional[str] = None, keywords: Optional[str] = None
    ) -> ErrorCategory:
        """Add or get error category.

        Args:
            name: Category name.
            description: Category description.
            keywords: Category keywords.

        Returns:
            ErrorCategory object.
        """
        session = self.get_session()
        try:
            category = session.query(ErrorCategory).filter(ErrorCategory.name == name).first()
            if not category:
                category = ErrorCategory(name=name, description=description, keywords=keywords)
                session.add(category)
                session.commit()
            session.refresh(category)
            return category
        finally:
            session.close()

    def update_error_category(self, error_id: int, category_id: int) -> None:
        """Update error log category.

        Args:
            error_id: Error log ID.
            category_id: Category ID.
        """
        session = self.get_session()
        try:
            error_log = session.query(ErrorLog).filter(ErrorLog.id == error_id).first()
            if error_log:
                error_log.category_id = category_id
                session.commit()
        finally:
            session.close()

    def add_error_pattern(
        self,
        pattern_name: str,
        error_signature: str,
        pattern_description: Optional[str] = None,
    ) -> ErrorPattern:
        """Add or update error pattern.

        Args:
            pattern_name: Pattern name.
            error_signature: Error signature for matching.
            pattern_description: Pattern description.

        Returns:
            ErrorPattern object.
        """
        session = self.get_session()
        try:
            pattern = (
                session.query(ErrorPattern)
                .filter(ErrorPattern.error_signature == error_signature)
                .first()
            )
            if pattern:
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow()
            else:
                pattern = ErrorPattern(
                    pattern_name=pattern_name,
                    error_signature=error_signature,
                    pattern_description=pattern_description,
                )
                session.add(pattern)
            session.commit()
            session.refresh(pattern)
            return pattern
        finally:
            session.close()

    def update_error_pattern(self, error_id: int, pattern_id: int) -> None:
        """Update error log pattern.

        Args:
            error_id: Error log ID.
            pattern_id: Pattern ID.
        """
        session = self.get_session()
        try:
            error_log = session.query(ErrorLog).filter(ErrorLog.id == error_id).first()
            if error_log:
                error_log.pattern_id = pattern_id
                session.commit()
        finally:
            session.close()

    def create_bug_report(
        self,
        title: str,
        description: str,
        priority: str,
        severity: str,
        reproduction_steps: Optional[str] = None,
        category: Optional[str] = None,
        error_rate: Optional[float] = None,
        affected_users: int = 0,
    ) -> BugReport:
        """Create a new bug report.

        Args:
            title: Bug report title.
            description: Bug report description.
            priority: Priority level (low, medium, high, urgent).
            severity: Severity level (low, medium, high, critical).
            reproduction_steps: Steps to reproduce the bug.
            category: Error category.
            error_rate: Error rate percentage.
            affected_users: Number of affected users.

        Returns:
            Created BugReport object.
        """
        session = self.get_session()
        try:
            bug_report = BugReport(
                title=title,
                description=description,
                priority=priority,
                severity=severity,
                reproduction_steps=reproduction_steps,
                category=category,
                error_rate=error_rate,
                affected_users=affected_users,
            )
            session.add(bug_report)
            session.commit()
            session.refresh(bug_report)
            return bug_report
        finally:
            session.close()

    def link_error_to_bug_report(self, error_id: int, bug_report_id: int) -> None:
        """Link error log to bug report.

        Args:
            error_id: Error log ID.
            bug_report_id: Bug report ID.
        """
        session = self.get_session()
        try:
            error_log = session.query(ErrorLog).filter(ErrorLog.id == error_id).first()
            if error_log:
                error_log.bug_report_id = bug_report_id
                session.commit()
        finally:
            session.close()

    def get_bug_reports(
        self, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BugReport]:
        """Get bug reports.

        Args:
            status: Filter by status (open, in_progress, resolved, closed).
            limit: Maximum number of reports to return.

        Returns:
            List of BugReport objects.
        """
        session = self.get_session()
        try:
            query = session.query(BugReport).order_by(BugReport.created_at.desc())
            if status:
                query = query.filter(BugReport.status == status)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_error_rate(
        self,
        application: str,
        environment: str,
        error_count: int,
        total_requests: int,
        time_window_start: datetime,
        time_window_end: datetime,
    ) -> ErrorRate:
        """Add error rate metric.

        Args:
            application: Application name.
            environment: Environment name.
            error_count: Number of errors.
            total_requests: Total number of requests.
            time_window_start: Start of time window.
            time_window_end: End of time window.

        Returns:
            Created ErrorRate object.
        """
        session = self.get_session()
        try:
            error_rate_value = (error_count / total_requests * 100) if total_requests > 0 else 0.0
            error_rate = ErrorRate(
                application=application,
                environment=environment,
                error_count=error_count,
                total_requests=total_requests,
                error_rate=error_rate_value,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
            )
            session.add(error_rate)
            session.commit()
            session.refresh(error_rate)
            return error_rate
        finally:
            session.close()

    def get_error_rates(
        self,
        application: Optional[str] = None,
        environment: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[ErrorRate]:
        """Get error rate metrics.

        Args:
            application: Filter by application.
            environment: Filter by environment.
            hours: Number of hours to look back.

        Returns:
            List of ErrorRate objects.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            query = session.query(ErrorRate).order_by(ErrorRate.time_window_start.desc())

            if application:
                query = query.filter(ErrorRate.application == application)
            if environment:
                query = query.filter(ErrorRate.environment == environment)
            if hours:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(ErrorRate.time_window_start >= cutoff)

            return query.all()
        finally:
            session.close()
