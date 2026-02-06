"""Database models and operations for security monitoring."""

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


class Application(Base):
    """Application being monitored."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    application_id = Column(String(100), unique=True, nullable=False)
    application_name = Column(String(200), nullable=False)
    version = Column(String(50))
    environment = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("SecurityScan", back_populates="application", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="application", cascade="all, delete-orphan")


class SecurityScan(Base):
    """Security scan result."""

    __tablename__ = "security_scans"

    id = Column(Integer, primary_key=True)
    scan_id = Column(String(100), unique=True, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    scan_type = Column(String(100), nullable=False)
    scan_tool = Column(String(100))
    status = Column(String(50), default="running")
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    vulnerabilities_found = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    scan_results = Column(Text)

    application = relationship("Application", back_populates="scans")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")


class Vulnerability(Base):
    """Security vulnerability."""

    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True)
    vulnerability_id = Column(String(100), unique=True, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    scan_id = Column(Integer, ForeignKey("security_scans.id"), nullable=True)
    cve_id = Column(String(50))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False)
    cvss_score = Column(Float)
    status = Column(String(50), default="open")
    discovered_at = Column(DateTime, default=datetime.utcnow)
    fixed_at = Column(DateTime, nullable=True)
    component = Column(String(200))
    affected_version = Column(String(50))

    application = relationship("Application", back_populates="vulnerabilities")
    scan = relationship("SecurityScan", back_populates="vulnerabilities")
    fixes = relationship("Fix", back_populates="vulnerability", cascade="all, delete-orphan")
    remediation_timeline = relationship("RemediationTimeline", back_populates="vulnerability", uselist=False, cascade="all, delete-orphan")


class Fix(Base):
    """Fix for vulnerability."""

    __tablename__ = "fixes"

    id = Column(Integer, primary_key=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=False)
    fix_type = Column(String(100), nullable=False)
    fix_description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    estimated_effort_hours = Column(Float)
    assigned_to = Column(String(200))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    vulnerability = relationship("Vulnerability", back_populates="fixes")


class RemediationTimeline(Base):
    """Remediation timeline for vulnerability."""

    __tablename__ = "remediation_timelines"

    id = Column(Integer, primary_key=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), unique=True, nullable=False)
    target_fix_date = Column(DateTime, nullable=False)
    estimated_completion_date = Column(DateTime, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)
    remediation_steps = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vulnerability = relationship("Vulnerability", back_populates="remediation_timeline")


class ComplianceReport(Base):
    """Security compliance report."""

    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True)
    report_id = Column(String(100), unique=True, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    report_type = Column(String(100), nullable=False)
    compliance_status = Column(String(50), nullable=False)
    compliance_score = Column(Float)
    total_vulnerabilities = Column(Integer, default=0)
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    medium_vulnerabilities = Column(Integer, default=0)
    low_vulnerabilities = Column(Integer, default=0)
    report_data = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application")


class SecurityMetric(Base):
    """Security performance metric."""

    __tablename__ = "security_metrics"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_vulnerabilities = Column(Integer, default=0)
    fixed_vulnerabilities = Column(Integer, default=0)
    average_fix_time_hours = Column(Float)
    compliance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application")


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

    def add_application(
        self,
        application_id: str,
        application_name: str,
        version: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Application:
        """Add a new application.

        Args:
            application_id: Application identifier.
            application_name: Application name.
            version: Application version.
            environment: Environment (production, staging, development).

        Returns:
            Created Application object.
        """
        session = self.get_session()
        try:
            application = Application(
                application_id=application_id,
                application_name=application_name,
                version=version,
                environment=environment,
            )
            session.add(application)
            session.commit()
            session.refresh(application)
            return application
        finally:
            session.close()

    def get_application(self, application_id: str) -> Optional[Application]:
        """Get application by application ID.

        Args:
            application_id: Application identifier.

        Returns:
            Application object or None.
        """
        session = self.get_session()
        try:
            return session.query(Application).filter(Application.application_id == application_id).first()
        finally:
            session.close()

    def add_security_scan(
        self,
        scan_id: str,
        application_id: int,
        scan_type: str,
        started_at: datetime,
        scan_tool: Optional[str] = None,
        status: str = "running",
    ) -> SecurityScan:
        """Add security scan.

        Args:
            scan_id: Scan identifier.
            application_id: Application ID.
            scan_type: Scan type (static, dynamic, dependency, etc.).
            started_at: Scan start time.
            scan_tool: Scan tool name.
            status: Scan status.

        Returns:
            Created SecurityScan object.
        """
        session = self.get_session()
        try:
            scan = SecurityScan(
                scan_id=scan_id,
                application_id=application_id,
                scan_type=scan_type,
                scan_tool=scan_tool,
                started_at=started_at,
                status=status,
            )
            session.add(scan)
            session.commit()
            session.refresh(scan)
            return scan
        finally:
            session.close()

    def get_security_scan(self, scan_id: str) -> Optional[SecurityScan]:
        """Get security scan by scan ID.

        Args:
            scan_id: Scan identifier.

        Returns:
            SecurityScan object or None.
        """
        session = self.get_session()
        try:
            return session.query(SecurityScan).filter(SecurityScan.scan_id == scan_id).first()
        finally:
            session.close()

    def update_scan_results(
        self,
        scan_id: str,
        completed_at: datetime,
        vulnerabilities_found: int,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0,
        scan_results: Optional[str] = None,
    ) -> None:
        """Update scan results.

        Args:
            scan_id: Scan identifier.
            completed_at: Scan completion time.
            vulnerabilities_found: Number of vulnerabilities found.
            critical_count: Number of critical vulnerabilities.
            high_count: Number of high severity vulnerabilities.
            medium_count: Number of medium severity vulnerabilities.
            low_count: Number of low severity vulnerabilities.
            scan_results: Scan results as JSON string.
        """
        session = self.get_session()
        try:
            scan = session.query(SecurityScan).filter(SecurityScan.scan_id == scan_id).first()
            if scan:
                scan.completed_at = completed_at
                scan.status = "completed"
                scan.vulnerabilities_found = vulnerabilities_found
                scan.critical_count = critical_count
                scan.high_count = high_count
                scan.medium_count = medium_count
                scan.low_count = low_count
                if scan_results:
                    scan.scan_results = scan_results
                session.commit()
        finally:
            session.close()

    def get_recent_scans(
        self, application_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[SecurityScan]:
        """Get recent security scans.

        Args:
            application_id: Optional application ID to filter by.
            limit: Maximum number of scans to return.

        Returns:
            List of SecurityScan objects.
        """
        session = self.get_session()
        try:
            query = session.query(SecurityScan).order_by(SecurityScan.started_at.desc())
            if application_id:
                query = query.filter(SecurityScan.application_id == application_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_vulnerability(
        self,
        vulnerability_id: str,
        application_id: int,
        title: str,
        severity: str,
        scan_id: Optional[int] = None,
        cve_id: Optional[str] = None,
        description: Optional[str] = None,
        cvss_score: Optional[float] = None,
        component: Optional[str] = None,
        affected_version: Optional[str] = None,
    ) -> Vulnerability:
        """Add vulnerability.

        Args:
            vulnerability_id: Vulnerability identifier.
            application_id: Application ID.
            title: Vulnerability title.
            severity: Severity level (critical, high, medium, low).
            scan_id: Optional scan ID.
            cve_id: Optional CVE identifier.
            description: Vulnerability description.
            cvss_score: CVSS score.
            component: Affected component.
            affected_version: Affected version.

        Returns:
            Created Vulnerability object.
        """
        session = self.get_session()
        try:
            vulnerability = Vulnerability(
                vulnerability_id=vulnerability_id,
                application_id=application_id,
                scan_id=scan_id,
                cve_id=cve_id,
                title=title,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                component=component,
                affected_version=affected_version,
            )
            session.add(vulnerability)
            session.commit()
            session.refresh(vulnerability)
            return vulnerability
        finally:
            session.close()

    def get_vulnerability(self, vulnerability_id: str) -> Optional[Vulnerability]:
        """Get vulnerability by vulnerability ID.

        Args:
            vulnerability_id: Vulnerability identifier.

        Returns:
            Vulnerability object or None.
        """
        session = self.get_session()
        try:
            return session.query(Vulnerability).filter(Vulnerability.vulnerability_id == vulnerability_id).first()
        finally:
            session.close()

    def get_open_vulnerabilities(
        self, application_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Vulnerability]:
        """Get open vulnerabilities.

        Args:
            application_id: Optional application ID to filter by.
            limit: Maximum number of vulnerabilities to return.

        Returns:
            List of Vulnerability objects ordered by severity.
        """
        session = self.get_session()
        try:
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            query = (
                session.query(Vulnerability)
                .filter(Vulnerability.status == "open")
                .order_by(Vulnerability.cvss_score.desc().nullslast())
            )
            if application_id:
                query = query.filter(Vulnerability.application_id == application_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_vulnerability_status(
        self, vulnerability_id: str, status: str, fixed_at: Optional[datetime] = None
    ) -> None:
        """Update vulnerability status.

        Args:
            vulnerability_id: Vulnerability identifier.
            status: New status (open, in_progress, fixed, false_positive).
            fixed_at: Fix datetime.
        """
        session = self.get_session()
        try:
            vulnerability = (
                session.query(Vulnerability)
                .filter(Vulnerability.vulnerability_id == vulnerability_id)
                .first()
            )
            if vulnerability:
                vulnerability.status = status
                if fixed_at:
                    vulnerability.fixed_at = fixed_at
                session.commit()
        finally:
            session.close()

    def add_fix(
        self,
        vulnerability_id: int,
        fix_type: str,
        fix_description: str,
        priority: str,
        estimated_effort_hours: Optional[float] = None,
        assigned_to: Optional[str] = None,
    ) -> Fix:
        """Add fix for vulnerability.

        Args:
            vulnerability_id: Vulnerability ID.
            fix_type: Fix type (patch, update, configuration, etc.).
            fix_description: Fix description.
            priority: Priority level (low, medium, high, urgent).
            estimated_effort_hours: Estimated effort in hours.
            assigned_to: Assigned to person/team.

        Returns:
            Created Fix object.
        """
        session = self.get_session()
        try:
            fix = Fix(
                vulnerability_id=vulnerability_id,
                fix_type=fix_type,
                fix_description=fix_description,
                priority=priority,
                estimated_effort_hours=estimated_effort_hours,
                assigned_to=assigned_to,
            )
            session.add(fix)
            session.commit()
            session.refresh(fix)
            return fix
        finally:
            session.close()

    def get_vulnerability_fixes(self, vulnerability_id: int) -> List[Fix]:
        """Get fixes for vulnerability.

        Args:
            vulnerability_id: Vulnerability ID.

        Returns:
            List of Fix objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Fix)
                .filter(Fix.vulnerability_id == vulnerability_id)
                .order_by(Fix.created_at.desc())
                .all()
            )
        finally:
            session.close()

    def add_remediation_timeline(
        self,
        vulnerability_id: int,
        target_fix_date: datetime,
        remediation_steps: Optional[str] = None,
        estimated_completion_date: Optional[datetime] = None,
    ) -> RemediationTimeline:
        """Add or update remediation timeline.

        Args:
            vulnerability_id: Vulnerability ID.
            target_fix_date: Target fix date.
            remediation_steps: Remediation steps as JSON string.
            estimated_completion_date: Estimated completion date.

        Returns:
            Created or updated RemediationTimeline object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(RemediationTimeline)
                .filter(RemediationTimeline.vulnerability_id == vulnerability_id)
                .first()
            )

            if existing:
                existing.target_fix_date = target_fix_date
                existing.estimated_completion_date = estimated_completion_date
                if remediation_steps:
                    existing.remediation_steps = remediation_steps
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                timeline = RemediationTimeline(
                    vulnerability_id=vulnerability_id,
                    target_fix_date=target_fix_date,
                    estimated_completion_date=estimated_completion_date,
                    remediation_steps=remediation_steps,
                )
                session.add(timeline)
                session.commit()
                session.refresh(timeline)
                return timeline
        finally:
            session.close()

    def get_remediation_timeline(
        self, vulnerability_id: int
    ) -> Optional[RemediationTimeline]:
        """Get remediation timeline for vulnerability.

        Args:
            vulnerability_id: Vulnerability ID.

        Returns:
            RemediationTimeline object or None.
        """
        session = self.get_session()
        try:
            return (
                session.query(RemediationTimeline)
                .filter(RemediationTimeline.vulnerability_id == vulnerability_id)
                .first()
            )
        finally:
            session.close()

    def add_compliance_report(
        self,
        report_id: str,
        application_id: int,
        report_type: str,
        compliance_status: str,
        total_vulnerabilities: int,
        critical_vulnerabilities: int = 0,
        high_vulnerabilities: int = 0,
        medium_vulnerabilities: int = 0,
        low_vulnerabilities: int = 0,
        compliance_score: Optional[float] = None,
        report_data: Optional[str] = None,
    ) -> ComplianceReport:
        """Add compliance report.

        Args:
            report_id: Report identifier.
            application_id: Application ID.
            report_type: Report type (security, compliance, audit).
            compliance_status: Compliance status (compliant, non_compliant, at_risk).
            total_vulnerabilities: Total number of vulnerabilities.
            critical_vulnerabilities: Number of critical vulnerabilities.
            high_vulnerabilities: Number of high severity vulnerabilities.
            medium_vulnerabilities: Number of medium severity vulnerabilities.
            low_vulnerabilities: Number of low severity vulnerabilities.
            compliance_score: Compliance score (0.0 to 100.0).
            report_data: Report data as JSON string.

        Returns:
            Created ComplianceReport object.
        """
        session = self.get_session()
        try:
            report = ComplianceReport(
                report_id=report_id,
                application_id=application_id,
                report_type=report_type,
                compliance_status=compliance_status,
                total_vulnerabilities=total_vulnerabilities,
                critical_vulnerabilities=critical_vulnerabilities,
                high_vulnerabilities=high_vulnerabilities,
                medium_vulnerabilities=medium_vulnerabilities,
                low_vulnerabilities=low_vulnerabilities,
                compliance_score=compliance_score,
                report_data=report_data,
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        finally:
            session.close()

    def get_recent_compliance_reports(
        self, application_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[ComplianceReport]:
        """Get recent compliance reports.

        Args:
            application_id: Optional application ID to filter by.
            limit: Maximum number of reports to return.

        Returns:
            List of ComplianceReport objects.
        """
        session = self.get_session()
        try:
            query = session.query(ComplianceReport).order_by(
                ComplianceReport.generated_at.desc()
            )
            if application_id:
                query = query.filter(ComplianceReport.application_id == application_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_security_metric(
        self,
        application_id: int,
        time_window_start: datetime,
        time_window_end: datetime,
        total_vulnerabilities: int,
        fixed_vulnerabilities: int,
        average_fix_time_hours: Optional[float] = None,
        compliance_score: Optional[float] = None,
    ) -> SecurityMetric:
        """Add security performance metric.

        Args:
            application_id: Application ID.
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_vulnerabilities: Total number of vulnerabilities.
            fixed_vulnerabilities: Number of fixed vulnerabilities.
            average_fix_time_hours: Average fix time in hours.
            compliance_score: Compliance score.

        Returns:
            Created SecurityMetric object.
        """
        session = self.get_session()
        try:
            metric = SecurityMetric(
                application_id=application_id,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_vulnerabilities=total_vulnerabilities,
                fixed_vulnerabilities=fixed_vulnerabilities,
                average_fix_time_hours=average_fix_time_hours,
                compliance_score=compliance_score,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_recent_metrics(
        self, application_id: Optional[int] = None, days: int = 30
    ) -> List[SecurityMetric]:
        """Get recent security metrics.

        Args:
            application_id: Optional application ID to filter by.
            days: Number of days to look back.

        Returns:
            List of SecurityMetric objects.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)
            query = (
                session.query(SecurityMetric)
                .filter(SecurityMetric.time_window_start >= cutoff)
                .order_by(SecurityMetric.time_window_start.desc())
            )
            if application_id:
                query = query.filter(SecurityMetric.application_id == application_id)
            return query.all()
        finally:
            session.close()
