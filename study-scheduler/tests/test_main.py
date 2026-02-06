"""Test suite for study scheduler system."""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Course,
    Exam,
    StudySession,
    LearningPreference,
)
from src.schedule_generator import ScheduleGenerator
from src.progress_tracker import ProgressTracker
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
        "scheduling": {
            "default_study_hours_per_day": 4.0,
            "study_session_duration_minutes": 90,
            "break_duration_minutes": 15,
            "preferred_study_times": ["09:00", "14:00", "19:00"],
            "days_before_exam_buffer": 2,
        },
        "progress_tracking": {
            "completion_threshold": 0.8,
            "adjustment_threshold": 0.6,
        },
        "recommendations": {
            "enabled": True,
        },
    }


@pytest.fixture
def sample_course(test_db):
    """Create sample course for testing."""
    course = test_db.add_course(
        name="Test Course",
        code="TEST101",
        difficulty="medium",
        priority="high",
        total_hours_required=40.0,
    )
    return course


@pytest.fixture
def sample_exam(test_db, sample_course):
    """Create sample exam for testing."""
    exam = test_db.add_exam(
        course_id=sample_course.id,
        name="Midterm Exam",
        exam_date=date.today() + timedelta(days=30),
        preparation_hours_required=20.0,
    )
    return exam


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            courses = session.query(Course).all()
            assert len(courses) == 0
        finally:
            session.close()

    def test_add_course(self, test_db):
        """Test adding course."""
        course = test_db.add_course(
            name="Test Course",
            code="TEST101",
            difficulty="hard",
            priority="high",
        )
        assert course.id is not None
        assert course.name == "Test Course"
        assert course.code == "TEST101"

    def test_add_exam(self, test_db, sample_course):
        """Test adding exam."""
        exam = test_db.add_exam(
            course_id=sample_course.id,
            name="Final Exam",
            exam_date=date.today() + timedelta(days=60),
        )
        assert exam.id is not None
        assert exam.name == "Final Exam"

    def test_add_study_session(self, test_db, sample_course):
        """Test adding study session."""
        session = test_db.add_study_session(
            course_id=sample_course.id,
            session_date=date.today(),
            start_time="09:00",
            end_time="10:30",
            duration_minutes=90,
            completion_status="scheduled",
        )
        assert session.id is not None
        assert session.course_id == sample_course.id


class TestScheduleGenerator:
    """Test schedule generator functionality."""

    def test_generate_schedule(self, test_db, sample_config, sample_course, sample_exam):
        """Test schedule generation."""
        generator = ScheduleGenerator(test_db, sample_config)
        schedule = generator.generate_schedule(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            course_ids=[sample_course.id],
        )

        assert isinstance(schedule, list)

    def test_prioritize_courses(self, test_db, sample_config):
        """Test course prioritization."""
        course1 = test_db.add_course(
            name="Course 1",
            code="C1",
            priority="high",
            total_hours_required=20.0,
        )
        course2 = test_db.add_course(
            name="Course 2",
            code="C2",
            priority="low",
            total_hours_required=10.0,
        )

        exam = test_db.add_exam(
            course_id=course1.id,
            name="Exam 1",
            exam_date=date.today() + timedelta(days=5),
        )

        generator = ScheduleGenerator(test_db, sample_config)
        prioritized = generator._prioritize_courses(
            [course1, course2],
            [exam],
            date.today(),
        )

        assert len(prioritized) == 2
        assert prioritized[0].id == course1.id


class TestProgressTracker:
    """Test progress tracker functionality."""

    def test_record_session_progress(self, test_db, sample_config, sample_course):
        """Test recording session progress."""
        session = test_db.add_study_session(
            course_id=sample_course.id,
            session_date=date.today(),
            duration_minutes=90,
            completion_status="scheduled",
        )

        tracker = ProgressTracker(test_db, sample_config)
        progress = tracker.record_session_progress(
            session_id=session.id,
            hours_studied=1.5,
            completion_percentage=1.0,
        )

        assert progress.id is not None
        assert progress.completion_percentage == 1.0

    def test_get_completion_rate(self, test_db, sample_config, sample_course):
        """Test completion rate calculation."""
        for i in range(5):
            session = test_db.add_study_session(
                course_id=sample_course.id,
                session_date=date.today() - timedelta(days=i),
                duration_minutes=90,
                completion_status="completed" if i < 3 else "scheduled",
            )

        tracker = ProgressTracker(test_db, sample_config)
        rate = tracker.get_completion_rate(course_id=sample_course.id, days=7)

        assert 0.0 <= rate <= 1.0

    def test_get_daily_progress(self, test_db, sample_config, sample_course):
        """Test daily progress retrieval."""
        session = test_db.add_study_session(
            course_id=sample_course.id,
            session_date=date.today(),
            duration_minutes=90,
            completion_status="completed",
        )

        tracker = ProgressTracker(test_db, sample_config)
        daily = tracker.get_daily_progress(course_id=sample_course.id)

        assert daily["scheduled_sessions"] == 1
        assert daily["completed_sessions"] == 1


class TestRecommendationEngine:
    """Test recommendation engine functionality."""

    def test_generate_recommendations(self, test_db, sample_config, sample_course):
        """Test recommendation generation."""
        for i in range(5):
            session = test_db.add_study_session(
                course_id=sample_course.id,
                session_date=date.today() - timedelta(days=i),
                duration_minutes=90,
                completion_status="incomplete" if i < 3 else "completed",
            )

        engine = RecommendationEngine(test_db, sample_config)
        recommendations = engine.generate_recommendations(course_id=sample_course.id, days=7)

        assert isinstance(recommendations, list)

    def test_check_exam_preparation(self, test_db, sample_config, sample_course, sample_exam):
        """Test exam preparation checking."""
        engine = RecommendationEngine(test_db, sample_config)
        recommendations = engine._check_exam_preparation(course_id=sample_course.id)

        assert isinstance(recommendations, list)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "scheduling" in config
            assert "learning_preferences" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
