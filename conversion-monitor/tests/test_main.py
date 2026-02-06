"""Unit tests for conversion monitoring system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Website, Session, Event, ConversionGoal
from src.event_processor import EventProcessor
from src.conversion_monitor import ConversionMonitor
from src.journey_tracker import JourneyTracker
from src.dropoff_identifier import DropOffIdentifier
from src.optimization_recommender import OptimizationRecommender


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "monitoring": {
            "time_window_hours": 24,
        },
        "events": {
            "event_processing_enabled": True,
        },
        "journey_tracking": {
            "track_enabled": True,
        },
        "dropoff_detection": {
            "min_dropoff_rate": 0.1,
        },
        "recommendations": {
            "recommendation_templates": {},
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


def test_conversion_monitor_calculate_rate(db_manager, sample_config):
    """Test calculating conversion rate."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com", "Example Site")
    goal = db_manager.add_conversion_goal(
        website.id, "Purchase", "purchase", target_url="/checkout/complete"
    )
    
    start_time = datetime.utcnow() - timedelta(hours=1)
    session1 = db_manager.add_session(website.id, "session1", start_time)
    session2 = db_manager.add_session(website.id, "session2", start_time)
    
    db_manager.update_session("session1", converted="true", conversion_goal_id=goal.id)
    
    monitor = ConversionMonitor(db_manager, sample_config["monitoring"])
    rate = monitor.calculate_conversion_rate(website.id, hours=2)
    
    assert rate["conversion_rate"] == 50.0
    assert rate["total_sessions"] == 2
    assert rate["converted_sessions"] == 1


def test_journey_tracker_track_journey(db_manager, sample_config):
    """Test tracking user journey."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    session = db_manager.add_session(website.id, "session1", datetime.utcnow())
    
    db_manager.add_event(session.id, "pageview", datetime.utcnow(), page_url="/home")
    db_manager.add_event(session.id, "pageview", datetime.utcnow(), page_url="/products")
    
    tracker = JourneyTracker(db_manager, sample_config["journey_tracking"])
    journey = tracker.track_journey(session.id)
    
    assert journey["total_steps"] == 2
    assert len(journey["journey_steps"]) == 2


def test_dropoff_identifier_identify_dropoffs(db_manager, sample_config):
    """Test identifying drop-offs."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    
    for i in range(10):
        session = db_manager.add_session(website.id, f"session{i}", datetime.utcnow())
        db_manager.add_event(session.id, "pageview", datetime.utcnow(), page_url="/home")
        if i < 5:
            db_manager.add_event(session.id, "pageview", datetime.utcnow(), page_url="/products")
    
    identifier = DropOffIdentifier(db_manager, sample_config["dropoff_detection"])
    dropoffs = identifier.identify_dropoffs(website.id)
    
    assert len(dropoffs) > 0


def test_optimization_recommender_generate_recommendations(db_manager, sample_config):
    """Test generating recommendations."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    
    db_manager.add_dropoff_point(website.id, 0.5, 100, 50)
    
    recommender = OptimizationRecommender(db_manager, sample_config["recommendations"])
    recommendations = recommender.generate_recommendations(website.id)
    
    assert len(recommendations) > 0


def test_event_processor_process_event(db_manager, sample_config):
    """Test processing event."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    
    processor = EventProcessor(db_manager, sample_config["events"])
    result = processor.process_event(
        website_id=website.id,
        session_id="session1",
        event_type="pageview",
        timestamp=datetime.utcnow(),
        page_url="/home",
    )
    
    assert result["success"]
    assert "event_id" in result


def test_database_manager_add_website(db_manager):
    """Test adding website."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com", "Example Site")
    
    assert website.id is not None
    assert website.domain == "example.com"


def test_database_manager_add_conversion_goal(db_manager):
    """Test adding conversion goal."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    goal = db_manager.add_conversion_goal(
        website.id, "Purchase", "purchase", target_url="/checkout/complete"
    )
    
    assert goal.id is not None
    assert goal.goal_name == "Purchase"


def test_database_manager_add_session(db_manager):
    """Test adding session."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    start_time = datetime.utcnow()
    session = db_manager.add_session(website.id, "session1", start_time)
    
    assert session.id is not None
    assert session.session_id == "session1"


def test_database_manager_add_event(db_manager):
    """Test adding event."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    session = db_manager.add_session(website.id, "session1", datetime.utcnow())
    
    event = db_manager.add_event(
        session.id, "pageview", datetime.utcnow(), page_url="/home"
    )
    
    assert event.id is not None
    assert event.event_type == "pageview"


def test_conversion_monitor_get_trends(db_manager, sample_config):
    """Test getting conversion trends."""
    db_manager.create_tables()
    website = db_manager.add_website("example.com")
    
    monitor = ConversionMonitor(db_manager, sample_config["monitoring"])
    trends = monitor.get_conversion_trends(website.id, days=7)
    
    assert "average_rate" in trends
    assert "trend" in trends
