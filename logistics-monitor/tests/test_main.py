"""Unit tests for logistics monitoring system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.config import load_config, get_settings
from src.database import DatabaseManager, Supplier, Shipment, Route, Delay
from src.shipment_tracker import ShipmentTracker
from src.delay_predictor import DelayPredictor
from src.route_optimizer import RouteOptimizer
from src.logistics_monitor import LogisticsMonitor


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "tracking": {
            "tracking_enabled": True,
        },
        "delay_prediction": {
            "delay_factors": {
                "weather": 0.3,
                "traffic": 0.2,
            },
        },
        "route_optimization": {
            "optimization_factors": {
                "distance": 0.4,
                "time": 0.4,
                "cost": 0.2,
            },
        },
        "monitoring": {
            "monitoring_enabled": True,
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


def test_shipment_tracker_track_shipment(db_manager, sample_config):
    """Test tracking shipment."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    tracker = ShipmentTracker(db_manager, sample_config["tracking"])
    tracking_info = tracker.track_shipment("shipment1")
    
    assert tracking_info["shipment_id"] == "shipment1"
    assert "status" in tracking_info


def test_delay_predictor_predict_delay(db_manager, sample_config):
    """Test predicting delay."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    predictor = DelayPredictor(db_manager, sample_config["delay_prediction"])
    prediction = predictor.predict_delay("shipment1", "weather", "Heavy rain")
    
    assert "predicted_delay_hours" in prediction
    assert prediction["delay_type"] == "weather"


def test_route_optimizer_optimize_route(db_manager, sample_config):
    """Test optimizing route."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    db_manager.add_route(
        shipment.id, "New York", "Los Angeles", 3944, 65.7, cost=1972
    )
    
    optimizer = RouteOptimizer(db_manager, sample_config["route_optimization"])
    optimization = optimizer.optimize_route("shipment1")
    
    assert "optimized_route_id" in optimization
    assert "savings" in optimization


def test_logistics_monitor_monitor(db_manager, sample_config):
    """Test monitoring logistics."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    db_manager.update_shipment_status("shipment1", "delivered", actual_delivery=datetime.utcnow())
    
    monitor = LogisticsMonitor(db_manager, sample_config["monitoring"])
    summary = monitor.monitor_logistics(days=7)
    
    assert "total_shipments" in summary
    assert "on_time_percentage" in summary


def test_database_manager_add_supplier(db_manager):
    """Test adding supplier."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier", "New York")
    
    assert supplier.id is not None
    assert supplier.supplier_id == "supplier1"


def test_database_manager_add_shipment(db_manager):
    """Test adding shipment."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    assert shipment.id is not None
    assert shipment.shipment_id == "shipment1"


def test_database_manager_add_route(db_manager):
    """Test adding route."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    route = db_manager.add_route(
        shipment.id, "New York", "Los Angeles", 3944, 65.7
    )
    
    assert route.id is not None
    assert route.distance_km == 3944


def test_database_manager_add_delay(db_manager):
    """Test adding delay."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles"
    )
    
    delay = db_manager.add_delay(
        shipment.id, "weather", 4.0, "Heavy rain", severity="medium"
    )
    
    assert delay.id is not None
    assert delay.predicted_delay_hours == 4.0


def test_delay_predictor_analyze_risk(db_manager, sample_config):
    """Test analyzing delay risk."""
    db_manager.create_tables()
    supplier = db_manager.add_supplier("supplier1", "Test Supplier")
    shipment = db_manager.add_shipment(
        "shipment1", supplier.id, "New York", "Los Angeles", priority="urgent"
    )
    
    predictor = DelayPredictor(db_manager, sample_config["delay_prediction"])
    risk = predictor.analyze_delay_risk("shipment1")
    
    assert "risk_score" in risk
    assert "risk_level" in risk
