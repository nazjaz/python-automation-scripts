"""Database models and operations for newsletter generator data."""

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


class Subscriber(Base):
    """Database model for newsletter subscribers."""

    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscriber_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    preferences = Column(Text)
    demographics = Column(Text)
    segment = Column(String(100), index=True)
    active = Column(Boolean, default=True, index=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    newsletters = relationship("NewsletterDistribution", back_populates="subscriber", cascade="all, delete-orphan")
    reading_history = relationship("ReadingHistory", back_populates="subscriber", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Subscriber(id={self.id}, subscriber_id={self.subscriber_id}, email={self.email})>"


class Article(Base):
    """Database model for articles."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    author = Column(String(255))
    source = Column(String(255), index=True)
    source_url = Column(String(500))
    category = Column(String(100), index=True)
    tags = Column(Text)
    published_date = Column(DateTime, index=True)
    quality_score = Column(Float, index=True)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    newsletter_items = relationship("NewsletterItem", back_populates="article", cascade="all, delete-orphan")
    reading_history = relationship("ReadingHistory", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, article_id={self.article_id}, title={self.title})>"


class Newsletter(Base):
    """Database model for newsletters."""

    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    newsletter_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    segment = Column(String(100), index=True)
    content_html = Column(Text)
    content_text = Column(Text)
    scheduled_send_time = Column(DateTime, index=True)
    sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    items = relationship("NewsletterItem", back_populates="newsletter", cascade="all, delete-orphan")
    distributions = relationship("NewsletterDistribution", back_populates="newsletter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Newsletter(id={self.id}, newsletter_id={self.newsletter_id}, "
            f"title={self.title}, segment={self.segment})>"
        )


class NewsletterItem(Base):
    """Database model for newsletter items (articles in newsletters)."""

    __tablename__ = "newsletter_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    newsletter_id = Column(Integer, ForeignKey("newsletters.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    featured = Column(Boolean, default=False, index=True)
    personalized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    newsletter = relationship("Newsletter", back_populates="items")
    article = relationship("Article", back_populates="newsletter_items")

    def __repr__(self) -> str:
        return (
            f"<NewsletterItem(id={self.id}, newsletter_id={self.newsletter_id}, "
            f"article_id={self.article_id}, position={self.position})>"
        )


class NewsletterDistribution(Base):
    """Database model for newsletter distributions."""

    __tablename__ = "newsletter_distributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    newsletter_id = Column(Integer, ForeignKey("newsletters.id"), nullable=False, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False, index=True)
    sent_at = Column(DateTime, index=True)
    opened = Column(Boolean, default=False, index=True)
    opened_at = Column(DateTime)
    clicked = Column(Boolean, default=False, index=True)
    clicked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    newsletter = relationship("Newsletter", back_populates="distributions")
    subscriber = relationship("Subscriber", back_populates="newsletters")

    def __repr__(self) -> str:
        return (
            f"<NewsletterDistribution(id={self.id}, newsletter_id={self.newsletter_id}, "
            f"subscriber_id={self.subscriber_id}, sent_at={self.sent_at})>"
        )


class ReadingHistory(Base):
    """Database model for subscriber reading history."""

    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    read_at = Column(DateTime, default=datetime.utcnow, index=True)
    time_spent_seconds = Column(Integer)
    fully_read = Column(Boolean, default=False)

    subscriber = relationship("Subscriber", back_populates="reading_history")
    article = relationship("Article", back_populates="reading_history")

    def __repr__(self) -> str:
        return (
            f"<ReadingHistory(id={self.id}, subscriber_id={self.subscriber_id}, "
            f"article_id={self.article_id}, read_at={self.read_at})>"
        )


class DatabaseManager:
    """Manages database operations for newsletter generator data."""

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

    def add_subscriber(
        self,
        subscriber_id: str,
        email: str,
        name: Optional[str] = None,
        preferences: Optional[str] = None,
        demographics: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Subscriber:
        """Add or update subscriber.

        Args:
            subscriber_id: Subscriber ID.
            email: Subscriber email.
            name: Optional subscriber name.
            preferences: Optional preferences JSON string.
            demographics: Optional demographics JSON string.
            segment: Optional segment.

        Returns:
            Subscriber object.
        """
        session = self.get_session()
        try:
            subscriber = (
                session.query(Subscriber)
                .filter(Subscriber.subscriber_id == subscriber_id)
                .first()
            )

            if subscriber is None:
                subscriber = Subscriber(
                    subscriber_id=subscriber_id,
                    email=email,
                    name=name,
                    preferences=preferences,
                    demographics=demographics,
                    segment=segment,
                )
                session.add(subscriber)
            else:
                subscriber.email = email
                subscriber.name = name
                subscriber.preferences = preferences
                subscriber.demographics = demographics
                subscriber.segment = segment
                subscriber.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(subscriber)
            return subscriber
        finally:
            session.close()

    def add_article(
        self,
        article_id: str,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        author: Optional[str] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        published_date: Optional[datetime] = None,
        quality_score: Optional[float] = None,
        relevance_score: Optional[float] = None,
    ) -> Article:
        """Add article.

        Args:
            article_id: Article ID.
            title: Article title.
            content: Optional article content.
            summary: Optional article summary.
            author: Optional author.
            source: Optional source.
            source_url: Optional source URL.
            category: Optional category.
            tags: Optional tags.
            published_date: Optional published date.
            quality_score: Optional quality score.
            relevance_score: Optional relevance score.

        Returns:
            Article object.
        """
        session = self.get_session()
        try:
            article = Article(
                article_id=article_id,
                title=title,
                content=content,
                summary=summary,
                author=author,
                source=source,
                source_url=source_url,
                category=category,
                tags=tags,
                published_date=published_date,
                quality_score=quality_score,
                relevance_score=relevance_score,
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            return article
        finally:
            session.close()

    def add_newsletter(
        self,
        newsletter_id: str,
        title: str,
        segment: Optional[str] = None,
        content_html: Optional[str] = None,
        content_text: Optional[str] = None,
        scheduled_send_time: Optional[datetime] = None,
    ) -> Newsletter:
        """Add newsletter.

        Args:
            newsletter_id: Newsletter ID.
            title: Newsletter title.
            segment: Optional segment.
            content_html: Optional HTML content.
            content_text: Optional text content.
            scheduled_send_time: Optional scheduled send time.

        Returns:
            Newsletter object.
        """
        session = self.get_session()
        try:
            newsletter = Newsletter(
                newsletter_id=newsletter_id,
                title=title,
                segment=segment,
                content_html=content_html,
                content_text=content_text,
                scheduled_send_time=scheduled_send_time,
            )
            session.add(newsletter)
            session.commit()
            session.refresh(newsletter)
            return newsletter
        finally:
            session.close()

    def add_newsletter_item(
        self,
        newsletter_id: int,
        article_id: int,
        position: int,
        featured: bool = False,
        personalized: bool = False,
    ) -> NewsletterItem:
        """Add newsletter item.

        Args:
            newsletter_id: Newsletter ID.
            article_id: Article ID.
            position: Item position in newsletter.
            featured: Whether item is featured.
            personalized: Whether item is personalized.

        Returns:
            NewsletterItem object.
        """
        session = self.get_session()
        try:
            item = NewsletterItem(
                newsletter_id=newsletter_id,
                article_id=article_id,
                position=position,
                featured=featured,
                personalized=personalized,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def add_distribution(
        self,
        newsletter_id: int,
        subscriber_id: int,
        sent_at: Optional[datetime] = None,
    ) -> NewsletterDistribution:
        """Add newsletter distribution.

        Args:
            newsletter_id: Newsletter ID.
            subscriber_id: Subscriber ID.
            sent_at: Optional sent timestamp.

        Returns:
            NewsletterDistribution object.
        """
        session = self.get_session()
        try:
            distribution = NewsletterDistribution(
                newsletter_id=newsletter_id,
                subscriber_id=subscriber_id,
                sent_at=sent_at,
            )
            session.add(distribution)
            session.commit()
            session.refresh(distribution)
            return distribution
        finally:
            session.close()

    def get_subscribers(
        self,
        segment: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Subscriber]:
        """Get subscribers with optional filtering.

        Args:
            segment: Optional segment filter.
            active_only: Whether to return only active subscribers.
            limit: Optional limit on number of results.

        Returns:
            List of Subscriber objects.
        """
        session = self.get_session()
        try:
            query = session.query(Subscriber)

            if active_only:
                query = query.filter(Subscriber.active == True)

            if segment:
                query = query.filter(Subscriber.segment == segment)

            query = query.order_by(Subscriber.subscribed_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_articles(
        self,
        category: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[Article]:
        """Get articles with optional filtering.

        Args:
            category: Optional category filter.
            min_quality_score: Optional minimum quality score filter.
            limit: Optional limit on number of results.

        Returns:
            List of Article objects.
        """
        session = self.get_session()
        try:
            query = session.query(Article)

            if category:
                query = query.filter(Article.category == category)

            if min_quality_score is not None:
                query = query.filter(Article.quality_score >= min_quality_score)

            query = query.order_by(Article.published_date.desc() if Article.published_date else Article.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_unsent_newsletters(
        self,
        limit: Optional[int] = None,
    ) -> List[Newsletter]:
        """Get unsent newsletters.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of unsent Newsletter objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Newsletter)
                .filter(Newsletter.sent == False)
                .order_by(Newsletter.scheduled_send_time)
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
