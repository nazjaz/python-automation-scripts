"""Unit tests for learning recommendation system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, User, Course, Enrollment
from src.behavior_analyzer import BehaviorAnalyzer
from src.completion_analyzer import CompletionAnalyzer
from src.difficulty_adapter import DifficultyAdapter
from src.objective_tracker import ObjectiveTracker
from src.recommendation_generator import RecommendationGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "behavior_analysis": {
            "analysis_enabled": True,
        },
        "completion_analysis": {
            "analysis_enabled": True,
        },
        "difficulty_adaptation": {
            "score_thresholds": {
                "beginner": 0.7,
                "intermediate": 0.75,
                "advanced": 0.8,
            },
        },
        "objective_tracking": {
            "tracking_enabled": True,
        },
        "recommendations": {
            "min_confidence": 0.5,
            "max_recommendations": 10,
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


def test_behavior_analyzer_analyze_behavior(db_manager, sample_config):
    """Test analyzing user behavior."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User")
    
    db_manager.add_user_behavior(user.id, "view", '{"page": "course1"}')
    db_manager.add_user_behavior(user.id, "click", '{"button": "enroll"}')
    
    analyzer = BehaviorAnalyzer(db_manager, sample_config["behavior_analysis"])
    analysis = analyzer.analyze_user_behavior(user.id)
    
    assert analysis["total_behaviors"] == 2
    assert "behavior_types" in analysis


def test_completion_analyzer_analyze_rate(db_manager, sample_config):
    """Test analyzing completion rate."""
    db_manager.create_tables()
    course = db_manager.add_course("course1", "Test Course")
    user = db_manager.add_user("user1")
    
    enrollment = db_manager.add_enrollment(user.id, course.id)
    db_manager.update_enrollment_completion(enrollment.id, 1.0, completed=True)
    
    analyzer = CompletionAnalyzer(db_manager, sample_config["completion_analysis"])
    rate = analyzer.analyze_completion_rate(course.id)
    
    assert rate["completion_rate"] == 100.0
    assert rate["completed_enrollments"] == 1


def test_difficulty_adapter_adapt_difficulty(db_manager, sample_config):
    """Test adapting difficulty."""
    db_manager.create_tables()
    user = db_manager.add_user("user1")
    course = db_manager.add_course("course1", "Test Course", difficulty_level="beginner")
    
    enrollment = db_manager.add_enrollment(user.id, course.id)
    db_manager.update_enrollment_completion(enrollment.id, 0.8)
    
    adapter = DifficultyAdapter(db_manager, sample_config["difficulty_adaptation"])
    rec = adapter.adapt_difficulty(user.id, course.id)
    
    assert "recommended_difficulty" in rec
    assert "confidence" in rec


def test_objective_tracker_track_progress(db_manager, sample_config):
    """Test tracking objective progress."""
    db_manager.create_tables()
    user = db_manager.add_user("user1")
    objective = db_manager.add_learning_objective(
        user.id, "Learn Python", "skill", target_skill="programming"
    )
    
    tracker = ObjectiveTracker(db_manager, sample_config["objective_tracking"])
    progress = tracker.track_objective_progress(objective.id)
    
    assert "total_progress" in progress
    assert progress["objective_name"] == "Learn Python"


def test_recommendation_generator_generate(db_manager, sample_config):
    """Test generating recommendations."""
    db_manager.create_tables()
    user = db_manager.add_user("user1")
    course = db_manager.add_course("course1", "Test Course", category="programming")
    
    db_manager.add_user_behavior(user.id, "view", '{"course": "course1"}')
    
    generator = RecommendationGenerator(db_manager, sample_config["recommendations"])
    recommendations = generator.generate_recommendations(user.id, limit=5)
    
    assert isinstance(recommendations, list)


def test_database_manager_add_user(db_manager):
    """Test adding user."""
    db_manager.create_tables()
    user = db_manager.add_user("user1", "Test User", "test@example.com")
    
    assert user.id is not None
    assert user.user_id == "user1"


def test_database_manager_add_course(db_manager):
    """Test adding course."""
    db_manager.create_tables()
    course = db_manager.add_course(
        "course1", "Test Course", difficulty_level="beginner"
    )
    
    assert course.id is not None
    assert course.course_name == "Test Course"


def test_database_manager_add_enrollment(db_manager):
    """Test adding enrollment."""
    db_manager.create_tables()
    user = db_manager.add_user("user1")
    course = db_manager.add_course("course1", "Test Course")
    
    enrollment = db_manager.add_enrollment(user.id, course.id)
    
    assert enrollment.id is not None
    assert enrollment.user_id == user.id


def test_behavior_analyzer_get_learning_style(db_manager, sample_config):
    """Test getting learning style."""
    db_manager.create_tables()
    user = db_manager.add_user("user1")
    
    for i in range(10):
        db_manager.add_user_behavior(user.id, "search", '{"query": "python"}')
    
    analyzer = BehaviorAnalyzer(db_manager, sample_config["behavior_analysis"])
    style = analyzer.get_learning_style(user.id)
    
    assert "learning_style" in style
    assert "confidence" in style
