"""Unit tests for content recommendation system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, User, Content, UserPreference
from src.preference_analyzer import PreferenceAnalyzer
from src.history_analyzer import HistoryAnalyzer
from src.engagement_analyzer import EngagementAnalyzer
from src.recommendation_generator import RecommendationGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "preference_analysis": {
            "analysis_enabled": True,
        },
        "history_analysis": {
            "analysis_enabled": True,
        },
        "engagement_analysis": {
            "analysis_enabled": True,
        },
        "recommendation": {
            "recommendation_weights": {
                "preference": 0.3,
                "history": 0.4,
                "engagement": 0.3,
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


def test_preference_analyzer_analyze(db_manager, sample_config):
    """Test analyzing preferences."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    db_manager.add_user_preference(user.id, "category", "technology", weight=1.5)
    
    analyzer = PreferenceAnalyzer(db_manager, sample_config["preference_analysis"])
    result = analyzer.analyze_preferences("user1")
    
    assert result["user_id"] == "user1"
    assert result["total_preferences"] > 0


def test_history_analyzer_analyze(db_manager, sample_config):
    """Test analyzing viewing history."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    content = db_manager.add_content("content1", "Test Content", "video", category="tech")
    db_manager.add_viewing_history(user.id, content.id, watch_duration_minutes=30)
    
    analyzer = HistoryAnalyzer(db_manager, sample_config["history_analysis"])
    result = analyzer.analyze_history("user1")
    
    assert result["user_id"] == "user1"
    assert "recent_views" in result


def test_engagement_analyzer_analyze(db_manager, sample_config):
    """Test analyzing engagement."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    
    analyzer = EngagementAnalyzer(db_manager, sample_config["engagement_analysis"])
    result = analyzer.analyze_engagement("user1")
    
    assert result["user_id"] == "user1"
    assert "total_engagement" in result


def test_recommendation_generator_generate(db_manager, sample_config):
    """Test generating recommendations."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    content = db_manager.add_content("content1", "Test Content", "video", category="tech")
    
    generator = RecommendationGenerator(db_manager, sample_config["recommendation"])
    result = generator.generate_recommendations("user1", limit=5)
    
    assert result.get("success")
    assert "recommendations_created" in result


def test_database_manager_add_user(db_manager):
    """Test adding user."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User", "test@example.com")
    
    assert user.id is not None
    assert user.user_id == "user1"


def test_database_manager_add_content(db_manager):
    """Test adding content."""
    db_manager.create_tables()
    content = db_manager.add_content("content1", "Test Content", "video", category="tech")
    
    assert content.id is not None
    assert content.content_id == "content1"


def test_database_manager_add_user_preference(db_manager):
    """Test adding user preference."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    preference = db_manager.add_user_preference(user.id, "category", "technology", weight=1.5)
    
    assert preference.id is not None
    assert preference.preference_value == "technology"


def test_database_manager_add_viewing_history(db_manager):
    """Test adding viewing history."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    content = db_manager.add_content("content1", "Test Content", "video")
    history = db_manager.add_viewing_history(user.id, content.id, watch_duration_minutes=30)
    
    assert history.id is not None
    assert history.watch_duration_minutes == 30


def test_database_manager_add_recommendation(db_manager):
    """Test adding recommendation."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    content = db_manager.add_content("content1", "Test Content", "video")
    recommendation = db_manager.add_recommendation(
        user.id, content.id, 0.85, "Matches preferences", "preference_based"
    )
    
    assert recommendation.id is not None
    assert recommendation.recommendation_score == 0.85


def test_preference_analyzer_get_score(db_manager, sample_config):
    """Test getting preference score."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    db_manager.add_user_preference(user.id, "category", "technology", weight=1.5)
    
    analyzer = PreferenceAnalyzer(db_manager, sample_config["preference_analysis"])
    score = analyzer.get_preference_score("user1", "technology", "video", "tech,programming")
    
    assert 0.0 <= score <= 1.0
