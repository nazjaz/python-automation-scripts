"""Test suite for content performance monitoring system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import load_config, get_settings
from src.database import DatabaseManager, ContentPost, ContentMetrics, ContentAnalysis
from src.metrics_analyzer import MetricsAnalyzer
from src.platform_connector import (
    PlatformManager,
    FacebookConnector,
    TwitterConnector,
)
from src.top_content_identifier import TopContentIdentifier
from src.strategy_recommender import StrategyRecommender
from src.report_generator import ReportGenerator


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
        "platforms": [
            {
                "name": "facebook",
                "enabled": True,
                "metrics": ["likes", "comments", "shares", "views", "reach"],
                "weight": {"engagement": 0.4, "reach": 0.3, "views": 0.3},
            },
            {
                "name": "twitter",
                "enabled": True,
                "metrics": ["likes", "retweets", "replies", "views", "impressions"],
                "weight": {"engagement": 0.5, "reach": 0.3, "views": 0.2},
            },
        ],
        "analysis": {
            "top_content_count": 10,
            "analysis_period_days": 30,
            "engagement_threshold": 0.05,
        },
        "strategy": {
            "recommendation_count": 5,
            "trend_analysis_days": 7,
        },
        "reporting": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "reports",
        },
    }


@pytest.fixture
def sample_content_post(test_db):
    """Create sample content post for testing."""
    post = test_db.add_content_post(
        platform="facebook",
        content_id="test_post_1",
        title="Test Post",
        content_type="image",
        posted_at=datetime.utcnow() - timedelta(days=1),
    )
    test_db.add_metrics(
        content_post_id=post.id,
        platform="facebook",
        metrics={
            "likes": 100,
            "comments": 20,
            "shares": 15,
            "views": 1000,
            "reach": 800,
        },
    )
    return post


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            posts = session.query(ContentPost).all()
            assert len(posts) == 0
        finally:
            session.close()

    def test_add_content_post(self, test_db):
        """Test adding content post."""
        post = test_db.add_content_post(
            platform="facebook",
            content_id="test_1",
            title="Test",
            content_type="video",
        )
        assert post.id is not None
        assert post.platform == "facebook"
        assert post.content_id == "test_1"

    def test_add_metrics(self, test_db):
        """Test adding metrics."""
        post = test_db.add_content_post(
            platform="twitter", content_id="tweet_1"
        )
        metrics = test_db.add_metrics(
            content_post_id=post.id,
            platform="twitter",
            metrics={"likes": 50, "retweets": 10},
        )
        assert len(metrics) == 2

    def test_get_metrics_for_post(self, test_db, sample_content_post):
        """Test retrieving metrics for post."""
        metrics = test_db.get_metrics_for_post(sample_content_post.id)
        assert "likes" in metrics
        assert metrics["likes"] == 100

    def test_save_analysis(self, test_db, sample_content_post):
        """Test saving analysis results."""
        analysis = test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
            reach_score=0.8,
        )
        assert analysis.id is not None
        assert analysis.overall_score == 0.75

    def test_get_top_content(self, test_db, sample_content_post):
        """Test getting top content."""
        test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
        )
        top_content = test_db.get_top_content(limit=10)
        assert len(top_content) == 1
        assert top_content[0].overall_score == 0.75


class TestMetricsAnalyzer:
    """Test metrics analyzer functionality."""

    def test_calculate_engagement_score(self, test_db, sample_config):
        """Test engagement score calculation."""
        analyzer = MetricsAnalyzer(test_db, sample_config["platforms"])
        metrics = {"likes": 100, "comments": 20, "shares": 15, "views": 1000}
        score = analyzer.calculate_engagement_score(metrics, "facebook")
        assert 0.0 <= score <= 1.0

    def test_calculate_overall_score(self, test_db, sample_config):
        """Test overall score calculation."""
        analyzer = MetricsAnalyzer(test_db, sample_config["platforms"])
        score = analyzer.calculate_overall_score(
            engagement_score=0.5, platform="facebook", reach_score=0.6, views_score=0.7
        )
        assert 0.0 <= score <= 1.0

    def test_analyze_content(self, test_db, sample_config, sample_content_post):
        """Test content analysis."""
        analyzer = MetricsAnalyzer(test_db, sample_config["platforms"])
        analysis = analyzer.analyze_content(sample_content_post.id, "facebook")
        assert "engagement_score" in analysis
        assert "overall_score" in analysis
        assert 0.0 <= analysis["overall_score"] <= 1.0


class TestTopContentIdentifier:
    """Test top content identifier functionality."""

    def test_get_top_content(self, test_db, sample_content_post):
        """Test getting top content."""
        test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
        )
        identifier = TopContentIdentifier(test_db, top_count=10)
        top_content = identifier.get_top_content()
        assert len(top_content) == 1
        assert top_content[0]["overall_score"] == 0.75


class TestStrategyRecommender:
    """Test strategy recommender functionality."""

    def test_analyze_content_trends(self, test_db, sample_config, sample_content_post):
        """Test content trend analysis."""
        identifier = TopContentIdentifier(test_db)
        recommender = StrategyRecommender(test_db, identifier, sample_config)
        trends = recommender.analyze_content_trends(days=7)
        assert "total_posts" in trends
        assert "avg_engagement" in trends

    def test_generate_recommendations(self, test_db, sample_config, sample_content_post):
        """Test recommendation generation."""
        test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
        )
        identifier = TopContentIdentifier(test_db)
        recommender = StrategyRecommender(test_db, identifier, sample_config)
        recommendations = recommender.generate_recommendations()
        assert isinstance(recommendations, list)


class TestPlatformConnector:
    """Test platform connector functionality."""

    def test_facebook_connector_normalize(self, test_db):
        """Test Facebook metrics normalization."""
        connector = FacebookConnector(test_db)
        raw_data = {"likes": 100, "comments": 20, "shares": 15, "views": 1000, "reach": 800}
        normalized = connector.normalize_metrics(raw_data)
        assert "likes" in normalized
        assert normalized["likes"] == 100

    def test_twitter_connector_normalize(self, test_db):
        """Test Twitter metrics normalization."""
        connector = TwitterConnector(test_db)
        raw_data = {
            "like_count": 50,
            "retweet_count": 10,
            "reply_count": 5,
            "view_count": 500,
            "impression_count": 400,
        }
        normalized = connector.normalize_metrics(raw_data)
        assert "likes" in normalized
        assert normalized["likes"] == 50


class TestReportGenerator:
    """Test report generator functionality."""

    def test_generate_csv_report(self, test_db, sample_config, sample_content_post, tmp_path):
        """Test CSV report generation."""
        test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
        )
        identifier = TopContentIdentifier(test_db)
        recommender = StrategyRecommender(test_db, identifier, sample_config)
        sample_config["reporting"]["output_directory"] = str(tmp_path)
        generator = ReportGenerator(test_db, identifier, recommender, sample_config)
        report_path = generator.generate_csv_report()
        assert report_path.exists()

    def test_generate_html_report(self, test_db, sample_config, sample_content_post, tmp_path):
        """Test HTML report generation."""
        test_db.save_analysis(
            content_post_id=sample_content_post.id,
            platform="facebook",
            engagement_score=0.15,
            overall_score=0.75,
        )
        identifier = TopContentIdentifier(test_db)
        recommender = StrategyRecommender(test_db, identifier, sample_config)
        sample_config["reporting"]["output_directory"] = str(tmp_path)
        generator = ReportGenerator(test_db, identifier, recommender, sample_config)
        report_path = generator.generate_html_report()
        assert report_path.exists()
        assert report_path.suffix == ".html"


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "platforms" in config
            assert "analysis" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
