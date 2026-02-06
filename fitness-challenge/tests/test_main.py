"""Unit tests for fitness challenge system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Participant, Challenge, Goal, ProgressEntry
from src.challenge_generator import ChallengeGenerator
from src.goal_setter import GoalSetter
from src.progress_tracker import ProgressTracker
from src.leaderboard_generator import LeaderboardGenerator
from src.message_sender import MessageSender


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "challenges": {
            "default_duration_days": 7,
            "challenge_templates": {
                "steps": {
                    "name": "Daily Steps Challenge",
                    "unit": "steps",
                    "base_value": 10000,
                    "duration_days": 7,
                },
            },
        },
        "goals": {
            "default_duration_days": 30,
            "goal_templates": {
                "steps": {
                    "name": "Daily Steps Goal",
                    "default_unit": "steps",
                },
            },
            "fitness_levels": {
                "beginner": {
                    "default_goals": [
                        {
                            "type": "steps",
                            "target_value": 5000,
                            "unit": "steps",
                            "duration_days": 30,
                        }
                    ],
                },
            },
        },
        "progress": {
            "tracking_enabled": True,
        },
        "leaderboard": {
            "update_frequency": "daily",
        },
        "messages": {
            "email_enabled": False,
            "sms_enabled": False,
            "message_templates": {
                "motivational": {
                    "subject": "Keep up the great work!",
                    "content": "Hi {name}!",
                },
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


def test_challenge_generator_generate_challenge(db_manager, sample_config):
    """Test generating a challenge."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com", fitness_level="beginner")
    
    generator = ChallengeGenerator(db_manager, sample_config["challenges"])
    challenge = generator.generate_challenge(participant.id, "steps")
    
    assert challenge is not None
    assert "challenge_name" in challenge
    assert challenge["challenge_type"] == "steps"


def test_goal_setter_set_goal(db_manager, sample_config):
    """Test setting a goal."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com", fitness_level="beginner")
    
    goal_setter = GoalSetter(db_manager, sample_config["goals"])
    goal = goal_setter.set_goal(participant.id, "steps", 10000, "steps")
    
    assert goal is not None
    assert goal["goal_type"] == "steps"
    assert goal["target_value"] == 10000


def test_goal_setter_set_personalized_goals(db_manager, sample_config):
    """Test setting personalized goals."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com", fitness_level="beginner")
    
    goal_setter = GoalSetter(db_manager, sample_config["goals"])
    goals = goal_setter.set_personalized_goals(participant.id)
    
    assert len(goals) > 0


def test_progress_tracker_record_progress(db_manager, sample_config):
    """Test recording progress."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    tracker = ProgressTracker(db_manager, sample_config["progress"])
    progress = tracker.record_progress(participant.id, 5000, "steps")
    
    assert progress is not None
    assert progress["value"] == 5000
    assert progress["unit"] == "steps"


def test_progress_tracker_get_progress_summary(db_manager, sample_config):
    """Test getting progress summary."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    tracker = ProgressTracker(db_manager, sample_config["progress"])
    tracker.record_progress(participant.id, 5000, "steps")
    tracker.record_progress(participant.id, 6000, "steps")
    
    summary = tracker.get_progress_summary(participant.id, days=7)
    assert summary["total_value"] == 11000
    assert summary["entry_count"] == 2


def test_leaderboard_generator_generate_leaderboard(db_manager, sample_config):
    """Test generating leaderboard."""
    db_manager.create_tables()
    participant1 = db_manager.add_participant("User 1", "user1@example.com")
    participant2 = db_manager.add_participant("User 2", "user2@example.com")
    
    tracker = ProgressTracker(db_manager, sample_config["progress"])
    tracker.record_progress(participant1.id, 10000, "steps")
    tracker.record_progress(participant2.id, 5000, "steps")
    
    generator = LeaderboardGenerator(db_manager, sample_config["leaderboard"])
    leaderboard = generator.generate_leaderboard()
    
    assert len(leaderboard) == 2
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["score"] >= leaderboard[1]["score"]


def test_message_sender_send_motivational_message(db_manager, sample_config):
    """Test sending motivational message."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    sender = MessageSender(db_manager, sample_config["messages"])
    message = sender.send_motivational_message(participant.id)
    
    assert message is not None
    assert message["message_type"] == "motivational"
    assert "content" in message


def test_database_manager_add_participant(db_manager):
    """Test adding participant."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com", fitness_level="beginner")
    
    assert participant.id is not None
    assert participant.name == "Test User"
    assert participant.email == "test@example.com"


def test_database_manager_create_challenge(db_manager):
    """Test creating challenge."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    
    challenge = db_manager.create_challenge(
        participant.id,
        "Steps Challenge",
        "steps",
        start_date,
        end_date,
        target_value=10000,
        target_unit="steps",
    )
    
    assert challenge.id is not None
    assert challenge.challenge_name == "Steps Challenge"


def test_database_manager_create_goal(db_manager):
    """Test creating goal."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    goal = db_manager.create_goal(
        participant.id,
        "Daily Steps",
        "steps",
        10000,
        "steps",
    )
    
    assert goal.id is not None
    assert goal.goal_name == "Daily Steps"
    assert goal.target_value == 10000


def test_database_manager_add_progress_entry(db_manager):
    """Test adding progress entry."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    progress = db_manager.add_progress_entry(
        participant.id,
        5000,
        "steps",
    )
    
    assert progress.id is not None
    assert progress.value == 5000
    assert progress.unit == "steps"


def test_challenge_generator_get_challenge_progress(db_manager, sample_config):
    """Test getting challenge progress."""
    db_manager.create_tables()
    participant = db_manager.add_participant("Test User", "test@example.com")
    
    generator = ChallengeGenerator(db_manager, sample_config["challenges"])
    challenge = generator.generate_challenge(participant.id, "steps")
    
    tracker = ProgressTracker(db_manager, sample_config["progress"])
    tracker.record_progress(participant.id, 5000, "steps", challenge_id=challenge["id"])
    
    progress = generator.get_challenge_progress(challenge["id"])
    assert progress["current_value"] == 5000
