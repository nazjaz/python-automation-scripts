"""Test suite for gift recommendation system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Recipient, Preference, PurchaseHistory, GiftItem
from src.preference_analyzer import PreferenceAnalyzer
from src.purchase_analyzer import PurchaseAnalyzer
from src.occasion_handler import OccasionHandler
from src.price_filter import PriceFilter
from src.recommendation_engine import RecommendationEngine


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
        "recipients": {
            "default_preferences": {
                "categories": [],
                "price_range": {"min": 0.0, "max": 1000.0},
            },
        },
        "gift_catalog": {
            "categories": ["electronics", "books", "clothing"],
        },
        "recommendations": {
            "max_recommendations": 10,
            "min_score_threshold": 0.3,
            "preference_weight": 0.4,
            "purchase_history_weight": 0.3,
            "occasion_weight": 0.2,
            "price_weight": 0.1,
        },
        "occasions": {
            "types": ["birthday", "anniversary"],
            "occasion_multipliers": {
                "birthday": 1.2,
                "anniversary": 1.15,
            },
        },
        "price_ranges": {
            "budget": 0.0,
            "low": 25.0,
            "medium": 100.0,
            "high": 500.0,
            "premium": 1000.0,
        },
    }


@pytest.fixture
def sample_recipient(test_db):
    """Create sample recipient for testing."""
    recipient = test_db.add_recipient(
        name="John Doe",
        email="john@example.com",
        age=30,
        relationship="friend",
    )
    return recipient


@pytest.fixture
def sample_gift_items(test_db):
    """Create sample gift items for testing."""
    items = []
    items.append(
        test_db.add_gift_item(
            name="Wireless Headphones",
            category="electronics",
            price=99.99,
            description="High-quality wireless headphones",
            brand="TechBrand",
        )
    )
    items.append(
        test_db.add_gift_item(
            name="Programming Book",
            category="books",
            price=29.99,
            description="Learn Python programming",
        )
    )
    return items


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            recipients = session.query(Recipient).all()
            assert len(recipients) == 0
        finally:
            session.close()

    def test_add_recipient(self, test_db):
        """Test adding recipient."""
        recipient = test_db.add_recipient(
            name="Jane Smith", email="jane@example.com", age=25
        )
        assert recipient.id is not None
        assert recipient.name == "Jane Smith"
        assert recipient.email == "jane@example.com"

    def test_add_preference(self, test_db, sample_recipient):
        """Test adding preference."""
        preference = test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            interest="gadgets",
            priority=5,
        )
        assert preference.id is not None
        assert preference.category == "electronics"

    def test_add_purchase(self, test_db, sample_recipient):
        """Test adding purchase history."""
        purchase = test_db.add_purchase(
            recipient_id=sample_recipient.id,
            item_name="Smart Watch",
            purchase_date=datetime.utcnow() - timedelta(days=30),
            category="electronics",
            price=199.99,
            rating=5,
        )
        assert purchase.id is not None
        assert purchase.item_name == "Smart Watch"

    def test_add_gift_item(self, test_db):
        """Test adding gift item."""
        item = test_db.add_gift_item(
            name="Test Item",
            category="electronics",
            price=50.0,
        )
        assert item.id is not None
        assert item.name == "Test Item"

    def test_get_preferences(self, test_db, sample_recipient):
        """Test getting preferences."""
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            priority=5,
        )
        preferences = test_db.get_preferences(sample_recipient.id)
        assert len(preferences) == 1
        assert preferences[0].category == "electronics"


class TestPreferenceAnalyzer:
    """Test preference analyzer functionality."""

    def test_get_preference_scores(self, test_db, sample_recipient):
        """Test preference score calculation."""
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            priority=5,
        )
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="books",
            priority=3,
        )

        analyzer = PreferenceAnalyzer(test_db)
        scores = analyzer.get_preference_scores(sample_recipient.id)
        assert "electronics" in scores
        assert "books" in scores
        assert scores["electronics"] > scores["books"]

    def test_get_top_categories(self, test_db, sample_recipient):
        """Test getting top categories."""
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            priority=5,
        )
        analyzer = PreferenceAnalyzer(test_db)
        top_categories = analyzer.get_top_categories(sample_recipient.id)
        assert "electronics" in top_categories


class TestPurchaseAnalyzer:
    """Test purchase analyzer functionality."""

    def test_get_category_frequency(self, test_db, sample_recipient):
        """Test category frequency calculation."""
        test_db.add_purchase(
            recipient_id=sample_recipient.id,
            item_name="Item 1",
            purchase_date=datetime.utcnow() - timedelta(days=10),
            category="electronics",
        )
        test_db.add_purchase(
            recipient_id=sample_recipient.id,
            item_name="Item 2",
            purchase_date=datetime.utcnow() - timedelta(days=20),
            category="electronics",
        )

        analyzer = PurchaseAnalyzer(test_db)
        frequency = analyzer.get_category_frequency(sample_recipient.id)
        assert frequency["electronics"] == 2

    def test_get_average_price(self, test_db, sample_recipient):
        """Test average price calculation."""
        test_db.add_purchase(
            recipient_id=sample_recipient.id,
            item_name="Item 1",
            purchase_date=datetime.utcnow(),
            category="electronics",
            price=100.0,
        )
        test_db.add_purchase(
            recipient_id=sample_recipient.id,
            item_name="Item 2",
            purchase_date=datetime.utcnow(),
            category="electronics",
            price=200.0,
        )

        analyzer = PurchaseAnalyzer(test_db)
        avg_price = analyzer.get_average_price(sample_recipient.id, "electronics")
        assert avg_price == 150.0


class TestOccasionHandler:
    """Test occasion handler functionality."""

    def test_get_occasion_multiplier(self, sample_config):
        """Test occasion multiplier retrieval."""
        handler = OccasionHandler(sample_config)
        multiplier = handler.get_occasion_multiplier("birthday")
        assert multiplier == 1.2

    def test_is_valid_occasion(self, sample_config):
        """Test occasion validation."""
        handler = OccasionHandler(sample_config)
        assert handler.is_valid_occasion("birthday")
        assert not handler.is_valid_occasion("invalid")


class TestPriceFilter:
    """Test price filter functionality."""

    def test_get_price_range_category(self, sample_config):
        """Test price range category determination."""
        filter_obj = PriceFilter(sample_config)
        assert filter_obj.get_price_range_category(10.0) == "low"
        assert filter_obj.get_price_range_category(50.0) == "medium"
        assert filter_obj.get_price_range_category(200.0) == "high"

    def test_filter_by_price_range(self, sample_config, sample_gift_items):
        """Test price range filtering."""
        filter_obj = PriceFilter(sample_config)
        filtered = filter_obj.filter_by_price_range(
            sample_gift_items, min_price=50.0, max_price=150.0
        )
        assert len(filtered) == 1
        assert filtered[0].name == "Wireless Headphones"


class TestRecommendationEngine:
    """Test recommendation engine functionality."""

    def test_calculate_item_score(
        self, test_db, sample_config, sample_recipient, sample_gift_items
    ):
        """Test item score calculation."""
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            priority=5,
        )

        engine = RecommendationEngine(test_db, sample_config)
        score = engine.calculate_item_score(
            sample_gift_items[0], sample_recipient.id, occasion="birthday"
        )
        assert 0.0 <= score <= 1.0

    def test_generate_recommendations(
        self, test_db, sample_config, sample_recipient, sample_gift_items
    ):
        """Test recommendation generation."""
        test_db.add_preference(
            recipient_id=sample_recipient.id,
            category="electronics",
            priority=5,
        )

        engine = RecommendationEngine(test_db, sample_config)
        recommendations = engine.generate_recommendations(
            recipient_id=sample_recipient.id,
            occasion="birthday",
            max_recommendations=5,
        )
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "recipients" in config
            assert "recommendations" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
