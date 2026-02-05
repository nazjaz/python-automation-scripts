"""Database models and operations for license monitoring."""

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


class License(Base):
    """License model for storing license information."""

    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_type = Column(String, nullable=False, index=True)
    license_key = Column(String, unique=True, nullable=False, index=True)
    assigned_to = Column(String, nullable=True, index=True)
    assigned_email = Column(String, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    cost = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    source = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LicenseUsage(Base):
    """License usage tracking model."""

    __tablename__ = "license_usage"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, index=True, nullable=False)
    user_email = Column(String, nullable=False, index=True)
    usage_date = Column(DateTime, default=datetime.utcnow, index=True)
    usage_duration_minutes = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class ComplianceRecord(Base):
    """Compliance tracking record."""

    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    license_type = Column(String, nullable=False, index=True)
    total_licenses = Column(Integer, nullable=False)
    assigned_licenses = Column(Integer, nullable=False)
    unused_licenses = Column(Integer, nullable=False)
    compliance_percentage = Column(Float, nullable=False)
    check_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default="compliant")
    notes = Column(Text, nullable=True)


class OptimizationRecommendation(Base):
    """Optimization recommendation model."""

    __tablename__ = "optimization_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    license_type = Column(String, nullable=False, index=True)
    recommendation_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    estimated_savings = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    priority = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")


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

    def create_license(
        self,
        license_type: str,
        license_key: str,
        source: str,
        assigned_to: Optional[str] = None,
        assigned_email: Optional[str] = None,
        cost: Optional[float] = None,
        currency: str = "USD",
        purchase_date: Optional[datetime] = None,
        expiration_date: Optional[datetime] = None,
    ) -> License:
        """Create a new license record.

        Args:
            license_type: Type of license.
            license_key: Unique license key.
            source: Source of license data.
            assigned_to: User assigned to license.
            assigned_email: Email of assigned user.
            cost: License cost.
            currency: Currency code.
            purchase_date: Purchase date.
            expiration_date: Expiration date.

        Returns:
            Created License object.
        """
        with self.get_session() as session:
            existing = (
                session.query(License)
                .filter(License.license_key == license_key)
                .first()
            )
            if existing:
                existing.assigned_to = assigned_to or existing.assigned_to
                existing.assigned_email = assigned_email or existing.assigned_email
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing

            license_obj = License(
                license_type=license_type,
                license_key=license_key,
                source=source,
                assigned_to=assigned_to,
                assigned_email=assigned_email,
                cost=cost,
                currency=currency,
                purchase_date=purchase_date,
                expiration_date=expiration_date,
            )
            session.add(license_obj)
            session.commit()
            session.refresh(license_obj)
            return license_obj

    def get_licenses_by_type(self, license_type: str) -> list[License]:
        """Get all licenses of a specific type.

        Args:
            license_type: License type name.

        Returns:
            List of License objects.
        """
        with self.get_session() as session:
            return (
                session.query(License)
                .filter(License.license_type == license_type, License.status == "active")
                .all()
            )

    def get_unused_licenses(
        self, threshold_days: int = 90
    ) -> list[License]:
        """Get licenses that haven't been used recently.

        Args:
            threshold_days: Number of days of inactivity to consider unused.

        Returns:
            List of unused License objects.
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)

        with self.get_session() as session:
            licenses = (
                session.query(License)
                .filter(License.status == "active")
                .all()
            )

            unused = []
            for license_obj in licenses:
                last_usage = (
                    session.query(LicenseUsage)
                    .filter(LicenseUsage.license_id == license_obj.id)
                    .order_by(LicenseUsage.usage_date.desc())
                    .first()
                )

                if not last_usage or last_usage.usage_date < cutoff_date:
                    unused.append(license_obj)

            return unused
