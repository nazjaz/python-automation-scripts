"""Database models and operations for refund processing."""

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


class Order(Base):
    """Order model for storing order information."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)
    customer_email = Column(String, nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    payment_provider = Column(String, nullable=False)
    payment_transaction_id = Column(String, nullable=False)
    order_date = Column(DateTime, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)


class RefundRequest(Base):
    """Refund request model."""

    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, nullable=False, index=True)
    customer_email = Column(String, nullable=False, index=True)
    requested_amount = Column(Float, nullable=False)
    refund_reason = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class Refund(Base):
    """Refund model for processed refunds."""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    refund_request_id = Column(Integer, index=True, nullable=False)
    order_id = Column(String, nullable=False, index=True)
    customer_email = Column(String, nullable=False, index=True)
    refund_amount = Column(Float, nullable=False)
    restocking_fee = Column(Float, default=0.0)
    net_refund_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    refund_reason = Column(String, nullable=False)
    payment_provider = Column(String, nullable=False)
    payment_refund_id = Column(String, nullable=True)
    status = Column(String, default="processing")
    approved_by = Column(String, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    confirmation_sent = Column(Boolean, default=False)


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

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by order ID.

        Args:
            order_id: Order identifier.

        Returns:
            Order object if found, None otherwise.
        """
        with self.get_session() as session:
            return (
                session.query(Order).filter(Order.order_id == order_id).first()
            )

    def create_refund_request(
        self,
        order_id: str,
        customer_email: str,
        requested_amount: float,
        refund_reason: str,
        description: Optional[str] = None,
    ) -> RefundRequest:
        """Create a new refund request.

        Args:
            order_id: Order identifier.
            customer_email: Customer email address.
            requested_amount: Requested refund amount.
            refund_reason: Reason for refund.
            description: Additional description (optional).

        Returns:
            Created RefundRequest object.
        """
        with self.get_session() as session:
            request = RefundRequest(
                order_id=order_id,
                customer_email=customer_email,
                requested_amount=requested_amount,
                refund_reason=refund_reason,
                description=description,
            )
            session.add(request)
            session.commit()
            session.refresh(request)
            return request

    def get_refund_count_for_order(self, order_id: str) -> int:
        """Get number of refunds for an order.

        Args:
            order_id: Order identifier.

        Returns:
            Number of refunds for the order.
        """
        with self.get_session() as session:
            return (
                session.query(Refund)
                .filter(Refund.order_id == order_id)
                .count()
            )

    def create_refund(
        self,
        refund_request_id: int,
        order_id: str,
        customer_email: str,
        refund_amount: float,
        restocking_fee: float,
        net_refund_amount: float,
        currency: str,
        refund_reason: str,
        payment_provider: str,
        payment_refund_id: Optional[str] = None,
        approved_by: Optional[str] = None,
    ) -> Refund:
        """Create a processed refund record.

        Args:
            refund_request_id: Refund request ID.
            order_id: Order identifier.
            customer_email: Customer email address.
            refund_amount: Refund amount before fees.
            restocking_fee: Restocking fee amount.
            net_refund_amount: Net refund amount after fees.
            currency: Currency code.
            refund_reason: Reason for refund.
            payment_provider: Payment provider name.
            payment_refund_id: Payment provider refund ID (optional).
            approved_by: Approver name (optional).

        Returns:
            Created Refund object.
        """
        with self.get_session() as session:
            refund = Refund(
                refund_request_id=refund_request_id,
                order_id=order_id,
                customer_email=customer_email,
                refund_amount=refund_amount,
                restocking_fee=restocking_fee,
                net_refund_amount=net_refund_amount,
                currency=currency,
                refund_reason=refund_reason,
                payment_provider=payment_provider,
                payment_refund_id=payment_refund_id,
                approved_by=approved_by,
            )
            session.add(refund)
            session.commit()
            session.refresh(refund)
            return refund

    def update_refund_status(
        self, refund_id: int, status: str, payment_refund_id: Optional[str] = None
    ) -> None:
        """Update refund status.

        Args:
            refund_id: Refund ID.
            status: New status.
            payment_refund_id: Payment provider refund ID (optional).
        """
        with self.get_session() as session:
            refund = session.query(Refund).filter(Refund.id == refund_id).first()
            if refund:
                refund.status = status
                if payment_refund_id:
                    refund.payment_refund_id = payment_refund_id
                if status == "completed":
                    refund.completed_at = datetime.utcnow()
                session.commit()
