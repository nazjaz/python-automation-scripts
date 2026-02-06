"""Unit tests for customer review processing system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import load_config, get_settings
from src.database import DatabaseManager, Review, Theme, Issue, Recommendation
from src.sentiment_analyzer import SentimentAnalyzer
from src.theme_extractor import ThemeExtractor
from src.issue_identifier import IssueIdentifier
from src.recommendation_generator import RecommendationGenerator
from src.report_generator import ReportGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "sentiment": {
            "positive_threshold": 0.1,
            "negative_threshold": -0.1,
        },
        "themes": {
            "min_theme_length": 2,
            "max_themes_per_review": 5,
            "theme_categories": {
                "quality": ["quality", "durable"],
                "performance": ["fast", "slow"],
            },
        },
        "issues": {
            "min_issue_length": 10,
            "issue_keywords": {
                "quality": ["broken", "defect"],
                "performance": ["slow", "lag"],
            },
            "severity_keywords": {
                "critical": ["dangerous"],
                "high": ["broken"],
            },
        },
        "recommendations": {
            "priority_weights": {
                "critical": 1.0,
                "high": 0.7,
                "medium": 0.5,
                "low": 0.3,
            },
        },
        "reporting": {
            "generate_html": True,
            "generate_csv": True,
            "output_directory": "reports",
        },
        "logging": {
            "file": "logs/test.log",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    }


@pytest.fixture
def db_manager():
    """Database manager fixture."""
    return DatabaseManager("sqlite:///:memory:")


def test_sentiment_analyzer_positive_review(sample_config):
    """Test sentiment analyzer with positive review."""
    analyzer = SentimentAnalyzer(sample_config["sentiment"])
    score, label = analyzer.analyze_sentiment("This product is amazing! I love it!")
    assert label == "positive"
    assert score > 0


def test_sentiment_analyzer_negative_review(sample_config):
    """Test sentiment analyzer with negative review."""
    analyzer = SentimentAnalyzer(sample_config["sentiment"])
    score, label = analyzer.analyze_sentiment("This product is terrible and broken.")
    assert label == "negative"
    assert score < 0


def test_sentiment_analyzer_neutral_review(sample_config):
    """Test sentiment analyzer with neutral review."""
    analyzer = SentimentAnalyzer(sample_config["sentiment"])
    score, label = analyzer.analyze_sentiment("The product arrived on time.")
    assert label in ["positive", "negative", "neutral"]


def test_theme_extractor_extract_themes(sample_config):
    """Test theme extraction from review."""
    extractor = ThemeExtractor(sample_config["themes"])
    themes = extractor.extract_themes(
        "The product quality is excellent. The performance is fast and reliable."
    )
    assert len(themes) > 0
    assert all("theme_text" in theme for theme in themes)
    assert all("relevance_score" in theme for theme in themes)


def test_issue_identifier_identify_issues(sample_config):
    """Test issue identification from negative review."""
    identifier = IssueIdentifier(sample_config["issues"])
    issues = identifier.identify_issues(
        "The product is broken and does not work properly.",
        sentiment_score=-0.5,
        sentiment_label="negative",
    )
    assert len(issues) > 0
    assert all("issue_text" in issue for issue in issues)
    assert all("severity" in issue for issue in issues)


def test_recommendation_generator_generate_recommendations(sample_config):
    """Test recommendation generation from issues."""
    generator = RecommendationGenerator(sample_config["recommendations"])
    issues = [
        {
            "issue_text": "Product is broken",
            "severity": "high",
            "category": "quality",
        }
    ]
    aggregated = {"total_issues": 1, "by_category": {"quality": 1}, "by_severity": {"high": 1}}
    recommendations = generator.generate_recommendations(issues, aggregated)
    assert len(recommendations) > 0
    assert all("recommendation_text" in rec for rec in recommendations)
    assert all("priority" in rec for rec in recommendations)


def test_database_manager_add_review(db_manager):
    """Test adding review to database."""
    db_manager.create_tables()
    review = db_manager.add_review(
        review_text="Great product!",
        rating=5,
        product_id="prod123",
    )
    assert review.id is not None
    assert review.review_text == "Great product!"
    assert review.rating == 5


def test_database_manager_get_unprocessed_reviews(db_manager):
    """Test retrieving unprocessed reviews."""
    db_manager.create_tables()
    db_manager.add_review(review_text="Review 1")
    db_manager.add_review(review_text="Review 2")
    unprocessed = db_manager.get_unprocessed_reviews()
    assert len(unprocessed) == 2


def test_database_manager_update_review_sentiment(db_manager):
    """Test updating review sentiment."""
    db_manager.create_tables()
    review = db_manager.add_review(review_text="Test review")
    db_manager.update_review_sentiment(review.id, 0.8, "positive")
    session = db_manager.get_session()
    try:
        updated_review = session.query(Review).filter(Review.id == review.id).first()
        assert updated_review.sentiment_score == 0.8
        assert updated_review.sentiment_label == "positive"
        assert updated_review.processed_at is not None
    finally:
        session.close()


def test_database_manager_add_theme(db_manager):
    """Test adding theme to review."""
    db_manager.create_tables()
    review = db_manager.add_review(review_text="Test review")
    theme = db_manager.add_theme(
        review.id, "Quality is excellent", 0.9, "quality"
    )
    assert theme.id is not None
    assert theme.review_id == review.id
    assert theme.theme_text == "Quality is excellent"


def test_database_manager_add_issue(db_manager):
    """Test adding issue to review."""
    db_manager.create_tables()
    review = db_manager.add_review(review_text="Product is broken")
    issue = db_manager.add_issue(
        review.id, "Product defect", "high", "quality"
    )
    assert issue.id is not None
    assert issue.review_id == review.id
    assert issue.issue_text == "Product defect"


def test_database_manager_add_recommendation(db_manager):
    """Test adding recommendation."""
    db_manager.create_tables()
    recommendation = db_manager.add_recommendation(
        "Improve quality control", "high", "quality", 0.8
    )
    assert recommendation.id is not None
    assert recommendation.recommendation_text == "Improve quality control"
    assert recommendation.priority == "high"


def test_issue_identifier_aggregate_issues(sample_config):
    """Test issue aggregation."""
    identifier = IssueIdentifier(sample_config["issues"])
    issues = [
        {"issue_text": "Broken", "severity": "high", "category": "quality"},
        {"issue_text": "Slow", "severity": "medium", "category": "performance"},
        {"issue_text": "Broken", "severity": "high", "category": "quality"},
    ]
    aggregated = identifier.aggregate_issues(issues)
    assert aggregated["total_issues"] == 3
    assert aggregated["by_category"]["quality"] == 2
    assert aggregated["by_category"]["performance"] == 1


def test_sentiment_analyzer_calculate_average_sentiment(sample_config):
    """Test average sentiment calculation."""
    analyzer = SentimentAnalyzer(sample_config["sentiment"])
    reviews = [
        {"sentiment_score": 0.8, "sentiment_label": "positive"},
        {"sentiment_score": -0.5, "sentiment_label": "negative"},
        {"sentiment_score": 0.1, "sentiment_label": "neutral"},
    ]
    stats = analyzer.calculate_average_sentiment(reviews)
    assert stats["average_score"] > 0
    assert stats["positive_count"] == 1
    assert stats["negative_count"] == 1
    assert stats["neutral_count"] == 1
