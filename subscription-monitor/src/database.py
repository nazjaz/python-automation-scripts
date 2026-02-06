"""Database models and operations for subscription monitor data."""

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


class Customer(Base):
    """Database model for customers."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    churn_risks = relationship("ChurnRisk", back_populates="customer", cascade="all, delete-orphan")
    campaigns = relationship("RetentionCampaign", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, customer_id={self.customer_id}, name={self.name})>"


class Subscription(Base):
    """Database model for subscriptions."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(String(100), unique=True, nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    billing_cycle = Column(String(50), nullable=False)
    monthly_revenue = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    renewal_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, index=True)
    auto_renewal = Column(Boolean, default=True, index=True)
    payment_method = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="subscriptions")
    renewals = relationship("Renewal", back_populates="subscription", cascade="all, delete-orphan")
    payment_failures = relationship("PaymentFailure", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, subscription_id={self.subscription_id}, "
            f"status={self.status}, renewal_date={self.renewal_date})>"
        )


class Renewal(Base):
    """Database model for subscription renewals."""

    __tablename__ = "renewals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    renewal_date = Column(Date, nullable=False, index=True)
    previous_renewal_date = Column(Date)
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="renewals")

    def __repr__(self) -> str:
        return (
            f"<Renewal(id={self.id}, subscription_id={self.subscription_id}, "
            f"renewal_date={self.renewal_date}, status={self.status})>"
        )


class PaymentFailure(Base):
    """Database model for payment failures."""

    __tablename__ = "payment_failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    failure_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String(255))
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="payment_failures")

    def __repr__(self) -> str:
        return (
            f"<PaymentFailure(id={self.id}, subscription_id={self.subscription_id}, "
            f"failure_date={self.failure_date}, resolved={self.resolved})>"
        )


class ChurnRisk(Base):
    """Database model for churn risk assessments."""

    __tablename__ = "churn_risks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(50), nullable=False, index=True)
    factors = Column(Text)
    engagement_score = Column(Float)
    days_since_last_activity = Column(Integer)
    payment_failure_count = Column(Integer, default=0)
    support_ticket_count = Column(Integer, default=0)
    assessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)

    customer = relationship("Customer", back_populates="churn_risks")

    def __repr__(self) -> str:
        return (
            f"<ChurnRisk(id={self.id}, customer_id={self.customer_id}, "
            f"risk_score={self.risk_score}, risk_level={self.risk_level})>"
        )


class RetentionCampaign(Base):
    """Database model for retention campaigns."""

    __tablename__ = "retention_campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    campaign_type = Column(String(100), nullable=False, index=True)
    triggered_by = Column(String(100))
    status = Column(String(50), default="pending", index=True)
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    converted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    customer = relationship("Customer", back_populates="campaigns")

    def __repr__(self) -> str:
        return (
            f"<RetentionCampaign(id={self.id}, customer_id={self.customer_id}, "
            f"campaign_type={self.campaign_type}, status={self.status})>"
        )


class SubscriptionMetric(Base):
    """Database model for subscription lifecycle metrics."""

    __tablename__ = "subscription_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(Date, nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<SubscriptionMetric(id={self.id}, metric_date={self.metric_date}, "
            f"metric_type={self.metric_type}, value={self.value})>"
        )


class DatabaseManager:
    """Manages database operations for subscription monitor data."""

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

    def add_customer(
        self,
        customer_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
    ) -> Customer:
        """Add or update customer.

        Args:
            customer_id: Customer ID.
            name: Customer name.
            email: Customer email.
            phone: Optional phone number.

        Returns:
            Customer object.
        """
        session = self.get_session()
        try:
            customer = (
                session.query(Customer)
                .filter(Customer.customer_id == customer_id)
                .first()
            )

            if customer is None:
                customer = Customer(
                    customer_id=customer_id,
                    name=name,
                    email=email,
                    phone=phone,
                )
                session.add(customer)
            else:
                customer.name = name
                customer.email = email
                customer.phone = phone
                customer.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(customer)
            return customer
        finally:
            session.close()

    def add_subscription(
        self,
        customer_id: int,
        subscription_id: str,
        plan_name: str,
        status: str,
        billing_cycle: str,
        monthly_revenue: float,
        start_date: date,
        renewal_date: date,
        auto_renewal: bool = True,
        payment_method: Optional[str] = None,
    ) -> Subscription:
        """Add subscription.

        Args:
            customer_id: Customer ID.
            subscription_id: Subscription ID.
            plan_name: Plan name.
            status: Subscription status.
            billing_cycle: Billing cycle.
            monthly_revenue: Monthly revenue.
            start_date: Start date.
            renewal_date: Renewal date.
            auto_renewal: Auto renewal enabled.
            payment_method: Optional payment method.

        Returns:
            Subscription object.
        """
        session = self.get_session()
        try:
            subscription = Subscription(
                customer_id=customer_id,
                subscription_id=subscription_id,
                plan_name=plan_name,
                status=status,
                billing_cycle=billing_cycle,
                monthly_revenue=monthly_revenue,
                start_date=start_date,
                renewal_date=renewal_date,
                auto_renewal=auto_renewal,
                payment_method=payment_method,
            )
            session.add(subscription)
            session.commit()
            session.refresh(subscription)
            return subscription
        finally:
            session.close()

    def add_renewal(
        self,
        subscription_id: int,
        renewal_date: date,
        amount: float,
        status: str,
        previous_renewal_date: Optional[date] = None,
    ) -> Renewal:
        """Add renewal record.

        Args:
            subscription_id: Subscription ID.
            renewal_date: Renewal date.
            amount: Renewal amount.
            status: Renewal status.
            previous_renewal_date: Optional previous renewal date.

        Returns:
            Renewal object.
        """
        session = self.get_session()
        try:
            renewal = Renewal(
                subscription_id=subscription_id,
                renewal_date=renewal_date,
                amount=amount,
                status=status,
                previous_renewal_date=previous_renewal_date,
            )
            session.add(renewal)
            session.commit()
            session.refresh(renewal)
            return renewal
        finally:
            session.close()

    def add_payment_failure(
        self,
        subscription_id: int,
        failure_date: datetime,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentFailure:
        """Add payment failure record.

        Args:
            subscription_id: Subscription ID.
            failure_date: Failure date.
            amount: Failed amount.
            reason: Optional failure reason.

        Returns:
            PaymentFailure object.
        """
        session = self.get_session()
        try:
            failure = PaymentFailure(
                subscription_id=subscription_id,
                failure_date=failure_date,
                amount=amount,
                reason=reason,
            )
            session.add(failure)
            session.commit()
            session.refresh(failure)
            return failure
        finally:
            session.close()

    def add_churn_risk(
        self,
        customer_id: int,
        risk_score: float,
        risk_level: str,
        factors: Optional[str] = None,
        engagement_score: Optional[float] = None,
        days_since_last_activity: Optional[int] = None,
        payment_failure_count: int = 0,
        support_ticket_count: int = 0,
    ) -> ChurnRisk:
        """Add churn risk assessment.

        Args:
            customer_id: Customer ID.
            risk_score: Risk score (0.0 to 1.0).
            risk_level: Risk level.
            factors: Optional risk factors description.
            engagement_score: Optional engagement score.
            days_since_last_activity: Optional days since last activity.
            payment_failure_count: Payment failure count.
            support_ticket_count: Support ticket count.

        Returns:
            ChurnRisk object.
        """
        session = self.get_session()
        try:
            risk = ChurnRisk(
                customer_id=customer_id,
                risk_score=risk_score,
                risk_level=risk_level,
                factors=factors,
                engagement_score=engagement_score,
                days_since_last_activity=days_since_last_activity,
                payment_failure_count=payment_failure_count,
                support_ticket_count=support_ticket_count,
            )
            session.add(risk)
            session.commit()
            session.refresh(risk)
            return risk
        finally:
            session.close()

    def add_retention_campaign(
        self,
        customer_id: int,
        campaign_type: str,
        triggered_by: Optional[str] = None,
    ) -> RetentionCampaign:
        """Add retention campaign.

        Args:
            customer_id: Customer ID.
            campaign_type: Campaign type.
            triggered_by: Optional trigger reason.

        Returns:
            RetentionCampaign object.
        """
        session = self.get_session()
        try:
            campaign = RetentionCampaign(
                customer_id=customer_id,
                campaign_type=campaign_type,
                triggered_by=triggered_by,
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)
            return campaign
        finally:
            session.close()

    def add_metric(
        self,
        metric_date: date,
        metric_type: str,
        value: float,
        metadata: Optional[str] = None,
    ) -> SubscriptionMetric:
        """Add subscription metric.

        Args:
            metric_date: Metric date.
            metric_type: Metric type.
            value: Metric value.
            metadata: Optional metadata.

        Returns:
            SubscriptionMetric object.
        """
        session = self.get_session()
        try:
            metric = SubscriptionMetric(
                metric_date=metric_date,
                metric_type=metric_type,
                value=value,
                metadata=metadata,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_subscriptions_due_for_renewal(
        self,
        days_ahead: int = 30,
        days_past: int = 7,
        status: Optional[str] = None,
    ) -> List[Subscription]:
        """Get subscriptions due for renewal.

        Args:
            days_ahead: Days ahead to check.
            days_past: Days past to check.
            status: Optional status filter.

        Returns:
            List of Subscription objects.
        """
        from datetime import timedelta

        today = date.today()
        start_date = today - timedelta(days=days_past)
        end_date = today + timedelta(days=days_ahead)

        session = self.get_session()
        try:
            query = (
                session.query(Subscription)
                .filter(
                    Subscription.renewal_date >= start_date,
                    Subscription.renewal_date <= end_date,
                )
            )

            if status:
                query = query.filter(Subscription.status == status)

            return query.all()
        finally:
            session.close()

    def get_high_risk_customers(
        self,
        risk_level: str = "high",
        limit: Optional[int] = None,
    ) -> List[ChurnRisk]:
        """Get high risk customers.

        Args:
            risk_level: Risk level filter.
            limit: Optional limit on number of results.

        Returns:
            List of ChurnRisk objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(ChurnRisk)
                .filter(
                    ChurnRisk.risk_level == risk_level,
                    ChurnRisk.resolved == False,
                )
                .order_by(ChurnRisk.risk_score.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_pending_campaigns(
        self,
        limit: Optional[int] = None,
    ) -> List[RetentionCampaign]:
        """Get pending retention campaigns.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of RetentionCampaign objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(RetentionCampaign)
                .filter(RetentionCampaign.status == "pending")
                .order_by(RetentionCampaign.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
