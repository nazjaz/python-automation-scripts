"""Database models and operations for content recommendation."""

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


class User(Base):
    """User information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(200), nullable=False)
    email = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    viewing_history = relationship("ViewingHistory", back_populates="user", cascade="all, delete-orphan")
    engagement_patterns = relationship("EngagementPattern", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class Content(Base):
    """Content item."""

    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    content_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content_type = Column(String(100), nullable=False)
    category = Column(String(100))
    tags = Column(Text)
    description = Column(Text)
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    viewing_history = relationship("ViewingHistory", back_populates="content", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="content", cascade="all, delete-orphan")


class UserPreference(Base):
    """User preference."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_type = Column(String(100), nullable=False)
    preference_value = Column(String(200), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class ViewingHistory(Base):
    """User viewing history."""

    __tablename__ = "viewing_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    watch_duration_minutes = Column(Integer)
    completion_percentage = Column(Float)
    rating = Column(Float)

    user = relationship("User", back_populates="viewing_history")
    content = relationship("Content", back_populates="viewing_history")


class EngagementPattern(Base):
    """User engagement pattern."""

    __tablename__ = "engagement_patterns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String(100), nullable=False)
    engagement_metric = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="engagement_patterns")


class Recommendation(Base):
    """Content recommendation."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    recommendation_score = Column(Float, nullable=False)
    recommendation_reason = Column(Text)
    recommendation_type = Column(String(100))
    generated_at = Column(DateTime, default=datetime.utcnow)
    shown_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="recommendations")
    content = relationship("Content", back_populates="recommendations")


class RecommendationMetric(Base):
    """Recommendation performance metric."""

    __tablename__ = "recommendation_metrics"

    id = Column(Integer, primary_key=True)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_recommendations = Column(Integer, default=0)
    shown_recommendations = Column(Integer, default=0)
    clicked_recommendations = Column(Integer, default=0)
    converted_recommendations = Column(Integer, default=0)
    average_score = Column(Float)
    click_through_rate = Column(Float)
    conversion_rate = Column(Float)
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

    def add_user(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
    ) -> User:
        """Add a new user.

        Args:
            user_id: User identifier.
            username: Username.
            email: Email address.

        Returns:
            Created User object.
        """
        session = self.get_session()
        try:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by user ID.

        Args:
            user_id: User identifier.

        Returns:
            User object or None.
        """
        session = self.get_session()
        try:
            return session.query(User).filter(User.user_id == user_id).first()
        finally:
            session.close()

    def add_content(
        self,
        content_id: str,
        title: str,
        content_type: str,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
    ) -> Content:
        """Add content item.

        Args:
            content_id: Content identifier.
            title: Content title.
            content_type: Content type (video, article, podcast, etc.).
            category: Content category.
            tags: Tags as comma-separated string.
            description: Content description.
            duration_minutes: Duration in minutes.

        Returns:
            Created Content object.
        """
        session = self.get_session()
        try:
            content = Content(
                content_id=content_id,
                title=title,
                content_type=content_type,
                category=category,
                tags=tags,
                description=description,
                duration_minutes=duration_minutes,
            )
            session.add(content)
            session.commit()
            session.refresh(content)
            return content
        finally:
            session.close()

    def get_content(self, content_id: str) -> Optional[Content]:
        """Get content by content ID.

        Args:
            content_id: Content identifier.

        Returns:
            Content object or None.
        """
        session = self.get_session()
        try:
            return session.query(Content).filter(Content.content_id == content_id).first()
        finally:
            session.close()

    def add_user_preference(
        self,
        user_id: int,
        preference_type: str,
        preference_value: str,
        weight: float = 1.0,
    ) -> UserPreference:
        """Add or update user preference.

        Args:
            user_id: User ID.
            preference_type: Preference type (category, tag, content_type, etc.).
            preference_value: Preference value.
            weight: Preference weight.

        Returns:
            Created or updated UserPreference object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(UserPreference)
                .filter(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_type == preference_type,
                    UserPreference.preference_value == preference_value,
                )
                .first()
            )

            if existing:
                existing.weight = weight
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                preference = UserPreference(
                    user_id=user_id,
                    preference_type=preference_type,
                    preference_value=preference_value,
                    weight=weight,
                )
                session.add(preference)
                session.commit()
                session.refresh(preference)
                return preference
        finally:
            session.close()

    def get_user_preferences(
        self, user_id: int, preference_type: Optional[str] = None
    ) -> List[UserPreference]:
        """Get user preferences.

        Args:
            user_id: User ID.
            preference_type: Optional preference type to filter by.

        Returns:
            List of UserPreference objects.
        """
        session = self.get_session()
        try:
            query = session.query(UserPreference).filter(UserPreference.user_id == user_id)
            if preference_type:
                query = query.filter(UserPreference.preference_type == preference_type)
            return query.order_by(UserPreference.weight.desc()).all()
        finally:
            session.close()

    def add_viewing_history(
        self,
        user_id: int,
        content_id: int,
        watch_duration_minutes: Optional[int] = None,
        completion_percentage: Optional[float] = None,
        rating: Optional[float] = None,
    ) -> ViewingHistory:
        """Add viewing history entry.

        Args:
            user_id: User ID.
            content_id: Content ID.
            watch_duration_minutes: Watch duration in minutes.
            completion_percentage: Completion percentage (0.0 to 100.0).
            rating: Rating (1.0 to 5.0).

        Returns:
            Created ViewingHistory object.
        """
        session = self.get_session()
        try:
            history = ViewingHistory(
                user_id=user_id,
                content_id=content_id,
                watch_duration_minutes=watch_duration_minutes,
                completion_percentage=completion_percentage,
                rating=rating,
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            return history
        finally:
            session.close()

    def get_user_viewing_history(
        self, user_id: int, limit: Optional[int] = None
    ) -> List[ViewingHistory]:
        """Get user viewing history.

        Args:
            user_id: User ID.
            limit: Maximum number of entries to return.

        Returns:
            List of ViewingHistory objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(ViewingHistory)
                .filter(ViewingHistory.user_id == user_id)
                .order_by(ViewingHistory.viewed_at.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_engagement_pattern(
        self,
        user_id: int,
        content_type: str,
        engagement_metric: str,
        metric_value: float,
        time_window_start: datetime,
        time_window_end: datetime,
    ) -> EngagementPattern:
        """Add engagement pattern.

        Args:
            user_id: User ID.
            content_type: Content type.
            engagement_metric: Engagement metric (views, watch_time, completion_rate, etc.).
            metric_value: Metric value.
            time_window_start: Start of time window.
            time_window_end: End of time window.

        Returns:
            Created EngagementPattern object.
        """
        session = self.get_session()
        try:
            pattern = EngagementPattern(
                user_id=user_id,
                content_type=content_type,
                engagement_metric=engagement_metric,
                metric_value=metric_value,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
            )
            session.add(pattern)
            session.commit()
            session.refresh(pattern)
            return pattern
        finally:
            session.close()

    def get_user_engagement_patterns(
        self, user_id: int, content_type: Optional[str] = None
    ) -> List[EngagementPattern]:
        """Get user engagement patterns.

        Args:
            user_id: User ID.
            content_type: Optional content type to filter by.

        Returns:
            List of EngagementPattern objects.
        """
        session = self.get_session()
        try:
            query = session.query(EngagementPattern).filter(EngagementPattern.user_id == user_id)
            if content_type:
                query = query.filter(EngagementPattern.content_type == content_type)
            return query.order_by(EngagementPattern.time_window_start.desc()).all()
        finally:
            session.close()

    def add_recommendation(
        self,
        user_id: int,
        content_id: int,
        recommendation_score: float,
        recommendation_reason: Optional[str] = None,
        recommendation_type: Optional[str] = None,
    ) -> Recommendation:
        """Add recommendation.

        Args:
            user_id: User ID.
            content_id: Content ID.
            recommendation_score: Recommendation score (0.0 to 1.0).
            recommendation_reason: Recommendation reason.
            recommendation_type: Recommendation type (preference_based, history_based, engagement_based, hybrid).

        Returns:
            Created Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                user_id=user_id,
                content_id=content_id,
                recommendation_score=recommendation_score,
                recommendation_reason=recommendation_reason,
                recommendation_type=recommendation_type,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_user_recommendations(
        self, user_id: int, limit: Optional[int] = None, shown_only: bool = False
    ) -> List[Recommendation]:
        """Get user recommendations.

        Args:
            user_id: User ID.
            limit: Maximum number of recommendations to return.
            shown_only: Only return shown recommendations.

        Returns:
            List of Recommendation objects ordered by score.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .order_by(Recommendation.recommendation_score.desc())
            )
            if shown_only:
                query = query.filter(Recommendation.shown_at.isnot(None))
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def mark_recommendation_shown(self, recommendation_id: int) -> None:
        """Mark recommendation as shown.

        Args:
            recommendation_id: Recommendation ID.
        """
        session = self.get_session()
        try:
            recommendation = (
                session.query(Recommendation)
                .filter(Recommendation.id == recommendation_id)
                .first()
            )
            if recommendation:
                recommendation.shown_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def mark_recommendation_clicked(self, recommendation_id: int) -> None:
        """Mark recommendation as clicked.

        Args:
            recommendation_id: Recommendation ID.
        """
        session = self.get_session()
        try:
            recommendation = (
                session.query(Recommendation)
                .filter(Recommendation.id == recommendation_id)
                .first()
            )
            if recommendation:
                recommendation.clicked_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def mark_recommendation_converted(self, recommendation_id: int) -> None:
        """Mark recommendation as converted (user viewed content).

        Args:
            recommendation_id: Recommendation ID.
        """
        session = self.get_session()
        try:
            recommendation = (
                session.query(Recommendation)
                .filter(Recommendation.id == recommendation_id)
                .first()
            )
            if recommendation:
                recommendation.converted_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def add_recommendation_metric(
        self,
        time_window_start: datetime,
        time_window_end: datetime,
        total_recommendations: int,
        shown_recommendations: int,
        clicked_recommendations: int,
        converted_recommendations: int,
        average_score: Optional[float] = None,
    ) -> RecommendationMetric:
        """Add recommendation performance metric.

        Args:
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_recommendations: Total number of recommendations.
            shown_recommendations: Number of shown recommendations.
            clicked_recommendations: Number of clicked recommendations.
            converted_recommendations: Number of converted recommendations.
            average_score: Average recommendation score.

        Returns:
            Created RecommendationMetric object.
        """
        session = self.get_session()
        try:
            click_through_rate = (
                clicked_recommendations / shown_recommendations * 100
                if shown_recommendations > 0
                else 0.0
            )
            conversion_rate = (
                converted_recommendations / clicked_recommendations * 100
                if clicked_recommendations > 0
                else 0.0
            )

            metric = RecommendationMetric(
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_recommendations=total_recommendations,
                shown_recommendations=shown_recommendations,
                clicked_recommendations=clicked_recommendations,
                converted_recommendations=converted_recommendations,
                average_score=average_score,
                click_through_rate=click_through_rate,
                conversion_rate=conversion_rate,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_recent_metrics(self, days: int = 7) -> List[RecommendationMetric]:
        """Get recent recommendation metrics.

        Args:
            days: Number of days to look back.

        Returns:
            List of RecommendationMetric objects.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)
            return (
                session.query(RecommendationMetric)
                .filter(RecommendationMetric.time_window_start >= cutoff)
                .order_by(RecommendationMetric.time_window_start.desc())
                .all()
            )
        finally:
            session.close()
