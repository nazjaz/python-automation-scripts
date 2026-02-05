"""Database models and operations for tracking onboarding progress."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Customer(Base):
    """Customer model for tracking onboarding information."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    account_id = Column(String, unique=True, index=True, nullable=True)
    onboarding_started_at = Column(DateTime, default=datetime.utcnow)
    onboarding_completed_at = Column(DateTime, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OnboardingStep(Base):
    """Onboarding step tracking model."""

    __tablename__ = "onboarding_steps"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    step_name = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResourceAssignment(Base):
    """Resource assignment tracking model."""

    __tablename__ = "resource_assignments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_name = Column(String, nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


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

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Retrieve customer by email address.

        Args:
            email: Customer email address.

        Returns:
            Customer object if found, None otherwise.
        """
        with self.get_session() as session:
            return session.query(Customer).filter(Customer.email == email).first()

    def create_customer(
        self,
        email: str,
        name: str,
        company_name: Optional[str] = None,
    ) -> Customer:
        """Create a new customer record.

        Args:
            email: Customer email address.
            name: Customer full name.
            company_name: Optional company name.

        Returns:
            Created Customer object.

        Raises:
            ValueError: If customer with email already exists.
        """
        with self.get_session() as session:
            existing = session.query(Customer).filter(Customer.email == email).first()
            if existing:
                raise ValueError(f"Customer with email {email} already exists")

            customer = Customer(email=email, name=name, company_name=company_name)
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer

    def update_customer_completion(
        self, customer_id: int, completion_percentage: float
    ) -> None:
        """Update customer onboarding completion percentage.

        Args:
            customer_id: Customer ID.
            completion_percentage: Completion percentage (0.0 to 1.0).
        """
        with self.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.completion_percentage = completion_percentage
                if completion_percentage >= 1.0:
                    customer.onboarding_completed_at = datetime.utcnow()
                session.commit()
