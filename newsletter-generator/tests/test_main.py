"""Test suite for newsletter generator system."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Subscriber,
    Article,
    Newsletter,
    NewsletterItem,
)
from src.article_curator import ArticleCurator
from src.layout_formatter import LayoutFormatter
from src.personalization_engine import PersonalizationEngine
from src.distribution_scheduler import DistributionScheduler


@pytest.fixture
def test_db():
    """Create test database."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "newsletter": {
            "max_articles_per_newsletter": 10,
            "min_articles_per_newsletter": 3,
        },
        "content_curation": {
            "min_quality_score": 0.6,
            "max_article_age_days": 30,
            "curation_criteria": ["relevance", "recency", "quality_score"],
        },
        "personalization": {
            "enabled": True,
            "use_subscriber_preferences": True,
            "use_reading_history": True,
        },
        "layout": {
            "template": "templates/newsletter_template.html",
            "sections": ["header", "greeting", "article_list"],
        },
        "distribution": {
            "default_send_time": "09:00",
            "batch_size": 100,
        },
    }


@pytest.fixture
def sample_subscriber(test_db):
    """Create sample subscriber for testing."""
    subscriber = test_db.add_subscriber(
        subscriber_id="SUB001",
        email="test@example.com",
        name="Test Subscriber",
        segment="all",
    )
    return subscriber


@pytest.fixture
def sample_article(test_db):
    """Create sample article for testing."""
    article = test_db.add_article(
        article_id="ART001",
        title="Test Article",
        summary="Test article summary",
        category="Technology",
        quality_score=0.8,
        published_date=datetime.utcnow(),
    )
    return article


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            subscribers = session.query(Subscriber).all()
            assert len(subscribers) == 0
        finally:
            session.close()

    def test_add_subscriber(self, test_db):
        """Test adding subscriber."""
        subscriber = test_db.add_subscriber(
            subscriber_id="SUB001",
            email="test@example.com",
            name="Test User",
        )
        assert subscriber.id is not None
        assert subscriber.subscriber_id == "SUB001"

    def test_add_article(self, test_db):
        """Test adding article."""
        article = test_db.add_article(
            article_id="ART001",
            title="Test Article",
            category="Technology",
            quality_score=0.8,
        )
        assert article.id is not None
        assert article.article_id == "ART001"


class TestArticleCurator:
    """Test article curator functionality."""

    def test_curate_articles(self, test_db, sample_config, sample_article):
        """Test article curation."""
        curator = ArticleCurator(test_db, sample_config)
        articles = curator.curate_articles(count=5)

        assert isinstance(articles, list)


class TestLayoutFormatter:
    """Test layout formatter functionality."""

    def test_format_newsletter(self, test_db, sample_config, sample_article):
        """Test newsletter formatting."""
        newsletter = test_db.add_newsletter(
            newsletter_id="NEWS001",
            title="Test Newsletter",
        )

        formatter = LayoutFormatter(test_db, sample_config)
        html = formatter.format_newsletter(newsletter, [sample_article])

        assert isinstance(html, str)
        assert newsletter.title in html


class TestPersonalizationEngine:
    """Test personalization engine functionality."""

    def test_personalize_articles(self, test_db, sample_config, sample_subscriber, sample_article):
        """Test article personalization."""
        personalizer = PersonalizationEngine(test_db, sample_config)
        personalized = personalizer.personalize_articles(sample_subscriber.id, [sample_article])

        assert isinstance(personalized, list)


class TestDistributionScheduler:
    """Test distribution scheduler functionality."""

    def test_schedule_distribution(self, test_db, sample_config):
        """Test distribution scheduling."""
        newsletter = test_db.add_newsletter(
            newsletter_id="NEWS001",
            title="Test Newsletter",
        )

        scheduler = DistributionScheduler(test_db, sample_config)
        result = scheduler.schedule_distribution(newsletter.id)

        assert result["success"] is True


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "newsletter" in config
            assert "content_curation" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
