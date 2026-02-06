"""Database models and operations for accessibility monitoring data."""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Date,
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


class Website(Base):
    """Database model for websites."""

    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(255))
    base_url = Column(String(500), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scans = relationship("AccessibilityScan", back_populates="website", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Website(id={self.id}, url={self.url}, name={self.name})>"


class AccessibilityScan(Base):
    """Database model for accessibility scans."""

    __tablename__ = "accessibility_scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    scan_date = Column(DateTime, nullable=False, index=True)
    page_url = Column(String(500), nullable=False, index=True)
    wcag_version = Column(String(10), default="2.1")
    compliance_level = Column(String(10))
    total_violations = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)
    high_violations = Column(Integer, default=0)
    medium_violations = Column(Integer, default=0)
    low_violations = Column(Integer, default=0)
    compliance_score = Column(Float)
    scan_duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website", back_populates="scans")
    violations = relationship("Violation", back_populates="scan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<AccessibilityScan(id={self.id}, website_id={self.website_id}, "
            f"page_url={self.page_url}, compliance_score={self.compliance_score})>"
        )


class Violation(Base):
    """Database model for WCAG violations."""

    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("accessibility_scans.id"), nullable=False, index=True)
    wcag_criterion = Column(String(50), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    element_type = Column(String(100))
    element_selector = Column(Text)
    violation_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    code_example = Column(Text)
    line_number = Column(Integer)
    column_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("AccessibilityScan", back_populates="violations")
    remediation_tasks = relationship("RemediationTask", back_populates="violation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Violation(id={self.id}, scan_id={self.scan_id}, "
            f"wcag_criterion={self.wcag_criterion}, severity={self.severity})>"
        )


class RemediationTask(Base):
    """Database model for remediation tasks."""

    __tablename__ = "remediation_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False, index=True)
    task_description = Column(Text, nullable=False)
    priority = Column(String(50), default="medium", index=True)
    status = Column(String(50), default="pending", index=True)
    assigned_to = Column(String(255))
    estimated_hours = Column(Float)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    violation = relationship("Violation", back_populates="remediation_tasks")

    def __repr__(self) -> str:
        return (
            f"<RemediationTask(id={self.id}, violation_id={self.violation_id}, "
            f"status={self.status}, priority={self.priority})>"
        )


class ProgressMetric(Base):
    """Database model for progress tracking metrics."""

    __tablename__ = "progress_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)
    compliance_score = Column(Float)
    total_violations = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)
    high_violations = Column(Integer, default=0)
    medium_violations = Column(Integer, default=0)
    low_violations = Column(Integer, default=0)
    pages_scanned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<ProgressMetric(id={self.id}, website_id={self.website_id}, "
            f"metric_date={self.metric_date}, compliance_score={self.compliance_score})>"
        )


class DatabaseManager:
    """Manages database operations for accessibility monitoring data."""

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

    def add_website(
        self,
        url: str,
        name: Optional[str] = None,
    ) -> Website:
        """Add or update website.

        Args:
            url: Website URL.
            name: Optional website name.

        Returns:
            Website object.
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        session = self.get_session()
        try:
            website = (
                session.query(Website)
                .filter(Website.url == url)
                .first()
            )

            if website is None:
                website = Website(
                    url=url,
                    name=name or base_url,
                    base_url=base_url,
                )
                session.add(website)
            else:
                website.name = name or website.name
                website.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(website)
            return website
        finally:
            session.close()

    def add_scan(
        self,
        website_id: int,
        page_url: str,
        wcag_version: str = "2.1",
        compliance_level: Optional[str] = None,
        total_violations: int = 0,
        critical_violations: int = 0,
        high_violations: int = 0,
        medium_violations: int = 0,
        low_violations: int = 0,
        compliance_score: Optional[float] = None,
        scan_duration_seconds: Optional[float] = None,
    ) -> AccessibilityScan:
        """Add accessibility scan.

        Args:
            website_id: Website ID.
            page_url: Page URL scanned.
            wcag_version: WCAG version.
            compliance_level: Compliance level (A, AA, AAA).
            total_violations: Total number of violations.
            critical_violations: Number of critical violations.
            high_violations: Number of high severity violations.
            medium_violations: Number of medium severity violations.
            low_violations: Number of low severity violations.
            compliance_score: Compliance score (0.0 to 1.0).
            scan_duration_seconds: Scan duration in seconds.

        Returns:
            AccessibilityScan object.
        """
        session = self.get_session()
        try:
            scan = AccessibilityScan(
                website_id=website_id,
                scan_date=datetime.utcnow(),
                page_url=page_url,
                wcag_version=wcag_version,
                compliance_level=compliance_level,
                total_violations=total_violations,
                critical_violations=critical_violations,
                high_violations=high_violations,
                medium_violations=medium_violations,
                low_violations=low_violations,
                compliance_score=compliance_score,
                scan_duration_seconds=scan_duration_seconds,
            )
            session.add(scan)
            session.commit()
            session.refresh(scan)
            return scan
        finally:
            session.close()

    def add_violation(
        self,
        scan_id: int,
        wcag_criterion: str,
        severity: str,
        violation_type: str,
        description: str,
        element_type: Optional[str] = None,
        element_selector: Optional[str] = None,
        recommendation: Optional[str] = None,
        code_example: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
    ) -> Violation:
        """Add violation.

        Args:
            scan_id: Scan ID.
            wcag_criterion: WCAG criterion code.
            severity: Violation severity.
            violation_type: Type of violation.
            description: Violation description.
            element_type: Optional element type.
            element_selector: Optional CSS selector.
            recommendation: Optional remediation recommendation.
            code_example: Optional code example.
            line_number: Optional line number.
            column_number: Optional column number.

        Returns:
            Violation object.
        """
        session = self.get_session()
        try:
            violation = Violation(
                scan_id=scan_id,
                wcag_criterion=wcag_criterion,
                severity=severity,
                violation_type=violation_type,
                description=description,
                element_type=element_type,
                element_selector=element_selector,
                recommendation=recommendation,
                code_example=code_example,
                line_number=line_number,
                column_number=column_number,
            )
            session.add(violation)
            session.commit()
            session.refresh(violation)
            return violation
        finally:
            session.close()

    def add_remediation_task(
        self,
        violation_id: int,
        task_description: str,
        priority: str = "medium",
        assigned_to: Optional[str] = None,
        estimated_hours: Optional[float] = None,
    ) -> RemediationTask:
        """Add remediation task.

        Args:
            violation_id: Violation ID.
            task_description: Task description.
            priority: Task priority.
            assigned_to: Optional assignee.
            estimated_hours: Optional estimated hours.

        Returns:
            RemediationTask object.
        """
        session = self.get_session()
        try:
            task = RemediationTask(
                violation_id=violation_id,
                task_description=task_description,
                priority=priority,
                assigned_to=assigned_to,
                estimated_hours=estimated_hours,
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()

    def get_scans(
        self,
        website_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[AccessibilityScan]:
        """Get scans with optional filtering.

        Args:
            website_id: Optional website ID filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            limit: Optional limit on number of results.

        Returns:
            List of AccessibilityScan objects.
        """
        session = self.get_session()
        try:
            query = session.query(AccessibilityScan)

            if website_id:
                query = query.filter(AccessibilityScan.website_id == website_id)

            if start_date:
                query = query.filter(AccessibilityScan.scan_date >= start_date)

            if end_date:
                query = query.filter(AccessibilityScan.scan_date <= end_date)

            query = query.order_by(AccessibilityScan.scan_date.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_violations(
        self,
        scan_id: Optional[int] = None,
        severity: Optional[str] = None,
        wcag_criterion: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Violation]:
        """Get violations with optional filtering.

        Args:
            scan_id: Optional scan ID filter.
            severity: Optional severity filter.
            wcag_criterion: Optional WCAG criterion filter.
            limit: Optional limit on number of results.

        Returns:
            List of Violation objects.
        """
        session = self.get_session()
        try:
            query = session.query(Violation)

            if scan_id:
                query = query.filter(Violation.scan_id == scan_id)

            if severity:
                query = query.filter(Violation.severity == severity)

            if wcag_criterion:
                query = query.filter(Violation.wcag_criterion == wcag_criterion)

            query = query.order_by(Violation.severity.desc(), Violation.wcag_criterion.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_progress_metric(
        self,
        website_id: int,
        metric_date: date,
        compliance_score: Optional[float] = None,
        total_violations: int = 0,
        critical_violations: int = 0,
        high_violations: int = 0,
        medium_violations: int = 0,
        low_violations: int = 0,
        pages_scanned: int = 0,
    ) -> ProgressMetric:
        """Add progress metric.

        Args:
            website_id: Website ID.
            metric_date: Metric date.
            compliance_score: Optional compliance score.
            total_violations: Total violations.
            critical_violations: Critical violations.
            high_violations: High severity violations.
            medium_violations: Medium severity violations.
            low_violations: Low severity violations.
            pages_scanned: Number of pages scanned.

        Returns:
            ProgressMetric object.
        """
        session = self.get_session()
        try:
            metric = ProgressMetric(
                website_id=website_id,
                metric_date=metric_date,
                compliance_score=compliance_score,
                total_violations=total_violations,
                critical_violations=critical_violations,
                high_violations=high_violations,
                medium_violations=medium_violations,
                low_violations=low_violations,
                pages_scanned=pages_scanned,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
