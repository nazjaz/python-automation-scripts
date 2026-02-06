"""Unit tests for complaint processing system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Customer, Complaint, Department
from src.complaint_processor import ComplaintProcessor
from src.issue_categorizer import IssueCategorizer
from src.department_router import DepartmentRouter
from src.resolution_tracker import ResolutionTracker
from src.followup_generator import FollowUpGenerator


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "categorization": {
            "category_keywords": {
                "billing": ["charge", "billing", "invoice"],
                "technical": ["error", "bug", "technical"],
            },
        },
        "routing": {
            "default_department": "Customer Service",
            "category_mapping": {
                "billing": "Billing",
                "technical": "Technical Support",
            },
        },
        "processing": {
            "processing_enabled": True,
        },
        "resolution_tracking": {
            "tracking_enabled": True,
        },
        "followups": {
            "followup_delay_hours": 24,
            "followup_templates": {},
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


def test_issue_categorizer_categorize(db_manager, sample_config):
    """Test categorizing complaint."""
    db_manager.create_tables()
    
    categorizer = IssueCategorizer(db_manager, sample_config["categorization"])
    result = categorizer.categorize_complaint("I was charged incorrectly on my invoice")
    
    assert result["category"] == "billing"
    assert "priority" in result
    assert "confidence" in result


def test_department_router_route(db_manager, sample_config):
    """Test routing complaint to department."""
    db_manager.create_tables()
    department = db_manager.add_department("Billing", "BILL")
    customer = db_manager.add_customer("customer1", "Test Customer")
    complaint = db_manager.add_complaint(
        "complaint1", customer.id, "Billing issue", category="billing"
    )
    
    router = DepartmentRouter(db_manager, sample_config["routing"])
    result = router.route_complaint("complaint1", "billing", "medium")
    
    assert "department_name" in result
    assert result["status"] == "assigned"


def test_resolution_tracker_track(db_manager, sample_config):
    """Test tracking resolution."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer")
    complaint = db_manager.add_complaint(
        "complaint1", customer.id, "Test complaint"
    )
    
    tracker = ResolutionTracker(db_manager, sample_config["resolution_tracking"])
    result = tracker.track_resolution("complaint1")
    
    assert "status" in result
    assert "is_resolved" in result


def test_followup_generator_generate(db_manager, sample_config):
    """Test generating follow-up."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer")
    complaint = db_manager.add_complaint(
        "complaint1", customer.id, "Test complaint"
    )
    db_manager.update_complaint_status("complaint1", "resolved")
    db_manager.add_resolution(
        complaint.id, "Issue resolved", "refund", "Agent1"
    )
    
    generator = FollowUpGenerator(db_manager, sample_config["followups"])
    result = generator.generate_followup("complaint1")
    
    assert result.get("success")
    assert "followup_id" in result


def test_complaint_processor_process(db_manager, sample_config):
    """Test processing complaint."""
    db_manager.create_tables()
    db_manager.add_department("Customer Service", "CS")
    
    processor = ComplaintProcessor(db_manager, sample_config["processing"])
    result = processor.process_complaint(
        "complaint1", "customer1", "I have a billing issue with my invoice"
    )
    
    assert result["success"]
    assert "category" in result
    assert "department" in result


def test_database_manager_add_customer(db_manager):
    """Test adding customer."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer", "test@example.com")
    
    assert customer.id is not None
    assert customer.customer_id == "customer1"


def test_database_manager_add_complaint(db_manager):
    """Test adding complaint."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer")
    complaint = db_manager.add_complaint(
        "complaint1", customer.id, "Test complaint", category="billing"
    )
    
    assert complaint.id is not None
    assert complaint.complaint_id == "complaint1"


def test_database_manager_add_department(db_manager):
    """Test adding department."""
    db_manager.create_tables()
    department = db_manager.add_department("Billing", "BILL", "Handles billing issues")
    
    assert department.id is not None
    assert department.department_name == "Billing"


def test_database_manager_add_resolution(db_manager):
    """Test adding resolution."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer")
    complaint = db_manager.add_complaint(
        "complaint1", customer.id, "Test complaint"
    )
    
    resolution = db_manager.add_resolution(
        complaint.id, "Issue resolved", "refund", "Agent1"
    )
    
    assert resolution.id is not None
    assert resolution.resolution_text == "Issue resolved"


def test_issue_categorizer_get_statistics(db_manager, sample_config):
    """Test getting category statistics."""
    db_manager.create_tables()
    customer = db_manager.add_customer("customer1", "Test Customer")
    db_manager.add_complaint("complaint1", customer.id, "Test", category="billing")
    
    categorizer = IssueCategorizer(db_manager, sample_config["categorization"])
    stats = categorizer.get_category_statistics()
    
    assert "total_complaints" in stats
