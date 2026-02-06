"""Database models and operations for backup monitoring data."""

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


class BackupLocation(Base):
    """Database model for backup locations."""

    __tablename__ = "backup_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    path = Column(String(500), nullable=False)
    backup_type = Column(String(50), nullable=False)
    schedule = Column(String(50))
    retention_days = Column(Integer, default=30)
    verify_integrity = Column(Boolean, default=True)
    test_restore = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    backups = relationship("Backup", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BackupLocation(id={self.id}, name={self.name}, path={self.path})>"


class Backup(Base):
    """Database model for backup records."""

    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("backup_locations.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    size_bytes = Column(Integer)
    checksum = Column(String(128))
    checksum_algorithm = Column(String(50))
    backup_timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="pending", index=True)
    error_message = Column(Text)

    location = relationship("BackupLocation", back_populates="backups")
    verifications = relationship("BackupVerification", back_populates="backup", cascade="all, delete-orphan")
    restore_tests = relationship("RestoreTest", back_populates="backup", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Backup(id={self.id}, filename={self.filename}, status={self.status})>"


class BackupVerification(Base):
    """Database model for backup verification results."""

    __tablename__ = "backup_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_id = Column(Integer, ForeignKey("backups.id"), nullable=False, index=True)
    verification_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    result = Column(Text)
    error_message = Column(Text)
    verified_at = Column(DateTime, default=datetime.utcnow, index=True)

    backup = relationship("Backup", back_populates="verifications")

    def __repr__(self) -> str:
        return (
            f"<BackupVerification(id={self.id}, backup_id={self.backup_id}, "
            f"verification_type={self.verification_type}, status={self.status})>"
        )


class RestoreTest(Base):
    """Database model for restore test results."""

    __tablename__ = "restore_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_id = Column(Integer, ForeignKey("backups.id"), nullable=False, index=True)
    test_location = Column(String(500))
    status = Column(String(50), nullable=False, index=True)
    duration_seconds = Column(Float)
    result = Column(Text)
    error_message = Column(Text)
    tested_at = Column(DateTime, default=datetime.utcnow, index=True)

    backup = relationship("Backup", back_populates="restore_tests")

    def __repr__(self) -> str:
        return (
            f"<RestoreTest(id={self.id}, backup_id={self.backup_id}, "
            f"status={self.status})>"
        )


class HealthMetric(Base):
    """Database model for backup health metrics."""

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("backup_locations.id"), nullable=False, index=True)
    metric_date = Column(DateTime, nullable=False, index=True)
    total_backups = Column(Integer, default=0)
    successful_backups = Column(Integer, default=0)
    failed_backups = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    verification_success_rate = Column(Float)
    restore_test_success_rate = Column(Float)
    health_score = Column(Float, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<HealthMetric(id={self.id}, location_id={self.location_id}, "
            f"health_score={self.health_score})>"
        )


class Alert(Base):
    """Database model for backup alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("backup_locations.id"), nullable=True, index=True)
    backup_id = Column(Integer, ForeignKey("backups.id"), nullable=True, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<Alert(id={self.id}, alert_type={self.alert_type}, "
            f"severity={self.severity}, resolved={self.resolved})>"
        )


class DatabaseManager:
    """Manages database operations for backup monitoring data."""

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

    def add_backup_location(
        self,
        name: str,
        path: str,
        backup_type: str,
        schedule: Optional[str] = None,
        retention_days: int = 30,
        verify_integrity: bool = True,
        test_restore: bool = False,
    ) -> BackupLocation:
        """Add or update backup location.

        Args:
            name: Location name.
            path: Backup path.
            backup_type: Type of backup (database, file, etc.).
            schedule: Optional schedule.
            retention_days: Retention period in days.
            verify_integrity: Whether to verify integrity.
            test_restore: Whether to test restore.

        Returns:
            BackupLocation object.
        """
        session = self.get_session()
        try:
            location = (
                session.query(BackupLocation)
                .filter(BackupLocation.name == name)
                .first()
            )

            if location is None:
                location = BackupLocation(
                    name=name,
                    path=path,
                    backup_type=backup_type,
                    schedule=schedule,
                    retention_days=retention_days,
                    verify_integrity=verify_integrity,
                    test_restore=test_restore,
                )
                session.add(location)
            else:
                location.path = path
                location.backup_type = backup_type
                location.schedule = schedule
                location.retention_days = retention_days
                location.verify_integrity = verify_integrity
                location.test_restore = test_restore
                location.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(location)
            return location
        finally:
            session.close()

    def add_backup(
        self,
        location_id: int,
        filename: str,
        filepath: str,
        backup_timestamp: datetime,
        size_bytes: Optional[int] = None,
        checksum: Optional[str] = None,
        checksum_algorithm: Optional[str] = None,
        status: str = "pending",
        error_message: Optional[str] = None,
    ) -> Backup:
        """Add backup record.

        Args:
            location_id: Location ID.
            filename: Backup filename.
            filepath: Full file path.
            backup_timestamp: When backup was created.
            size_bytes: Optional file size.
            checksum: Optional checksum.
            checksum_algorithm: Optional checksum algorithm.
            status: Backup status.
            error_message: Optional error message.

        Returns:
            Backup object.
        """
        session = self.get_session()
        try:
            backup = Backup(
                location_id=location_id,
                filename=filename,
                filepath=filepath,
                backup_timestamp=backup_timestamp,
                size_bytes=size_bytes,
                checksum=checksum,
                checksum_algorithm=checksum_algorithm,
                status=status,
                error_message=error_message,
            )
            session.add(backup)
            session.commit()
            session.refresh(backup)
            return backup
        finally:
            session.close()

    def add_verification(
        self,
        backup_id: int,
        verification_type: str,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> BackupVerification:
        """Add backup verification result.

        Args:
            backup_id: Backup ID.
            verification_type: Type of verification.
            status: Verification status.
            result: Optional result text.
            error_message: Optional error message.

        Returns:
            BackupVerification object.
        """
        session = self.get_session()
        try:
            verification = BackupVerification(
                backup_id=backup_id,
                verification_type=verification_type,
                status=status,
                result=result,
                error_message=error_message,
            )
            session.add(verification)
            session.commit()
            session.refresh(verification)
            return verification
        finally:
            session.close()

    def add_restore_test(
        self,
        backup_id: int,
        status: str,
        test_location: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> RestoreTest:
        """Add restore test result.

        Args:
            backup_id: Backup ID.
            status: Test status.
            test_location: Optional test location.
            duration_seconds: Optional test duration.
            result: Optional result text.
            error_message: Optional error message.

        Returns:
            RestoreTest object.
        """
        session = self.get_session()
        try:
            restore_test = RestoreTest(
                backup_id=backup_id,
                status=status,
                test_location=test_location,
                duration_seconds=duration_seconds,
                result=result,
                error_message=error_message,
            )
            session.add(restore_test)
            session.commit()
            session.refresh(restore_test)
            return restore_test
        finally:
            session.close()

    def add_health_metric(
        self,
        location_id: int,
        metric_date: datetime,
        total_backups: int = 0,
        successful_backups: int = 0,
        failed_backups: int = 0,
        total_size_bytes: int = 0,
        verification_success_rate: Optional[float] = None,
        restore_test_success_rate: Optional[float] = None,
        health_score: Optional[float] = None,
    ) -> HealthMetric:
        """Add health metric.

        Args:
            location_id: Location ID.
            metric_date: Metric date.
            total_backups: Total number of backups.
            successful_backups: Number of successful backups.
            failed_backups: Number of failed backups.
            total_size_bytes: Total backup size.
            verification_success_rate: Optional verification success rate.
            restore_test_success_rate: Optional restore test success rate.
            health_score: Optional health score.

        Returns:
            HealthMetric object.
        """
        session = self.get_session()
        try:
            metric = HealthMetric(
                location_id=location_id,
                metric_date=metric_date,
                total_backups=total_backups,
                successful_backups=successful_backups,
                failed_backups=failed_backups,
                total_size_bytes=total_size_bytes,
                verification_success_rate=verification_success_rate,
                restore_test_success_rate=restore_test_success_rate,
                health_score=health_score,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def add_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        location_id: Optional[int] = None,
        backup_id: Optional[int] = None,
    ) -> Alert:
        """Add alert.

        Args:
            alert_type: Alert type.
            severity: Alert severity.
            message: Alert message.
            location_id: Optional location ID.
            backup_id: Optional backup ID.

        Returns:
            Alert object.
        """
        session = self.get_session()
        try:
            alert = Alert(
                location_id=location_id,
                backup_id=backup_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
        finally:
            session.close()

    def get_backup_locations(self, enabled_only: bool = True) -> List[BackupLocation]:
        """Get backup locations.

        Args:
            enabled_only: Whether to return only enabled locations.

        Returns:
            List of BackupLocation objects.
        """
        session = self.get_session()
        try:
            query = session.query(BackupLocation)
            if enabled_only:
                query = query.filter(BackupLocation.enabled == True)
            return query.all()
        finally:
            session.close()

    def get_recent_backups(
        self,
        location_id: Optional[int] = None,
        limit: int = 100,
        days: Optional[int] = None,
    ) -> List[Backup]:
        """Get recent backups.

        Args:
            location_id: Optional location filter.
            limit: Maximum number of results.
            days: Optional number of days to look back.

        Returns:
            List of Backup objects.
        """
        session = self.get_session()
        try:
            query = session.query(Backup)

            if location_id:
                query = query.filter(Backup.location_id == location_id)

            if days:
                from datetime import timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Backup.created_at >= cutoff_date)

            query = query.order_by(Backup.created_at.desc()).limit(limit)

            return query.all()
        finally:
            session.close()

    def get_failed_backups(
        self,
        location_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[Backup]:
        """Get failed backups.

        Args:
            location_id: Optional location filter.
            days: Optional number of days to look back.

        Returns:
            List of failed Backup objects.
        """
        session = self.get_session()
        try:
            query = session.query(Backup).filter(Backup.status == "failed")

            if location_id:
                query = query.filter(Backup.location_id == location_id)

            if days:
                from datetime import timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Backup.created_at >= cutoff_date)

            query = query.order_by(Backup.created_at.desc())

            return query.all()
        finally:
            session.close()

    def get_unresolved_alerts(
        self,
        location_id: Optional[int] = None,
    ) -> List[Alert]:
        """Get unresolved alerts.

        Args:
            location_id: Optional location filter.

        Returns:
            List of unresolved Alert objects.
        """
        session = self.get_session()
        try:
            query = session.query(Alert).filter(Alert.resolved == False)

            if location_id:
                query = query.filter(Alert.location_id == location_id)

            query = query.order_by(Alert.created_at.desc())

            return query.all()
        finally:
            session.close()
