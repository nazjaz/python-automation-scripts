"""Database models and operations for customer review processing."""

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


class Review(Base):
    """Customer review model."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer)
    product_id = Column(String(100))
    product_name = Column(String(200))
    customer_id = Column(String(100))
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))

    themes = relationship("Theme", back_populates="review", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")


class Theme(Base):
    """Extracted theme from review."""

    __tablename__ = "themes"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    theme_text = Column(String(200), nullable=False)
    relevance_score = Column(Float)
    category = Column(String(100))

    review = relationship("Review", back_populates="themes")


class Issue(Base):
    """Product issue identified from review."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    issue_text = Column(String(200), nullable=False)
    severity = Column(String(20))
    category = Column(String(100))
    frequency = Column(Integer, default=1)

    review = relationship("Review", back_populates="issues")


class Recommendation(Base):
    """Improvement recommendation generated from analysis."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True)
    recommendation_text = Column(Text, nullable=False)
    priority = Column(String(20))
    category = Column(String(100))
    impact_score = Column(Float)
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

    def add_review(
        self,
        review_text: str,
        rating: Optional[int] = None,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        customer_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Review:
        """Add a new review to the database.

        Args:
            review_text: Review text content.
            rating: Review rating (1-5).
            product_id: Product identifier.
            product_name: Product name.
            customer_id: Customer identifier.
            source: Review source (e.g., 'amazon', 'google').

        Returns:
            Created Review object.
        """
        session = self.get_session()
        try:
            review = Review(
                review_text=review_text,
                rating=rating,
                product_id=product_id,
                product_name=product_name,
                customer_id=customer_id,
                source=source,
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()

    def get_unprocessed_reviews(self, limit: Optional[int] = None) -> List[Review]:
        """Get reviews that have not been processed.

        Args:
            limit: Maximum number of reviews to return.

        Returns:
            List of unprocessed Review objects.
        """
        session = self.get_session()
        try:
            query = session.query(Review).filter(Review.processed_at.is_(None))
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_review_sentiment(
        self, review_id: int, sentiment_score: float, sentiment_label: str
    ) -> None:
        """Update review sentiment information.

        Args:
            review_id: Review ID.
            sentiment_score: Sentiment score (-1.0 to 1.0).
            sentiment_label: Sentiment label (positive, negative, neutral).
        """
        session = self.get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if review:
                review.sentiment_score = sentiment_score
                review.sentiment_label = sentiment_label
                review.processed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def add_theme(
        self, review_id: int, theme_text: str, relevance_score: float, category: str
    ) -> Theme:
        """Add theme to review.

        Args:
            review_id: Review ID.
            theme_text: Theme text.
            relevance_score: Theme relevance score.
            category: Theme category.

        Returns:
            Created Theme object.
        """
        session = self.get_session()
        try:
            theme = Theme(
                review_id=review_id,
                theme_text=theme_text,
                relevance_score=relevance_score,
                category=category,
            )
            session.add(theme)
            session.commit()
            session.refresh(theme)
            return theme
        finally:
            session.close()

    def add_issue(
        self,
        review_id: int,
        issue_text: str,
        severity: str,
        category: str,
        frequency: int = 1,
    ) -> Issue:
        """Add issue to review.

        Args:
            review_id: Review ID.
            issue_text: Issue description.
            severity: Issue severity (low, medium, high, critical).
            category: Issue category.
            frequency: Issue frequency count.

        Returns:
            Created Issue object.
        """
        session = self.get_session()
        try:
            issue = Issue(
                review_id=review_id,
                issue_text=issue_text,
                severity=severity,
                category=category,
                frequency=frequency,
            )
            session.add(issue)
            session.commit()
            session.refresh(issue)
            return issue
        finally:
            session.close()

    def add_recommendation(
        self,
        recommendation_text: str,
        priority: str,
        category: str,
        impact_score: float,
        issue_id: Optional[int] = None,
    ) -> Recommendation:
        """Add improvement recommendation.

        Args:
            recommendation_text: Recommendation description.
            priority: Recommendation priority (low, medium, high, urgent).
            category: Recommendation category.
            impact_score: Expected impact score.
            issue_id: Associated issue ID.

        Returns:
            Created Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                recommendation_text=recommendation_text,
                priority=priority,
                category=category,
                impact_score=impact_score,
                issue_id=issue_id,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_reviews_by_sentiment(
        self, sentiment_label: str, limit: Optional[int] = None
    ) -> List[Review]:
        """Get reviews by sentiment label.

        Args:
            sentiment_label: Sentiment label to filter by.
            limit: Maximum number of reviews to return.

        Returns:
            List of Review objects.
        """
        session = self.get_session()
        try:
            query = session.query(Review).filter(Review.sentiment_label == sentiment_label)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_all_issues(self, limit: Optional[int] = None) -> List[Issue]:
        """Get all identified issues.

        Args:
            limit: Maximum number of issues to return.

        Returns:
            List of Issue objects.
        """
        session = self.get_session()
        try:
            query = session.query(Issue)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_all_recommendations(self, limit: Optional[int] = None) -> List[Recommendation]:
        """Get all recommendations.

        Args:
            limit: Maximum number of recommendations to return.

        Returns:
            List of Recommendation objects.
        """
        session = self.get_session()
        try:
            query = session.query(Recommendation).order_by(Recommendation.impact_score.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
