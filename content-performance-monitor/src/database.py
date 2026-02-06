"""Database models and operations for content performance data."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class ContentPost(Base):
    """Database model for content posts."""

    __tablename__ = "content_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    content_id = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(500))
    content_type = Column(String(50))
    posted_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ContentPost(id={self.id}, platform={self.platform}, content_id={self.content_id})>"


class ContentMetrics(Base):
    """Database model for content performance metrics."""

    __tablename__ = "content_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_post_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<ContentMetrics(id={self.id}, content_post_id={self.content_post_id}, "
            f"metric_name={self.metric_name}, metric_value={self.metric_value})>"
        )


class ContentAnalysis(Base):
    """Database model for content analysis results."""

    __tablename__ = "content_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_post_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    engagement_score = Column(Float, nullable=False)
    reach_score = Column(Float)
    views_score = Column(Float)
    overall_score = Column(Float, nullable=False, index=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    recommendations = Column(Text)

    def __repr__(self) -> str:
        return (
            f"<ContentAnalysis(id={self.id}, content_post_id={self.content_post_id}, "
            f"overall_score={self.overall_score})>"
        )


class DatabaseManager:
    """Manages database operations for content performance data."""

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

    def add_content_post(
        self,
        platform: str,
        content_id: str,
        title: Optional[str] = None,
        content_type: Optional[str] = None,
        posted_at: Optional[datetime] = None,
    ) -> ContentPost:
        """Add or update content post.

        Args:
            platform: Platform name (e.g., 'facebook', 'twitter').
            content_id: Unique content identifier on platform.
            title: Content title or description.
            content_type: Type of content (e.g., 'video', 'image', 'text').
            posted_at: When content was posted.

        Returns:
            ContentPost object.
        """
        session = self.get_session()
        try:
            post = (
                session.query(ContentPost)
                .filter(ContentPost.content_id == content_id)
                .first()
            )

            if post is None:
                post = ContentPost(
                    platform=platform,
                    content_id=content_id,
                    title=title,
                    content_type=content_type,
                    posted_at=posted_at or datetime.utcnow(),
                )
                session.add(post)
                session.commit()
                session.refresh(post)
            else:
                if title:
                    post.title = title
                if content_type:
                    post.content_type = content_type
                if posted_at:
                    post.posted_at = posted_at
                session.commit()
                session.refresh(post)

            return post
        finally:
            session.close()

    def add_metrics(
        self,
        content_post_id: int,
        platform: str,
        metrics: dict,
    ) -> List[ContentMetrics]:
        """Add metrics for a content post.

        Args:
            content_post_id: ID of the content post.
            platform: Platform name.
            metrics: Dictionary of metric names to values.

        Returns:
            List of ContentMetrics objects created.
        """
        session = self.get_session()
        try:
            metric_objects = []
            for metric_name, metric_value in metrics.items():
                metric_obj = ContentMetrics(
                    content_post_id=content_post_id,
                    platform=platform,
                    metric_name=metric_name,
                    metric_value=float(metric_value),
                )
                session.add(metric_obj)
                metric_objects.append(metric_obj)

            session.commit()
            for metric_obj in metric_objects:
                session.refresh(metric_obj)

            return metric_objects
        finally:
            session.close()

    def get_content_posts(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ContentPost]:
        """Get content posts with optional filtering.

        Args:
            platform: Optional platform filter.
            limit: Optional limit on number of results.
            offset: Offset for pagination.

        Returns:
            List of ContentPost objects.
        """
        session = self.get_session()
        try:
            query = session.query(ContentPost)
            if platform:
                query = query.filter(ContentPost.platform == platform)

            query = query.order_by(ContentPost.posted_at.desc())

            if limit:
                query = query.limit(limit).offset(offset)

            return query.all()
        finally:
            session.close()

    def get_metrics_for_post(
        self, content_post_id: int
    ) -> dict:
        """Get all metrics for a content post.

        Args:
            content_post_id: ID of the content post.

        Returns:
            Dictionary mapping metric names to values.
        """
        session = self.get_session()
        try:
            metrics = (
                session.query(ContentMetrics)
                .filter(ContentMetrics.content_post_id == content_post_id)
                .all()
            )

            result = {}
            for metric in metrics:
                result[metric.metric_name] = metric.metric_value

            return result
        finally:
            session.close()

    def save_analysis(
        self,
        content_post_id: int,
        platform: str,
        engagement_score: float,
        overall_score: float,
        reach_score: Optional[float] = None,
        views_score: Optional[float] = None,
        recommendations: Optional[str] = None,
    ) -> ContentAnalysis:
        """Save content analysis results.

        Args:
            content_post_id: ID of the content post.
            platform: Platform name.
            engagement_score: Calculated engagement score.
            overall_score: Overall performance score.
            reach_score: Optional reach score.
            views_score: Optional views score.
            recommendations: Optional recommendations text.

        Returns:
            ContentAnalysis object.
        """
        session = self.get_session()
        try:
            analysis = ContentAnalysis(
                content_post_id=content_post_id,
                platform=platform,
                engagement_score=engagement_score,
                reach_score=reach_score,
                views_score=views_score,
                overall_score=overall_score,
                recommendations=recommendations,
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
        finally:
            session.close()

    def get_top_content(
        self,
        platform: Optional[str] = None,
        limit: int = 10,
        days: Optional[int] = None,
    ) -> List[ContentAnalysis]:
        """Get top-performing content based on overall score.

        Args:
            platform: Optional platform filter.
            limit: Number of top content items to return.
            days: Optional number of days to look back.

        Returns:
            List of ContentAnalysis objects ordered by overall_score.
        """
        session = self.get_session()
        try:
            from datetime import timedelta

            query = session.query(ContentAnalysis)

            if platform:
                query = query.filter(ContentAnalysis.platform == platform)

            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(ContentAnalysis.analyzed_at >= cutoff_date)

            query = query.order_by(ContentAnalysis.overall_score.desc()).limit(limit)

            return query.all()
        finally:
            session.close()
