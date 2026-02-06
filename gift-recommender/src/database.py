"""Database models and operations for gift recommendation data."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class Recipient(Base):
    """Database model for gift recipients."""

    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    age = Column(Integer)
    relationship = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    preferences = relationship("Preference", back_populates="recipient", cascade="all, delete-orphan")
    purchase_history = relationship("PurchaseHistory", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Recipient(id={self.id}, name={self.name}, email={self.email})>"


class Preference(Base):
    """Database model for recipient preferences."""

    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    interest = Column(String(255))
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("Recipient", back_populates="preferences")

    def __repr__(self) -> str:
        return (
            f"<Preference(id={self.id}, recipient_id={self.recipient_id}, "
            f"category={self.category}, interest={self.interest})>"
        )


class PurchaseHistory(Base):
    """Database model for purchase history."""

    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False, index=True)
    item_name = Column(String(500), nullable=False)
    category = Column(String(100))
    price = Column(Float)
    purchase_date = Column(DateTime, nullable=False, index=True)
    rating = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("Recipient", back_populates="purchase_history")

    def __repr__(self) -> str:
        return (
            f"<PurchaseHistory(id={self.id}, recipient_id={self.recipient_id}, "
            f"item_name={self.item_name}, purchase_date={self.purchase_date})>"
        )


class GiftItem(Base):
    """Database model for gift catalog items."""

    __tablename__ = "gift_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False, index=True)
    brand = Column(String(255))
    tags = Column(String(500))
    availability = Column(String(50), default="in_stock")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GiftItem(id={self.id}, name={self.name}, category={self.category}, price={self.price})>"


class Recommendation(Base):
    """Database model for gift recommendations."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False, index=True)
    gift_item_id = Column(Integer, ForeignKey("gift_items.id"), nullable=False, index=True)
    occasion = Column(String(100))
    score = Column(Float, nullable=False, index=True)
    price_range = Column(String(50))
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.id}, recipient_id={self.recipient_id}, "
            f"gift_item_id={self.gift_item_id}, score={self.score})>"
        )


class DatabaseManager:
    """Manages database operations for gift recommendation data."""

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

    def add_recipient(
        self,
        name: str,
        email: Optional[str] = None,
        age: Optional[int] = None,
        relationship: Optional[str] = None,
    ) -> Recipient:
        """Add or update recipient.

        Args:
            name: Recipient name.
            email: Optional email address.
            age: Optional age.
            relationship: Optional relationship type.

        Returns:
            Recipient object.
        """
        session = self.get_session()
        try:
            recipient = None
            if email:
                recipient = (
                    session.query(Recipient)
                    .filter(Recipient.email == email)
                    .first()
                )

            if recipient is None:
                recipient = Recipient(
                    name=name,
                    email=email,
                    age=age,
                    relationship=relationship,
                )
                session.add(recipient)
            else:
                recipient.name = name
                if age:
                    recipient.age = age
                if relationship:
                    recipient.relationship = relationship
                recipient.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(recipient)
            return recipient
        finally:
            session.close()

    def add_preference(
        self,
        recipient_id: int,
        category: str,
        interest: Optional[str] = None,
        priority: int = 1,
    ) -> Preference:
        """Add preference for recipient.

        Args:
            recipient_id: ID of the recipient.
            category: Preference category.
            interest: Optional interest description.
            priority: Priority level (1-10, higher is more important).

        Returns:
            Preference object.
        """
        session = self.get_session()
        try:
            preference = Preference(
                recipient_id=recipient_id,
                category=category,
                interest=interest,
                priority=priority,
            )
            session.add(preference)
            session.commit()
            session.refresh(preference)
            return preference
        finally:
            session.close()

    def add_purchase(
        self,
        recipient_id: int,
        item_name: str,
        purchase_date: datetime,
        category: Optional[str] = None,
        price: Optional[float] = None,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> PurchaseHistory:
        """Add purchase to history.

        Args:
            recipient_id: ID of the recipient.
            item_name: Name of purchased item.
            purchase_date: Date of purchase.
            category: Optional item category.
            price: Optional purchase price.
            rating: Optional rating (1-5).
            notes: Optional notes.

        Returns:
            PurchaseHistory object.
        """
        session = self.get_session()
        try:
            purchase = PurchaseHistory(
                recipient_id=recipient_id,
                item_name=item_name,
                category=category,
                price=price,
                purchase_date=purchase_date,
                rating=rating,
                notes=notes,
            )
            session.add(purchase)
            session.commit()
            session.refresh(purchase)
            return purchase
        finally:
            session.close()

    def add_gift_item(
        self,
        name: str,
        category: str,
        price: float,
        description: Optional[str] = None,
        brand: Optional[str] = None,
        tags: Optional[str] = None,
        availability: str = "in_stock",
    ) -> GiftItem:
        """Add gift item to catalog.

        Args:
            name: Item name.
            category: Item category.
            price: Item price.
            description: Optional description.
            brand: Optional brand name.
            tags: Optional comma-separated tags.
            availability: Availability status.

        Returns:
            GiftItem object.
        """
        session = self.get_session()
        try:
            item = GiftItem(
                name=name,
                category=category,
                price=price,
                description=description,
                brand=brand,
                tags=tags,
                availability=availability,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def get_recipient(self, recipient_id: int) -> Optional[Recipient]:
        """Get recipient by ID.

        Args:
            recipient_id: Recipient ID.

        Returns:
            Recipient object or None.
        """
        session = self.get_session()
        try:
            return session.query(Recipient).filter(Recipient.id == recipient_id).first()
        finally:
            session.close()

    def get_recipient_by_email(self, email: str) -> Optional[Recipient]:
        """Get recipient by email.

        Args:
            email: Email address.

        Returns:
            Recipient object or None.
        """
        session = self.get_session()
        try:
            return session.query(Recipient).filter(Recipient.email == email).first()
        finally:
            session.close()

    def get_preferences(self, recipient_id: int) -> List[Preference]:
        """Get all preferences for recipient.

        Args:
            recipient_id: Recipient ID.

        Returns:
            List of Preference objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Preference)
                .filter(Preference.recipient_id == recipient_id)
                .all()
            )
        finally:
            session.close()

    def get_purchase_history(
        self,
        recipient_id: int,
        limit: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[PurchaseHistory]:
        """Get purchase history for recipient.

        Args:
            recipient_id: Recipient ID.
            limit: Optional limit on number of results.
            days: Optional number of days to look back.

        Returns:
            List of PurchaseHistory objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(PurchaseHistory)
                .filter(PurchaseHistory.recipient_id == recipient_id)
                .order_by(PurchaseHistory.purchase_date.desc())
            )

            if days:
                from datetime import timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(PurchaseHistory.purchase_date >= cutoff_date)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_gift_items(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[GiftItem]:
        """Get gift items with optional filtering.

        Args:
            category: Optional category filter.
            min_price: Optional minimum price.
            max_price: Optional maximum price.
            limit: Optional limit on number of results.

        Returns:
            List of GiftItem objects.
        """
        session = self.get_session()
        try:
            query = session.query(GiftItem).filter(GiftItem.availability == "in_stock")

            if category:
                query = query.filter(GiftItem.category == category)

            if min_price is not None:
                query = query.filter(GiftItem.price >= min_price)

            if max_price is not None:
                query = query.filter(GiftItem.price <= max_price)

            query = query.order_by(GiftItem.price)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def save_recommendation(
        self,
        recipient_id: int,
        gift_item_id: int,
        score: float,
        occasion: Optional[str] = None,
        price_range: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> Recommendation:
        """Save gift recommendation.

        Args:
            recipient_id: Recipient ID.
            gift_item_id: Gift item ID.
            score: Recommendation score.
            occasion: Optional occasion type.
            price_range: Optional price range category.
            reasoning: Optional reasoning text.

        Returns:
            Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                recipient_id=recipient_id,
                gift_item_id=gift_item_id,
                score=score,
                occasion=occasion,
                price_range=price_range,
                reasoning=reasoning,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_recommendations(
        self,
        recipient_id: int,
        limit: Optional[int] = None,
    ) -> List[Recommendation]:
        """Get recommendations for recipient.

        Args:
            recipient_id: Recipient ID.
            limit: Optional limit on number of results.

        Returns:
            List of Recommendation objects ordered by score.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Recommendation)
                .filter(Recommendation.recipient_id == recipient_id)
                .order_by(Recommendation.score.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
